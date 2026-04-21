"""Stage 4 · 题目 + 五阶段期望 + 评分细则 → 04_tests.md

输入:03_context.md + 02_plan.md(processes + test_plan) + 01_understanding.md(glossary)
输出:OUT_DIR / 04_tests.md + stage4_items.jsonl

处理步骤(§4.6):
  4.1 Prompt 组装(单次 LLM 调用输出完整 item JSON)
  4.2 五阶段期望行为生成(LLM 输出,decompose.expected_steps 必须等于 source_process.steps)
  4.3 评分细则生成(LLM 输出;权重 2/2/3/2/1,含 ≥1 fatal_deduction + ≥1 veto_item)
  4.4 难度自校准(纯本地计算,6 维量化;与 Stage 2 assigned_difficulty 不一致写备注)

**本阶段不做任何领域硬编码。** 领域词由 Stage 1 glossary 注入 LLM;
LLM 返空/schema 不合法 → 记入 generation_errors;全部失败 → MissingInputError。

并发/断点续传基础设施参考 data_syn/pipeline/runner.py,但不照搬其
background/review/enhance/conflict 多阶段管线——§4.6 已自洽。
"""
from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, Section, iso_now, md_table, read_md, truncate, write_md
from .input_spec import AgentInput, MissingField, MissingInputError
from .io_utils import extract_local_keywords
from .llm_client import LLMClient, get_default_client

log = logging.getLogger("questforge.stage4")


# ========== JSONL 工具(线程安全) ==========
def _load_done_ids(path: Path) -> set[str]:
    """读已落盘的 stage4_items.jsonl,返回已完成 test_id 集合(断点续传)。"""
    if not path.exists():
        return set()
    done: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                tid = obj.get("test_id")
                if tid:
                    done.add(str(tid))
            except json.JSONDecodeError:
                continue
    return done


def _read_existing_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def _append_jsonl(path: Path, item: dict[str, Any], lock: threading.Lock) -> None:
    line = json.dumps(item, ensure_ascii=False) + "\n"
    with lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(line)


# ========== 任务构建 ==========
def _build_tasks(
    test_contexts: list[dict[str, Any]],
    plan_by_tid: dict[str, dict[str, Any]],
    pid2proc: dict[str, dict[str, Any]],
    domain: str,
) -> list[dict[str, Any]]:
    """每道题一条 task_info:test_id + 上下文 + 代表流程 + Stage 2 规划信息。"""
    tasks: list[dict[str, Any]] = []
    for tctx in test_contexts:
        tid = tctx["test_id"]
        plan = plan_by_tid.get(tid)
        if plan is None:
            log.warning("[Stage4] 找不到 %s 的 Stage 2 规划项,跳过", tid)
            continue
        rep = pid2proc.get(plan["source_process"])
        if rep is None:
            log.warning("[Stage4] 找不到 %s 的 source_process=%s", tid, plan.get("source_process"))
            continue
        tasks.append(
            {
                "test_id": tid,
                "difficulty": plan["difficulty"],
                "focus_stages": plan.get("focus_stages", []),
                "source_process_id": plan["source_process"],
                "test_ctx": tctx,
                "rep_process": rep,
                "domain": domain,
            }
        )
    return tasks


def _build_user_payload(task: dict[str, Any], glossary: dict[str, str]) -> str:
    """组装单题 user 消息。领域词用 glossary 的 top-N 个键值对。"""
    tctx = task["test_ctx"]
    rep = task["rep_process"]

    brief_tctx = {
        "test_id": tctx["test_id"],
        "difficulty": tctx.get("difficulty"),
        "primary_assets": tctx.get("primary_assets", []),
        "fragments": [
            {"frag_id": f["frag_id"], "asset_id": f["asset_id"], "snippet": f.get("snippet", "")}
            for f in tctx.get("fragments", [])
        ],
        "keyword_pool": tctx.get("keyword_pool", []),
        "constraints": [
            {"id": c["id"], "text": c["text"], "source": c.get("source", "")}
            for c in tctx.get("constraints", [])
        ],
        "interferences": [
            {"id": i["id"], "text": i["text"], "trap": i.get("trap", False)}
            for i in tctx.get("interferences", [])
        ],
    }
    brief_proc = {
        "id": rep.get("id"),
        "name": rep.get("name"),
        "actors": rep.get("actors", []),
        "triggers": rep.get("triggers", []),
        "steps": rep.get("steps", []),
        "outputs": rep.get("outputs", []),
        "cross_process_dependency": rep.get("cross_process_dependency", "单流程"),
    }
    brief_gloss = dict(list(glossary.items())[:20])

    schema = {
        "test_id": task["test_id"],
        "difficulty": "basic|advanced|expert",
        "difficulty_score": "float",
        "domain": task["domain"],
        "prompt": "string (20-300字,问句收尾,禁封闭式)",
        "context": {
            "user_role": "string",
            "intent_type": "string (如 单一知识查询/多意图综合决策/模糊推断)",
            "constraints": ["string (与 Stage 3 constraints.text 对齐)"],
            "interference_items": ["string (与 Stage 3 interferences.text 对齐)"],
            "success_criteria": ["string"],
        },
        "reference": {
            "define_problem": {
                "intent_understanding": "string",
                "implicit_needs": ["string"],
                "problem_essence": "string",
            },
            "decompose": {
                "expected_steps": ["string (严格等于 source_process.steps 的 name 列表)"],
                "priority_ordering": "string",
            },
            "solution": {
                "information_sources": ["string (含 KB/FRAG 出处 + snippet 摘要)"],
                "cross_doc_integration": "string",
            },
            "execution": {
                "output_format": "string",
                "exception_handling": "string",
            },
            "metacognition": {
                "source_annotation": "string",
                "uncertainty_acknowledgment": "string",
                "boundary_awareness": "string",
            },
        },
        "rubric": {
            "total_max_score": 10,
            "stages": [
                {
                    "stage_name": "定义问题|拆解问题|方案生成|执行落地|元认知",
                    "max_score": "2/2/3/2/1",
                    "weight": "float",
                    "scoring_points": [
                        {
                            "description": "string",
                            "score": "float",
                            "evidence_type": "keyword_match|semantic_match|llm_judge",
                            "keywords": ["string (evidence_type!=llm_judge 时必填)"],
                        }
                    ],
                }
            ],
            "fatal_deductions": [{"description": "string", "detection_rule": "string"}],
            "veto_items": [{"description": "string", "detection_rule": "string"}],
        },
        "source_process": task["source_process_id"],
        "inferred": bool(rep.get("inferred", False)),
        "tags": ["string"],
    }

    return (
        f"<stage3_test_context>{json.dumps(brief_tctx, ensure_ascii=False)}</stage3_test_context>\n"
        f"<source_process>{json.dumps(brief_proc, ensure_ascii=False)}</source_process>\n"
        f"<glossary>{json.dumps(brief_gloss, ensure_ascii=False)}</glossary>\n"
        f"<domain>{task['domain']}</domain>\n"
        f"<difficulty>{task['difficulty']}</difficulty>\n"
        f"<focus_stages>{json.dumps(task['focus_stages'], ensure_ascii=False)}</focus_stages>\n\n"
        f"请为 test_id={task['test_id']} 输出 1 条 item,严格按以下 JSON Schema "
        f"(字段描述用于参考,实际请输出真实值;不要添加 schema 中未列出的字段):\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
        f"**只输出 JSON 对象本身**,不要包装在 {{\"items\":[...]}} 里,不要添加解释、注释或 markdown 围栏。"
    )


# ========== 单题生成 ==========
def _generate_one(
    task: dict[str, Any],
    client: LLMClient,
    system_prompt: str,
    glossary: dict[str, str],
    program_start: float,
) -> tuple[dict[str, Any] | None, str]:
    tid = task["test_id"]
    t0 = time.time()
    elapsed = t0 - program_start
    log.info("[Stage4][DIAG] T+%.0fs | API开始 | %s | difficulty=%s", elapsed, tid, task["difficulty"])

    user = _build_user_payload(task, glossary)
    raw = client.chat_json(
        system_prompt,
        user,
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.STAGE4_LLM_MAX_TOKENS,
    )
    dur = time.time() - t0

    if not isinstance(raw, dict) or not raw:
        log.warning("[Stage4][DIAG] T+%.0fs | API结束 | %s | 耗时=%.0fs | 空/非对象",
                    time.time() - program_start, tid, dur)
        return None, "LLM 返空或非 JSON 对象"

    # LLM 可能仍然包了一层 {"items":[...]} — 兼容解包
    if "items" in raw and isinstance(raw["items"], list) and raw["items"]:
        raw = raw["items"][0]

    item, errs = _validate_item(raw, task)
    if errs:
        log.warning("[Stage4][DIAG] T+%.0fs | API结束 | %s | 耗时=%.0fs | 校验失败: %s",
                    time.time() - program_start, tid, dur, "; ".join(errs))
        return None, f"schema 校验失败:{'; '.join(errs)}"

    log.info("[Stage4][DIAG] T+%.0fs | API结束 | %s | 耗时=%.0fs | 生成成功",
             time.time() - program_start, tid, dur)
    return item, ""


# ========== Schema 校验 ==========
_REQUIRED_STAGES = ("定义问题", "拆解问题", "方案生成", "执行落地", "元认知")
_REFERENCE_KEYS = ("define_problem", "decompose", "solution", "execution", "metacognition")
_EVIDENCE_TYPES = {"keyword_match", "semantic_match", "llm_judge"}


def _validate_item(raw: dict[str, Any], task: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """schema 校验。返回 (item or None, errors)。不做内容改写,只做结构校验。"""
    errs: list[str] = []

    if raw.get("test_id") != task["test_id"]:
        raw["test_id"] = task["test_id"]  # LLM 偶发写错,强制对齐

    # prompt 长度
    prompt = (raw.get("prompt") or "").strip()
    plow, phigh = config.STAGE4_PROMPT_LEN
    if not (plow <= len(prompt) <= phigh):
        errs.append(f"prompt 长度 {len(prompt)} 不在 [{plow}, {phigh}]")

    # reference 五段非空
    ref = raw.get("reference") or {}
    for k in _REFERENCE_KEYS:
        sub = ref.get(k)
        if not isinstance(sub, dict) or not sub:
            errs.append(f"reference.{k} 缺失或为空")

    # decompose.expected_steps == source_process.steps
    expected = (ref.get("decompose") or {}).get("expected_steps") or []
    src_steps = [s.get("name", "").strip() for s in task["rep_process"].get("steps", [])]
    if [s.strip() for s in expected] != src_steps:
        errs.append("reference.decompose.expected_steps 与 source_process.steps 不一致")

    # rubric 权重
    rubric = raw.get("rubric") or {}
    if rubric.get("total_max_score") != 10:
        errs.append(f"rubric.total_max_score={rubric.get('total_max_score')} 不等于 10")

    stages = rubric.get("stages") or []
    stage_names = [s.get("stage_name", "") for s in stages]
    if set(stage_names) != set(_REQUIRED_STAGES):
        errs.append(f"rubric.stages 名称集合不等于 {_REQUIRED_STAGES}(实际:{stage_names})")
    else:
        for s in stages:
            sn = s.get("stage_name", "")
            expected_max = config.STAGE4_STAGE_WEIGHTS.get(sn)
            if expected_max is None:
                continue
            if float(s.get("max_score", 0)) != expected_max:
                errs.append(f"rubric.{sn}.max_score={s.get('max_score')} != {expected_max}")
            pts = s.get("scoring_points") or []
            # 元认知权重仅 1 分,设计文档例题也只用 1 个 scoring_point;其余阶段 ≥ 2
            min_points = 1 if sn == "元认知" else 2
            if len(pts) < min_points:
                errs.append(f"rubric.{sn}.scoring_points 少于 {min_points}")
            for p in pts:
                et = p.get("evidence_type")
                if et not in _EVIDENCE_TYPES:
                    errs.append(f"rubric.{sn} 的 scoring_point.evidence_type={et} 不合法")

    # fatal / veto
    if not (rubric.get("fatal_deductions") or []):
        errs.append("rubric.fatal_deductions 为空")
    if not (rubric.get("veto_items") or []):
        errs.append("rubric.veto_items 为空")

    if errs:
        return None, errs

    # 补齐 source_process 与 inferred(防 LLM 遗漏)
    raw.setdefault("source_process", task["source_process_id"])
    raw.setdefault("inferred", bool(task["rep_process"].get("inferred", False)))
    raw.setdefault("tags", [])
    return raw, []


# ========== 难度自校准(Step 4.4) ==========
def _bucket(value: int, thresholds: tuple[int, int]) -> int:
    """按 (lo, hi) 阈值给 1/2/3 分:value ≤ lo → 1, ≤ hi → 2, 否则 → 3。"""
    if value <= thresholds[0]:
        return 1
    if value <= thresholds[1]:
        return 2
    return 3


def _intent_score(intent_type: str) -> int:
    text = (intent_type or "").strip()
    if any(kw in text for kw in ("模糊", "矛盾", "冲突")):
        return 3
    if any(kw in text for kw in ("多意图", "综合", "跨", "复合")):
        return 2
    return 1


def _calibrate_difficulty(
    item: dict[str, Any], test_ctx: dict[str, Any], rep_process: dict[str, Any]
) -> tuple[float, str]:
    ref = item.get("reference") or {}
    context = item.get("context") or {}

    intent = _intent_score(context.get("intent_type", ""))
    info_sources = len((ref.get("solution") or {}).get("information_sources") or [])
    constraints_n = len(test_ctx.get("constraints") or [])
    interference_n = len(test_ctx.get("interferences") or [])
    outputs_n = len(rep_process.get("outputs") or [])
    stages_nonempty = sum(
        1 for k in _REFERENCE_KEYS if isinstance(ref.get(k), dict) and ref.get(k)
    )

    scores = [
        intent,
        _bucket(info_sources, (1, 3)),
        _bucket(constraints_n, (1, 3)),
        _bucket(interference_n, (0, 1)),
        _bucket(outputs_n, (2, 4)),
        _bucket(stages_nonempty, (3, 4)),
    ]
    avg = sum(scores) / len(scores)

    basic_thr = config.STAGE4_DIFFICULTY_SCORE_THRESHOLDS["basic"]
    advanced_thr = config.STAGE4_DIFFICULTY_SCORE_THRESHOLDS["advanced"]
    if avg <= basic_thr:
        label = "basic"
    elif avg <= advanced_thr:
        label = "advanced"
    else:
        label = "expert"
    return avg, label


# ========== 校验清单辅助 ==========
def _prompt_len_ok(item: dict[str, Any]) -> bool:
    n = len((item.get("prompt") or "").strip())
    lo, hi = config.STAGE4_PROMPT_LEN
    return lo <= n <= hi


def _reference_complete(item: dict[str, Any]) -> bool:
    ref = item.get("reference") or {}
    return all(isinstance(ref.get(k), dict) and ref.get(k) for k in _REFERENCE_KEYS)


def _decompose_match(item: dict[str, Any], pid2proc: dict[str, dict[str, Any]]) -> bool:
    rep = pid2proc.get(item.get("source_process") or "")
    if not rep:
        return False
    expected = ((item.get("reference") or {}).get("decompose") or {}).get("expected_steps") or []
    src = [s.get("name", "").strip() for s in rep.get("steps", [])]
    return [s.strip() for s in expected] == src


def _rubric_weights_ok(item: dict[str, Any]) -> bool:
    rubric = item.get("rubric") or {}
    if rubric.get("total_max_score") != 10:
        return False
    stages = rubric.get("stages") or []
    by_name = {s.get("stage_name"): float(s.get("max_score", 0)) for s in stages}
    for name, expected in config.STAGE4_STAGE_WEIGHTS.items():
        if by_name.get(name) != expected:
            return False
    return True


def _fatal_veto_ok(item: dict[str, Any]) -> bool:
    rubric = item.get("rubric") or {}
    return bool(rubric.get("fatal_deductions")) and bool(rubric.get("veto_items"))


def _constraints_embedded(item: dict[str, Any], test_ctx: dict[str, Any]) -> bool:
    """每条 Stage 3 constraint 的 top-2 关键词至少命中 1 个于 prompt。"""
    prompt_txt = item.get("prompt") or ""
    for c in test_ctx.get("constraints") or []:
        kws = extract_local_keywords(c.get("text", ""), top_k=2)
        if not kws:
            continue
        if not any(kw in prompt_txt for kw in kws):
            return False
    return True


# ========== MD 渲染 ==========
def _render_overview_table(items: list[dict[str, Any]], tctx_by_id: dict[str, dict[str, Any]]) -> str:
    rows = []
    for it in items:
        tctx = tctx_by_id.get(it["test_id"], {})
        rows.append(
            [
                it["test_id"],
                it.get("difficulty", "-"),
                it.get("difficulty_score", "-"),
                len(tctx.get("constraints") or []),
                len(tctx.get("interferences") or []),
                "+".join(tctx.get("primary_assets") or []) or "-",
                it.get("source_process", "-"),
            ]
        )
    return md_table(
        ["ID", "难度", "difficulty_score", "约束", "干扰", "主资产", "对应流程"], rows
    )


def _render_item_section(item: dict[str, Any], tctx: dict[str, Any]) -> str:
    ref = item.get("reference") or {}
    rubric = item.get("rubric") or {}

    lines = [
        f"## {item['test_id']} · {(item.get('context') or {}).get('intent_type','')}({item.get('difficulty','-')})",
        "",
        "### prompt",
        f"> {item.get('prompt','').strip()}",
        "",
        "### 约束与干扰",
    ]
    cons = tctx.get("constraints") or []
    itfs = tctx.get("interferences") or []
    lines.append("- 约束:" + ("、".join(c["text"] for c in cons) if cons else "无"))
    trap_mark = lambda x: "陷阱·" if x.get("trap") else ""
    lines.append(
        "- 干扰:" + ("、".join(f"{trap_mark(i)}{i['text']}" for i in itfs) if itfs else "无")
    )
    lines.append("")

    # 五阶段期望
    lines.append("### 五阶段期望")
    lines.append(md_table(
        ["阶段", "期望"],
        [
            ["定义问题", truncate(str(ref.get("define_problem") or {}), 120)],
            ["拆解问题", truncate(str(ref.get("decompose") or {}), 120)],
            ["方案生成", truncate(str(ref.get("solution") or {}), 120)],
            ["执行落地", truncate(str(ref.get("execution") or {}), 120)],
            ["元认知", truncate(str(ref.get("metacognition") or {}), 120)],
        ],
    ))
    lines.append("")

    # 评分细则
    lines.append("### 评分细则")
    rubric_rows = []
    for s in rubric.get("stages") or []:
        pts = s.get("scoring_points") or []
        pts_desc = " · ".join(
            f"{p.get('description','')}({p.get('score','-')}, {p.get('evidence_type','-')})"
            for p in pts
        )
        rubric_rows.append([s.get("stage_name"), s.get("max_score"), s.get("weight"), truncate(pts_desc, 160)])
    lines.append(md_table(["阶段", "满分", "权重", "scoring_points"], rubric_rows))
    lines.append("")

    # fatal / veto
    lines.append("### 致命扣分项 / 一票否决项")
    for f in rubric.get("fatal_deductions") or []:
        lines.append(f"- **致命扣分**:{f.get('description','')} → {f.get('detection_rule','')}")
    for v in rubric.get("veto_items") or []:
        lines.append(f"- **一票否决**:{v.get('description','')} → {v.get('detection_rule','')}")

    return "\n".join(lines)


# ========== 主入口 ==========
def run(stage3_md: Path | str, out_dir: Path | None, agent_input: AgentInput) -> Path:
    out_dir = Path(out_dir) if out_dir else config.ensure_out_dir(agent_input.out_dir)
    out_path = out_dir / "04_tests.md"

    # --- 读上游 ---
    stage3 = read_md(stage3_md)
    art3 = stage3["artifacts"]
    test_contexts: list[dict[str, Any]] = art3.get("test_contexts", [])
    if not test_contexts:
        raise MissingInputError(
            stage="Stage 4 · 题目生成",
            report=[
                MissingField(
                    field_name="03_context.md 的 test_contexts",
                    why_needed="Stage 4 依赖 Stage 3 产出的知识后台",
                    suggested_format="重跑 Stage 3",
                    example="python -m questforge.run_pipeline --only stage3 --input-json <path>",
                )
            ],
        )

    stage3_path = Path(stage3_md)
    stage2_md = stage3_path.parent / "02_plan.md"
    stage1_md = stage3_path.parent / "01_understanding.md"
    if not stage2_md.exists() or not stage1_md.exists():
        raise FileNotFoundError(f"缺少上游 {stage2_md} 或 {stage1_md}")

    art2 = read_md(stage2_md)["artifacts"]
    art1 = read_md(stage1_md)["artifacts"]
    pid2proc = {p["id"]: p for p in art2.get("processes", [])}
    test_plan = art2.get("test_plan", [])
    plan_by_tid = {t["test_id"]: t for t in test_plan}
    glossary: dict[str, str] = art1.get("glossary", {})

    # --- LLM 必备 ---
    client = get_default_client()
    if not client.use_llm:
        raise MissingInputError(
            stage="Stage 4 · 题目生成",
            report=[
                MissingField(
                    field_name="LLM_API_KEY",
                    why_needed="题目/期望/评分细则生成全部依赖 LLM,不做本地兜底",
                    suggested_format="配置 .env 里的 LLM_API_KEY",
                    example="LLM_API_KEY=sk-xxx",
                )
            ],
        )

    # --- 加载 system prompt ---
    system_prompt = (
        config.REPO_ROOT / "questforge" / "prompts" / "stage4_item.txt"
    ).read_text(encoding="utf-8")

    # --- 构建任务 + 断点续传 ---
    tasks = _build_tasks(test_contexts, plan_by_tid, pid2proc, agent_input.domain)
    items_jsonl = out_dir / "stage4_items.jsonl"
    done_ids = _load_done_ids(items_jsonl)
    items_existing = _read_existing_items(items_jsonl)
    pending = [t for t in tasks if t["test_id"] not in done_ids]

    if done_ids:
        log.info("[Stage4] 跳过 %d 个已完成 test:%s", len(done_ids), sorted(done_ids))

    log.info(
        "[Stage4] 任务 %d(待执行 %d · 并发 %d · 输出 %s)",
        len(tasks), len(pending), config.STAGE4_MAX_WORKERS, items_jsonl,
    )

    # --- 并发生成 ---
    program_start = time.time()
    write_lock = threading.Lock()
    new_items: list[dict[str, Any]] = []
    errors: list[tuple[str, str]] = []

    if pending:
        with ThreadPoolExecutor(max_workers=config.STAGE4_MAX_WORKERS) as executor:
            futures = {
                executor.submit(_generate_one, t, client, system_prompt, glossary, program_start): t["test_id"]
                for t in pending
            }
            for fut in as_completed(futures):
                tid = futures[fut]
                try:
                    item, err = fut.result()
                except Exception as e:  # pragma: no cover
                    errors.append((tid, f"异常:{type(e).__name__}: {e}"))
                    log.exception("[Stage4] %s 任务异常", tid)
                    continue
                if item is not None:
                    new_items.append(item)
                    _append_jsonl(items_jsonl, item, write_lock)
                else:
                    errors.append((tid, err))

    items = items_existing + new_items

    if not items:
        raise MissingInputError(
            stage="Stage 4 · 题目生成",
            report=[
                MissingField(
                    field_name="LLM 输出",
                    why_needed="全部题目生成失败,Pipeline 不自造题目",
                    suggested_format=(
                        "检查 LLM_MODEL / LLM_API_KEY / prompts/stage4_item.txt;"
                        f"失败明细:{'; '.join(f'{t}: {e}' for t, e in errors[:3])}"
                    ),
                    example="python -m questforge.run_pipeline --only stage4 --input-json ...",
                )
            ],
        )

    # --- Step 4.4 本地难度校准 ---
    tctx_by_id = {tc["test_id"]: tc for tc in test_contexts}
    mismatches: list[dict[str, Any]] = []
    for item in items:
        tctx = tctx_by_id.get(item["test_id"])
        if tctx is None:
            continue
        rep = pid2proc.get(item.get("source_process") or "", {})
        score, label = _calibrate_difficulty(item, tctx, rep)
        planned = (plan_by_tid.get(item["test_id"]) or {}).get("difficulty")
        item["difficulty_score"] = round(score, 2)
        item["difficulty"] = label
        if planned and label != planned:
            mismatches.append(
                {
                    "test_id": item["test_id"],
                    "planned": planned,
                    "calibrated": label,
                    "difficulty_score": item["difficulty_score"],
                }
            )

    items.sort(key=lambda x: x.get("test_id", ""))

    # --- 校验清单 ---
    checklist = Checklist()
    checklist.add(
        f"items 数 == test_plan 数({len(tasks)})", len(items) == len(tasks)
    )
    checklist.add(
        f"每道 TEST 的 prompt 长度 {config.STAGE4_PROMPT_LEN[0]}-{config.STAGE4_PROMPT_LEN[1]} 字",
        all(_prompt_len_ok(it) for it in items),
    )
    checklist.add("每道 TEST 的 reference 覆盖 5 阶段", all(_reference_complete(it) for it in items))
    checklist.add(
        "每道 TEST 的 decompose.expected_steps 与 source_process.steps 一致",
        all(_decompose_match(it, pid2proc) for it in items),
    )
    checklist.add(
        "每道 TEST 的 rubric 总分=10 且权重 2/2/3/2/1",
        all(_rubric_weights_ok(it) for it in items),
    )
    checklist.add(
        "每道 TEST ≥1 fatal_deduction + ≥1 veto_item",
        all(_fatal_veto_ok(it) for it in items),
    )
    checklist.add(
        "每道 TEST 的 prompt 嵌入所有 Stage 3 约束项关键词",
        all(_constraints_embedded(it, tctx_by_id.get(it["test_id"], {})) for it in items),
    )

    # --- Artifacts ---
    artifacts_out = {
        "generation_summary": {
            "total_planned": len(tasks),
            "generated": len(items),
            "failed": [{"test_id": t, "reason": r} for t, r in errors],
        },
        "items": items,
        "difficulty_mismatches": mismatches,
    }

    # --- Sections ---
    sections = [
        Section("题目一览", _render_overview_table(items, tctx_by_id)),
        Section("难度自校准一致性", _render_mismatch_section(mismatches)),
        Section(
            "逐题详情",
            "\n\n".join(_render_item_section(it, tctx_by_id.get(it["test_id"], {})) for it in items),
        ),
    ]

    summary = (
        f"共生成 {len(items)}/{len(tasks)} 道题(失败 {len(errors)});"
        f"难度一致 {len(items) - len(mismatches)} 道、偏移 {len(mismatches)} 道;"
        f"平均 difficulty_score {sum(it.get('difficulty_score',0) for it in items)/max(len(items),1):.2f}。"
    )

    remarks_lines: list[str] = []
    if mismatches:
        remarks_lines.append("难度自校准与 Stage 2 规划不一致(本阶段不覆盖 Stage 2,留待 Stage 5 裁决):")
        for m in mismatches:
            remarks_lines.append(
                f"  - {m['test_id']}: 规划={m['planned']},校准={m['calibrated']}"
                f"(score={m['difficulty_score']})"
            )
    if errors:
        remarks_lines.append("以下 TEST 生成失败,需 `--only stage4` 续跑:")
        for tid, reason in errors:
            remarks_lines.append(f"  - {tid}: {reason}")

    frontmatter = {
        "stage": 4,
        "stage_name": "test_items",
        "version": "1.0",
        "upstream": "03_context.md",
        "downstream": "05_report.md",
        "domain": agent_input.domain,
        "created_at": iso_now(),
        "created_by": "agent-stage4",
        "pass_gate": checklist.all_passed(),
    }

    write_md(
        out_path,
        frontmatter=frontmatter,
        title="Stage 4 · 题目 + 期望 + 评分细则",
        summary=summary,
        sections=sections,
        artifacts=artifacts_out,
        checklist=checklist,
        remarks="\n".join(remarks_lines) if remarks_lines else "(无)",
    )
    return out_path


def _render_mismatch_section(mismatches: list[dict[str, Any]]) -> str:
    if not mismatches:
        return "全部题目的难度自校准与 Stage 2 规划一致。"
    return md_table(
        ["TEST", "Stage 2 规划", "Stage 4 校准", "difficulty_score"],
        [
            [m["test_id"], m["planned"], m["calibrated"], m["difficulty_score"]]
            for m in mismatches
        ],
    )


__all__ = ["run"]
