"""QuestForge 通用输入契约 & 缺失输入反馈机制。

对齐设计文档 §2.3 `AgentInput` 与 §2.4 Phase 0 预处理。
框架的核心承诺:**不做本地兜底**——LLM 或输入不足以完成任务时,
以结构化 `MissingInputError` 把"补什么、为什么补、怎么补"透传给用户。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ========== 输入通道枚举 ==========
CHANNEL_DESIGN_DOC = "design_doc"
CHANNEL_GUI = "gui"
CHANNEL_CODE = "code"
CHANNEL_USER_LOG = "user_log"
SUPPORTED_CHANNELS = {CHANNEL_DESIGN_DOC, CHANNEL_GUI, CHANNEL_CODE, CHANNEL_USER_LOG}
# 当前 Pipeline 实际支持的通道(其余通道只做占位)
IMPLEMENTED_CHANNELS = {CHANNEL_DESIGN_DOC}


# ========== 样例文件配置 ==========
@dataclass
class SampleFileConfig:
    """描述一个样例文件的读取方式。

    支持两种写法:
    - 单列明细:给出 `category_col` + `content_col`,按类别聚合
    - 多列原样读入:给出 `columns` 列表,每行作为一条样例
    """

    label: str  # 用户可读的类别标签,如 "文书纠错"/"语义检索"
    file: Path
    sheet: str = "Sheet1"
    category_col: str | None = None
    content_col: str | None = None
    columns: list[str] = field(default_factory=list)


# ========== 主输入 ==========
@dataclass
class AgentInput:
    """题目生成 Agent 的通用输入。

    仅 design_doc 通道当前有完整实现;其余通道字段预留。
    """

    # 必须
    source_channel: str
    business_goal: str  # 一句话业务目标
    domain: str  # 业务领域名,如 "纪检材料智能审查" / "客服对话质检"

    # design_doc 通道使用
    docs_dir: Path | None = None  # PRD / 架构文档目录
    data_dir: Path | None = None  # 业务数据资产目录(xlsx/docx)
    samples: list[SampleFileConfig] = field(default_factory=list)

    # 可选补强(任一缺失时 Pipeline 会请求用户补)
    glossary_seed: dict[str, str] = field(default_factory=dict)
    weak_points: list[str] = field(default_factory=list)
    business_processes: list[dict[str, Any]] = field(default_factory=list)

    # 产物目录(可选:用户自定义)
    out_dir: Path | None = None

    # ---- 工厂方法 ----
    @classmethod
    def from_json(cls, path: Path | str) -> "AgentInput":
        """从 JSON 文件加载;字符串路径自动解析为相对输入 JSON 的绝对路径。"""
        p = Path(path).resolve()
        raw = json.loads(p.read_text(encoding="utf-8"))
        base = p.parent
        return cls._from_raw(raw, base)

    @classmethod
    def _from_raw(cls, raw: dict[str, Any], base: Path) -> "AgentInput":
        def _resolve(x: Any) -> Path | None:
            if not x:
                return None
            q = Path(x)
            return q if q.is_absolute() else (base / q).resolve()

        samples_raw = raw.get("samples") or []
        samples = [
            SampleFileConfig(
                label=s["label"],
                file=_resolve(s["file"]) or Path(s["file"]),
                sheet=s.get("sheet", "Sheet1"),
                category_col=s.get("category_col"),
                content_col=s.get("content_col"),
                columns=list(s.get("columns", [])),
            )
            for s in samples_raw
        ]

        return cls(
            source_channel=raw.get("source_channel", CHANNEL_DESIGN_DOC),
            business_goal=raw.get("business_goal", "").strip(),
            domain=raw.get("domain", "").strip(),
            docs_dir=_resolve(raw.get("docs_dir")),
            data_dir=_resolve(raw.get("data_dir")),
            samples=samples,
            glossary_seed=dict(raw.get("glossary_seed", {})),
            weak_points=list(raw.get("weak_points", [])),
            business_processes=list(raw.get("business_processes", [])),
            out_dir=_resolve(raw.get("out_dir")),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Path → str 便于序列化
        for k, v in list(d.items()):
            if isinstance(v, Path):
                d[k] = str(v)
        d["samples"] = [
            {**asdict(s), "file": str(s.file)} for s in self.samples
        ]
        return d


# ========== 缺失输入反馈 ==========
@dataclass
class MissingField:
    """一个具体缺失字段的"补什么、为什么、怎么补、例子"四元组。"""

    field_name: str
    why_needed: str
    suggested_format: str
    example: str = ""

    def render(self) -> str:
        lines = [
            f"- **字段**:`{self.field_name}`",
            f"  - 为什么需要:{self.why_needed}",
            f"  - 建议格式:{self.suggested_format}",
        ]
        if self.example:
            lines.append(f"  - 示例:{self.example}")
        return "\n".join(lines)


class MissingInputError(Exception):
    """Pipeline 任一阶段遇到输入不足时抛出。

    用户应根据 `.format_for_user()` 的补充单补齐,再用 `--only stageN` 断点续跑。
    """

    def __init__(
        self,
        stage: str,
        report: list[MissingField],
        hint: str = "",
    ) -> None:
        self.stage = stage
        self.report = report
        self.hint = hint
        super().__init__(
            f"[{stage}] 缺失 {len(report)} 项输入;请补齐后重跑。"
        )

    def format_for_user(self) -> str:
        lines = [
            f"## ⚠️ {self.stage} 中断:需要补充输入",
            "",
        ]
        if self.hint:
            lines.extend([self.hint, ""])
        lines.append("### 请补齐以下字段,然后从该阶段断点续跑:")
        lines.append("")
        for item in self.report:
            lines.append(item.render())
            lines.append("")
        return "\n".join(lines)


__all__ = [
    "CHANNEL_DESIGN_DOC",
    "CHANNEL_GUI",
    "CHANNEL_CODE",
    "CHANNEL_USER_LOG",
    "SUPPORTED_CHANNELS",
    "IMPLEMENTED_CHANNELS",
    "SampleFileConfig",
    "AgentInput",
    "MissingField",
    "MissingInputError",
]
