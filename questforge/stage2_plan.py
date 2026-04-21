"""Stage 2 · 业务流程提取 + 题目规划 → 02_plan.md

输入:01_understanding.md + AgentInput(用户可能已提供 business_processes)
输出:OUT_DIR / 02_plan.md

处理步骤(§4.4):
  2.1 流程提取或推导(第一层 Fallback)
  2.2 分类维度动态提取
  2.3 聚类与类型命名
  2.4 代表流程选择
  2.5 题目规划
  2.6 覆盖矩阵蓝图

**本阶段不做任何领域硬编码。** LLM 失败或输出不足 → MissingInputError。
"""
from __future__ import annotations

import json
import logging
from itertools import combinations
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, IdCounter, Section, iso_now, md_table, read_md, write_md
from .input_spec import AgentInput, MissingField, MissingInputError
from .llm_client import LLMClient, get_default_client

log = logging.getLogger("questforge.stage2")


# ========== Step 2.1 · 流程提取(LLM 或 用户提供) ==========
def _transcribe_user_processes(user_bps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """用户已提供 business_processes 时直接转录,统一 id 与 inferred 标记。"""
    counter = IdCounter("BP")
    normalized: list[dict[str, Any]] = []
    for p in user_bps:
        pid = p.get("id")
        if not pid or not pid.startswith("BP-"):
            pid = counter.next()
        normalized.append(
            {
                "id": pid,
                "name": (p.get("name") or "").strip() or "未命名流程",
                "actors": p.get("actors") or [],
                "triggers": p.get("triggers") or [],
                "steps": p.get("steps") or [],
                "outputs": p.get("outputs") or [],
                "cross_process_dependency": p.get("cross_process_dependency", "单流程"),
                "inferred": False,
            }
        )
    return normalized


def _llm_processes(client: LLMClient, artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """调用 LLM 按 `流程 = 用户 × 功能 × 业务目标` 推导业务流程。"""
    system_path = config.REPO_ROOT / "questforge/prompts/stage2_process.txt"
    system = system_path.read_text(encoding="utf-8")
    user = (
        "<stage1_artifacts>\n"
        + json.dumps(
            {
                "business_goal": artifacts.get("business_goal", {}),
                "user_groups": artifacts.get("user_groups", []),
                "features": artifacts.get("features", []),
                "knowledge_assets": [
                    {k: a[k] for k in ("id", "category", "key_fields")}
                    for a in artifacts.get("knowledge_assets", [])
                ],
                "glossary_keys": list(artifacts.get("glossary", {}).keys())[:20],
            },
            ensure_ascii=False,
        )
        + "\n</stage1_artifacts>\n"
        "请按如下 schema 输出 processes 列表(每条流程至少 3 个 step,标 inferred=true):\n"
        '{"processes":[{"id":"BP-xxx","name":"string",'
        '"actors":[{"id":"UG-xxx","role":"string","level":"业务|管理"}],'
        '"triggers":[{"type":"string","description":"string"}],'
        '"steps":[{"no":1,"name":"string"}],'
        '"outputs":[{"name":"string","category":"string"}],'
        '"cross_process_dependency":"单流程|跨流程","inferred":true}]}'
    )
    out = client.chat_json(system, user, max_tokens=3000)
    return out.get("processes", []) if isinstance(out, dict) else []


# ========== Step 2.2 · 分类维度提取 ==========
def _extract_dimensions(processes: list[dict[str, Any]]) -> dict[str, list[str]]:
    trigger_types = {t.get("type", "") for p in processes for t in p.get("triggers", [])}
    output_cats = {o.get("category", "") for p in processes for o in p.get("outputs", [])}
    actor_levels = {a.get("level", "") for p in processes for a in p.get("actors", [])}
    cross_types = {p.get("cross_process_dependency", "") for p in processes}
    return {
        "trigger.type": sorted(x for x in trigger_types if x),
        "outputs.category": sorted(x for x in output_cats if x),
        "actors.level": sorted(x for x in actor_levels if x),
        "cross_process_dependency": sorted(x for x in cross_types if x),
    }


# ========== Step 2.3 · 聚类 + complexity ==========
def _main_trigger(p) -> str:
    tr = p.get("triggers") or []
    return tr[0].get("type") if tr else "未知触发"


def _main_output_category(p) -> str:
    outs = p.get("outputs") or []
    return outs[0].get("category") if outs else "未知输出"


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(len(sa | sb), 1)


def _steps_names(p) -> list[str]:
    return [s.get("name", "") for s in p.get("steps", [])]


def _complexity(p: dict[str, Any]) -> float:
    step = len(p.get("steps", []))
    outs = len(p.get("outputs", []))
    cross = 1 if p.get("cross_process_dependency") == "跨流程" else 0
    actor_levels = {a.get("level") for a in p.get("actors", [])}
    cross_actor = 1 if len(actor_levels) > 1 else 0
    score = (
        0.30 * min(step / 5.0, 1.0)
        + 0.30 * min((cross + cross_actor) / 2.0, 1.0)
        + 0.40 * min(outs / 3.0, 1.0)
    )
    return round(min(max(score, 0.0), 1.0), 2)


def _cluster(processes: list[dict[str, Any]]) -> dict[str, list[str]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for p in processes:
        key = (_main_trigger(p), p.get("cross_process_dependency", "单流程"))
        buckets.setdefault(key, []).append(p)

    clusters: dict[str, list[str]] = {}
    idc = IdCounter("PT")
    for (_trig, _cross), ps in buckets.items():
        scored = sorted(ps, key=_complexity)
        cmin, cmax = _complexity(scored[0]), _complexity(scored[-1])
        if len(ps) >= 2 and (cmax - cmin) > 0.3:
            mid = (cmin + cmax) / 2
            low = [p for p in ps if _complexity(p) <= mid]
            high = [p for p in ps if _complexity(p) > mid]
            if low and high:
                clusters[idc.next()] = [p["id"] for p in low]
                clusters[idc.next()] = [p["id"] for p in high]
                continue
        clusters[idc.next()] = [p["id"] for p in ps]

    for (k1, ps1), (k2, ps2) in combinations(buckets.items(), 2):
        if k1 == k2:
            continue
        sim = _jaccard(_steps_names(ps1[0]), _steps_names(ps2[0]))
        if sim >= 0.8:
            log.info("⚠ 跨 bucket 相似度 %.2f:%s ↔ %s(保留独立类型)", sim, k1, k2)
    return clusters


def _assign_difficulty(score: float) -> str:
    basic_ub = config.DIFFICULTY_THRESHOLDS["basic"]
    adv_ub = config.DIFFICULTY_THRESHOLDS["advanced"]
    if score <= basic_ub:
        return "basic"
    if score <= adv_ub:
        return "advanced"
    return "expert"


# ========== Step 2.4 · 代表 + Step 2.5 · 题目规划 ==========
def _pick_representative(members: list[dict[str, Any]], all_processes: list[dict[str, Any]]) -> tuple[str, float]:
    coverage = len(members) / max(len(all_processes), 1)
    best = None
    best_imp = -1.0
    best_score = 0.0
    for p in members:
        c = _complexity(p)
        bv = (len(p.get("outputs", [])) + len(p.get("actors", []))) / 5.0
        bv = max(bv, 0.3)
        imp = c * coverage * bv
        if imp > best_imp:
            best_imp = imp
            best = p
            best_score = c
    return best["id"], best_score


def _format_type_name(main_trigger: str, main_output: str, cross: str) -> str:
    """通用类型命名:`{触发}-{输出}类`。不绑定任何具体领域。"""
    scope = "跨文档" if cross == "跨流程" else "单文档"
    # 若 output 名包含"纠错/审核/校对"等,直接点名更可读
    if any(kw in main_output for kw in ("纠错", "审核", "校对", "比对")):
        return f"{main_trigger}-{main_output}类"
    return f"{main_trigger}-{scope}类"


def _plan_tests(
    processes: list[dict[str, Any]], clusters: dict[str, list[str]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pid2proc = {p["id"]: p for p in processes}
    process_types: list[dict[str, Any]] = []
    test_plan: list[dict[str, Any]] = []

    tc = IdCounter("TEST")
    for pt_id, member_ids in clusters.items():
        members = [pid2proc[m] for m in member_ids]
        rep_id, _ = _pick_representative(members, processes)
        rep = pid2proc[rep_id]
        cluster_cx = max(_complexity(p) for p in members)
        difficulty = _assign_difficulty(cluster_cx)

        main_trigger = _main_trigger(rep)
        main_output = _main_output_category(rep)
        cross = rep.get("cross_process_dependency", "单流程")
        pt_name = _format_type_name(main_trigger, main_output, cross)

        # 通用规则:输出类别含"纠错"等词 → 最低 advanced(天然含识别+依据+规范三步)
        if any(kw in main_output for kw in ("纠错", "审核", "校对")) and difficulty == "basic":
            difficulty = "advanced"
            cluster_cx = max(cluster_cx, config.DIFFICULTY_THRESHOLDS["basic"] + 0.05)

        process_types.append(
            {
                "type_id": pt_id,
                "name": pt_name,
                "members": member_ids,
                "representative": rep_id,
                "complexity_score": round(cluster_cx, 2),
                "assigned_difficulty": difficulty,
            }
        )
        focus_stages = _derive_focus_stages(difficulty, main_trigger, main_output)
        test_plan.append(
            {
                "test_id": tc.next(),
                "process_type": pt_id,
                "source_process": rep_id,
                "difficulty": difficulty,
                "focus_stages": focus_stages,
            }
        )
    return process_types, test_plan


# ========== Step 2.6 · 覆盖矩阵蓝图 ==========
def _derive_focus_stages(difficulty: str, trigger: str, output: str) -> list[str]:
    """按难度与流程特征选 focus_stages(通用规则)。"""
    if difficulty == "expert":
        return list(config.FIVE_STAGES)
    if any(kw in output for kw in ("纠错", "审核", "校对")):
        return ["执行落地", "元认知"]
    if any(kw in trigger for kw in ("研判", "分析", "决策")):
        return ["拆解问题", "方案生成"]
    return ["定义问题"]


def _build_coverage_matrix(test_plan: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    matrix: dict[str, dict[str, str]] = {}
    for t in test_plan:
        row = {s: "常规" for s in config.FIVE_STAGES}
        for s in t.get("focus_stages", []):
            if s in row:
                row[s] = "重点"
        matrix[t["test_id"]] = row
    return matrix


# ========== 主流程 ==========
def run(stage1_md: Path | str, out_dir: Path | None, agent_input: AgentInput) -> Path:
    out_dir = Path(out_dir) if out_dir else config.ensure_out_dir(agent_input.out_dir)
    out_path = out_dir / "02_plan.md"

    parsed = read_md(stage1_md)
    artifacts = parsed["artifacts"]
    log.info(
        "[Stage2] 上游 pass_gate=%s, features=%d, user_groups=%d",
        parsed["frontmatter"].get("pass_gate"),
        len(artifacts.get("features", [])),
        len(artifacts.get("user_groups", [])),
    )

    # ===== Step 2.1 流程提取 =====
    if agent_input.business_processes:
        processes = _transcribe_user_processes(agent_input.business_processes)
        llm_used = False
        fallback_1 = False
        remarks_extra = "用户已在 AgentInput.business_processes 提供流程,直接转录"
    else:
        client = get_default_client()
        if not client.use_llm:
            raise MissingInputError(
                stage="Stage 2 · 业务流程提取",
                report=[
                    MissingField(
                        field_name="LLM_API_KEY",
                        why_needed="源文档未提供 business_processes,必须由 LLM 推导",
                        suggested_format="在 .env 配置 LLM_API_KEY,或在 example_input.json 提供 business_processes",
                        example='"business_processes": [{"id":"BP-001","name":"...","steps":[...]}]',
                    )
                ],
            )
        processes = _llm_processes(client, artifacts)
        if len(processes) < 2:
            raise MissingInputError(
                stage="Stage 2 · 业务流程提取",
                report=[
                    MissingField(
                        field_name="business_processes",
                        why_needed=(
                            f"LLM 仅推出 {len(processes)} 条流程(< 2),不足以做聚类"
                            "——可能因为 features.input/output 描述过于简略"
                        ),
                        suggested_format=(
                            "两种选择:(a) 补充 docs_dir 里的 PRD/架构;"
                            "(b) 在 example_input.json 的 business_processes 字段手工列出"
                        ),
                        example='"business_processes": [{"id":"BP-001","name":"...","triggers":[{"type":"..."}],...}]',
                    )
                ],
            )
        llm_used = True
        fallback_1 = True
        remarks_extra = "业务流程由 LLM 推导(第一层 Fallback)"

    # ===== Step 2.2-2.6 =====
    dimensions = _extract_dimensions(processes)
    effective_dims = {k: v for k, v in dimensions.items() if len(v) >= 2}

    clusters = _cluster(processes)
    process_types, test_plan = _plan_tests(processes, clusters)
    coverage_matrix = _build_coverage_matrix(test_plan)

    remarks: list[str] = [remarks_extra]
    if len(effective_dims) < 2:
        remarks.append(f"有效分类维度不足({len(effective_dims)}/4),以触发+跨流程组合为聚类主轴")
    if len(test_plan) < 3:
        remarks.append(f"聚类数 {len(test_plan)} < 3,可回头补次优流程")

    artifacts_out = {
        "fallback_status": {
            "business_processes_present": not fallback_1,
            "capability_scope_present": bool(agent_input.weak_points),
            "llm_path_taken": llm_used,
        },
        "processes": processes,
        "dimensions": dimensions,
        "effective_dimensions": list(effective_dims.keys()),
        "process_types": process_types,
        "test_plan": test_plan,
        "coverage_matrix_plan": coverage_matrix,
    }

    # ===== 校验清单(§4.4,通用) =====
    checklist = Checklist()
    ok_steps = all(len(p.get("steps", [])) >= 3 for p in processes)
    checklist.add(f"每条 BP ≥ 3 个步骤(共 {len(processes)} 条 BP)", ok_steps)

    vocab = set(config.TRIGGER_VOCAB) | set(artifacts.get("glossary", {}).keys())
    tr_types = {t.get("type") for p in processes for t in p.get("triggers", [])}
    checklist.add(
        "触发类型取值来自预设词表或 Stage 1 glossary",
        all(t in vocab for t in tr_types if t) or not tr_types,
    )

    checklist.add(
        f"聚类后的类型数 = test_plan 题目数({len(process_types)} vs {len(test_plan)})",
        len(process_types) == len(test_plan),
    )

    diffs = {t["difficulty"] for t in test_plan}
    if len(diffs) < 2:
        remarks.append(
            f"难度分配仅覆盖 {sorted(diffs)} 1 级;如需梯度评测,建议补充 business_processes"
            "或调整 features.input/output 以诱导 LLM 推出复杂度差异大的流程"
        )

    each_has_focus = all(any(v == "重点" for v in row.values()) for row in coverage_matrix.values())
    checklist.add("覆盖矩阵蓝图中每道题至少 1 个'重点'阶段", each_has_focus)

    checklist.add("test_plan 非空", len(test_plan) > 0)

    # ===== 渲染 MD =====
    summary = (
        f"共提取 {len(processes)} 条业务流程({'用户提供' if not fallback_1 else 'LLM 推导'});"
        f"按'触发-跨流程'组合聚类为 {len(process_types)} 个类型,规划 {len(test_plan)} 道题:"
        + "、".join(
            f"{len([t for t in test_plan if t['difficulty']==d])} {d}"
            for d in ("basic", "advanced", "expert")
        )
        + "。"
        + (f"第一层 Fallback 已触发(源文档无流程定义段)。" if fallback_1 else "")
    )

    sections = [
        Section(
            "Fallback 触发情况",
            md_table(
                ["项", "状态", "说明"],
                [
                    [
                        "business_processes 段存在",
                        "✓" if not fallback_1 else "✗",
                        "用户直接提供" if not fallback_1 else "走 LLM 推导",
                    ],
                    [
                        "capability_scope.weak_points",
                        "✓" if agent_input.weak_points else "✗",
                        "Stage 3 是否触发第二层 Fallback",
                    ],
                ],
            ),
        ),
        Section(
            "业务流程清单",
            md_table(
                ["ID", "名称", "触发", "参与者", "步骤数", "输出类别", "inferred"],
                [
                    [
                        p["id"],
                        p["name"],
                        _main_trigger(p),
                        "+".join(a.get("id", "") for a in p.get("actors", [])),
                        len(p.get("steps", [])),
                        _main_output_category(p),
                        p.get("inferred", True),
                    ]
                    for p in processes
                ],
            ),
        ),
        Section(
            "分类维度扫描",
            md_table(
                ["维度", "取值数", "取值"],
                [[dim, len(vals), "、".join(vals) if vals else "—"] for dim, vals in dimensions.items()],
            ),
        ),
        Section(
            "流程分类与代表",
            md_table(
                ["类型 ID", "类型名", "成员 BP", "代表 BP", "复杂度", "分配难度"],
                [
                    [
                        pt["type_id"],
                        pt["name"],
                        ",".join(pt["members"]),
                        pt["representative"],
                        pt["complexity_score"],
                        pt["assigned_difficulty"],
                    ]
                    for pt in process_types
                ],
            ),
        ),
        Section(
            "题目规划",
            md_table(
                ["题号", "流程类型", "代表流程", "难度", "focus_stages"],
                [
                    [t["test_id"], t["process_type"], t["source_process"], t["difficulty"], "、".join(t["focus_stages"])]
                    for t in test_plan
                ],
            ),
        ),
        Section(
            "覆盖矩阵蓝图",
            md_table(
                [""] + config.FIVE_STAGES,
                [[tid] + [coverage_matrix[tid][s] for s in config.FIVE_STAGES] for tid in coverage_matrix],
            ),
        ),
    ]

    frontmatter = {
        "stage": 2,
        "stage_name": "process_and_plan",
        "version": "1.0",
        "upstream": "01_understanding.md",
        "downstream": "03_context.md",
        "domain": agent_input.domain,
        "created_at": iso_now(),
        "created_by": "agent-stage2",
        "pass_gate": checklist.all_passed(),
    }

    write_md(
        out_path,
        frontmatter=frontmatter,
        title="Stage 2 · 业务流程提取 + 题目规划",
        summary=summary,
        sections=sections,
        artifacts=artifacts_out,
        checklist=checklist,
        remarks="\n".join(f"- {r}" for r in remarks) if remarks else "(无)",
    )
    return out_path


__all__ = ["run"]
