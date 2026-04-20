"""通用工具：MD 读写、frontmatter、ID 生成、JSON artifacts 解析。

所有阶段产物共享同一 MD 骨架（见 题目生成Agent设计文档.md §4.2）。
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable

_CST = timezone(timedelta(hours=8))

log = logging.getLogger("questforge.common")


# ========== ID 生成 ==========
class IdCounter:
    """按 prefix 自增生成全局唯一 ID。

    用法：
        ug = IdCounter("UG"); ug.next() -> "UG-001"
        frag = IdCounter("FRAG-001"); frag.next() -> "FRAG-001-001"
    """

    def __init__(self, prefix: str, width: int = 3, start: int = 0):
        self.prefix = prefix
        self.width = width
        self.n = start

    def next(self) -> str:
        self.n += 1
        return f"{self.prefix}-{self.n:0{self.width}d}"

    def peek(self) -> str:
        return f"{self.prefix}-{self.n + 1:0{self.width}d}"


def iso_now() -> str:
    """CST 时区的 ISO8601 时间串。"""
    return datetime.now(_CST).isoformat(timespec="seconds")


# ========== MD 渲染 ==========
@dataclass
class Section:
    heading: str  # 不含 "## "
    body: str  # markdown 片段，可含表格/列表


@dataclass
class Checklist:
    items: list[tuple[str, bool]] = field(default_factory=list)  # (text, passed)

    def add(self, text: str, passed: bool) -> None:
        self.items.append((text, passed))

    def all_passed(self) -> bool:
        return bool(self.items) and all(p for _, p in self.items)

    def render(self) -> str:
        lines = [f"- [{'x' if passed else ' '}] {text}" for text, passed in self.items]
        return "\n".join(lines) if lines else "- [ ] （无校验项）"


def _render_frontmatter(meta: dict[str, Any]) -> str:
    """YAML-lite frontmatter（只支持标量值，足够本 Pipeline 用）。"""
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def write_md(
    path: Path,
    *,
    frontmatter: dict[str, Any],
    title: str,
    summary: str,
    sections: Iterable[Section],
    artifacts: dict[str, Any],
    checklist: Checklist,
    remarks: str = "",
) -> Path:
    """按设计文档 §4.2 的骨架渲染 MD。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    parts.append(_render_frontmatter(frontmatter))
    parts.append("")
    parts.append(f"# {title}")
    parts.append("")
    parts.append("## 摘要")
    parts.append(summary.strip())
    parts.append("")
    for sec in sections:
        parts.append(f"## {sec.heading}")
        parts.append(sec.body.rstrip())
        parts.append("")
    parts.append("## 结构化数据")
    parts.append("```json")
    parts.append(json.dumps(artifacts, ensure_ascii=False, indent=2))
    parts.append("```")
    parts.append("")
    parts.append("## 下一阶段校验清单")
    parts.append(checklist.render())
    parts.append("")
    parts.append("## 备注与遗留问题")
    parts.append(remarks.strip() if remarks else "（无）")
    parts.append("")

    path.write_text("\n".join(parts), encoding="utf-8")
    log.info("wrote MD: %s", path)
    return path


# ========== MD 解析 ==========
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_ARTIFACTS_RE = re.compile(
    r"##\s*结构化数据\s*\n```json\s*\n(.*?)\n```", re.DOTALL
)


def read_md(path: Path | str) -> dict[str, Any]:
    """解析 QuestForge 阶段产物：返回 frontmatter、artifacts、raw 三部分。"""
    text = Path(path).read_text(encoding="utf-8")
    meta: dict[str, Any] = {}
    m = _FRONTMATTER_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if v.lower() in ("true", "false"):
                meta[k] = v.lower() == "true"
            else:
                meta[k] = v

    artifacts: dict[str, Any] = {}
    a = _ARTIFACTS_RE.search(text)
    if a:
        try:
            artifacts = json.loads(a.group(1))
        except json.JSONDecodeError as e:
            log.error("failed to parse artifacts in %s: %s", path, e)
            raise

    return {"frontmatter": meta, "artifacts": artifacts, "raw": text}


# ========== 工具函数 ==========
def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    """渲染一个 markdown 表格。"""
    if not rows:
        return f"| {' | '.join(headers)} |\n|{'|'.join(['---'] * len(headers))}|\n| {' | '.join(['—'] * len(headers))} |"
    head = "| " + " | ".join(headers) + " |"
    sep = "|" + "|".join(["---"] * len(headers)) + "|"
    body = "\n".join(
        "| " + " | ".join(str(c).replace("\n", " ").replace("|", "\\|") for c in row) + " |"
        for row in rows
    )
    return "\n".join([head, sep, body])


def truncate(text: str, n: int = 60) -> str:
    text = (text or "").replace("\n", " ")
    return text if len(text) <= n else text[:n] + "…"
