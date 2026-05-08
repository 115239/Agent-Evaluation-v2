"""业务数据 I/O:多格式资产加载(xlsx/csv/docx/txt/md/pdf)、Fragment 构造、关键字抽取、样例诉求解析。

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


# ========== 支持的资产格式 ==========
TABULAR_EXTS = {".xlsx", ".xls", ".xlsm", ".csv"}
TEXTUAL_EXTS = {".docx", ".txt", ".md", ".pdf"}
SUPPORTED_EXTS = TABULAR_EXTS | TEXTUAL_EXTS

TEXT_COLUMNS = ["标题", "段落"]
_TEXT_MIN_LEN = 10  # 段落最短字符数,过短的视为标题/碎片不单独成行


class UnsupportedFormatError(ValueError):
    """资产扩展名不在 SUPPORTED_EXTS 中,或解析所需依赖缺失。"""


# ========== 数据类 ==========
@dataclass
class KBFragment:
    frag_id: str
    asset_id: str
    row_no: int
    key_text: str
    full_row: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


# ========== 多格式加载分派 ==========
def load_kb(path: Path, sheet: str) -> pd.DataFrame:
    """按扩展名分派的资产加载器,统一返回 str 类型 DataFrame、空值填 ''.

    - xlsx/xls/xlsm: 走 openpyxl,使用传入 sheet
    - csv: UTF-8 → GBK 回退
    - docx: python-docx,展开为 ["标题","段落"] 形态
    - txt/md: 纯文本切段为 ["标题","段落"]
    - pdf: pypdf 逐页 extract_text,切段为 ["标题","段落"]
    - 其他扩展名 / 老 .doc 二进制: 抛 UnsupportedFormatError
    """
    ext = path.suffix.lower()
    if ext in {".xlsx", ".xls", ".xlsm"}:
        df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl", dtype=str)
    elif ext == ".csv":
        df = _read_csv_with_fallback(path)
    elif ext == ".docx":
        df = _read_docx_as_table(path)
    elif ext in {".txt", ".md"}:
        df = _read_text_as_table(path, is_markdown=(ext == ".md"))
    elif ext == ".pdf":
        df = _read_pdf_as_table(path)
    elif ext == ".doc":
        raise UnsupportedFormatError(
            f"不支持老二进制 .doc 文件 ({path.name})。请先用 Word 另存为 .docx 后重试。"
        )
    else:
        raise UnsupportedFormatError(f"不支持的资产扩展名: {ext} ({path.name})")
    return df.fillna("").astype(str)


def _read_csv_with_fallback(path: Path) -> pd.DataFrame:
    last_err: Exception | None = None
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            return pd.read_csv(path, dtype=str, encoding=enc, keep_default_na=False)
        except UnicodeDecodeError as e:
            last_err = e
            continue
    raise UnsupportedFormatError(
        f"CSV 编码无法识别 ({path.name}):尝试 utf-8/utf-8-sig/gbk/gb18030 均失败"
    ) from last_err


def _read_docx_as_table(path: Path) -> pd.DataFrame:
    try:
        import docx  # type: ignore
    except ImportError as e:
        raise UnsupportedFormatError(
            "解析 docx 需 python-docx。请 `pip install python-docx>=1.0` 后重跑。"
        ) from e

    doc = docx.Document(str(path))
    body = doc.element.body
    rows: list[dict[str, str]] = []
    current_heading = ""

    para_iter = iter(doc.paragraphs)
    table_iter = iter(doc.tables)
    para_map = {p._element: p for p in doc.paragraphs}
    table_map = {t._element: t for t in doc.tables}

    for child in body.iterchildren():
        if child in para_map:
            para = para_map[child]
            text = (para.text or "").strip()
            if not text:
                continue
            style = (para.style.name if para.style is not None else "") or ""
            if style.startswith("Heading") or style.startswith("标题"):
                current_heading = text
                continue
            if len(text) < _TEXT_MIN_LEN:
                # 过短段落跳过(避免污染索引);如确为标题则其样式应已被识别
                continue
            rows.append({"标题": current_heading, "段落": text})
        elif child in table_map:
            table = table_map[child]
            tbl_rows = list(table.rows)
            if not tbl_rows:
                continue
            header = [c.text.strip() for c in tbl_rows[0].cells]
            for tr in tbl_rows[1:]:
                cells = [c.text.strip() for c in tr.cells]
                pairs = [
                    f"{h}={v}"
                    for h, v in zip(header, cells, strict=False)
                    if (h or v) and v
                ]
                if pairs:
                    rows.append({"标题": current_heading, "段落": "; ".join(pairs)})

    if not rows:
        # 兜底:正文为空的退化处理,保证下游不崩(rows=0,Stage 1 LLM 会拒识并报缺失)
        return pd.DataFrame(columns=TEXT_COLUMNS)
    return pd.DataFrame(rows, columns=TEXT_COLUMNS)


_MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_PARA_SPLIT_RE = re.compile(r"\n\s*\n+")


def _read_text_with_fallback(path: Path) -> str:
    last_err: Exception | None = None
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
            continue
    raise UnsupportedFormatError(
        f"文本编码无法识别 ({path.name}):尝试 utf-8/utf-8-sig/gbk/gb18030 均失败"
    ) from last_err


def _read_text_as_table(path: Path, *, is_markdown: bool) -> pd.DataFrame:
    raw = _read_text_with_fallback(path)
    rows: list[dict[str, str]] = []
    current_heading = ""

    if is_markdown:
        # 保留 md 的标题层级,逐行扫描
        buffer: list[str] = []

        def _flush() -> None:
            nonlocal buffer
            if not buffer:
                return
            text = "\n".join(buffer).strip()
            buffer = []
            for chunk in _PARA_SPLIT_RE.split(text):
                chunk = chunk.strip()
                if len(chunk) >= _TEXT_MIN_LEN:
                    rows.append({"标题": current_heading, "段落": chunk})

        for line in raw.splitlines():
            m = _MD_HEADING_RE.match(line)
            if m:
                _flush()
                current_heading = m.group(2).strip()
            else:
                buffer.append(line)
        _flush()
    else:
        for chunk in _PARA_SPLIT_RE.split(raw):
            chunk = chunk.strip()
            if len(chunk) >= _TEXT_MIN_LEN:
                rows.append({"标题": "", "段落": chunk})

    if not rows:
        return pd.DataFrame(columns=TEXT_COLUMNS)
    return pd.DataFrame(rows, columns=TEXT_COLUMNS)


def _read_pdf_as_table(path: Path) -> pd.DataFrame:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as e:
        raise UnsupportedFormatError(
            "解析 PDF 需 pypdf。请 `pip install pypdf>=4.0` 后重跑。"
        ) from e

    reader = PdfReader(str(path))
    rows: list[dict[str, str]] = []
    for idx, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as e:  # 个别页面解析失败不阻断整本
            log.warning("PDF 第 %d 页解析失败 (%s): %s", idx, path.name, e)
            continue
        heading = f"第{idx}页"
        for chunk in _PARA_SPLIT_RE.split(text):
            chunk = chunk.strip()
            if len(chunk) >= _TEXT_MIN_LEN:
                rows.append({"标题": heading, "段落": chunk})

    if not rows:
        return pd.DataFrame(columns=TEXT_COLUMNS)
    return pd.DataFrame(rows, columns=TEXT_COLUMNS)


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
