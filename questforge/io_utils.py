"""业务数据 I/O:xlsx 加载、Fragment 构造、关键字抽取、样例诉求解析。

所有函数与领域无关;领域词汇由 Stage 1 产出的 glossary 注入下游阶段使用。
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .input_spec import SampleFileConfig

log = logging.getLogger("questforge.io")


# ========== 数据类 ==========
@dataclass
class KBFragment:
    frag_id: str
    asset_id: str
    row_no: int
    key_text: str
    full_row: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


# ========== xlsx 加载 ==========
def load_kb(path: Path, sheet: str) -> pd.DataFrame:
    """稳健加载 xlsx,统一 str 类型,空值填 ''."""
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl", dtype=str)
    df = df.fillna("")
    return df


# ========== Fragment / 索引 ==========
def _compose_key_text(row: pd.Series, key_fields: list[str]) -> str:
    parts = []
    for f in key_fields:
        if f in row.index:
            val = str(row[f]).strip()
            if val:
                parts.append(val)
    return " | ".join(parts)


def build_fragments(
    df: pd.DataFrame,
    *,
    asset_id: str,
    key_fields: list[str],
    metadata_extractor=None,
) -> list[KBFragment]:
    """逐行构造 KBFragment。frag_id 形如 FRAG-001-2345(asset 尾三位 + row_no)。"""
    tail = asset_id.split("-")[-1]
    frags: list[KBFragment] = []
    for idx, row in df.iterrows():
        key_text = _compose_key_text(row, key_fields)
        if not key_text:
            continue
        meta = metadata_extractor(row) if metadata_extractor else {}
        frags.append(
            KBFragment(
                frag_id=f"FRAG-{tail}-{idx:04d}",
                asset_id=asset_id,
                row_no=int(idx),
                key_text=key_text,
                full_row=row.to_dict(),
                metadata=meta,
            )
        )
    return frags


# ========== 关键字抽取(领域无关启发式) ==========
_GENERIC_WORDS = {
    "问题", "方面", "情况", "工作", "相关", "有关", "以及", "进行",
    "内容", "要求", "规定", "制度", "基本", "具体", "什么", "怎么",
    "如何", "是否", "能否", "为何",
}

_CH_RE = re.compile(r"[\u4e00-\u9fa5]+")
_SPLIT_RE = re.compile(r"[,。;;,\.\s、《》【】\(\)\[\]():|/\-—]+")


def _jieba_words(text: str) -> list[str]:
    """可选走 jieba 分词;不可用时用标点/空格切段。"""
    try:
        import jieba  # type: ignore

        jieba.setLogLevel(60)
        return [w for w in jieba.lcut(text) if w.strip()]
    except Exception:
        return [seg for seg in _SPLIT_RE.split(text) if seg]


def extract_local_keywords(
    text: str,
    *,
    min_len: int = 4,
    max_len: int = 8,
    top_k: int = 3,
    domain_hints: set[str] | None = None,
) -> list[str]:
    """
    词级启发式 4-8 字短语提取(领域无关):
    - jieba 分词(不可用则切段)
    - 单词 + 相邻 2-3 词合并,仅保留 4-8 字中文
    - 过滤泛词
    - 排序:若传入 `domain_hints`,命中者优先;否则仅按词长+频率
    """
    if not text:
        return []
    words = _jieba_words(text)
    candidates: list[str] = []

    for w in words:
        if min_len <= len(w) <= max_len and _CH_RE.fullmatch(w) and w not in _GENERIC_WORDS:
            candidates.append(w)
    for n in (2, 3):
        for i in range(len(words) - n + 1):
            chunk = "".join(words[i : i + n])
            if min_len <= len(chunk) <= max_len and _CH_RE.fullmatch(chunk):
                if chunk in _GENERIC_WORDS:
                    continue
                candidates.append(chunk)

    if not candidates:
        return []

    freq = Counter(candidates)
    hints = domain_hints or set()

    def _score(ph: str) -> tuple[int, int, int]:
        hit = int(any(h and h in ph for h in hints))
        return (hit, len(ph), freq[ph])

    uniq = sorted(set(candidates), key=_score, reverse=True)
    return uniq[:top_k]


# ========== 倒排索引 ==========
def build_inverted_index(
    fragments: list[KBFragment],
    *,
    per_frag_top_k: int = 5,
    domain_hints: set[str] | None = None,
) -> dict[str, list[str]]:
    """关键字 → [frag_id]。用本地启发式抽词;可传入领域提示词优化排序。"""
    index: dict[str, list[str]] = {}
    for frag in fragments:
        kws = extract_local_keywords(frag.key_text, top_k=per_frag_top_k, domain_hints=domain_hints)
        for kw in kws:
            index.setdefault(kw, []).append(frag.frag_id)
    return index


def search_fragments(
    index: dict[str, list[str]], fragments_by_id: dict[str, KBFragment], query: str
) -> list[str]:
    """倒排索引粗搜:对 query 内的所有候选短语取并集。"""
    hits: list[str] = []
    for kw in extract_local_keywords(query, top_k=10):
        hits.extend(index.get(kw, []))
    seen = set()
    ordered = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            ordered.append(h)
    return ordered


# ========== 样例数据解析(通用,接收 SampleFileConfig 列表) ==========
def load_sample_usecases(samples: list[SampleFileConfig]) -> dict[str, list[dict[str, Any]]]:
    """根据用户声明的 SampleFileConfig 列表加载样例。

    - 若 sample 提供 `category_col + content_col`:按 category 分组,每组含 {content, ...原列}
    - 若 sample 提供 `columns` 列表:每行作为完整 dict 加入 `label` 分组
    - 两种都没给:按整表的所有列加入 `label` 分组
    """
    result: dict[str, list[dict[str, Any]]] = {}
    for s in samples:
        try:
            df = load_kb(s.file, s.sheet)
        except Exception as e:
            log.warning("加载样例文件失败 %s:%s", s.file, e)
            continue

        if s.category_col and s.content_col:
            for cat, sub in df.groupby(s.category_col):
                items = [
                    {**{c: str(r.get(c, "")).strip() for c in df.columns}, "content": str(r[s.content_col]).strip()}
                    for _, r in sub.iterrows()
                    if str(r.get(s.content_col, "")).strip()
                ]
                if items:
                    result[str(cat).strip() or s.label] = items
        else:
            cols = s.columns or list(df.columns)
            items = []
            for _, r in df.iterrows():
                row = {col: str(r.get(col, "")).strip() for col in cols}
                if any(v for v in row.values()):
                    items.append(row)
            if items:
                result[s.label] = items
    return result


# ========== KB 资产卡片 ==========
def summarize_kb(asset: dict[str, Any], max_sample_rows: int = 3) -> dict[str, Any]:
    """为 Stage 1 产出"资产卡片"信息:行数 + 列名 + 前 N 行样本。

    调用方应预先扫描目录并传入 dict,含 id/name/file(Path)/sheet/key_fields/authority/category。
    """
    path = asset["file"]
    sheet = asset["sheet"]
    df = load_kb(path, sheet)
    sample_rows = df.head(max_sample_rows).to_dict(orient="records")
    for row in sample_rows:
        for k, v in list(row.items()):
            if isinstance(v, str) and len(v) > 200:
                row[k] = v[:200] + "…"
    return {
        "id": asset["id"],
        "name": asset["name"],
        "file": Path(path).name,
        "sheet": sheet,
        "rows": int(len(df)),
        "key_fields": list(asset.get("key_fields", [])),
        "authority": asset.get("authority", "未知"),
        "category": asset.get("category", "未分类"),
        "columns": list(df.columns),
        "sample_rows": sample_rows,
    }
