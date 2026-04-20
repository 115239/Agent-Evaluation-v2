"""业务数据 I/O：xlsx 加载、Fragment 构造、关键字抽取、样例诉求解析。"""
from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from . import config

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
    """稳健加载 xlsx，统一 str 类型，空值填 ''."""
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
    """逐行构造 KBFragment。frag_id 形如 FRAG-001-2345（asset 尾三位 + row_no）。"""
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


# ========== 关键字抽取（本地启发式，不调 LLM） ==========
# 领域核心词：命中其一即认为贴合纪检场景
_DOMAIN_CORE_WORDS = [
    "纪检", "监察", "反腐", "廉政", "执纪", "违纪", "监督", "巡视",
    "巡察", "问责", "处分", "党风", "党纪", "八项规定", "四种形态",
    "定性", "量纪", "腐败", "违规", "作风", "廉洁",
]

# 常见"泛词"忽略
_GENERIC_WORDS = {
    "问题", "方面", "情况", "工作", "相关", "有关", "以及", "进行",
    "内容", "要求", "规定", "制度", "基本", "具体", "什么", "怎么",
    "如何", "是否", "能否", "为何",
}

_CH_RE = re.compile(r"[\u4e00-\u9fa5]+")
_SPLIT_RE = re.compile(r"[，。；;,\.\s、《》【】\(\)\[\]（）:：\|/\-—]+")


def _jieba_words(text: str) -> list[str]:
    """可选走 jieba 分词；不可用时用标点/空格切段再按 2-6 字窗滑动。"""
    try:
        import jieba  # type: ignore

        jieba.setLogLevel(60)  # 屏蔽 jieba 启动日志
        return [w for w in jieba.lcut(text) if w.strip()]
    except Exception:
        return [seg for seg in _SPLIT_RE.split(text) if seg]


def extract_local_keywords(
    text: str, *, min_len: int = 4, max_len: int = 8, top_k: int = 3
) -> list[str]:
    """
    词级启发式 4-8 字短语提取：
    - 优先用 jieba 分词（不可用则按标点/空格切段）
    - 对相邻词做 2-3 合并（产生完整词边界的短语），仅保留 4-8 字长度
    - 过滤泛词；按"是否包含领域核心词"和词频排序
    - 只保留完整中文短语（不跨空格/标点边界）
    """
    if not text:
        return []
    words = _jieba_words(text)
    candidates: list[str] = []

    # 单词候选
    for w in words:
        if min_len <= len(w) <= max_len and _CH_RE.fullmatch(w) and w not in _GENERIC_WORDS:
            candidates.append(w)

    # 相邻 2-3 词合并
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

    def _score(ph: str) -> tuple[int, int, int]:
        in_core = any(w in ph for w in _DOMAIN_CORE_WORDS)
        return (int(in_core), len(ph), freq[ph])

    uniq = sorted(set(candidates), key=_score, reverse=True)
    return uniq[:top_k]


# ========== 倒排索引 ==========
def build_inverted_index(
    fragments: list[KBFragment], *, per_frag_top_k: int = 5
) -> dict[str, list[str]]:
    """关键字 → [frag_id]。用本地启发式抽词。"""
    index: dict[str, list[str]] = {}
    for frag in fragments:
        kws = extract_local_keywords(frag.key_text, top_k=per_frag_top_k)
        for kw in kws:
            index.setdefault(kw, []).append(frag.frag_id)
    return index


def search_fragments(
    index: dict[str, list[str]], fragments_by_id: dict[str, KBFragment], query: str
) -> list[str]:
    """倒排索引粗搜：对 query 内的所有候选短语取并集。"""
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


# ========== 样例数据解析 ==========
def load_sample_usecases() -> dict[str, list[dict[str, Any]]]:
    """
    返回：
      {
        "语义检索": [{"序号":..,"样例内容":..}, ...],
        "定性量纪": [...],
        "文书纠错": [{"测试文书":..,"测试样例":..,"纠正答案":..}, ...]
      }
    """
    result: dict[str, list[dict[str, Any]]] = {}

    ru = config.SAMPLE_FILES["retrieval_usecase"]
    try:
        df = load_kb(ru["file"], ru["sheet"])
        cat_col = ru["category_col"]
        content_col = ru["content_col"]
        for cat, sub in df.groupby(cat_col):
            items = [
                {"序号": r.get("序号", ""), "样例内容": str(r[content_col]).strip()}
                for _, r in sub.iterrows()
                if str(r[content_col]).strip()
            ]
            result[str(cat).strip()] = items
    except Exception as e:
        log.warning("加载 AI 测试用例失败：%s", e)

    dc = config.SAMPLE_FILES["doc_correction"]
    try:
        df = load_kb(dc["file"], dc["sheet"])
        items = []
        for _, r in df.iterrows():
            row = {col: str(r.get(col, "")).strip() for col in dc["columns"]}
            if row.get("测试样例"):
                items.append(row)
        result["文书纠错"] = items
    except Exception as e:
        log.warning("加载文书纠错样例失败：%s", e)

    return result


# ========== KB 资产卡片 ==========
def summarize_kb(asset: dict[str, Any], max_sample_rows: int = 3) -> dict[str, Any]:
    """为 Stage 1 产出"资产卡片"信息：行数 + 列名 + 前 N 行样本。"""
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
        "key_fields": list(asset["key_fields"]),
        "authority": asset["authority"],
        "category": asset["category"],
        "columns": list(df.columns),
        "sample_rows": sample_rows,
    }

