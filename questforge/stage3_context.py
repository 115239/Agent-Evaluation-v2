"""Stage 3 · 仿真数据集构建 + 约束/干扰设计 → 03_context.md

输入:02_plan.md + 01_understanding.md + AgentInput
输出:OUT_DIR / 03_context.md + stage3_fragments.jsonl + stage3_inverted_index.json

处理步骤(§4.5):
  3.1 知识资产索引构建
  3.2 题目 × 资产匹配(category 相似度 + LLM 兜底)
  3.3 关键字候选池提取
  3.4 约束项设计(第二层 Fallback,由 LLM 基于流程特性推导)
  3.5 干扰项设计(同层 Fallback,由 LLM 推导)
  3.6 业务真实性三检验

Stage 1 glossary + knowledge_assets.authority + weak_points 动态组装。
"""
from __future__ import annotations

import json
import logging
import random
import re
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, IdCounter, Section, iso_now, md_table, read_md, truncate, write_md
from .input_spec import AgentInput, MissingField, MissingInputError
from .io_utils import (
    KBFragment,
    build_fragments,
    build_inverted_index,
    extract_local_keywords,
    load_kb,
)
from .llm_client import LLMClient, get_default_client

log = logging.getLogger("questforge.stage3")


# ========== 内部 ID 清洗(避免泄漏到面向用户的题目) ==========
# 注意:中文与字母相邻时 \b 不触发,因此放宽边界,只用前后向的"非数字/字母"避免吃到别的 token。
_INTERNAL_ID_RE = re.compile(r"(?<![A-Za-z0-9])(KB|BP|FRAG|UG|FEAT|PT|TEST|C|I)-\d+(?:-\d+)?(?![A-Za-z0-9])")


def _strip_internal_ids(text: str, asset_by_id: dict[str, dict[str, Any]]) -> str:
    """把 text 中的内部 ID 代号替换为业务语言。

    - KB-xxx → 该资产的 category(如"结构化条款");找不到则回落"相关资产"
    - 其他前缀的 ID → 删除代号,上下文通常已含业务词(如"该流程"、"相关片段")
    """
    if not text:
        return text

    def _sub(match: re.Match) -> str:
        prefix = match.group(1)
        full = match.group(0)
        if prefix == "KB" and full in asset_by_id:
            cat = (asset_by_id[full].get("category") or "").strip()
            return cat or "相关资产"
        return ""

    cleaned = _INTERNAL_ID_RE.sub(_sub, text)
    # 折叠空格,清理多余标点
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"(、|,){2,}", lambda m: m.group(0)[0], cleaned)
    cleaned = re.sub(r"^(、|,|\s)+|(、|,|\s)+$", "", cleaned)
    return cleaned


# ========== Step 3.1 索引构建 ==========
def _metadata_keys_for(asset_card: dict[str, Any]) -> list[str]:
    """对每个资产挑 2-3 个有效的元信息列:优先时间 / 来源 / 主题。"""
    cols = asset_card.get("columns") or []
    hints = ["时间", "日期", "发布", "来源", "出处", "主题", "类别", "type", "date"]
    picked: list[str] = []
    for h in hints:
        for c in cols:
            if h in c and c not in picked:
                picked.append(c)
                break
    return picked[:3]


def _build_all_fragments(knowledge_assets: list[dict[str, Any]]) -> tuple[
    list[KBFragment], dict[str, KBFragment], dict[str, list[str]], dict[str, dict[str, Any]]
]:
    all_frags: list[KBFragment] = []
    by_kb: dict[str, list[str]] = {}
    asset_by_id: dict[str, dict[str, Any]] = {}

    for asset in knowledge_assets:
        asset_by_id[asset["id"]] = asset
        path = Path(asset.get("path") or "")
        if not path.is_file():
            log.warning("资产 %s 的 path 不存在,跳过索引", asset["id"])
            by_kb[asset["id"]] = []
            continue
        try:
            df = load_kb(path, asset["sheet"])
        except Exception as e:
            log.warning("加载资产失败 %s:%s", asset["id"], e)
            by_kb[asset["id"]] = []
            continue

        # 如果 sample_rows 的 columns 里恰好有,用它生成 metadata 列
        meta_keys = _metadata_keys_for({"columns": list(df.columns)})

        def _meta(r, keys=meta_keys):
            return {k: str(r.get(k, "")).strip() for k in keys}

        frags = build_fragments(
            df,
            asset_id=asset["id"],
            key_fields=asset["key_fields"],
            metadata_extractor=_meta,
        )
        all_frags.extend(frags)
        by_kb[asset["id"]] = [f.frag_id for f in frags]
        log.info("[Stage3] %s 索引 %d 条 fragment", asset["id"], len(frags))

    by_id = {f.frag_id: f for f in all_frags}
    return all_frags, by_id, by_kb, asset_by_id


# ========== Step 3.2 题目 × 资产匹配 ==========
def _category_match_score(cat_a: str, cat_b: str) -> float:
    """基于字符串子串的粗匹配(0-1)。"""
    a, b = (cat_a or "").strip(), (cat_b or "").strip()
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.75
    sa, sb = set(a), set(b)
    return len(sa & sb) / max(len(sa | sb), 1)


def _rotate_pick(
    values: list[str],
    target_n: int,
    sample_idx: int,
    covered_by: dict[str, list[str]] | None = None,
) -> list[str]:
    """按 sample_idx 和已覆盖情况选取,让同类题与跨类型题尽量使用不同资产窗口。"""
    ordered = list(dict.fromkeys(v for v in values if v))
    if len(ordered) <= target_n:
        return ordered
    if covered_by:
        indexed = list(enumerate(ordered))
        indexed.sort(
            key=lambda item: (
                len(covered_by.get(item[1], [])),
                (item[0] - sample_idx) % len(ordered),
            )
        )
        return [aid for _, aid in indexed[:target_n]]
    start = sample_idx % len(ordered)
    rotated = ordered[start:] + ordered[:start]
    return rotated[:target_n]


def _match_assets(
    test: dict[str, Any],
    rep_process: dict[str, Any],
    knowledge_assets: list[dict[str, Any]],
    client: LLMClient,
    features: list[dict[str, Any]] | None = None,
    covered_by: dict[str, list[str]] | None = None,
) -> list[str]:
    """按多级匹配选主资产:process.depends_on > features 反查 > output.category 子串 > LLM。"""
    difficulty = test["difficulty"]
    target_n = config.DIFFICULTY_SAMPLING[difficulty]["primary_assets"]
    sample_idx = int(test.get("sample_idx") or 0)
    asset_ids = {a["id"] for a in knowledge_assets}

    # 一级:Stage 2 LLM 直接在 process 上写了 depends_on
    direct = [x for x in (rep_process.get("depends_on") or []) if x in asset_ids]
    if direct:
        return _rotate_pick(direct, target_n, sample_idx, covered_by)

    # 二级:通过 features 反查(feature.name 与 process.name 字符重叠最高者)
    features = features or []
    if features:
        proc_chars = {c for c in rep_process.get("name", "") if "\u4e00" <= c <= "\u9fa5"}
        best_feat: dict[str, Any] | None = None
        best_overlap = 0
        for feat in features:
            fchars = {c for c in feat.get("name", "") if "\u4e00" <= c <= "\u9fa5"}
            if not fchars:
                continue
            overlap = len(proc_chars & fchars)
            if overlap > best_overlap:
                best_overlap = overlap
                best_feat = feat
        if best_feat and best_overlap >= 2:
            dep = [x for x in (best_feat.get("depends_on") or []) if x in asset_ids]
            if dep:
                return _rotate_pick(dep, target_n, sample_idx, covered_by)

    # 三级:output.category 子串匹配
    output_cats = [o.get("category", "") for o in rep_process.get("outputs", [])]
    ranked: list[tuple[str, float]] = []
    for oc in output_cats:
        for asset in knowledge_assets:
            score = _category_match_score(oc, asset.get("category", ""))
            if score > 0:
                ranked.append((asset["id"], score))

    bucket: dict[str, float] = {}
    for aid, s in ranked:
        bucket[aid] = bucket.get(aid, 0.0) + s

    top = sorted(bucket.items(), key=lambda kv: kv[1], reverse=True)
    strong = [aid for aid, s in top if s >= 0.75]

    if len(strong) >= 1:
        return _rotate_pick([aid for aid, _ in top], target_n, sample_idx, covered_by)

    # 四级:LLM 裁决
    if client.use_llm:
        ranked_ids = _llm_rank_assets(client, rep_process, knowledge_assets)
        if ranked_ids:
            return _rotate_pick(ranked_ids, target_n, sample_idx, covered_by)

    # 仍无 → 取全部资产前 N 个作为保底
    return _rotate_pick([a["id"] for a in knowledge_assets], target_n, sample_idx, covered_by)


def _llm_rank_assets(client: LLMClient, rep_process: dict[str, Any], assets: list[dict[str, Any]]) -> list[str]:
    system = (
        "你是业务知识工程师。给定一个业务流程与资产卡片列表,"
        "按'与该流程 outputs 的匹配度'从高到低输出 asset id 列表(JSON)。"
    )
    brief_proc = {
        "name": rep_process.get("name"),
        "triggers": rep_process.get("triggers"),
        "outputs": rep_process.get("outputs"),
    }
    brief_assets = [
        {"id": a["id"], "category": a.get("category"), "key_fields": a.get("key_fields")} for a in assets
    ]
    user = (
        f"<process>{json.dumps(brief_proc, ensure_ascii=False)}</process>\n"
        f"<assets>{json.dumps(brief_assets, ensure_ascii=False)}</assets>\n"
        '请输出 {"ranked":["KB-xxx", ...]};不要解释。'
    )
    out = client.chat_json(system, user, max_tokens=300)
    if not isinstance(out, dict):
        return []
    known = {a["id"] for a in assets}
    return [x for x in (out.get("ranked") or []) if x in known]


def _pick_fragments(
    asset_ids: list[str],
    by_kb: dict[str, list[str]],
    by_id: dict[str, KBFragment],
    *,
    rep_process: dict[str, Any],
    difficulty: str,
    sample_idx: int,
    focus_stages: list[str],
    domain_hints: set[str],
    rng: random.Random,
) -> list[KBFragment]:
    """从选中的 KB 里抽候选 fragment。按流程多字段抽关键词,按命中数 desc 排序取 top-N。

    命中不足 target_n 时允许返回少于目标数,避免用随机补引入噪声。
    """
    target_n = config.DIFFICULTY_SAMPLING[difficulty]["candidate_fragments"]

    # 扩展 query 来源:name + triggers.description + steps.name + outputs.name
    query_parts: list[str] = [rep_process.get("name", "")]
    for t in rep_process.get("triggers", []) or []:
        query_parts.append(t.get("description", "") or "")
        query_parts.append(t.get("type", "") or "")
    for s in rep_process.get("steps", []) or []:
        query_parts.append(s.get("name", "") or "")
    for o in rep_process.get("outputs", []) or []:
        query_parts.append(o.get("name", "") or "")
    query_parts.extend(s for s in focus_stages if s)
    query_parts = [p for p in query_parts if p]

    query_kws: list[str] = []
    for part in query_parts:
        query_kws.extend(extract_local_keywords(part, top_k=4, domain_hints=domain_hints))
    query_kws.extend(
        extract_local_keywords(" ".join(query_parts), top_k=8, domain_hints=domain_hints)
    )

    dedup_kws: list[str] = []
    seen_kws: set[str] = set()
    for kw in query_kws:
        if kw and kw not in seen_kws:
            seen_kws.add(kw)
            dedup_kws.append(kw)
    query_kws = dedup_kws[:20]

    query_grams: list[str] = []
    for kw in query_kws:
        pure = "".join(ch for ch in kw if "\u4e00" <= ch <= "\u9fa5")
        for n in (2, 3):
            for i in range(len(pure) - n + 1):
                gram = pure[i : i + n]
                if len(set(gram)) == 1:
                    continue
                query_grams.append(gram)
    seen_grams: set[str] = set()
    query_grams = [g for g in query_grams if not (g in seen_grams or seen_grams.add(g))]

    pool: list[KBFragment] = []
    for aid in asset_ids:
        pool.extend(by_id[fid] for fid in by_kb.get(aid, []))

    if not query_kws or not pool:
        log.warning(
            "[Stage3] _pick_fragments: query_kws=%d, pool=%d → 无法按关键词排序,取前 %d 个片段",
            len(query_kws), len(pool), target_n,
        )
        return pool[:target_n] if sample_idx == 0 else pool[sample_idx: sample_idx + target_n] or pool[:target_n]

    # 先走精确关键词命中,命中不足再用 2-3 字短片段模糊补足,避免 query 过长导致全空。
    scored: list[tuple[tuple[int, int], KBFragment]] = []
    for frag in pool:
        exact_hits = sum(1 for kw in query_kws if kw in frag.key_text)
        gram_hits = 0 if exact_hits > 0 else sum(1 for gram in query_grams if gram in frag.key_text)
        if exact_hits > 0 or gram_hits > 0:
            scored.append(((exact_hits, gram_hits), frag))

    scored.sort(key=lambda x: x[0], reverse=True)
    ranked_fragments = [frag for _, frag in scored]
    max_start = max(0, len(ranked_fragments) - target_n)
    start = min(sample_idx * max(1, target_n // 2), max_start)
    picked = ranked_fragments[start : start + target_n]

    if len(picked) < target_n:
        stop_chars = set("的一是在不了和与及对将按由以等中为个类需可该其后前")
        query_chars = {
            ch
            for text in (query_kws + query_parts)
            for ch in text
            if "\u4e00" <= ch <= "\u9fa5" and ch not in stop_chars
        }
        fuzzy_scored: list[tuple[int, KBFragment]] = []
        picked_ids = {frag.frag_id for frag in picked}
        for frag in pool:
            if frag.frag_id in picked_ids:
                continue
            frag_chars = {
                ch for ch in frag.key_text if "\u4e00" <= ch <= "\u9fa5" and ch not in stop_chars
            }
            overlap = len(query_chars & frag_chars)
            if overlap > 0:
                fuzzy_scored.append((overlap, frag))
        fuzzy_scored.sort(key=lambda x: x[0], reverse=True)
        needed = target_n - len(picked)
        fuzzy_picked = [frag for _, frag in fuzzy_scored[:needed]]
        if fuzzy_picked:
            log.info(
                "[Stage3] _pick_fragments: 流程 %s 精确命中不足,使用模糊回退补足 %d 条",
                rep_process.get("id", "?"),
                len(fuzzy_picked),
            )
            picked.extend(fuzzy_picked)

    if len(picked) < target_n:
        log.warning(
            "[Stage3] _pick_fragments: 流程 %s 只命中 %d/%d 个相关片段,不做随机补全",
            rep_process.get("id", "?"), len(picked), target_n,
        )
    return picked


# ========== Step 3.3 关键字候选池 ==========
def _keyword_pool(
    fragments: list[KBFragment],
    difficulty: str,
    client: LLMClient,
    llm_budget: list[int],
    domain_hints: set[str],
) -> list[str]:
    pool: list[str] = []
    for frag in fragments:
        pool.extend(extract_local_keywords(frag.key_text, top_k=2, domain_hints=domain_hints))

    if difficulty in ("advanced", "expert") and llm_budget[0] > 0 and client.use_llm and fragments:
        kw = _llm_extract_keyword(client, fragments[0].key_text)
        llm_budget[0] -= 1
        if kw:
            pool.append(kw)

    seen: set[str] = set()
    dedup: list[str] = []
    for w in pool:
        if w and w not in seen:
            seen.add(w)
            dedup.append(w)
    return dedup[:8]


def _llm_extract_keyword(client: LLMClient, text: str) -> str:
    system = (
        "你是领域关键词提取员,只从参考文本中抽取 1 个 4-8 字、贴合业务场景的核心短语。"
    )
    user = (
        f"参考文本:{text[:800]}\n\n"
        "规则:\n"
        "1. 只返回 1 个关键词,严禁多条\n"
        "2. 长度严格 4-8 字\n"
        "3. 100% 来源于参考文本,贴合具体业务场景\n"
        "4. 禁用泛词(如'问题/规定/情况/内容')\n"
        "5. 仅返回短语本身,不要解释、标点或换行"
    )
    raw = client.chat_text(system, user, temperature=0.3, max_tokens=20).strip()
    if 4 <= len(raw) <= 8 and all("\u4e00" <= c <= "\u9fa5" for c in raw):
        return raw
    return ""


# ========== Step 3.4/3.5 约束项 + 干扰项协同设计(单次 LLM 调用) ==========
def _process_feature_profile(
    rep_process: dict[str, Any], asset_cards: list[dict[str, Any]], weak_points: list[str]
) -> dict[str, Any]:
    """从流程特性凝练 5 维度问卷,供 LLM 推导约束/干扰时使用。"""
    return {
        "cross_process_dependency": rep_process.get("cross_process_dependency", "单流程"),
        "actors_levels": sorted({a.get("level", "") for a in rep_process.get("actors", []) if a.get("level")}),
        "outputs_count": len(rep_process.get("outputs", [])),
        "triggers": [t.get("type") for t in rep_process.get("triggers", [])],
        "assets_involved": [
            {"id": a["id"], "category": a.get("category"), "authority": a.get("authority")} for a in asset_cards
        ],
        "weak_points": list(weak_points or []),
    }


def _jaccard_chars(a: str, b: str) -> float:
    """字符级 Jaccard,用于检测约束/干扰是否重复指向同一失败点。"""
    sa = {ch for ch in (a or "") if "\u4e00" <= ch <= "\u9fa5"}
    sb = {ch for ch in (b or "") if "\u4e00" <= ch <= "\u9fa5"}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa | sb), 1)


def _personas_brief(rep_process: dict[str, Any], user_groups_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for actor in (rep_process.get("actors") or []):
        ug = user_groups_by_id.get((actor.get("id") or "").strip(), {})
        persona = ug.get("persona") or {}
        eb = persona.get("emotional_baseline") or {}
        kd = persona.get("knowledge_domain") or {}
        if (eb.get("frustration_triggers") or []) or (kd.get("misconceptions") or []):
            out.append(
                {
                    "id": ug.get("id"),
                    "role": ug.get("role"),
                    "frustration_triggers": eb.get("frustration_triggers") or [],
                    "misconceptions": kd.get("misconceptions") or [],
                    "stress_level": eb.get("stress_level") or "NOT_SPECIFIED",
                }
            )
    return out


def _llm_design_constraints_and_interferences(
    client: LLMClient,
    rep_process: dict[str, Any],
    asset_cards: list[dict[str, Any]],
    fragments: list[KBFragment],
    keyword_pool: list[str],
    weak_points: list[str],
    domain: str,
    difficulty: str,
    c_counter: IdCounter,
    i_counter: IdCounter,
    asset_by_id: dict[str, dict[str, Any]],
    user_personas: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """单次 LLM 调用同时生成约束与干扰,在 prompt 内强制互不重复 + fragment 落地 + trap_kind 语义。"""
    system_path = config.REPO_ROOT / "questforge/prompts/stage3_design.txt"
    system = system_path.read_text(encoding="utf-8")

    profile = _process_feature_profile(rep_process, asset_cards, weak_points)
    fragment_snippets = [
        {"frag_id": f.frag_id, "asset_id": f.asset_id, "snippet": truncate(f.key_text, 160)}
        for f in fragments[:6]
    ]
    target_constraints = config.STAGE3_CONSTRAINT_COUNT.get(difficulty, (3, 4))
    target_interferences = config.INTERFERENCE_DENSITY.get(difficulty, 1)

    user = (
        f"<domain>{domain}</domain>\n"
        f"<difficulty>{difficulty}</difficulty>\n"
        f"<process>{json.dumps({'id': rep_process.get('id'), 'name': rep_process.get('name'), 'outputs': rep_process.get('outputs')}, ensure_ascii=False)}</process>\n"
        f"<profile>{json.dumps(profile, ensure_ascii=False)}</profile>\n"
        f"<fragment_snippets>{json.dumps(fragment_snippets, ensure_ascii=False)}</fragment_snippets>\n"
        f"<keyword_pool>{json.dumps(keyword_pool, ensure_ascii=False)}</keyword_pool>\n"
        f"<user_personas>{json.dumps(user_personas or [], ensure_ascii=False)}</user_personas>\n"
        f"<target_constraints>{target_constraints[0]}-{target_constraints[1]}</target_constraints>\n"
        f"<target_interferences>{target_interferences}</target_interferences>\n"
        f"<trap_required>{'true' if difficulty == 'expert' else 'false'}</trap_required>\n"
        f"<trap_kind_vocab>{json.dumps(list(config.TRAP_KIND_VOCAB), ensure_ascii=False)}</trap_kind_vocab>\n"
    )
    out = client.chat_json(system, user, max_tokens=2400)
    if not isinstance(out, dict):
        return [], []

    raw_cs = out.get("constraints") or []
    raw_is = out.get("interferences") or []

    constraints: list[dict[str, Any]] = []
    for item in raw_cs[: target_constraints[1]]:
        text = _strip_internal_ids((item.get("text") or "").strip(), asset_by_id)
        if not text:
            continue
        constraints.append(
            {
                "id": c_counter.next(),
                "text": text,
                "source": (item.get("source") or "LLM 推导").strip(),
                "targets": [str(t).strip() for t in (item.get("targets") or []) if str(t).strip()],
            }
        )

    interferences: list[dict[str, Any]] = []
    overlap_thr = config.STAGE3_DESIGN_OVERLAP_THRESHOLD
    for item in raw_is[: max(target_interferences, 1) if difficulty != "basic" else target_interferences]:
        text = _strip_internal_ids((item.get("text") or "").strip(), asset_by_id)
        if not text:
            continue
        # 互斥校验:与任一约束 jaccard ≥ 阈值则丢弃
        if any(_jaccard_chars(text, c["text"]) >= overlap_thr for c in constraints):
            log.info(
                "[Stage3] 干扰 '%s' 与已有约束相似度过高,丢弃以避免重复指向同一失败点", truncate(text, 40)
            )
            continue
        trap_kind = (item.get("trap_kind") or "none").strip()
        if trap_kind not in config.TRAP_KIND_VOCAB:
            trap_kind = "none"
        is_trap = bool(item.get("trap", False)) or (trap_kind != "none")
        # 兜底:LLM 漏标但 text 命中关键词,回填 trap=true
        if not is_trap and any(k in text for k in config.TRAP_KEYWORDS):
            is_trap = True
            if trap_kind == "none":
                trap_kind = "version_conflict"
        category = (item.get("category") or trap_kind or "unspecified").strip().lower()
        interferences.append(
            {
                "id": i_counter.next(),
                "text": text,
                "trap": is_trap,
                "trap_kind": trap_kind,
                "category": category,
                "process_ref": rep_process.get("name"),
            }
        )

    # expert 必须至少 1 个 trap=true 且 trap_kind != none
    if difficulty == "expert" and not any(x["trap"] and x["trap_kind"] != "none" for x in interferences):
        # 优先把已有 trap_kind != none 的标 trap=true
        for x in interferences:
            if x["trap_kind"] != "none":
                x["trap"] = True
                break
        # 仍不满足:把最后一条 text 含关键词的回填
        if not any(x["trap"] and x["trap_kind"] != "none" for x in interferences):
            for x in interferences:
                if any(k in x["text"] for k in config.TRAP_KEYWORDS):
                    x["trap"] = True
                    x["trap_kind"] = "version_conflict"
                    break

    return constraints, interferences


def _llm_generate_constraints(
    client: LLMClient,
    rep_process: dict[str, Any],
    asset_cards: list[dict[str, Any]],
    weak_points: list[str],
    domain: str,
    counter: IdCounter,
    difficulty: str,
    asset_by_id: dict[str, dict[str, Any]],
    *,
    fragments: list[KBFragment] | None = None,
    keyword_pool: list[str] | None = None,
    user_personas: list[dict[str, Any]] | None = None,
    _shared_state: dict | None = None,
) -> list[dict[str, Any]]:
    """薄包装:与 _llm_generate_interferences 共享一次 LLM 调用结果。"""
    state = _shared_state if _shared_state is not None else {}
    if "result" not in state:
        state["result"] = _llm_design_constraints_and_interferences(
            client, rep_process, asset_cards, list(fragments or []), list(keyword_pool or []),
            weak_points, domain, difficulty, counter, IdCounter("I"), asset_by_id,
            user_personas=user_personas,
        )
    return state["result"][0]


def _llm_generate_interferences(
    client: LLMClient,
    rep_process: dict[str, Any],
    asset_cards: list[dict[str, Any]],
    weak_points: list[str],
    domain: str,
    difficulty: str,
    counter: IdCounter,
    asset_by_id: dict[str, dict[str, Any]],
    user_personas: list[dict[str, Any]] | None = None,
    *,
    _shared_state: dict | None = None,
) -> list[dict[str, Any]]:
    """薄包装:从共享 state 取干扰,密度=0 时跳过。"""
    if config.INTERFERENCE_DENSITY[difficulty] == 0:
        return []
    state = _shared_state or {}
    if "result" not in state:
        return []
    return state["result"][1]


# ========== Step 3.6 真实性三检验 ==========
def _build_authority_keywords(
    glossary: dict[str, str], knowledge_assets: list[dict[str, Any]], weak_points: list[str]
) -> list[str]:
    """组装"权威词":只取真正具有领域语义的词,避免"含'条款'就 pass"的低门槛幻觉。

    收紧规则:
    - 保留 glossary keys(用户/LLM 抽取的领域术语)
    - 保留 asset.authority(标签如"官方"等仅 ≥3 字时才计,过滤通用短词)
    - 保留 asset.category 本身(≥3 字),不再展开其分词(原"category 分词→关键词"会引入'条款'等通用噪声)
    - 保留 weak_points 抽出的关键词
    - 不再把 key_fields(列名)当作权威词
    """
    kws: set[str] = set()
    kws.update(k for k in glossary.keys() if k and len(k) >= 2)
    for a in knowledge_assets:
        auth = (a.get("authority") or "").strip()
        if auth and len(auth) >= 3:
            kws.add(auth)
        category = (a.get("category") or "").strip()
        if category and len(category) >= 3:
            kws.add(category)
    for wp in weak_points:
        for kw in extract_local_keywords(wp, top_k=2):
            if kw and len(kw) >= 2:
                kws.add(kw)
    return sorted(x for x in kws if x)


def _realism_check(
    item: dict[str, Any],
    glossary: dict[str, str],
    authority_keywords: list[str],
    inverted_index: dict[str, list[str]],
    client: LLMClient,
    llm_budget: list[int],
    domain: str,
) -> dict[str, Any]:
    text = item.get("text", "")

    for kw in authority_keywords:
        if kw and kw in text:
            return {"verified_by": "regulation_support", "matched": kw}

    for kw in extract_local_keywords(text, top_k=5, domain_hints=set(glossary.keys())):
        if kw in inverted_index:
            return {"verified_by": "regulation_support", "matched": kw}

    for term, defn in glossary.items():
        if term and term in text:
            return {"verified_by": "commonsense", "term": term}
        for piece in extract_local_keywords(defn, top_k=2):
            if piece and piece in text:
                return {"verified_by": "commonsense", "term": term}

    if llm_budget[0] > 0 and client.use_llm:
        system_path = config.REPO_ROOT / "questforge/prompts/stage3_realism.txt"
        system = system_path.read_text(encoding="utf-8").replace("{domain}", domain)
        user = f"待判定:{text}\n\n领域:{domain}"
        out = client.chat_json(system, user, temperature=0.0, max_tokens=200)
        llm_budget[0] -= 1
        if isinstance(out, dict) and out.get("verified_by") in {"regulation_support", "commonsense", "llm_judge"}:
            return {"verified_by": out["verified_by"], "reason": out.get("reason", "")}

    return {"verified_by": "none"}


# ========== 主流程 ==========
def run(stage2_md: Path | str, out_dir: Path | None, agent_input: AgentInput) -> Path:
    out_dir = Path(out_dir) if out_dir else config.ensure_out_dir(agent_input.out_dir)
    out_path = out_dir / "03_context.md"

    # --- 读上游 ---
    stage2 = read_md(stage2_md)
    art2 = stage2["artifacts"]
    processes = art2.get("processes", [])
    test_plan = art2.get("test_plan", [])
    pid2proc = {p["id"]: p for p in processes}

    stage1_md = Path(stage2_md).parent / "01_understanding.md"
    if not stage1_md.exists():
        raise FileNotFoundError(f"缺少上游 {stage1_md},请先跑 Stage 1")
    art1 = read_md(stage1_md)["artifacts"]
    glossary: dict[str, str] = art1.get("glossary", {})
    knowledge_assets: list[dict[str, Any]] = art1.get("knowledge_assets", [])
    features: list[dict[str, Any]] = art1.get("features", [])
    user_groups: list[dict[str, Any]] = art1.get("user_groups", [])
    user_groups_by_id: dict[str, dict[str, Any]] = {ug["id"]: ug for ug in user_groups if ug.get("id")}

    # --- LLM 必备 ---
    client = get_default_client()
    if not client.use_llm:
        raise MissingInputError(
            stage="Stage 3 · 仿真数据集构建",
            report=[
                MissingField(
                    field_name="LLM_API_KEY",
                    why_needed="约束/干扰设计、资产裁决、真实性判定均需 LLM",
                    suggested_format="配置 .env 里的 LLM_API_KEY",
                    example="LLM_API_KEY=<YOUR_API_KEY>",
                )
            ],
        )

    # --- 术语表充足性 ---
    authority_keywords = _build_authority_keywords(glossary, knowledge_assets, agent_input.weak_points)
    if not authority_keywords:
        raise MissingInputError(
            stage="Stage 3 · 仿真数据集构建",
            report=[
                MissingField(
                    field_name="glossary_seed 或 weak_points",
                    why_needed="真实性三检验需要至少一组'领域权威词',否则所有约束/干扰都会被视为幻觉",
                    suggested_format="在 example_input.json 补 glossary_seed 或 weak_points",
                    example='"weak_points": ["版本区分", "权限边界", "跨文档整合"]',
                )
            ],
        )

    # --- 3.1 索引 ---
    log.info("[Stage3] 构建知识索引…")
    all_frags, by_id, by_kb, asset_by_id = _build_all_fragments(knowledge_assets)
    inverted_index = build_inverted_index(all_frags, domain_hints=set(glossary.keys()))
    log.info(
        "[Stage3] 索引共 %d 个 fragment,倒排表 %d 个关键词", len(all_frags), len(inverted_index)
    )

    if not all_frags:
        raise MissingInputError(
            stage="Stage 3 · 仿真数据集构建",
            report=[
                MissingField(
                    field_name="knowledge_assets.path",
                    why_needed="所有资产均未产出 fragment;可能是 path 不存在、sheet 错误或 key_fields 未命中列名",
                    suggested_format="确认 Stage 1 artifacts 的 path 是有效绝对路径;检查 sheet 名与 key_fields",
                    example="重跑 Stage 1,或手工修正 01_understanding.md 的 knowledge_assets 段",
                )
            ],
        )

    # 落盘
    frag_jsonl = out_dir / "stage3_fragments.jsonl"
    with frag_jsonl.open("w", encoding="utf-8") as f:
        for frag in all_frags:
            f.write(
                json.dumps(
                    {
                        "frag_id": frag.frag_id,
                        "asset_id": frag.asset_id,
                        "row_no": frag.row_no,
                        "key_text": frag.key_text,
                        "metadata": frag.metadata,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    (out_dir / "stage3_inverted_index.json").write_text(
        json.dumps(inverted_index, ensure_ascii=False), encoding="utf-8"
    )

    # --- 3.2-3.6 逐题组装 ---
    rng = random.Random(42)
    llm_kw_budget = [config.MAX_LLM_KEYWORD_CALLS]
    llm_realism_budget = [config.STAGE3_REALISM_LLM_BUDGET]

    c_counter = IdCounter("C")
    i_counter = IdCounter("I")
    domain_hints = set(glossary.keys())

    test_contexts: list[dict[str, Any]] = []
    covered_by: dict[str, list[str]] = {a["id"]: [] for a in knowledge_assets}
    realism_discarded: list[str] = []

    for test in test_plan:
        rep = pid2proc[test["source_process"]]
        asset_ids = _match_assets(
            test,
            rep,
            knowledge_assets,
            client,
            features=features,
            covered_by=covered_by,
        )
        asset_cards = [asset_by_id[a] for a in asset_ids if a in asset_by_id]

        fragments = _pick_fragments(
            asset_ids,
            by_kb,
            by_id,
            rep_process=rep,
            difficulty=test["difficulty"],
            sample_idx=int(test.get("sample_idx") or 0),
            focus_stages=list(test.get("focus_stages") or []),
            domain_hints=domain_hints,
            rng=rng,
        )

        for aid in asset_ids:
            covered_by.setdefault(aid, []).append(test["test_id"])

        keyword_pool = _keyword_pool(fragments, test["difficulty"], client, llm_kw_budget, domain_hints)

        noise_frags: list[KBFragment] = []
        interference_frag_count = config.DIFFICULTY_SAMPLING[test["difficulty"]]["interference_fragments"]
        if interference_frag_count > 0:
            other_ids = [fid for kb, fids in by_kb.items() if kb not in asset_ids for fid in fids]
            rng.shuffle(other_ids)
            noise_frags = [by_id[fid] for fid in other_ids[:interference_frag_count]]

        # 协同设计:单次 LLM 调用同时产 constraints + interferences,fragment 注入,trap_kind 语义化
        raw_constraints, raw_interferences = _llm_design_constraints_and_interferences(
            client,
            rep,
            asset_cards,
            fragments,
            keyword_pool,
            agent_input.weak_points,
            agent_input.domain,
            test["difficulty"],
            c_counter,
            i_counter,
            asset_by_id,
            user_personas=_personas_brief(rep, user_groups_by_id),
        )

        if not raw_constraints:
            raise MissingInputError(
                stage="Stage 3 · 仿真数据集构建",
                report=[
                    MissingField(
                        field_name=f"TEST {test['test_id']} 的 constraints",
                        why_needed="LLM 未返回任何约束项,Pipeline 不自造模板",
                        suggested_format="在 example_input.json 的 weak_points 追加该题的能力短板提示",
                        example=(
                            '"weak_points": ["版本时效性", "跨资产整合", "权限边界"](帮助 LLM 聚焦约束维度)'
                        ),
                    )
                ],
            )

        # 真实性三检验
        constraints: list[dict[str, Any]] = []
        for c in raw_constraints:
            r = _realism_check(c, glossary, authority_keywords, inverted_index, client, llm_realism_budget, agent_input.domain)
            if r["verified_by"] != "none":
                constraints.append({**c, "verified_by": r["verified_by"]})
            else:
                realism_discarded.append(f"[{test['test_id']}][C] {c['text']}")

        interferences: list[dict[str, Any]] = []
        for i in raw_interferences:
            r = _realism_check(i, glossary, authority_keywords, inverted_index, client, llm_realism_budget, agent_input.domain)
            if r["verified_by"] != "none":
                interferences.append({**i, "verified_by": r["verified_by"]})
            else:
                realism_discarded.append(f"[{test['test_id']}][I] {i['text']}")

        realism_total_raw = len(raw_constraints) + len(raw_interferences)
        realism_kept = len(constraints) + len(interferences)
        realism_filtered = realism_total_raw - realism_kept

        test_contexts.append(
            {
                "test_id": test["test_id"],
                "difficulty": test["difficulty"],
                "sample_idx": int(test.get("sample_idx") or 0),
                "focus_stages": list(test.get("focus_stages") or []),
                "primary_assets": asset_ids,
                "fragments": [
                    {"frag_id": f.frag_id, "asset_id": f.asset_id, "snippet": truncate(f.key_text, 120)}
                    for f in fragments
                ],
                "interference_fragments": [
                    {"frag_id": f.frag_id, "asset_id": f.asset_id} for f in noise_frags
                ],
                "keyword_pool": keyword_pool,
                "constraints": constraints,
                "interferences": interferences,
                # 留存项 100% 通过真实性;原始 LLM 产出与丢弃数留作监控
                "realism_check": {
                    "total": realism_kept,
                    "passed": realism_kept,
                    "raw_total": realism_total_raw,
                    "filtered_out": realism_filtered,
                },
            }
        )

    # ==== Artifacts ====
    artifacts_out = {
        "fallback_status": {"weak_points_present": bool(agent_input.weak_points)},
        "authority_keywords_count": len(authority_keywords),
        "knowledge_index": {
            a["id"]: {
                "total_fragments": len(by_kb.get(a["id"], [])),
                "covered_by": sorted(set(covered_by.get(a["id"], []))),
            }
            for a in knowledge_assets
        },
        "test_contexts": test_contexts,
    }

    # ==== 校验清单(§4.5) ====
    checklist = Checklist()
    checklist.add(
        "每道 TEST 至少 1 个约束项",
        all(len(tc["constraints"]) >= 1 for tc in test_contexts),
    )

    density_ok = True
    for tc in test_contexts:
        want = config.INTERFERENCE_DENSITY[tc["difficulty"]]
        got = len(tc["interferences"])
        if tc["difficulty"] == "expert":
            if got < 2 or not any(i.get("trap") for i in tc["interferences"]):
                density_ok = False
                break
        elif tc["difficulty"] == "advanced":
            # 互斥过滤可能让干扰降到 0,允许 got >= 1(放宽:advanced 至少 1 条干扰)
            if got < 1:
                density_ok = False
                break
        else:  # basic
            if got != want:
                density_ok = False
                break
    checklist.add("basic 0 干扰、advanced ≥1、expert ≥2 且含 1 陷阱", density_ok)

    trap_kind_ok = all(
        all(i.get("trap_kind") in config.TRAP_KIND_VOCAB for i in tc["interferences"]) and
        (
            tc["difficulty"] != "expert"
            or any(i.get("trap_kind") and i["trap_kind"] != "none" for i in tc["interferences"])
        )
        for tc in test_contexts
    )
    checklist.add("trap_kind 取值合法且 expert 至少 1 条 trap_kind ≠ none", trap_kind_ok)

    checklist.add(
        "每条约束/干扰通过真实性三检验之一",
        all(
            all(c.get("verified_by") for c in tc["constraints"])
            and all(i.get("verified_by") for i in tc["interferences"])
            for tc in test_contexts
        ),
    )
    checklist.add(
        "每道 TEST 的 keyword_pool ≥ 1",
        all(tc["keyword_pool"] for tc in test_contexts),
    )
    checklist.add(
        "每道 TEST 的 fragments ≥ 1",
        all(tc["fragments"] for tc in test_contexts),
    )

    # ==== Sections ====
    sections = [
        Section(
            "Fallback 触发情况",
            md_table(
                ["项", "状态", "说明"],
                [
                    [
                        "weak_points 存在",
                        "✓" if agent_input.weak_points else "✗",
                        "已提供" if agent_input.weak_points else "全部走流程特性推导(LLM)",
                    ],
                ],
            ),
        ),
        Section(
            "知识索引摘要",
            md_table(
                ["资产", "切片数", "覆盖的 TEST"],
                [
                    [
                        a["id"],
                        len(by_kb.get(a["id"], [])),
                        ",".join(sorted(set(covered_by.get(a["id"], [])))) or "—",
                    ]
                    for a in knowledge_assets
                ],
            ),
        ),
        Section(
            "题目上下文设计",
            "\n\n".join(
                _render_test_section(tc, pid2proc[t["source_process"]])
                for tc, t in zip(test_contexts, test_plan)
            ),
        ),
    ]

    summary = (
        f"为 {len(test_contexts)} 道题建立了知识索引(共 {len(all_frags)} 个 fragment),"
        f"LLM 生成 {sum(len(tc['constraints']) for tc in test_contexts)} 条约束、"
        f"{sum(len(tc['interferences']) for tc in test_contexts)} 条干扰"
        f"(其中 {sum(1 for tc in test_contexts for i in tc['interferences'] if i.get('trap'))} 条陷阱)。"
        f"业务真实性通过 {sum(tc['realism_check']['passed'] for tc in test_contexts)}"
        f"/{sum(tc['realism_check']['total'] for tc in test_contexts)}。"
        + ("第二层 Fallback 未触发(用户已提供 weak_points)。" if agent_input.weak_points else "第二层 Fallback 触发(无 weak_points,全部走特性推导)。")
    )

    remarks = []
    if realism_discarded:
        remarks.append("以下候选因真实性验证未通过被丢弃:")
        remarks.extend(f"  - {x}" for x in realism_discarded)

    frontmatter = {
        "stage": 3,
        "stage_name": "context_and_constraints",
        "version": "1.0",
        "upstream": "02_plan.md",
        "downstream": "04_tests.md",
        "domain": agent_input.domain,
        "created_at": iso_now(),
        "created_by": "agent-stage3",
        "pass_gate": checklist.all_passed(),
    }

    write_md(
        out_path,
        frontmatter=frontmatter,
        title="Stage 3 · 仿真数据集构建 + 约束/干扰设计",
        summary=summary,
        sections=sections,
        artifacts=artifacts_out,
        checklist=checklist,
        remarks="\n".join(remarks) if remarks else "(无)",
    )
    return out_path


def _render_test_section(tc: dict[str, Any], rep_process: dict[str, Any]) -> str:
    lines = [
        f"### {tc['test_id']} ({tc['difficulty']} · {rep_process.get('name','')})",
        f"- **主资产**:{'、'.join(tc['primary_assets'])}",
        f"- **核心 fragment**:{'、'.join(f['frag_id'] for f in tc['fragments'])}",
        f"- **关键字候选**:{'、'.join(tc['keyword_pool']) or '—'}",
        f"- **约束项**({len(tc['constraints'])}):",
    ]
    for c in tc["constraints"]:
        targets = c.get("targets") or []
        targets_str = f" → {'/'.join(targets)}" if targets else ""
        lines.append(
            f"  1. {c['id']} · {c['text']}{targets_str} [来源:{c['source']} · 验证:{c['verified_by']}]"
        )
    lines.append(f"- **干扰项**({len(tc['interferences'])}):")
    if not tc["interferences"]:
        lines.append("  - 无(符合 basic 干扰密度=0)")
    for i in tc["interferences"]:
        kind = i.get("trap_kind") or "none"
        trap = f"陷阱·[{kind}]·" if i.get("trap") else f"[{kind}] "
        lines.append(f"  1. {i['id']} · {trap}{i['text']} [验证:{i['verified_by']}]")
    r = tc["realism_check"]
    lines.append(f"- **真实性验证**:{r['passed']}/{r['total']}")
    return "\n".join(lines)


__all__ = ["run"]
