"""Phase 0 · 输入预处理 → 00_input_assessment.md

对齐设计文档 §2.4。核心职责:
- 完整性检查(各字段是否满足最小输入集)
- 质量评估(启发式打分,指出可提升项)
- 通道适配(当前仅支持 design_doc)
- 补充建议(列出"建议补充"的可选项)
- 不满足最小输入集则终止 Pipeline,抛 MissingInputError

**本阶段不做任何本地兜底。**缺什么告诉用户去补,不代替用户决策。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, Section, iso_now, md_table, write_md
from .input_spec import (
    CHANNEL_DESIGN_DOC,
    IMPLEMENTED_CHANNELS,
    SUPPORTED_CHANNELS,
    AgentInput,
    MissingField,
    MissingInputError,
)
from .io_utils import SUPPORTED_EXTS, UnsupportedFormatError, load_kb

log = logging.getLogger("questforge.phase0")


# ========== 评估报告 ==========
@dataclass
class InputAssessmentReport:
    completeness: dict[str, bool] = field(default_factory=dict)
    quality_score: float = 0.0
    conflicts: list[str] = field(default_factory=list)
    recommended_strategy: str = ""
    suggestions: list[str] = field(default_factory=list)
    missing_required: list[MissingField] = field(default_factory=list)

    @property
    def can_proceed(self) -> bool:
        return all(self.completeness.values()) and not self.missing_required


# ========== 子检查 ==========
_DATA_ASSET_EXTS = set(SUPPORTED_EXTS)
_DOCS_EXCERPT_MAX_CHARS = 8000


def _check_completeness(agent_input: AgentInput) -> tuple[dict[str, bool], list[MissingField]]:
    """必需字段体检。返回 (状态字典, 缺失报告)。"""
    status: dict[str, bool] = {}
    missing: list[MissingField] = []

    # source_channel
    ok = agent_input.source_channel in SUPPORTED_CHANNELS
    status["source_channel ∈ {design_doc, gui, code, user_log}"] = ok
    if not ok:
        missing.append(
            MissingField(
                field_name="source_channel",
                why_needed="Pipeline 需要根据通道选择输入解析策略",
                suggested_format='四选一:"design_doc" / "gui" / "code" / "user_log"',
                example='"source_channel": "design_doc"',
            )
        )
    impl_ok = agent_input.source_channel in IMPLEMENTED_CHANNELS
    status[f"source_channel 已在当前 Pipeline 实现({','.join(sorted(IMPLEMENTED_CHANNELS))})"] = impl_ok
    if ok and not impl_ok:
        missing.append(
            MissingField(
                field_name="source_channel",
                why_needed=f"通道 `{agent_input.source_channel}` 尚未实现",
                suggested_format="改为已实现通道,或等待对应通道落地",
                example='"source_channel": "design_doc"',
            )
        )

    # business_goal
    goal = (agent_input.business_goal or "").strip()
    ok = bool(goal) and len(goal) >= 10
    status["business_goal 一句话业务目标(≥10 字)"] = ok
    if not ok:
        missing.append(
            MissingField(
                field_name="business_goal",
                why_needed="整个 Pipeline 以业务目标为主轴推导用户/功能/流程/题目",
                suggested_format="一句话中文描述,说明'上线后要解决什么问题,给谁用,达成什么指标'",
                example='"business_goal": "为客服主管提供对话质检与教练建议,降低申诉率"',
            )
        )

    # domain
    ok = bool((agent_input.domain or "").strip())
    status["domain 业务领域名"] = ok
    if not ok:
        missing.append(
            MissingField(
                field_name="domain",
                why_needed="领域名用于 prompt 模板的占位替换、跨阶段一致性检查、报告归档",
                suggested_format="简短领域名(不超过 20 字)",
                example='"domain": "客服对话质检"',
            )
        )

    # design_doc 通道专属
    if agent_input.source_channel == CHANNEL_DESIGN_DOC:
        dd = agent_input.data_dir
        ok = bool(dd) and Path(dd).is_dir()
        status["data_dir 业务数据资产目录存在"] = ok
        if not ok:
            missing.append(
                MissingField(
                    field_name="data_dir",
                    why_needed="Stage 1 要登记知识库资产,Stage 3 要基于它构建索引并抽片段",
                    suggested_format="一个目录的绝对或相对路径;目录内含 xlsx/docx/csv",
                    example='"data_dir": "datasets/my_project/knowledge"',
                )
            )

        assets: list[Path] = []
        if ok:
            assets = _scan_assets(Path(dd))
            asset_ok = len(assets) > 0
            status["data_dir 至少含 1 个资产文件(xlsx/docx/csv)"] = asset_ok
            if not asset_ok:
                missing.append(
                    MissingField(
                        field_name="data_dir",
                        why_needed="没有可读资产时 Stage 3 无法索引片段",
                        suggested_format=f"目录内放置扩展名 ∈ {sorted(_DATA_ASSET_EXTS)} 的文件",
                        example="- knowledge/my_kb.xlsx\n    - knowledge/case_library.xlsx",
                    )
                )

        if agent_input.docs_dir is not None and not Path(agent_input.docs_dir).is_dir():
            status["docs_dir(若提供)应为目录"] = False
            missing.append(
                MissingField(
                    field_name="docs_dir",
                    why_needed="docs_dir 存在时 Stage 1 会从 PRD/架构提取功能描述",
                    suggested_format="一个现存目录;不需要则保持 null",
                    example='"docs_dir": null',
                )
            )
        else:
            status["docs_dir(若提供)应为目录"] = True

        # samples 可选但若提供则文件必须存在
        bad_samples = [s.file for s in agent_input.samples if not Path(s.file).is_file()]
        if bad_samples:
            status["samples 所声明的文件均存在"] = False
            missing.append(
                MissingField(
                    field_name="samples",
                    why_needed="samples 用于 Stage 1 抽取 user_groups.typical_query 原文示例",
                    suggested_format="每个 sample 指向一个真实存在的文件;file 可为相对 example_input.json 的相对路径",
                    example=f"缺失文件:{bad_samples}",
                )
            )
        else:
            status["samples 所声明的文件均存在"] = True

    return status, missing


def _scan_assets(data_dir: Path) -> list[Path]:
    if not data_dir.is_dir():
        return []
    return sorted(p for p in data_dir.iterdir() if p.suffix.lower() in _DATA_ASSET_EXTS and p.is_file())


def _load_docs_dir_text(docs_dir: Path | None) -> str:
    """读取 docs_dir 下所有支持格式文件的纯文本拼接,用于 Stage 1 注入 LLM。

    每个文件以 `## 文件名` 起头,正文按行写入。返回截断到 _DOCS_EXCERPT_MAX_CHARS 字符。
    任何单文件解析失败仅 log warning,不阻断 Phase 0。
    """
    if not docs_dir:
        return ""
    docs_path = Path(docs_dir)
    if not docs_path.is_dir():
        return ""
    chunks: list[str] = []
    total = 0
    for p in sorted(docs_path.iterdir()):
        if not p.is_file() or p.suffix.lower() not in _DATA_ASSET_EXTS:
            continue
        try:
            sheet = "main"
            if p.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
                # 表格类文档对 PRD 注入意义不大,跳过避免噪音
                continue
            df = load_kb(p, sheet)
        except (UnsupportedFormatError, Exception) as e:  # noqa: BLE001
            log.warning("docs_dir 读取 %s 失败:%s", p.name, e)
            continue
        if df.empty:
            continue
        # docx/txt/md/pdf 都是 ["标题","段落"] 形态;其余以全部列拼接
        if list(df.columns) == ["标题", "段落"]:
            lines: list[str] = []
            cur_heading = ""
            for _, row in df.iterrows():
                heading = str(row.get("标题") or "").strip()
                para = str(row.get("段落") or "").strip()
                if heading and heading != cur_heading:
                    lines.append(f"### {heading}")
                    cur_heading = heading
                if para:
                    lines.append(para)
            body = "\n".join(lines)
        else:
            body = "\n".join(
                " | ".join(str(v).strip() for v in row.values if str(v).strip())
                for _, row in df.iterrows()
            )
        if not body.strip():
            continue
        chunk = f"## {p.name}\n{body}"
        chunks.append(chunk)
        total += len(chunk)
        if total >= _DOCS_EXCERPT_MAX_CHARS:
            break
    excerpt = "\n\n".join(chunks)
    if len(excerpt) > _DOCS_EXCERPT_MAX_CHARS:
        excerpt = excerpt[:_DOCS_EXCERPT_MAX_CHARS] + "\n…(已截断)"
    return excerpt


def _estimate_quality(agent_input: AgentInput, assets: list[Path]) -> float:
    score = 0.0
    goal_len = len((agent_input.business_goal or "").strip())
    if goal_len >= 20:
        score += 0.3
    if len(assets) >= 2:
        score += 0.3
    if agent_input.samples:
        score += 0.2
    if len(agent_input.glossary_seed) >= 3:
        score += 0.2
    return round(min(score, 1.0), 2)


def _recommend_strategy(agent_input: AgentInput) -> str:
    if agent_input.business_processes:
        return "transcribe(源文档已含 business_processes,Stage 2 直接转录)"
    return "derive(源文档无 business_processes,Stage 2 触发第一层 Fallback,由 LLM 推导)"


def _build_suggestions(agent_input: AgentInput, assets: list[Path]) -> list[str]:
    hints: list[str] = []
    if not agent_input.business_processes:
        hints.append(
            "未提供 `business_processes`。Stage 2 将由 LLM 推导流程;若有现成的流程定义,"
            "建议提供以避免 LLM 幻觉。"
        )
    if not agent_input.weak_points:
        hints.append(
            "未提供 `weak_points`(能力边界/已知短板)。Stage 3 将通过流程特性推导约束;"
            "若有明确短板(如'版本区分/权限边界'),建议提供,可显著提升题目靶向性。"
        )
    if not agent_input.docs_dir:
        hints.append(
            "未提供 `docs_dir`(PRD/架构文档目录)。Stage 1 将仅从 business_goal + 资产列头"
            "推导用户画像与功能;有 PRD 则更精确。"
        )
    if not agent_input.samples:
        hints.append(
            "未提供 `samples`(诉求样例)。Stage 1 的 user_groups.typical_query 将由 LLM 生成,"
            "建议提供真实用户原话样例以保证语感真实。"
        )
    if len(agent_input.glossary_seed) < 3:
        hints.append(
            "`glossary_seed` 条目 <3。Stage 3 真实性检验依赖领域术语表,"
            "若 LLM 无法从 PRD/资产中自动抽取足够术语,会在 Stage 1 再次请求补充。"
        )
    if not agent_input.out_dir:
        hints.append(
            f"未指定 `out_dir`,默认使用 {config.OUT_DIR}。"
        )
    return hints


# ========== 主流程 ==========
def run(agent_input: AgentInput, out_dir: Path | None = None) -> tuple[Path, InputAssessmentReport]:
    """执行 Phase 0。

    返回 (00_input_assessment.md 路径, 评估报告)。
    若 can_proceed=false,抛 MissingInputError。
    """
    effective_out = Path(out_dir) if out_dir else config.ensure_out_dir(agent_input.out_dir)
    effective_out.mkdir(parents=True, exist_ok=True)
    out_path = effective_out / "00_input_assessment.md"

    completeness, missing = _check_completeness(agent_input)
    assets = (
        _scan_assets(Path(agent_input.data_dir)) if agent_input.data_dir and Path(agent_input.data_dir).is_dir() else []
    )
    quality = _estimate_quality(agent_input, assets)
    strategy = _recommend_strategy(agent_input)
    suggestions = _build_suggestions(agent_input, assets)

    report = InputAssessmentReport(
        completeness=completeness,
        quality_score=quality,
        conflicts=[],  # 本阶段不做 LLM 冲突检测,留待 Stage 1-3 过程中识别
        recommended_strategy=strategy,
        suggestions=suggestions,
        missing_required=missing,
    )

    # ==== 渲染 MD ====
    checklist = Checklist()
    for text, passed in completeness.items():
        checklist.add(text, passed)

    summary_parts = [
        f"通道 = `{agent_input.source_channel}`。",
        f"完整性 {sum(completeness.values())}/{len(completeness)} 通过,"
        f"质量评分 {quality}(0-1)。",
        f"推荐策略:{strategy}。",
    ]
    if report.can_proceed:
        summary_parts.append("✅ 输入满足最小要求,可进入 Stage 1。")
    else:
        summary_parts.append(
            f"⛔ 缺少 {len(missing)} 项必需输入,Pipeline 将在此中断并请求补充。"
        )

    sections = [
        Section(
            "完整性检查",
            md_table(
                ["项", "状态"],
                [[k, "✓" if v else "✗"] for k, v in completeness.items()],
            ),
        ),
        Section(
            "质量评分明细",
            md_table(
                ["维度", "贡献"],
                [
                    ["business_goal 字数 ≥ 20", "+0.30" if len((agent_input.business_goal or "").strip()) >= 20 else "+0"],
                    ["data_dir 资产数 ≥ 2", f"+0.30({len(assets)} 个)" if len(assets) >= 2 else f"+0({len(assets)} 个)"],
                    ["samples 非空", "+0.20" if agent_input.samples else "+0"],
                    ["glossary_seed ≥ 3 条", "+0.20" if len(agent_input.glossary_seed) >= 3 else "+0"],
                ],
            ),
        ),
        Section(
            "资产扫描",
            md_table(
                ["文件", "扩展名"],
                [[p.name, p.suffix] for p in assets] or [["—", "—"]],
            ),
        ),
        Section(
            "推荐策略",
            f"**{strategy}**",
        ),
        Section(
            "补充建议",
            "\n".join(f"- {h}" for h in suggestions) if suggestions else "(无)",
        ),
    ]

    if missing:
        sections.append(
            Section(
                "必需输入缺失清单",
                "\n\n".join(m.render() for m in missing),
            )
        )

    frontmatter = {
        "stage": 0,
        "stage_name": "input_assessment",
        "version": "1.0",
        "upstream": "AgentInput(用户提供)",
        "downstream": "01_understanding.md",
        "domain": agent_input.domain or "UNSPECIFIED",
        "created_at": iso_now(),
        "created_by": "agent-phase0",
        "pass_gate": report.can_proceed,
    }

    docs_excerpt = _load_docs_dir_text(Path(agent_input.docs_dir)) if agent_input.docs_dir else ""

    artifacts = {
        "agent_input": agent_input.to_dict(),
        "completeness": completeness,
        "quality_score": quality,
        "recommended_strategy": strategy,
        "suggestions": suggestions,
        "docs_text_excerpt": docs_excerpt,
        "missing_required": [
            {
                "field": m.field_name,
                "why": m.why_needed,
                "format": m.suggested_format,
                "example": m.example,
            }
            for m in missing
        ],
    }

    write_md(
        out_path,
        frontmatter=frontmatter,
        title="Phase 0 · 输入预处理",
        summary="\n".join(summary_parts),
        sections=sections,
        artifacts=artifacts,
        checklist=checklist,
        remarks=(
            "Pipeline 不做本地兜底。以上缺失项必须由用户补齐后重跑。"
            if missing
            else "(无)"
        ),
    )

    if not report.can_proceed:
        raise MissingInputError(
            stage="Phase 0 · 输入预处理",
            report=missing,
            hint=(
                "Pipeline 发现输入不满足最小要求。请参考 "
                f"`{out_path}` 补齐后,用同一 `--input-json` 再次运行 "
                "`python -m questforge.run_pipeline`。"
            ),
        )

    return out_path, report


__all__ = ["InputAssessmentReport", "run"]
