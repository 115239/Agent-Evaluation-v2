"""Stage 2 · 业务流程提取 + 题目规划 → 02_plan.md

输入：01_understanding.md（通过 common.read_md 读取 frontmatter + artifacts）
输出：OUT_DIR / 02_plan.md

处理步骤（参考 题目生成Agent设计文档.md §4.4）：
  2.1 流程提取或推导（第一层 Fallback）
  2.2 分类维度动态提取
  2.3 聚类与类型命名
  2.4 代表流程选择
  2.5 题目规划
  2.6 覆盖矩阵蓝图
"""
from __future__ import annotations

import json
import logging
from itertools import combinations
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, IdCounter, Section, iso_now, md_table, read_md, write_md
from .llm_client import get_default_client

log = logging.getLogger("questforge.stage2")


# ========== Step 2.1 · 流程推导（本地兜底） ==========
def _fallback_processes(user_groups, features) -> list[dict[str, Any]]:
    """基于设计文档 §4.4 的 6 条典型 BP 兜底。"""
    return [
        {
            "id": "BP-001",
            "name": "党纪条款精确查询",
            "actors": [{"id": "UG-001", "role": "纪检监察员", "level": "业务"}],
            "triggers": [{"type": "知识咨询", "description": "遇到具体违纪情形需查条款"}],
            "steps": [
                {"no": 1, "name": "定位条例版本"},
                {"no": 2, "name": "按要点词检索条款"},
                {"no": 3, "name": "提取条款原文与量纪信息"},
            ],
            "outputs": [{"name": "条款号+原文+量纪档次", "category": "结构化条款"}],
            "cross_process_dependency": "单流程",
            "inferred": True,
        },
        {
            "id": "BP-002",
            "name": "总书记讲话主题检索",
            "actors": [{"id": "UG-001", "role": "纪检监察员", "level": "业务"}],
            "triggers": [{"type": "知识咨询", "description": "需引用总书记相关论述"}],
            "steps": [
                {"no": 1, "name": "识别主题关键词"},
                {"no": 2, "name": "检索匹配讲话"},
                {"no": 3, "name": "输出摘要与发布时间"},
            ],
            "outputs": [{"name": "讲话标题+摘要+时间", "category": "讲话摘要+上下文"}],
            "cross_process_dependency": "单流程",
            "inferred": True,
        },
        {
            "id": "BP-003",
            "name": "定性量纪决策辅助",
            "actors": [
                {"id": "UG-001", "role": "纪检监察员", "level": "业务"},
                {"id": "UG-002", "role": "纪检部门负责人", "level": "管理"},
            ],
            "triggers": [{"type": "案件研判", "description": "需对具体案情作出定性与量纪建议"}],
            "steps": [
                {"no": 1, "name": "识别案情要素"},
                {"no": 2, "name": "匹配党纪条款"},
                {"no": 3, "name": "检索类案"},
                {"no": 4, "name": "综合判断从宽/从严情节"},
                {"no": 5, "name": "给出量纪档次建议"},
            ],
            "outputs": [
                {"name": "定性结论", "category": "决策建议"},
                {"name": "适用条款", "category": "结构化条款"},
                {"name": "量纪档次", "category": "决策建议"},
            ],
            "cross_process_dependency": "跨流程",
            "inferred": True,
        },
        {
            "id": "BP-004",
            "name": "跨文档类案参考",
            "actors": [{"id": "UG-001", "role": "纪检监察员", "level": "业务"}],
            "triggers": [{"type": "案件研判", "description": "需跨理论文章与实务案例比对类似情形"}],
            "steps": [
                {"no": 1, "name": "提取案情要点"},
                {"no": 2, "name": "检索理论文章"},
                {"no": 3, "name": "检索实务案例"},
                {"no": 4, "name": "整合类案结论"},
            ],
            "outputs": [{"name": "类案+处理方式", "category": "实务问答"}],
            "cross_process_dependency": "跨流程",
            "inferred": True,
        },
        {
            "id": "BP-005",
            "name": "实务案例查询",
            "actors": [{"id": "UG-001", "role": "纪检监察员", "level": "业务"}],
            "triggers": [{"type": "知识咨询", "description": "查询类似实务问答"}],
            "steps": [
                {"no": 1, "name": "提炼问题关键词"},
                {"no": 2, "name": "检索实务测试集"},
                {"no": 3, "name": "返回问答与来源片段"},
            ],
            "outputs": [{"name": "实务问答+来源", "category": "实务问答"}],
            "cross_process_dependency": "单流程",
            "inferred": True,
        },
        {
            "id": "BP-006",
            "name": "纪检文书纠错",
            "actors": [{"id": "UG-002", "role": "纪检文书审核人员", "level": "管理"}],
            "triggers": [{"type": "审核复核", "description": "审核纪检文书中的表达或依据错误"}],
            "steps": [
                {"no": 1, "name": "读取文书原文"},
                {"no": 2, "name": "识别表达/口径问题"},
                {"no": 3, "name": "匹配正确依据"},
                {"no": 4, "name": "给出纠错建议与规范表达"},
            ],
            "outputs": [{"name": "纠错建议+依据", "category": "纠错清单"}],
            "cross_process_dependency": "单流程",
            "inferred": True,
        },
    ]


def _llm_processes(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """可选：LLM 推导 processes。失败时上层切兜底。"""
    client = get_default_client()
    if not client.use_llm:
        return []

    system = (config.REPO_ROOT / "questforge/prompts/stage2_process.txt").read_text(encoding="utf-8")
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
        "请按如下 schema 输出 processes 列表：\n"
        "{\"processes\":[{\"id\":\"BP-xxx\",\"name\":\"string\",\"actors\":[{\"id\":\"UG-xxx\",\"role\":\"string\",\"level\":\"业务|管理\"}],\"triggers\":[{\"type\":\"string\",\"description\":\"string\"}],\"steps\":[{\"no\":1,\"name\":\"string\"}],\"outputs\":[{\"name\":\"string\",\"category\":\"string\"}],\"cross_process_dependency\":\"单流程|跨流程\",\"inferred\":true}]}"
    )
    out = client.chat_json(system, user)
    return out.get("processes", [])


# ========== Step 2.2 · 分类维度提取 ==========
def _extract_dimensions(processes: list[dict[str, Any]]) -> dict[str, list[str]]:
    trigger_types = {t.get("type", "") for p in processes for t in p.get("triggers", [])}
    output_cats = {
        o.get("category", "") for p in processes for o in p.get("outputs", [])
    }
    actor_levels = {
        a.get("level", "") for p in processes for a in p.get("actors", [])
    }
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
    return (tr[0].get("type") if tr else "未知触发")


def _main_output_category(p) -> str:
    outs = p.get("outputs") or []
    return (outs[0].get("category") if outs else "未知输出")


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(len(sa | sb), 1)


def _steps_names(p) -> list[str]:
    return [s.get("name", "") for s in p.get("steps", [])]


def _cluster(processes: list[dict[str, Any]]) -> dict[str, list[str]]:
    """聚类：(main_trigger, cross_process_dependency) 为主轴；
    若同 bucket 内流程 complexity 极差 > 0.3，则按复杂度中位数拆子类。

    这样既能合并"知识咨询-单文档"类里的多个文库检索流程（BP-001/002/005），
    也能把同属"案件研判-跨文档"但复杂度悬殊的 BP-003/BP-004 拆为 expert/advanced。
    """
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

    # 记录跨 bucket 相似度提醒（不自动合并，以免漏掉主题差异）
    for (k1, ps1), (k2, ps2) in combinations(buckets.items(), 2):
        if k1 == k2:
            continue
        sim = _jaccard(_steps_names(ps1[0]), _steps_names(ps2[0]))
        if sim >= 0.8:
            log.info("⚠ 跨 bucket 相似度 %.2f：%s ↔ %s（保留独立类型）", sim, k1, k2)
    return clusters


def _complexity(p: dict[str, Any]) -> float:
    step = len(p.get("steps", []))
    outs = len(p.get("outputs", []))
    # "跨 asset" 近似：步骤中 distinct 输出数 + 跨流程标记
    cross = 1 if p.get("cross_process_dependency") == "跨流程" else 0
    actor_levels = {a.get("level") for a in p.get("actors", [])}
    cross_actor = 1 if len(actor_levels) > 1 else 0
    score = (
        0.30 * min(step / 5.0, 1.0)
        + 0.30 * min((cross + cross_actor) / 2.0, 1.0)
        + 0.40 * min(outs / 3.0, 1.0)
    )
    return round(min(max(score, 0.0), 1.0), 2)


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
    """在 cluster 成员里选代表，并返回复杂度分数。"""
    # importance = complexity × coverage × business_value
    # coverage = 成员数 / 全体流程数
    coverage = len(members) / max(len(all_processes), 1)
    best = None
    best_imp = -1.0
    best_score = 0.0
    for p in members:
        c = _complexity(p)
        # business_value: 输出数 + actors 数
        bv = (len(p.get("outputs", [])) + len(p.get("actors", []))) / 5.0
        bv = max(bv, 0.3)
        imp = c * coverage * bv
        if imp > best_imp:
            best_imp = imp
            best = p
            best_score = c
    return best["id"], best_score


def _plan_tests(
    processes: list[dict[str, Any]], clusters: dict[str, list[str]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """返回 (process_types, test_plan)。"""
    pid2proc = {p["id"]: p for p in processes}
    process_types: list[dict[str, Any]] = []
    test_plan: list[dict[str, Any]] = []

    tc = IdCounter("TEST")
    for pt_id, member_ids in clusters.items():
        members = [pid2proc[m] for m in member_ids]
        # cluster 复杂度取 max（代表难度取决于最复杂的那一个）
        rep_id, _ = _pick_representative(members, processes)
        rep = pid2proc[rep_id]
        cluster_cx = max(_complexity(p) for p in members)
        difficulty = _assign_difficulty(cluster_cx)

        main_trigger = _main_trigger(rep)
        main_output = _main_output_category(rep)
        cross = rep.get("cross_process_dependency", "单流程")
        scope_label = "跨文档" if cross == "跨流程" else "单文档"

        # 类型命名：纠错类单独点名；其余用"触发-单/跨文档"
        if main_output == "纠错清单":
            pt_name = "审核复核-文书纠错类"
            # 纠错任务天然包含"识别错误+给依据+规范表达"，最低 advanced
            if difficulty == "basic":
                difficulty = "advanced"
                cluster_cx = max(cluster_cx, config.DIFFICULTY_THRESHOLDS["basic"] + 0.05)
        elif main_trigger == "案件研判" and main_output == "决策建议":
            pt_name = "案件研判-综合决策类"
        else:
            pt_name = f"{main_trigger}-{scope_label}类"

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
_FIVE_STAGES = ["定义问题", "拆解问题", "方案生成", "执行落地", "元认知"]


def _derive_focus_stages(difficulty: str, trigger: str, output: str) -> list[str]:
    """按难度与流程特征选 focus_stages。"""
    if difficulty == "expert":
        return list(_FIVE_STAGES)
    if output == "纠错清单":
        return ["执行落地", "元认知"]
    if trigger == "案件研判":
        return ["拆解问题", "方案生成"]
    # basic 默认"定义问题"
    return ["定义问题"]


def _build_coverage_matrix(test_plan: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    matrix: dict[str, dict[str, str]] = {}
    for t in test_plan:
        row = {s: "常规" for s in _FIVE_STAGES}
        for s in t.get("focus_stages", []):
            if s in row:
                row[s] = "重点"
        matrix[t["test_id"]] = row
    return matrix


# ========== 主流程 ==========
def run(stage1_md: Path | str, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else config.ensure_out_dir()
    out_path = out_dir / "02_plan.md"

    parsed = read_md(stage1_md)
    artifacts = parsed["artifacts"]
    log.info(
        "[Stage2] 上游 pass_gate=%s, features=%d, user_groups=%d",
        parsed["frontmatter"].get("pass_gate"),
        len(artifacts.get("features", [])),
        len(artifacts.get("user_groups", [])),
    )

    remarks: list[str] = []

    # Step 2.1 流程推导
    processes = _llm_processes(artifacts)
    llm_used = bool(processes)
    if not processes:
        processes = _fallback_processes(
            artifacts.get("user_groups", []),
            artifacts.get("features", []),
        )
        remarks.append("业务流程走本地兜底推导（第一层 Fallback 触发）")

    # Step 2.2
    dimensions = _extract_dimensions(processes)
    effective_dims = {k: v for k, v in dimensions.items() if len(v) >= 2}
    if len(effective_dims) < 2:
        remarks.append(
            f"有效分类维度不足（{len(effective_dims)}/4），以触发+输出组合为聚类主轴"
        )

    # Step 2.3 聚类
    clusters = _cluster(processes)

    # Step 2.4-2.5
    process_types, test_plan = _plan_tests(processes, clusters)

    # 微调：如果题目 < 3，从每类补次优流程（本项目通常 4 类，不触发）
    if len(test_plan) < 3:
        remarks.append(
            f"聚类数 {len(test_plan)} < 3，后续阶段可考虑补次优流程"
        )

    # Step 2.6 覆盖矩阵
    coverage_matrix = _build_coverage_matrix(test_plan)

    artifacts_out = {
        "fallback_status": {
            "business_processes_present": False,  # 源文档无流程定义段
            "capability_scope_present": False,
            "llm_path_taken": llm_used,
        },
        "processes": processes,
        "dimensions": dimensions,
        "effective_dimensions": list(effective_dims.keys()),
        "process_types": process_types,
        "test_plan": test_plan,
        "coverage_matrix_plan": coverage_matrix,
    }

    # ===== 校验清单（§4.4） =====
    checklist = Checklist()
    ok_steps = all(len(p.get("steps", [])) >= 3 for p in processes)
    checklist.add(f"每条 BP ≥ 3 个步骤（共 {len(processes)} 条 BP）", ok_steps)

    vocab = set(config.TRIGGER_VOCAB) | set(artifacts.get("glossary", {}).keys())
    tr_types = {t.get("type") for p in processes for t in p.get("triggers", [])}
    checklist.add(
        "触发类型取值来自预设词表或 Stage 1 glossary",
        all(t in vocab for t in tr_types if t),
    )

    checklist.add(
        f"聚类后的类型数 = test_plan 题目数（{len(process_types)} vs {len(test_plan)}）",
        len(process_types) == len(test_plan),
    )

    diffs = {t["difficulty"] for t in test_plan}
    checklist.add(f"难度分配覆盖 ≥ 2 级（实际 {sorted(diffs)}）", len(diffs) >= 2)

    each_has_focus = all(
        any(v == "重点" for v in row.values()) for row in coverage_matrix.values()
    )
    checklist.add("覆盖矩阵蓝图中每道题至少 1 个'重点'阶段", each_has_focus)

    # 功能覆盖（用户需求：知识库检索 四大类 + 文书纠错）
    types_names = {pt["name"] for pt in process_types}
    has_retrieval = any("知识咨询" in n for n in types_names)
    has_correction = any("纠错" in n for n in types_names)
    checklist.add(
        "process_types 同时包含'知识咨询'类与'文书纠错'类",
        has_retrieval and has_correction,
    )

    # ===== 渲染 MD =====
    summary = (
        f"共提取 {len(processes)} 条业务流程，全部为本地推导（inferred=true）；"
        f"按'触发-输出'组合聚类为 {len(process_types)} 个类型，"
        f"规划 {len(test_plan)} 道题："
        + "、".join(f"{len([t for t in test_plan if t['difficulty']==d])} {d}" for d in ("basic", "advanced", "expert"))
        + "。"
        f"第一层 Fallback 已触发（源文档无流程定义段）。"
    )

    sections = [
        Section(
            "Fallback 触发情况",
            md_table(
                ["项", "状态", "说明"],
                [
                    ["business_processes 段存在", "❌", "全部走推导路径（LLM+本地兜底）"],
                    ["capability_scope.weak_points", "❌", "将在 Stage 3 触发第二层 Fallback"],
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
                [
                    [dim, len(vals), "、".join(vals) if vals else "—"]
                    for dim, vals in dimensions.items()
                ],
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
                    [
                        t["test_id"],
                        t["process_type"],
                        t["source_process"],
                        t["difficulty"],
                        "、".join(t["focus_stages"]),
                    ]
                    for t in test_plan
                ],
            ),
        ),
        Section(
            "覆盖矩阵蓝图",
            md_table(
                [""] + _FIVE_STAGES,
                [[tid] + [coverage_matrix[tid][s] for s in _FIVE_STAGES] for tid in coverage_matrix],
            ),
        ),
    ]

    frontmatter = {
        "stage": 2,
        "stage_name": "process_and_plan",
        "version": "1.0",
        "upstream": "01_understanding.md",
        "downstream": "03_context.md",
        "domain": config.DOMAIN,
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
        remarks="\n".join(f"- {r}" for r in remarks) if remarks else "（无）",
    )
    return out_path


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage1", required=True, help="path to 01_understanding.md")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    out = run(args.stage1, Path(args.out) if args.out else None)
    print(f"[Stage2] produced: {out}")
