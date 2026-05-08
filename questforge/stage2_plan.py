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
                "depends_on": p.get("depends_on") or [],
                "inferred": False,
            }
        )
    return normalized


def _llm_processes(client: LLMClient, artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """调用 LLM 按 `流程 = 用户 × 功能 × 业务目标` 推导业务流程。

    注入 docs_digest、features.input/output、knowledge_assets sample_rows + columns,
    让 LLM 看到原始文档与真实数据再推流程。
    """
    system_path = config.REPO_ROOT / "questforge/prompts/stage2_process.txt"
    system = system_path.read_text(encoding="utf-8")
    payload = {
        "business_goal": artifacts.get("business_goal", {}),
        "user_groups": artifacts.get("user_groups", []),
        "features": [
            {
                "id": f.get("id"),
                "name": f.get("name"),
                "input": f.get("input"),
                "output": f.get("output"),
                "depends_on": f.get("depends_on"),
            }
            for f in artifacts.get("features", [])
        ],
        "knowledge_assets": [
            {
                "id": a["id"],
                "category": a.get("category"),
                "authority": a.get("authority"),
                "key_fields": a.get("key_fields"),
                "columns": (a.get("columns") or [])[:12],
                "sample_rows": (a.get("sample_rows") or [])[:1],
            }
            for a in artifacts.get("knowledge_assets", [])
        ],
        "glossary_keys": list(artifacts.get("glossary", {}).keys())[:20],
        "docs_digest": (artifacts.get("docs_digest") or "")[:3500],
    }
    user = (
        "<stage1_artifacts>\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n</stage1_artifacts>\n"
        "请按如下 schema 输出 processes 列表(每条流程至少 3 个 step,标 inferred=true):\n"
        '{"processes":[{"id":"BP-xxx","name":"string",'
        '"actors":[{"id":"UG-xxx","role":"string","level":"业务|管理"}],'
        '"triggers":[{"type":"string","description":"string"}],'
        '"steps":[{"no":1,"name":"string"}],'
        '"outputs":[{"name":"string","category":"string"}],'
        '"depends_on":["KB-xxx"],'
        '"cross_process_dependency":"单流程|跨流程",'
        '"expected_difficulty":"basic|advanced|expert",'
        '"inferred":true}]}\n'
        "注意:depends_on 必须引用 knowledge_assets 中已存在的 KB id,"
        "expected_difficulty 必须真实反映 steps/outputs/cross 三项构成。"
    )
    out = client.chat_json(system, user, max_tokens=4000)
    raw = out.get("processes", []) if isinstance(out, dict) else []
    return [n for n in (_normalize_process_schema(p) for p in raw) if n]


def _llm_extend_processes(
    client: LLMClient,
    artifacts: dict[str, Any],
    existing: list[dict[str, Any]],
    target_kind: str,
) -> list[dict[str, Any]]:
    """补强调用:基于已生成流程,要求 LLM 追加更高/更低复杂度的流程。

    target_kind 为 'expert' 时要求 steps≥6 / outputs≥2 / cross / 含管理层;
    为 'basic' 时反之。返回新增流程列表(可空)。
    """
    system_path = config.REPO_ROOT / "questforge/prompts/stage2_process.txt"
    system = system_path.read_text(encoding="utf-8")
    brief_existing = [
        {
            "id": p["id"],
            "name": p.get("name"),
            "steps_count": len(p.get("steps", [])),
            "outputs_count": len(p.get("outputs", [])),
            "cross": p.get("cross_process_dependency"),
            "expected_difficulty": p.get("expected_difficulty"),
        }
        for p in existing
    ]
    if target_kind == "expert":
        spec = (
            "新增至少 1 条 expert 流程: steps≥6 / outputs≥2 /"
            " cross_process_dependency=跨流程 / actors 含 level=管理 的角色。"
        )
    else:
        spec = (
            "新增至少 1 条 basic 流程: steps≤3 / outputs=1 /"
            " cross_process_dependency=单流程 / actors 仅业务层。"
        )
    payload = {
        "business_goal": artifacts.get("business_goal", {}),
        "knowledge_assets": [
            {"id": a["id"], "category": a.get("category"), "authority": a.get("authority")}
            for a in artifacts.get("knowledge_assets", [])
        ],
        "docs_digest": (artifacts.get("docs_digest") or "")[:1800],
    }
    user = (
        "<stage1_artifacts>\n" + json.dumps(payload, ensure_ascii=False) + "\n</stage1_artifacts>\n"
        "<existing_processes>\n" + json.dumps(brief_existing, ensure_ascii=False) + "\n</existing_processes>\n"
        f"现有流程在复杂度上有缺口,{spec}\n"
        "新增流程的 id 不得与 existing 重复;同样按 stage2_process schema 输出 processes 数组。"
    )
    out = client.chat_json(system, user, max_tokens=2200)
    raw = out.get("processes", []) if isinstance(out, dict) else []
    return [n for n in (_normalize_process_schema(p) for p in raw) if n]


def _next_bp_id(taken: set[str]) -> str:
    n = 1
    while f"BP-{n:03d}" in taken:
        n += 1
    return f"BP-{n:03d}"


def _normalize_process_schema(p: dict[str, Any]) -> dict[str, Any] | None:
    """把 LLM 偶尔返回的字符串/None 归一为 dict 列表;不可修复则返回 None。"""
    if not isinstance(p, dict) or not p.get("name"):
        return None

    def _to_dicts(items: Any, default_keys: tuple[str, ...]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for it in items or []:
            if isinstance(it, dict):
                out.append(it)
            elif isinstance(it, str) and it.strip():
                # 字符串退化:塞到第一个默认键里
                out.append({default_keys[0]: it.strip()})
        return out

    p["triggers"] = _to_dicts(p.get("triggers"), ("type", "description"))
    p["steps"] = _to_dicts(p.get("steps"), ("name",))
    p["outputs"] = _to_dicts(p.get("outputs"), ("name", "category"))
    p["actors"] = _to_dicts(p.get("actors"), ("role",))
    if not isinstance(p.get("depends_on"), list):
        p["depends_on"] = []
    if "cross_process_dependency" not in p:
        p["cross_process_dependency"] = "单流程"
    return p


def _audit_complexity_gradient(
    processes: list[dict[str, Any]],
    artifacts: dict[str, Any],
    client: LLMClient,
) -> tuple[list[dict[str, Any]], str]:
    """检查复杂度梯度;不达标则尝试 1 次 LLM 补强。返回(processes, audit_note)。"""
    if not processes:
        return processes, "processes 为空,跳过梯度自检"
    scores = [_complexity(p) for p in processes]
    diffs = {_assign_difficulty(s) for s in scores}
    span = max(scores) - min(scores)
    has_expert = "expert" in diffs

    if span >= 0.3 and len(diffs) >= 2 and has_expert:
        return processes, "复杂度梯度自检通过"

    target = "expert" if not has_expert else "basic"
    log.info("[Stage2] 复杂度梯度不足(span=%.2f, diffs=%s),触发 LLM 补强 → %s", span, diffs, target)
    extra = _llm_extend_processes(client, artifacts, processes, target)
    if not extra:
        return processes, f"梯度不足且 LLM 补强未返回新流程(target={target})"

    existing_ids = {p["id"] for p in processes}
    merged = list(processes)
    for p in extra:
        pid = p.get("id")
        if not pid or pid in existing_ids or not pid.startswith("BP-"):
            pid = _next_bp_id(existing_ids)
        existing_ids.add(pid)
        p["id"] = pid
        p["inferred"] = True
        p.setdefault("expected_difficulty", target)
        merged.append(p)
    return merged, f"已通过 LLM 补强追加 {len(extra)} 条 {target} 流程"


def _audit_feature_coverage(
    processes: list[dict[str, Any]],
    features: list[dict[str, Any]],
    artifacts: dict[str, Any],
    client: LLMClient,
) -> tuple[list[dict[str, Any]], list[str]]:
    """用户提供 business_processes 时校验是否覆盖所有 features。

    任一 feature 名未在任何 BP 名/depends_on 中体现,且 LLM 可用 → 自动补 1 条;
    不可用 → 返回缺口列表给上层 raise MissingInputError。
    """
    if not processes or not features:
        return processes, []

    proc_text = " ".join(
        (p.get("name") or "") + " " + " ".join(p.get("depends_on") or []) for p in processes
    )
    uncovered = [
        f for f in features
        if (f.get("name") or "") and (f.get("name") not in proc_text)
        and not any(dep in (p.get("depends_on") or []) for p in processes for dep in (f.get("depends_on") or []))
    ]
    if not uncovered:
        return processes, []

    if not client.use_llm:
        return processes, [f.get("name", "?") for f in uncovered]

    log.info("[Stage2] 用户提供流程未覆盖 %d 个 feature,触发 LLM 补全", len(uncovered))
    extra = _llm_extend_processes(client, artifacts, processes, target_kind="basic")
    if not extra:
        return processes, [f.get("name", "?") for f in uncovered]

    existing_ids = {p["id"] for p in processes}
    for p in extra:
        pid = p.get("id")
        if not pid or pid in existing_ids or not pid.startswith("BP-"):
            pid = _next_bp_id(existing_ids)
        existing_ids.add(pid)
        p["id"] = pid
        p["inferred"] = True
        p["audit_supplement"] = True
        processes.append(p)
    return processes, []


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
    buckets: dict[tuple[str, str, str, bool], list[dict[str, Any]]] = {}
    for p in processes:
        has_mgmt = any(a.get("level") == "管理" for a in p.get("actors", []) or [])
        key = (
            _main_trigger(p),
            p.get("cross_process_dependency", "单流程"),
            _main_output_category(p),
            has_mgmt,
        )
        buckets.setdefault(key, []).append(p)

    clusters: dict[str, list[str]] = {}
    idc = IdCounter("PT")
    for key, ps in buckets.items():
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


def _member_sampling_novelty(candidate: dict[str, Any], chosen: list[dict[str, Any]]) -> float:
    """给 cluster 内候选流程打“新颖度”分,优先挑和已选流程更不重合的 source_process。"""
    if not chosen:
        return 1.0

    cand_steps = _steps_names(candidate)
    cand_assets = candidate.get("depends_on") or []
    cand_output = _main_output_category(candidate)
    novelty_scores: list[float] = []
    for other in chosen:
        step_overlap = _jaccard(cand_steps, _steps_names(other))
        asset_overlap = _jaccard(cand_assets, other.get("depends_on") or [])
        output_overlap = 1.0 if cand_output == _main_output_category(other) else 0.0
        overlap = 0.5 * step_overlap + 0.4 * asset_overlap + 0.1 * output_overlap
        novelty_scores.append(1 - overlap)
    return min(novelty_scores)


def _ordered_members_for_sampling(members: list[dict[str, Any]], rep_id: str) -> list[dict[str, Any]]:
    """先放 representative,剩余成员按与已选流程的差异度贪心排序。"""
    pid2proc = {member["id"]: member for member in members}
    ordered = [pid2proc[rep_id]]
    remaining = [member for member in members if member["id"] != rep_id]

    while remaining:
        best = max(
            remaining,
            key=lambda proc: (_member_sampling_novelty(proc, ordered), _complexity(proc)),
        )
        ordered.append(best)
        remaining = [member for member in remaining if member["id"] != best["id"]]
    return ordered


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

        sampled_members = _ordered_members_for_sampling(members, rep_id)
        planned_tests = min(max(1, config.TESTS_PER_TYPE), len(sampled_members))

        process_types.append(
            {
                "type_id": pt_id,
                "name": pt_name,
                "members": member_ids,
                "representative": rep_id,
                "complexity_score": round(cluster_cx, 2),
                "assigned_difficulty": difficulty,
                "planned_tests": planned_tests,
            }
        )

        for idx, source_proc in enumerate(sampled_members[:planned_tests]):
            focus_stages = _derive_focus_stages(
                difficulty,
                _main_trigger(source_proc),
                _main_output_category(source_proc),
                idx,
            )
            test_plan.append(
                {
                    "test_id": tc.next(),
                    "process_type": pt_id,
                    "source_process": source_proc["id"],
                    "difficulty": difficulty,
                    "focus_stages": focus_stages,
                    "sample_idx": idx,
                }
            )
    return process_types, test_plan


# ========== Step 2.6 · 覆盖矩阵蓝图 ==========
def _derive_focus_stages(
    difficulty: str, trigger: str, output: str, sample_idx: int = 0
) -> list[str]:
    """按难度与流程特征选 focus_stages;sample_idx 让同 type 多道题分散焦点。"""
    if difficulty == "expert":
        return list(config.FIVE_STAGES)

    # 特殊分支:输出为纠错/审核类
    if any(kw in output for kw in ("纠错", "审核", "校对")):
        rota = [
            ["执行落地", "元认知"],
            ["方案生成", "执行落地"],
            ["定义问题", "元认知"],
        ]
        return rota[sample_idx % len(rota)]

    # 特殊分支:触发为研判/分析类
    if any(kw in trigger for kw in ("研判", "分析", "决策")):
        rota = [
            ["拆解问题", "方案生成"],
            ["定义问题", "方案生成"],
            ["拆解问题", "元认知"],
        ]
        return rota[sample_idx % len(rota)]

    # 通用梯度
    if difficulty == "basic":
        rota = [
            ["定义问题"],
            ["执行落地"],
            ["拆解问题"],
        ]
    else:  # advanced
        rota = [
            ["定义问题", "方案生成"],
            ["拆解问题", "执行落地"],
            ["方案生成", "元认知"],
        ]
    return rota[sample_idx % len(rota)]


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
    client = get_default_client()
    audit_notes: list[str] = []
    if agent_input.business_processes:
        processes = _transcribe_user_processes(agent_input.business_processes)
        # 用户路径补全检测:覆盖度审计
        processes, uncovered = _audit_feature_coverage(
            processes, artifacts.get("features", []), artifacts, client
        )
        if uncovered:
            raise MissingInputError(
                stage="Stage 2 · 业务流程提取",
                report=[
                    MissingField(
                        field_name="business_processes 覆盖度",
                        why_needed=(
                            f"用户提供的 business_processes 未覆盖以下 features: {uncovered}; "
                            "Stage 2 需要每个核心 feature 至少出现在一条 BP 的 name 或 depends_on 中,"
                            "否则 Stage 3 无法为这些 feature 生成题目"
                        ),
                        suggested_format=(
                            "两种选择:(a) 在 example_input.json 的 business_processes 追加上述 features 的对应流程;"
                            "(b) 启用 LLM(配置 LLM_API_KEY) 让 Pipeline 自动补全"
                        ),
                        example=(
                            '"business_processes": [..., {"id":"BP-X","name":"<feature 名>",'
                            '"depends_on":["KB-..."],"steps":[...],...}]'
                        ),
                    )
                ],
            )
        llm_used = False
        fallback_1 = False
        remarks_extra = "用户已在 AgentInput.business_processes 提供流程,直接转录"
    else:
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
        # 复杂度梯度自检 + 必要时 1 次 LLM 补强
        processes, audit_note = _audit_complexity_gradient(processes, artifacts, client)
        audit_notes.append(audit_note)
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
    remarks.extend(audit_notes)
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

    expected_tests = sum(int(pt.get("planned_tests", 0)) for pt in process_types)
    checklist.add(
        f"test_plan 题目数与按类型多样性规划一致({expected_tests} vs {len(test_plan)})",
        len(test_plan) == expected_tests,
    )

    diffs = {t["difficulty"] for t in test_plan}
    if len(diffs) < 2:
        remarks.append(
            f"难度分配仅覆盖 {sorted(diffs)} 1 级;如需梯度评测,建议补充 business_processes"
            "或调整 features.input/output 以诱导 LLM 推出复杂度差异大的流程"
        )
    limited_types = [pt for pt in process_types if pt.get("planned_tests", 0) < max(1, config.TESTS_PER_TYPE)]
    if limited_types:
        remarks.append(
            "以下类型因缺少可拉开独立性的成员流程,未按配置值重复采样:"
            + "、".join(f"{pt['type_id']}({pt['planned_tests']}/{config.TESTS_PER_TYPE})" for pt in limited_types)
        )

    each_has_focus = all(any(v == "重点" for v in row.values()) for row in coverage_matrix.values())
    checklist.add("覆盖矩阵蓝图中每道题至少 1 个'重点'阶段", each_has_focus)

    checklist.add("test_plan 非空", len(test_plan) > 0)

    # ===== 渲染 MD =====
    summary = (
        f"共提取 {len(processes)} 条业务流程({'用户提供' if not fallback_1 else 'LLM 推导'});"
        f"按'触发×跨流程×输出×管理层'组合聚类为 {len(process_types)} 个类型,"
        f"按类型多样性实际规划 {len(test_plan)} 道(单类最多 {config.TESTS_PER_TYPE} 道):"
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
                ["类型 ID", "类型名", "成员 BP", "代表 BP", "复杂度", "分配难度", "规划题数"],
                [
                    [
                        pt["type_id"],
                        pt["name"],
                        ",".join(pt["members"]),
                        pt["representative"],
                        pt["complexity_score"],
                        pt["assigned_difficulty"],
                        pt.get("planned_tests", 0),
                    ]
                    for pt in process_types
                ],
            ),
        ),
        Section(
            "题目规划",
            md_table(
                ["题号", "流程类型", "来源流程", "难度", "focus_stages"],
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
