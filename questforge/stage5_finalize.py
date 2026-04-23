"""Stage 5 · 验证 + benchmark → 05_report.md + dataset.{json,xlsx}

输入:04_tests.md + 03_context.md + 02_plan.md + 01_understanding.md
输出:
  - OUT_DIR / 05_report.md
  - OUT_DIR / dataset.json
  - OUT_DIR / dataset.xlsx
  - OUT_DIR / traceability.json
  - OUT_DIR / dataset_supplementary/{rubrics,coverage_matrix,traceability}.json

本阶段纯本地执行,不依赖 LLM。
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd

from . import config
from .common import Checklist, Section, iso_now, md_table, read_md, write_md
from .input_spec import AgentInput, MissingField, MissingInputError
from .io_utils import extract_local_keywords

log = logging.getLogger("questforge.stage5")

_REFERENCE_STAGE_MAP: list[tuple[str, str]] = [
    ("定义问题", "define_problem"),
    ("拆解问题", "decompose"),
    ("方案生成", "solution"),
    ("执行落地", "execution"),
    ("元认知", "metacognition"),
]
_REFERENCE_KEYS = tuple(key for _, key in _REFERENCE_STAGE_MAP)
_ALLOWED_EVIDENCE = {"keyword_match", "semantic_match", "llm_judge"}
_FEAT_ID_RE = re.compile(r"\bFEAT-\d+\b")


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list_nonempty(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(v).strip() for v in values if str(v).strip()]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _unique_preserve(items: list[Any]) -> list[Any]:
    seen = set()
    out = []
    for item in items:
        marker = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, dict) else item
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out


def _reference_complete(item: dict[str, Any]) -> bool:
    ref = item.get("reference") or {}
    return all(isinstance(ref.get(key), dict) and ref.get(key) for key in _REFERENCE_KEYS)


def _atomic_stage_points(stage_key: str, payload: dict[str, Any]) -> int:
    if stage_key == "define_problem":
        return int(_nonempty_text(payload.get("intent_understanding"))) + len(
            _list_nonempty(payload.get("implicit_needs"))
        ) + int(_nonempty_text(payload.get("problem_essence")))
    if stage_key == "decompose":
        return len(_list_nonempty(payload.get("expected_steps"))) + int(
            _nonempty_text(payload.get("priority_ordering"))
        )
    if stage_key == "solution":
        return len(_list_nonempty(payload.get("information_sources"))) + int(
            _nonempty_text(payload.get("cross_doc_integration"))
        )
    if stage_key == "execution":
        return int(_nonempty_text(payload.get("output_format"))) + int(
            _nonempty_text(payload.get("exception_handling"))
        )
    if stage_key == "metacognition":
        return int(_nonempty_text(payload.get("source_annotation"))) + int(
            _nonempty_text(payload.get("uncertainty_acknowledgment"))
        ) + int(_nonempty_text(payload.get("boundary_awareness")))
    return 0


def _stage_rich_threshold(stage_name: str) -> int:
    return {
        "定义问题": 3,
        "拆解问题": 4,
        "方案生成": 2,
        "执行落地": 2,
        "元认知": 3,
    }.get(stage_name, 2)


def _build_answer_template(item: dict[str, Any]) -> str:
    ref = item.get("reference") or {}
    define = ref.get("define_problem") or {}
    decompose = ref.get("decompose") or {}
    solution = ref.get("solution") or {}
    execution = ref.get("execution") or {}
    meta = ref.get("metacognition") or {}

    parts = [
        (
            "定义问题：识别意图="
            f"{(define.get('intent_understanding') or '').strip()}；"
            f"隐含诉求={'、'.join(_list_nonempty(define.get('implicit_needs'))) or '无'}；"
            f"问题本质={(define.get('problem_essence') or '').strip()}"
        ),
        (
            "拆解问题：步骤="
            f"{' → '.join(_list_nonempty(decompose.get('expected_steps'))) or '无'}；"
            f"优先顺序={(decompose.get('priority_ordering') or '').strip()}"
        ),
        (
            "方案生成：信息源="
            f"{' | '.join(_list_nonempty(solution.get('information_sources'))) or '无'}；"
            f"跨文档整合={(solution.get('cross_doc_integration') or '').strip()}"
        ),
        (
            "执行落地：输出格式="
            f"{(execution.get('output_format') or '').strip()}；"
            f"异常处理={(execution.get('exception_handling') or '').strip()}"
        ),
        (
            "元认知：出处标注="
            f"{(meta.get('source_annotation') or '').strip()}；"
            f"不确定性={(meta.get('uncertainty_acknowledgment') or '').strip()}；"
            f"边界意识={(meta.get('boundary_awareness') or '').strip()}"
        ),
    ]
    return "\n".join(parts)


def _dataset_meta(
    *,
    agent_input: AgentInput,
    business_goal: dict[str, Any],
    items: list[dict[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    difficulty_distribution = dict(Counter((item.get("difficulty") or "unknown") for item in items))
    return {
        "version": "1.0",
        "domain": agent_input.domain,
        "business_goal": (business_goal.get("one_liner") or agent_input.business_goal or "").strip(),
        "success_metric": (business_goal.get("success_metric") or "NOT_SPECIFIED").strip(),
        "created_at": created_at,
        "total_items": len(items),
        "difficulty_distribution": difficulty_distribution,
        "source_channel": agent_input.source_channel,
    }


def _user_profile_hit(
    item: dict[str, Any],
    process: dict[str, Any],
    user_group_by_id: dict[str, dict[str, Any]],
) -> tuple[bool, list[str]]:
    context = item.get("context") or {}
    prompt = (item.get("prompt") or "").strip()
    context_role = (context.get("user_role") or "").strip()
    roles: list[str] = []
    for actor in process.get("actors") or []:
        actor_id = actor.get("id") or ""
        mapped = (user_group_by_id.get(actor_id) or {}).get("role")
        role = (mapped or actor.get("role") or "").strip()
        if role:
            roles.append(role)
    roles = _unique_preserve(roles)

    hit_roles = [
        role
        for role in roles
        if role and (
            role in context_role
            or role in prompt
            or (bool(context_role) and context_role in role)
        )
    ]
    if not roles and context_role:
        return True, [context_role]
    return bool(hit_roles), (hit_roles or roles or ([context_role] if context_role else []))


def _quantifiable_criteria(item: dict[str, Any]) -> bool:
    rubric = item.get("rubric") or {}
    if rubric.get("total_max_score") != 10:
        return False
    stages = rubric.get("stages") or []
    if {s.get("stage_name") for s in stages} != set(config.FIVE_STAGES):
        return False
    for stage in stages:
        if stage.get("stage_name") not in config.STAGE4_STAGE_WEIGHTS:
            return False
        if float(stage.get("max_score", 0)) != config.STAGE4_STAGE_WEIGHTS[stage["stage_name"]]:
            return False
        for point in stage.get("scoring_points") or []:
            evidence_type = point.get("evidence_type")
            if evidence_type not in _ALLOWED_EVIDENCE:
                return False
            if evidence_type == "keyword_match" and not _list_nonempty(point.get("keywords")):
                return False
            if not _nonempty_text(point.get("description")):
                return False
    return True


def _prediction_power_hits(
    item: dict[str, Any],
    process: dict[str, Any],
    business_goal: dict[str, Any],
) -> list[str]:
    goal_texts = [
        (business_goal.get("success_metric") or "").strip(),
        (business_goal.get("one_liner") or "").strip(),
    ]
    goal_texts.extend((out.get("name") or "").strip() for out in process.get("outputs") or [])
    goal_texts.extend(_list_nonempty((item.get("context") or {}).get("success_criteria")))

    candidates: list[str] = []
    for text in goal_texts:
        if not text:
            continue
        candidates.append(text)
        candidates.extend(extract_local_keywords(text, top_k=6))
    candidates = [c for c in candidates if c and len(c) >= 2]
    candidates = _unique_preserve(candidates)

    haystack = " ".join(
        [
            (item.get("prompt") or "").strip(),
            " ".join(_list_nonempty(item.get("tags"))),
            (item.get("answer_template") or "").strip(),
        ]
    )
    hits = [c for c in candidates if c in haystack]
    return _unique_preserve(hits)[:5]


def _validate_principles(
    items: list[dict[str, Any]],
    *,
    tctx_by_id: dict[str, dict[str, Any]],
    process_by_id: dict[str, dict[str, Any]],
    user_group_by_id: dict[str, dict[str, Any]],
    business_goal: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for item in items:
        tid = item["test_id"]
        process = process_by_id.get(item.get("source_process") or "", {})
        test_ctx = tctx_by_id.get(tid, {})

        role_hit, roles = _user_profile_hit(item, process, user_group_by_id)
        realism = test_ctx.get("realism_check") or {}
        realism_total = int(realism.get("total") or 0)
        realism_passed = int(realism.get("passed") or 0)
        real_encounter = role_hit and realism_total > 0 and realism_total == realism_passed

        five_stage_coverage = _reference_complete(item)
        quantifiable_criteria = _quantifiable_criteria(item)

        constraint_n = len(test_ctx.get("constraints") or [])
        interference_n = len(test_ctx.get("interferences") or [])
        difficulty_score = float(item.get("difficulty_score") or 0)
        discrimination = difficulty_score >= 1.5 or (constraint_n + interference_n) >= 2

        metric_hits = _prediction_power_hits(item, process, business_goal)
        prediction_power = bool(metric_hits)

        notes = []
        if roles:
            notes.append(f"角色={' / '.join(roles)}")
        notes.append(f"真实性={realism_passed}/{realism_total}")
        if metric_hits:
            notes.append(f"metric_hits={'/'.join(metric_hits)}")

        results[tid] = {
            "real_encounter": real_encounter,
            "five_stage_coverage": five_stage_coverage,
            "quantifiable_criteria": quantifiable_criteria,
            "discrimination": discrimination,
            "prediction_power": prediction_power,
            "passed": all(
                [
                    real_encounter,
                    five_stage_coverage,
                    quantifiable_criteria,
                    discrimination,
                    prediction_power,
                ]
            ),
            "notes": notes,
        }
    return results


def _gap_hint(stage_name: str, points: int, item: dict[str, Any]) -> str:
    ref = item.get("reference") or {}
    if stage_name == "拆解问题":
        steps = _list_nonempty((ref.get("decompose") or {}).get("expected_steps"))
        if len(steps) <= 3:
            return "补充异常分支或更细的步骤约束"
    if stage_name == "方案生成":
        sources = _list_nonempty((ref.get("solution") or {}).get("information_sources"))
        if len(sources) <= 1:
            return "补充信息源或跨文档整合策略"
    if stage_name == "元认知":
        return "补充不确定性或边界意识说明"
    return "补充该阶段的 reference 检验点"


def _compute_coverage_matrix(
    items: list[dict[str, Any]],
    coverage_blueprint: dict[str, dict[str, str]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    actual: dict[str, dict[str, Any]] = {}
    gaps: list[dict[str, Any]] = []

    for item in items:
        tid = item["test_id"]
        ref = item.get("reference") or {}
        actual[tid] = {}
        for stage_name, stage_key in _REFERENCE_STAGE_MAP:
            payload = ref.get(stage_key) or {}
            points = _atomic_stage_points(stage_key, payload)
            covered = points >= 1
            rich = points >= _stage_rich_threshold(stage_name)
            blueprint = (coverage_blueprint.get(tid) or {}).get(stage_name, "常规")
            actual[tid][stage_name] = {
                "blueprint": blueprint,
                "covered": covered,
                "rich": rich,
                "points": points,
            }

            severity = ""
            if blueprint == "重点":
                if not covered:
                    severity = "high"
                elif not rich:
                    severity = "medium"
            else:
                if not covered:
                    severity = "medium"
                elif not rich:
                    severity = "low"
            if severity:
                gaps.append(
                    {
                        "test_id": tid,
                        "stage": stage_name,
                        "severity": severity,
                        "hint": _gap_hint(stage_name, points, item),
                    }
                )
    return actual, gaps


def _discrimination_estimate(
    items: list[dict[str, Any]],
    tctx_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        tid = item["test_id"]
        test_ctx = tctx_by_id.get(tid, {})
        difficulty_score = float(item.get("difficulty_score") or 0)
        difficulty_norm = _clamp((difficulty_score - 1.0) / 2.0)
        constraint_norm = _clamp(len(test_ctx.get("constraints") or []) / 4.0)
        interference_norm = _clamp(len(test_ctx.get("interferences") or []) / 2.0)
        cross_asset_norm = _clamp((len(_unique_preserve(test_ctx.get("primary_assets") or [])) - 1) / 2.0)

        est_d = (
            0.4 * difficulty_norm
            + 0.2 * constraint_norm
            + 0.3 * interference_norm
            + 0.1 * cross_asset_norm
        )
        if est_d >= 0.40:
            grade = "优秀"
        elif est_d >= 0.30:
            grade = "合格"
        elif est_d >= 0.20:
            grade = "待改进"
        else:
            grade = "淘汰"

        major = []
        if constraint_norm >= 0.75:
            major.append("约束密度高")
        if interference_norm >= 0.5:
            major.append("干扰设计强")
        if cross_asset_norm >= 0.5:
            major.append("跨资产整合")
        if difficulty_norm >= 0.65:
            major.append("难度偏高")
        if not major:
            major.append("难度偏低但可作为基线题")

        out[tid] = {
            "est_D": round(est_d, 2),
            "grade": grade,
            "difficulty_score_normalized": round(difficulty_norm, 2),
            "constraint_density_normalized": round(constraint_norm, 2),
            "interference_density_normalized": round(interference_norm, 2),
            "cross_asset_degree_normalized": round(cross_asset_norm, 2),
            "major_contributors": major,
        }
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(len(a | b), 1)


def _independence_score(
    items: list[dict[str, Any]],
    tctx_by_id: dict[str, dict[str, Any]],
) -> tuple[float, list[str], list[dict[str, Any]]]:
    if len(items) <= 1:
        return 1.0, [], []

    pair_details: list[dict[str, Any]] = []
    for left, right in combinations(items, 2):
        lctx = tctx_by_id.get(left["test_id"], {})
        rctx = tctx_by_id.get(right["test_id"], {})
        left_assets = set(lctx.get("primary_assets") or [])
        right_assets = set(rctx.get("primary_assets") or [])
        left_keywords = set(_list_nonempty(lctx.get("keyword_pool")))
        right_keywords = set(_list_nonempty(rctx.get("keyword_pool")))
        left_steps = set(
            _list_nonempty(((left.get("reference") or {}).get("decompose") or {}).get("expected_steps"))
        )
        right_steps = set(
            _list_nonempty(((right.get("reference") or {}).get("decompose") or {}).get("expected_steps"))
        )

        asset_overlap = _jaccard(left_assets, right_assets)
        keyword_overlap = _jaccard(left_keywords, right_keywords)
        step_overlap = _jaccard(left_steps, right_steps)
        pair_overlap = 0.5 * asset_overlap + 0.3 * keyword_overlap + 0.2 * step_overlap
        pair_details.append(
            {
                "pair": [left["test_id"], right["test_id"]],
                "asset_overlap": round(asset_overlap, 2),
                "keyword_overlap": round(keyword_overlap, 2),
                "step_overlap": round(step_overlap, 2),
                "pair_overlap": round(pair_overlap, 2),
            }
        )

    pair_details.sort(key=lambda x: x["pair_overlap"], reverse=True)
    top = pair_details[0]
    return round(1 - top["pair_overlap"], 2), top["pair"], pair_details


def _features_for_process(
    process: dict[str, Any], feature_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    ids: list[str] = []
    steps = process.get("steps") or []
    for step in steps:
        step_name = (step.get("name") or "").strip()
        ids.extend(_FEAT_ID_RE.findall(step_name))
        for fid, feature in feature_by_id.items():
            fname = (feature.get("name") or "").strip()
            if fname and fname in step_name and fid not in ids:
                ids.append(fid)
    ids = _unique_preserve([fid for fid in ids if fid in feature_by_id])
    return [{"id": fid, "name": feature_by_id[fid].get("name", "")} for fid in ids]


def _traceability(
    items: list[dict[str, Any]],
    *,
    tctx_by_id: dict[str, dict[str, Any]],
    process_by_id: dict[str, dict[str, Any]],
    feature_by_id: dict[str, dict[str, Any]],
    user_group_by_id: dict[str, dict[str, Any]],
    asset_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in items:
        tid = item["test_id"]
        test_ctx = tctx_by_id.get(tid, {})
        process = process_by_id.get(item.get("source_process") or "", {})
        features = _features_for_process(process, feature_by_id)

        user_groups = []
        for actor in process.get("actors") or []:
            actor_id = actor.get("id") or ""
            role = ((user_group_by_id.get(actor_id) or {}).get("role") or actor.get("role") or "").strip()
            if actor_id and role:
                user_groups.append({"id": actor_id, "role": role})
        user_groups = _unique_preserve(user_groups)

        asset_ids = _unique_preserve(
            list(test_ctx.get("primary_assets") or [])
            + [frag.get("asset_id") for frag in test_ctx.get("fragments") or [] if frag.get("asset_id")]
        )
        knowledge_assets = [
            {"id": aid, "file": (asset_by_id.get(aid) or {}).get("file", "")}
            for aid in asset_ids
        ]

        fragments = [
            {
                "frag_id": frag.get("frag_id"),
                "asset_id": frag.get("asset_id"),
                "snippet": frag.get("snippet", ""),
            }
            for frag in test_ctx.get("fragments") or []
        ]
        interference_frags = [
            {
                "frag_id": frag.get("frag_id"),
                "asset_id": frag.get("asset_id"),
                "snippet": frag.get("snippet", ""),
            }
            for frag in test_ctx.get("interference_fragments") or []
        ]

        path_ids = [tid]
        if process.get("id"):
            path_ids.append(process["id"])
        path_ids.extend(f["id"] for f in features if f.get("id"))
        path_ids.extend(g["id"] for g in user_groups if g.get("id"))
        path_ids.extend(a["id"] for a in knowledge_assets if a.get("id"))
        path_ids.extend(f["frag_id"] for f in fragments if f.get("frag_id"))
        path_ids.extend(f["frag_id"] for f in interference_frags if f.get("frag_id"))

        out[tid] = {
            "test_id": tid,
            "chain": {
                "process": {
                    "id": process.get("id", ""),
                    "name": process.get("name", ""),
                },
                "features": features,
                "user_groups": user_groups,
                "knowledge_assets": knowledge_assets,
                "fragments": fragments,
                "interference_fragments": interference_frags,
            },
            "path_ids": path_ids,
        }
    return out


def _build_dataset_items(
    items: list[dict[str, Any]],
    *,
    tctx_by_id: dict[str, dict[str, Any]],
    asset_by_id: dict[str, dict[str, Any]],
    validation: dict[str, dict[str, Any]],
    domain: str,
) -> list[dict[str, Any]]:
    dataset_items: list[dict[str, Any]] = []
    for item in items:
        tid = item["test_id"]
        test_ctx = tctx_by_id.get(tid, {})
        source_asset_ids = _unique_preserve(
            list(test_ctx.get("primary_assets") or [])
            + [frag.get("asset_id") for frag in test_ctx.get("fragments") or [] if frag.get("asset_id")]
        )
        source_documents = [
            (asset_by_id.get(aid) or {}).get("file", aid)
            for aid in source_asset_ids
            if (asset_by_id.get(aid) or {}).get("file", aid)
        ]
        source_fragments = [
            {
                "frag_id": frag.get("frag_id"),
                "asset_id": frag.get("asset_id"),
                "snippet": frag.get("snippet", ""),
            }
            for frag in test_ctx.get("fragments") or []
        ]

        dataset_item = {
            "test_id": tid,
            "difficulty": item.get("difficulty"),
            "difficulty_score": item.get("difficulty_score"),
            "domain": item.get("domain") or domain,
            "prompt": item.get("prompt", ""),
            "answer_template": _build_answer_template(item),
            "source_documents": source_documents,
            "source_fragments": source_fragments,
            "constraints": test_ctx.get("constraints") or [],
            "interferences": test_ctx.get("interferences") or [],
            "reference": item.get("reference") or {},
            "rubric": item.get("rubric") or {},
            "context": item.get("context") or {},
            "source_process": item.get("source_process"),
            "tags": item.get("tags") or [],
            "validation": validation.get(tid) or {},
        }
        if "inferred" in item:
            dataset_item["inferred"] = item.get("inferred")
        dataset_items.append(dataset_item)
    return dataset_items


def _format_fragment_lines(
    source_fragments: list[dict[str, Any]], asset_by_id: dict[str, dict[str, Any]]
) -> str:
    lines = []
    for idx, frag in enumerate(source_fragments, start=1):
        asset_file = (asset_by_id.get(frag.get("asset_id") or "") or {}).get("file", frag.get("asset_id", ""))
        lines.append(
            f"片段{idx}({frag.get('frag_id','')} / {asset_file}): {frag.get('snippet','')}"
        )
    return "\n".join(lines)


def _write_dataset_excel(
    path: Path,
    dataset_items: list[dict[str, Any]],
    *,
    asset_by_id: dict[str, dict[str, Any]],
    dataset_meta: dict[str, Any],
) -> None:
    main_rows = []
    rubric_rows = []
    constraint_rows = []

    for item in dataset_items:
        main_rows.append(
            {
                "问题": item.get("prompt", ""),
                "答案": item.get("answer_template", ""),
                "实际答案": "",
                "来源文档": "；".join(item.get("source_documents") or []),
                "来源片段": _format_fragment_lines(item.get("source_fragments") or [], asset_by_id),
                "标记结果": "",
                "结果": "",
            }
        )

        rubric = item.get("rubric") or {}
        for stage in rubric.get("stages") or []:
            for point in stage.get("scoring_points") or []:
                rubric_rows.append(
                    {
                        "test_id": item["test_id"],
                        "阶段": stage.get("stage_name", ""),
                        "满分": stage.get("max_score", ""),
                        "得分点": point.get("description", ""),
                        "evidence_type": point.get("evidence_type", ""),
                        "keywords": "；".join(_list_nonempty(point.get("keywords"))),
                    }
                )

        for constraint in item.get("constraints") or []:
            constraint_rows.append(
                {
                    "test_id": item["test_id"],
                    "类型": "约束",
                    "内容": constraint.get("text", ""),
                    "来源维度": constraint.get("source", ""),
                    "真实性验证": constraint.get("verified_by", ""),
                }
            )
        for interference in item.get("interferences") or []:
            constraint_rows.append(
                {
                    "test_id": item["test_id"],
                    "类型": "干扰",
                    "内容": interference.get("text", ""),
                    "来源维度": interference.get("source", ""),
                    "真实性验证": interference.get("verified_by", ""),
                }
            )

    meta_df = pd.DataFrame(
        [
            {
                "version": dataset_meta["version"],
                "domain": dataset_meta["domain"],
                "total_items": dataset_meta["total_items"],
                "difficulty_distribution": json.dumps(
                    dataset_meta["difficulty_distribution"], ensure_ascii=False
                ),
                "created_at": dataset_meta["created_at"],
            }
        ]
    )

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(main_rows).to_excel(writer, sheet_name="主表", index=False)
        pd.DataFrame(rubric_rows).to_excel(writer, sheet_name="评分细则", index=False)
        pd.DataFrame(constraint_rows).to_excel(writer, sheet_name="约束干扰", index=False)
        meta_df.to_excel(writer, sheet_name="元信息", index=False)


def _validate_dataset_json(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    meta = payload.get("dataset_meta") or {}
    items = payload.get("items")
    if not isinstance(meta, dict):
        errors.append("dataset_meta 缺失")
    else:
        for key in (
            "version",
            "domain",
            "business_goal",
            "success_metric",
            "created_at",
            "total_items",
            "difficulty_distribution",
            "source_channel",
        ):
            if key not in meta:
                errors.append(f"dataset_meta.{key} 缺失")
    if not isinstance(items, list) or not items:
        errors.append("items 为空")
        return errors

    test_ids = [str(item.get("test_id") or "") for item in items]
    if len(test_ids) != len(set(test_ids)):
        errors.append("test_id 重复")

    required_item_keys = {
        "test_id",
        "difficulty",
        "difficulty_score",
        "prompt",
        "answer_template",
        "source_documents",
        "source_fragments",
        "constraints",
        "interferences",
        "reference",
        "rubric",
        "context",
        "source_process",
        "tags",
        "validation",
    }
    for item in items:
        missing = sorted(required_item_keys - set(item.keys()))
        if missing:
            errors.append(f"{item.get('test_id','?')} 缺失字段: {', '.join(missing)}")
    return errors


def _validate_dataset_excel(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return ["dataset.xlsx 未生成"]

    try:
        xls = pd.ExcelFile(path, engine="openpyxl")
    except Exception as exc:  # pragma: no cover
        return [f"dataset.xlsx 打开失败: {exc}"]

    required_sheets = {"主表", "评分细则", "约束干扰", "元信息"}
    if not required_sheets.issubset(set(xls.sheet_names)):
        errors.append(f"sheet 缺失: {sorted(required_sheets - set(xls.sheet_names))}")

    expected_main_cols = ["问题", "答案", "实际答案", "来源文档", "来源片段", "标记结果", "结果"]
    main_df = pd.read_excel(path, sheet_name="主表", engine="openpyxl", dtype=str)
    if list(main_df.columns) != expected_main_cols:
        errors.append(f"主表列不匹配: {list(main_df.columns)}")
    return errors


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _render_principle_table(validation: dict[str, dict[str, Any]]) -> str:
    rows = []
    for tid in sorted(validation):
        result = validation[tid]
        rows.append(
            [
                tid,
                "✓" if result["real_encounter"] else "✗",
                "✓" if result["five_stage_coverage"] else "✗",
                "✓" if result["quantifiable_criteria"] else "✗",
                "✓" if result["discrimination"] else "✗",
                "✓" if result["prediction_power"] else "✗",
                "✓" if result["passed"] else "✗",
            ]
        )
    return md_table(
        ["TEST", "真实性", "闭环性", "可量化", "区分度", "预测力", "passed"],
        rows,
    )


def _render_coverage_table(actual: dict[str, dict[str, Any]]) -> str:
    rows = []
    for tid in sorted(actual):
        row = [tid]
        for stage_name in config.FIVE_STAGES:
            info = actual[tid][stage_name]
            actual_desc = "覆盖✓" if info["covered"] and info["rich"] else ("⚠️偏薄" if info["covered"] else "未覆盖✗")
            row.append(
                f"蓝图={info['blueprint']} / 实际={actual_desc} / 点数={info['points']}"
            )
        rows.append(row)
    return md_table(["TEST"] + config.FIVE_STAGES, rows)


def _render_gap_list(gaps: list[dict[str, Any]]) -> str:
    if not gaps:
        return "（无）"
    return "\n".join(
        f"- {gap['test_id']} · {gap['stage']} · severity={gap['severity']} · {gap['hint']}"
        for gap in gaps
    )


def _render_discrimination_table(discrimination: dict[str, dict[str, Any]]) -> str:
    rows = []
    for tid in sorted(discrimination):
        item = discrimination[tid]
        rows.append(
            [
                tid,
                item["est_D"],
                item["grade"],
                " / ".join(item["major_contributors"]),
            ]
        )
    return md_table(["TEST", "est_D", "分级", "主要贡献项"], rows)


def _render_independence_section(
    independence_score: float,
    most_overlapping_pair: list[str],
    pair_details: list[dict[str, Any]],
) -> str:
    lines = []
    if most_overlapping_pair:
        lines.append(
            f"- 最高重合对:{most_overlapping_pair[0]} × {most_overlapping_pair[1]}, "
            f"overlap = {pair_details[0]['pair_overlap']}"
        )
    else:
        lines.append("- 仅 1 道题,无需成对比较")
    lines.append(f"- independence_score = {independence_score}")
    lines.append("")
    if pair_details:
        lines.append(
            md_table(
                ["pair", "asset", "keyword", "step", "pair_overlap"],
                [
                    [
                        " × ".join(detail["pair"]),
                        detail["asset_overlap"],
                        detail["keyword_overlap"],
                        detail["step_overlap"],
                        detail["pair_overlap"],
                    ]
                    for detail in pair_details
                ],
            )
        )
    return "\n".join(lines)


def run(stage4_md: Path | str, out_dir: Path | None, agent_input: AgentInput) -> Path:
    out_dir = Path(out_dir) if out_dir else config.ensure_out_dir(agent_input.out_dir)
    out_path = out_dir / "05_report.md"

    stage4 = read_md(stage4_md)
    items_raw: list[dict[str, Any]] = (stage4["artifacts"] or {}).get("items", [])
    if not items_raw:
        raise MissingInputError(
            stage="Stage 5 · 验证与打包",
            report=[
                MissingField(
                    field_name="04_tests.md 的 items",
                    why_needed="Stage 5 依赖 Stage 4 题目集执行验证与打包",
                    suggested_format="先完成 Stage 4 或重跑 stage4",
                    example="python -m questforge.run_pipeline --only stage4 --input-json <path>",
                )
            ],
        )

    stage4_path = Path(stage4_md)
    parent = stage4_path.parent
    stage3_md = parent / "03_context.md"
    stage2_md = parent / "02_plan.md"
    stage1_md = parent / "01_understanding.md"
    if not (stage3_md.exists() and stage2_md.exists() and stage1_md.exists()):
        raise FileNotFoundError(f"缺少上游产物: {stage1_md}, {stage2_md}, {stage3_md}")

    art3 = read_md(stage3_md)["artifacts"]
    art2 = read_md(stage2_md)["artifacts"]
    art1 = read_md(stage1_md)["artifacts"]

    tctx_by_id = {tc["test_id"]: tc for tc in art3.get("test_contexts", [])}
    process_by_id = {proc["id"]: proc for proc in art2.get("processes", [])}
    user_group_by_id = {ug["id"]: ug for ug in art1.get("user_groups", [])}
    feature_by_id = {feat["id"]: feat for feat in art1.get("features", [])}
    asset_by_id = {asset["id"]: asset for asset in art1.get("knowledge_assets", [])}
    coverage_blueprint = art2.get("coverage_matrix_plan", {})
    business_goal = art1.get("business_goal") or {}

    items = sorted(items_raw, key=lambda x: x.get("test_id", ""))
    created_at = iso_now()

    validation = _validate_principles(
        items,
        tctx_by_id=tctx_by_id,
        process_by_id=process_by_id,
        user_group_by_id=user_group_by_id,
        business_goal=business_goal,
    )
    actual_coverage, coverage_gaps = _compute_coverage_matrix(items, coverage_blueprint)
    discrimination = _discrimination_estimate(items, tctx_by_id)
    independence_score, most_overlapping_pair, pair_details = _independence_score(items, tctx_by_id)
    traceability = _traceability(
        items,
        tctx_by_id=tctx_by_id,
        process_by_id=process_by_id,
        feature_by_id=feature_by_id,
        user_group_by_id=user_group_by_id,
        asset_by_id=asset_by_id,
    )

    dataset_items = _build_dataset_items(
        items,
        tctx_by_id=tctx_by_id,
        asset_by_id=asset_by_id,
        validation=validation,
        domain=agent_input.domain,
    )
    dataset_meta = _dataset_meta(
        agent_input=agent_input,
        business_goal=business_goal,
        items=items,
        created_at=created_at,
    )
    dataset_payload = {
        "dataset_meta": dataset_meta,
        "coverage_matrix": actual_coverage,
        "items": dataset_items,
    }

    supplementary_dir = out_dir / "dataset_supplementary"
    supplementary_dir.mkdir(parents=True, exist_ok=True)
    dataset_json_path = out_dir / "dataset.json"
    dataset_xlsx_path = out_dir / "dataset.xlsx"
    traceability_path = out_dir / "traceability.json"

    _write_json(dataset_json_path, dataset_payload)
    _write_json(traceability_path, traceability)
    _write_json(
        supplementary_dir / "coverage_matrix.json",
        {
            "blueprint": coverage_blueprint,
            "actual": actual_coverage,
            "coverage_gaps": coverage_gaps,
        },
    )
    _write_json(
        supplementary_dir / "rubrics.json",
        {item["test_id"]: item.get("rubric") or {} for item in dataset_items},
    )
    _write_json(supplementary_dir / "traceability.json", traceability)
    _write_dataset_excel(
        dataset_xlsx_path,
        dataset_items,
        asset_by_id=asset_by_id,
        dataset_meta=dataset_meta,
    )

    dataset_json_errors = _validate_dataset_json(dataset_payload)
    dataset_xlsx_errors = _validate_dataset_excel(dataset_xlsx_path)

    severity_count = Counter(gap["severity"] for gap in coverage_gaps)
    grade_count = dict(Counter(item["grade"] for item in discrimination.values()))

    checklist = Checklist()
    checklist.add(
        "所有 TEST 的 passed=true",
        all(item.get("passed") for item in validation.values()),
    )
    checklist.add(
        "覆盖矩阵盲区 severity=high 数 = 0",
        severity_count.get("high", 0) == 0,
    )
    checklist.add("独立性评分 ≥ 0.5", independence_score >= 0.5)
    checklist.add("dataset.json 结构校验通过", not dataset_json_errors)
    checklist.add("dataset.xlsx 已生成且关键 sheet 存在", not dataset_xlsx_errors)

    sections = [
        Section("5 设计原则验证", _render_principle_table(validation)),
        Section("覆盖矩阵对齐(实际 vs 蓝图)", _render_coverage_table(actual_coverage)),
        Section("盲区清单", _render_gap_list(coverage_gaps)),
        Section("先验区分度估计", _render_discrimination_table(discrimination)),
        Section(
            "独立性评分",
            _render_independence_section(independence_score, most_overlapping_pair, pair_details),
        ),
        Section(
            "最终产物清单",
            "\n".join(
                [
                    f"- `dataset.json` — {dataset_json_path}",
                    f"- `dataset.xlsx` — {dataset_xlsx_path}",
                    f"- `05_report.md` — {out_path}",
                    f"- `traceability.json` — {traceability_path}",
                    f"- `dataset_supplementary/` — {supplementary_dir}",
                ]
            ),
        ),
    ]

    summary = (
        f"{len(items)} 道题中 {sum(1 for item in validation.values() if item['passed'])} 道通过 5 设计原则验证；"
        f"覆盖矩阵高/中/低严重度问题分别为 {severity_count.get('high', 0)}/"
        f"{severity_count.get('medium', 0)}/{severity_count.get('low', 0)}；"
        f"先验区分度分级={grade_count}；独立性评分 {independence_score}。"
    )

    artifacts = {
        "validation": {
            "by_principle": validation,
            "coverage_matrix": actual_coverage,
            "coverage_gaps": coverage_gaps,
            "discrimination_estimate": discrimination,
            "independence_score": independence_score,
            "most_overlapping_pair": most_overlapping_pair,
            "pair_details": pair_details,
        },
        "dataset_meta": dataset_meta,
    }

    remarks = []
    if dataset_json_errors:
        remarks.append("dataset.json 校验失败:")
        remarks.extend(f"  - {err}" for err in dataset_json_errors)
    if dataset_xlsx_errors:
        remarks.append("dataset.xlsx 校验失败:")
        remarks.extend(f"  - {err}" for err in dataset_xlsx_errors)
    if not remarks:
        remarks.append("（无）")

    frontmatter = {
        "stage": 5,
        "stage_name": "validation_and_finalize",
        "version": "1.0",
        "upstream": "04_tests.md",
        "downstream": "最终产物",
        "domain": agent_input.domain,
        "created_at": created_at,
        "created_by": "agent-stage5",
        "pass_gate": checklist.all_passed(),
    }

    write_md(
        out_path,
        frontmatter=frontmatter,
        title="Stage 5 · 验证报告 + benchmark",
        summary=summary,
        sections=sections,
        artifacts=artifacts,
        checklist=checklist,
        remarks="\n".join(remarks),
    )
    return out_path


__all__ = ["run"]
