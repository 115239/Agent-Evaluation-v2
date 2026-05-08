"""Stage 6 · 先验答题模拟自检 → 06_self_eval.md + dataset_supplementary/self_eval.json

借鉴 Future AGI SimulatorAgent 的离线压缩版:
- 用 LLM 模拟"完美答题者"(读 reference)与"基线答题者"(只读 prompt)
- 用 LLM 当评分员(读 rubric)分别给两份答案打分
- score_diff = perfect - baseline,差越大说明 rubric 区分能力越强

默认通过抽样运行(每难度 1 道),通过 STAGE6_SAMPLE_PER_DIFFICULTY 调整。
默认关闭(STAGE6_ENABLED=1 或 --only stage6 才会跑)。
"""
from __future__ import annotations

import json
import logging
import statistics
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, Section, iso_now, md_table, read_md, truncate, write_md
from .input_spec import AgentInput, MissingField, MissingInputError
from .llm_client import LLMClient, get_default_client

log = logging.getLogger("questforge.stage6")

_PROMPTS_DIR = config.REPO_ROOT / "questforge" / "prompts"


# ========== 抽样 ==========
def _sample_items(
    items: list[dict[str, Any]], per_difficulty: int
) -> list[dict[str, Any]]:
    """按 difficulty 分层抽样,保留每难度前 per_difficulty 道(test_id 字典序)。"""
    if per_difficulty <= 0:
        return items
    by_diff: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for it in items:
        by_diff[it.get("difficulty") or "unknown"].append(it)
    sampled: list[dict[str, Any]] = []
    for diff, group in by_diff.items():
        group_sorted = sorted(group, key=lambda x: x.get("test_id", ""))
        sampled.extend(group_sorted[:per_difficulty])
    return sorted(sampled, key=lambda x: x.get("test_id", ""))


# ========== LLM 调用 ==========
def _read_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def _simulate_one(
    item: dict[str, Any], client: LLMClient, perfect_sys: str, baseline_sys: str, judge_sys: str
) -> dict[str, Any]:
    tid = item["test_id"]
    prompt = item.get("prompt", "")
    reference = item.get("reference") or {}
    rubric = item.get("rubric") or {}

    perfect_user = (
        f"<prompt>{prompt}</prompt>\n"
        f"<reference>{json.dumps(reference, ensure_ascii=False)}</reference>"
    )
    baseline_user = f"<prompt>{prompt}</prompt>"

    perfect_answer = client.chat_text(perfect_sys, perfect_user, max_tokens=600)
    baseline_answer = client.chat_text(baseline_sys, baseline_user, max_tokens=400)

    judge_user_perfect = (
        f"<prompt>{prompt}</prompt>\n"
        f"<answer>{perfect_answer}</answer>\n"
        f"<rubric>{json.dumps(rubric, ensure_ascii=False)}</rubric>"
    )
    judge_user_baseline = (
        f"<prompt>{prompt}</prompt>\n"
        f"<answer>{baseline_answer}</answer>\n"
        f"<rubric>{json.dumps(rubric, ensure_ascii=False)}</rubric>"
    )

    perfect_score = client.chat_json(judge_sys, judge_user_perfect, max_tokens=600)
    baseline_score = client.chat_json(judge_sys, judge_user_baseline, max_tokens=600)

    p_total = float((perfect_score or {}).get("total") or 0)
    b_total = float((baseline_score or {}).get("total") or 0)
    return {
        "test_id": tid,
        "difficulty": item.get("difficulty"),
        "perfect_answer": perfect_answer,
        "baseline_answer": baseline_answer,
        "perfect_score": perfect_score or {},
        "baseline_score": baseline_score or {},
        "score_diff": round(p_total - b_total, 2),
        "perfect_total": round(p_total, 2),
        "baseline_total": round(b_total, 2),
    }


# ========== 渲染 ==========
def _grade_diff(diff: float) -> str:
    if diff >= 5.0:
        return "强"
    if diff >= 3.0:
        return "合格"
    if diff >= 1.0:
        return "弱"
    return "不合格"


def _render_overview(results: list[dict[str, Any]]) -> str:
    rows = [
        [
            r["test_id"],
            r.get("difficulty", "-"),
            r["perfect_total"],
            r["baseline_total"],
            r["score_diff"],
            _grade_diff(r["score_diff"]),
        ]
        for r in results
    ]
    return md_table(
        ["TEST", "难度", "perfect", "baseline", "diff", "区分等级"], rows
    )


def _render_samples(results: list[dict[str, Any]], top: int = 3) -> str:
    sample = sorted(results, key=lambda x: x["score_diff"])[:top]
    lines: list[str] = []
    for r in sample:
        lines.append(f"### {r['test_id']} · diff={r['score_diff']}")
        lines.append(f"- **完美答案** (perfect={r['perfect_total']}): {truncate(r['perfect_answer'], 220)}")
        lines.append(f"- **基线答案** (baseline={r['baseline_total']}): {truncate(r['baseline_answer'], 220)}")
        lines.append("")
    return "\n".join(lines) if lines else "(无)"


# ========== 主入口 ==========
def run(stage4_md: Path | str, out_dir: Path | None, agent_input: AgentInput) -> Path:
    out_dir = Path(out_dir) if out_dir else config.ensure_out_dir(agent_input.out_dir)
    out_path = out_dir / "06_self_eval.md"

    # --- 上游 ---
    stage4 = read_md(stage4_md)
    items_raw: list[dict[str, Any]] = (stage4["artifacts"] or {}).get("items", [])
    if not items_raw:
        raise MissingInputError(
            stage="Stage 6 · 先验自检",
            report=[
                MissingField(
                    field_name="04_tests.md 的 items",
                    why_needed="Stage 6 依赖 Stage 4 的 items(prompt + reference + rubric)",
                    suggested_format="先完成 Stage 4 或重跑 stage4",
                    example="python -m questforge.run_pipeline --only stage4 --input-json <path>",
                )
            ],
        )

    # --- LLM 必备 ---
    client = get_default_client()
    if not client.use_llm:
        raise MissingInputError(
            stage="Stage 6 · 先验自检",
            report=[
                MissingField(
                    field_name="LLM_API_KEY",
                    why_needed="Stage 6 全部依赖 LLM(2 次答题模拟 + 2 次 judge,每题 4 次)",
                    suggested_format="配置 .env 里的 LLM_API_KEY",
                    example="LLM_API_KEY=<YOUR_API_KEY>",
                )
            ],
        )

    # --- 抽样 ---
    sampled = _sample_items(items_raw, config.STAGE6_SAMPLE_PER_DIFFICULTY)
    log.info(
        "[Stage6] 抽样 %d/%d 道(每难度 %d)",
        len(sampled),
        len(items_raw),
        config.STAGE6_SAMPLE_PER_DIFFICULTY,
    )

    perfect_sys = _read_prompt("stage6_perfect.txt")
    baseline_sys = _read_prompt("stage6_baseline.txt")
    judge_sys = _read_prompt("stage6_judge.txt")

    # --- 并发跑 ---
    results: list[dict[str, Any]] = []
    errors: list[tuple[str, str]] = []
    program_start = time.time()
    write_lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=config.STAGE6_MAX_WORKERS) as executor:
        futures = {
            executor.submit(_simulate_one, it, client, perfect_sys, baseline_sys, judge_sys): it["test_id"]
            for it in sampled
        }
        for fut in as_completed(futures):
            tid = futures[fut]
            try:
                r = fut.result()
            except Exception as e:  # pragma: no cover
                errors.append((tid, f"异常:{type(e).__name__}: {e}"))
                log.exception("[Stage6] %s 任务异常", tid)
                continue
            with write_lock:
                results.append(r)
            log.info(
                "[Stage6][DIAG] T+%.0fs | %s done | perfect=%.2f baseline=%.2f diff=%.2f",
                time.time() - program_start,
                tid,
                r["perfect_total"],
                r["baseline_total"],
                r["score_diff"],
            )

    if not results:
        raise MissingInputError(
            stage="Stage 6 · 先验自检",
            report=[
                MissingField(
                    field_name="LLM 输出",
                    why_needed="全部抽样题目均失败,Pipeline 无法继续 self_eval",
                    suggested_format=(
                        "检查 LLM_MODEL / LLM_API_KEY / prompts/stage6_*.txt;"
                        f"失败明细:{'; '.join(f'{t}: {e}' for t, e in errors[:3])}"
                    ),
                    example="python -m questforge.run_pipeline --only stage6 --input-json <path>",
                )
            ],
        )

    results.sort(key=lambda x: x["test_id"])

    # --- 聚合 ---
    diffs = [r["score_diff"] for r in results]
    perfects = [r["perfect_total"] for r in results]
    baselines = [r["baseline_total"] for r in results]
    grade_dist = dict(Counter(_grade_diff(d) for d in diffs))

    summary_metrics = {
        "n_sampled": len(results),
        "n_total": len(items_raw),
        "diff_mean": round(statistics.mean(diffs), 2) if diffs else 0.0,
        "diff_median": round(statistics.median(diffs), 2) if diffs else 0.0,
        "diff_min": round(min(diffs), 2) if diffs else 0.0,
        "diff_max": round(max(diffs), 2) if diffs else 0.0,
        "perfect_mean": round(statistics.mean(perfects), 2) if perfects else 0.0,
        "baseline_mean": round(statistics.mean(baselines), 2) if baselines else 0.0,
        "grade_distribution": grade_dist,
    }

    # --- 落盘 self_eval.json ---
    supplementary_dir = out_dir / "dataset_supplementary"
    supplementary_dir.mkdir(parents=True, exist_ok=True)
    self_eval_path = supplementary_dir / "self_eval.json"
    self_eval_path.write_text(
        json.dumps(
            {
                "metrics": summary_metrics,
                "items": results,
                "errors": [{"test_id": t, "reason": r} for t, r in errors],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --- 校验清单 ---
    checklist = Checklist()
    threshold = config.STAGE6_DIFF_PASS_THRESHOLD
    checklist.add(
        f"diff_mean ≥ {threshold}(实际 {summary_metrics['diff_mean']})",
        summary_metrics["diff_mean"] >= threshold,
    )
    checklist.add(
        f"perfect_mean ≥ baseline_mean + {threshold}",
        summary_metrics["perfect_mean"] >= summary_metrics["baseline_mean"] + threshold,
    )
    checklist.add(
        "全部抽样题目都拿到 perfect/baseline 双份打分",
        all(r["perfect_score"] and r["baseline_score"] for r in results),
    )

    # --- 渲染 ---
    sections = [
        Section(
            "总览",
            "\n".join(
                [
                    f"- 抽样 {summary_metrics['n_sampled']} / {summary_metrics['n_total']} 道",
                    f"- diff: mean={summary_metrics['diff_mean']} / median={summary_metrics['diff_median']}"
                    f" / min={summary_metrics['diff_min']} / max={summary_metrics['diff_max']}",
                    f"- perfect mean={summary_metrics['perfect_mean']} | baseline mean={summary_metrics['baseline_mean']}",
                    f"- 区分等级分布: {grade_dist}",
                    f"- 完整数据见 `dataset_supplementary/self_eval.json`",
                ]
            ),
        ),
        Section("逐题打分", _render_overview(results)),
        Section("最弱区分度样例(diff 最低 3 道)", _render_samples(results, top=3)),
    ]
    if errors:
        sections.append(
            Section(
                "失败题目",
                "\n".join(f"- {tid}: {reason}" for tid, reason in errors),
            )
        )

    summary = (
        f"抽样 {len(results)} / {len(items_raw)} 道做先验自检;"
        f"perfect mean={summary_metrics['perfect_mean']},baseline mean={summary_metrics['baseline_mean']},"
        f"diff mean={summary_metrics['diff_mean']}({_grade_diff(summary_metrics['diff_mean'])})。"
    )

    artifacts = {
        "metrics": summary_metrics,
        "items": results,
        "errors": [{"test_id": t, "reason": r} for t, r in errors],
    }

    frontmatter = {
        "stage": 6,
        "stage_name": "self_eval",
        "version": "1.0",
        "upstream": "04_tests.md",
        "downstream": "(终)",
        "domain": agent_input.domain,
        "created_at": iso_now(),
        "created_by": "agent-stage6",
        "pass_gate": checklist.all_passed(),
    }

    write_md(
        out_path,
        frontmatter=frontmatter,
        title="Stage 6 · 先验答题模拟自检",
        summary=summary,
        sections=sections,
        artifacts=artifacts,
        checklist=checklist,
        remarks="(无)" if not errors else f"{len(errors)} 道抽样题目失败,见'失败题目'段",
    )
    return out_path


__all__ = ["run"]
