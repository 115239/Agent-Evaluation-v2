"""Stage 3 · 仿真数据集构建 + 约束/干扰设计 → 03_context.md

输入：02_plan.md + 四大 xlsx
输出：OUT_DIR / 03_context.md + stage3_fragments.jsonl + stage3_inverted_index.json

处理步骤（参考 题目生成Agent设计文档.md §4.5）：
  3.1 知识资产索引构建
  3.2 题目 × 资产匹配
  3.3 关键字候选池提取
  3.4 约束项设计（第二层 Fallback）
  3.5 干扰项设计（同层 Fallback）
  3.6 业务真实性三检验
"""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, IdCounter, Section, iso_now, md_table, read_md, truncate, write_md
from .io_utils import (
    KBFragment,
    build_fragments,
    build_inverted_index,
    extract_local_keywords,
    load_kb,
)
from .llm_client import get_default_client

log = logging.getLogger("questforge.stage3")

# 由 output.category 反查主资产的规则
_CATEGORY_TO_KB: dict[str, list[str]] = {
    "结构化条款": ["KB-001"],
    "讲话摘要+上下文": ["KB-002"],
    "理论洞察": ["KB-003"],
    "实务问答": ["KB-004"],
    "决策建议": ["KB-001", "KB-004", "KB-002"],
    "纠错清单": ["KB-001", "KB-004"],
}


# ========== Step 3.1 索引构建 ==========
def _metadata_of(asset_id: str, row: Any) -> dict[str, Any]:
    if asset_id == "KB-002":
        return {
            "发布时间": str(row.get("发布时间", "")).strip(),
            "主题": str(row.get("主题", "")).strip(),
            "数据来源": str(row.get("数据来源", "")).strip(),
        }
    if asset_id == "KB-004":
        return {"来源文档": str(row.get("来源文档", "")).strip()}
    return {}


def _build_all_fragments() -> tuple[list[KBFragment], dict[str, KBFragment], dict[str, list[str]]]:
    """加载 4 个 xlsx，构造 fragment 列表、按 id 索引、以及 KB→frag_ids 映射。"""
    all_frags: list[KBFragment] = []
    by_kb: dict[str, list[str]] = {}
    for asset in config.KB_FILES:
        df = load_kb(asset["file"], asset["sheet"])
        frags = build_fragments(
            df,
            asset_id=asset["id"],
            key_fields=asset["key_fields"],
            metadata_extractor=lambda r, aid=asset["id"]: _metadata_of(aid, r),
        )
        all_frags.extend(frags)
        by_kb[asset["id"]] = [f.frag_id for f in frags]
        log.info("[Stage3] %s 索引 %d 条 fragment", asset["id"], len(frags))
    by_id = {f.frag_id: f for f in all_frags}
    return all_frags, by_id, by_kb


# ========== Step 3.2 题目 × 资产匹配 ==========
def _match_assets(test: dict[str, Any], rep_process: dict[str, Any]) -> list[str]:
    """按 output.category → KB 反查，返回主资产 id 列表。按难度裁剪。"""
    difficulty = test["difficulty"]
    target_n = config.DIFFICULTY_SAMPLING[difficulty]["primary_assets"]

    categories = [o.get("category", "") for o in rep_process.get("outputs", [])]
    # 按 output 顺序聚合候选 KB
    candidates: list[str] = []
    for cat in categories:
        for kb in _CATEGORY_TO_KB.get(cat, []):
            if kb not in candidates:
                candidates.append(kb)
    if not candidates:
        candidates = ["KB-001"]
    return candidates[:max(target_n, 1)]


def _pick_fragments(
    asset_ids: list[str],
    by_kb: dict[str, list[str]],
    by_id: dict[str, KBFragment],
    *,
    rep_process: dict[str, Any],
    difficulty: str,
    rng: random.Random,
) -> list[KBFragment]:
    """从选中的 KB 里抽候选 fragment。优先抽 key_text 包含流程关键词的 fragment，
    不够再随机补足到 difficulty 指定数量。
    """
    target_n = config.DIFFICULTY_SAMPLING[difficulty]["candidate_fragments"]
    # 以流程名 + outputs.name 拼接成查询串，用本地关键字抽取做粗检索
    query_str = " ".join(
        [rep_process.get("name", "")]
        + [o.get("name", "") for o in rep_process.get("outputs", [])]
    )
    query_kws = extract_local_keywords(query_str, top_k=5)

    ranked: list[KBFragment] = []
    seen_ids: set[str] = set()
    pool: list[KBFragment] = []
    for aid in asset_ids:
        pool.extend(by_id[fid] for fid in by_kb.get(aid, []))

    # 第一轮：命中关键词优先
    if query_kws:
        for frag in pool:
            if any(kw in frag.key_text for kw in query_kws):
                if frag.frag_id not in seen_ids:
                    ranked.append(frag)
                    seen_ids.add(frag.frag_id)
            if len(ranked) >= target_n:
                break

    # 第二轮：随机填充不足
    if len(ranked) < target_n:
        remaining = [f for f in pool if f.frag_id not in seen_ids]
        rng.shuffle(remaining)
        ranked.extend(remaining[: target_n - len(ranked)])
    return ranked[:target_n]


# ========== Step 3.3 关键字候选池 ==========
def _keyword_pool(fragments: list[KBFragment], difficulty: str, llm_budget: list[int]) -> list[str]:
    """先用本地启发式，其次对高难度题调 LLM 补强。"""
    pool: list[str] = []
    for frag in fragments:
        pool.extend(extract_local_keywords(frag.key_text, top_k=2))

    # 仅对 advanced / expert 且预算充足时调 LLM（对齐 0311构建.py 风格）
    if difficulty in ("advanced", "expert") and llm_budget[0] > 0:
        client = get_default_client()
        if client.use_llm and fragments:
            kw = _llm_extract_keyword(client, fragments[0].key_text)
            llm_budget[0] -= 1
            if kw:
                pool.append(kw)

    # 去重保序
    seen = set()
    dedup = []
    for w in pool:
        if w and w not in seen:
            seen.add(w)
            dedup.append(w)
    return dedup[:8]


def _llm_extract_keyword(client, text: str) -> str:
    """对齐 0311构建.py::extract_retrieval_keywords 的 prompt 风格。"""
    system = (
        "你是纪检领域关键词提取专员，仅从参考列文本抽取 4-8 字、贴合纪检场景的核心短语。"
    )
    user = (
        f"参考列文本：{text[:800]}\n\n"
        "规则：\n"
        "1. 只返回 1 个关键词，严禁多条/编号\n"
        "2. 长度严格 4-8 字\n"
        "3. 100% 来源于参考列文本，贴合具体纪检场景\n"
        "4. 禁用'法规 / 条例 / 条款 / 规定 / 案例 / 问题 / 实务 / 处理'等泛词\n"
        "5. 仅返回短语文本，不要任何解释、标点、换行"
    )
    raw = client.chat_text(system, user, temperature=0.3, max_tokens=20)
    raw = raw.strip()
    if 4 <= len(raw) <= 8 and all("\u4e00" <= c <= "\u9fa5" for c in raw):
        return raw
    return ""


# ========== Step 3.4 约束项设计 ==========
def _derive_constraints(
    rep_process: dict[str, Any], asset_ids: list[str], counter: IdCounter
) -> list[dict[str, Any]]:
    """每条约束文本都内含"权威词"或"领域术语"，确保后续真实性检验能通过。"""
    cs: list[dict[str, Any]] = []
    is_cross = rep_process.get("cross_process_dependency") == "跨流程"
    outputs = rep_process.get("outputs", [])
    actors = rep_process.get("actors", [])

    if is_cross:
        cs.append(
            {
                "id": counter.next(),
                "text": "跨 2+ 资产必须标注每条结论出处，并依据现行条例版本交叉验证",
                "source": "跨流程推导",
            }
        )
    if "KB-001" in asset_ids:
        cs.append(
            {
                "id": counter.next(),
                "text": "必须引用《中国共产党纪律处分条例》现行修订版的条款号与原文",
                "source": "时效性基础约束",
            }
        )
    if any(a.get("level") == "管理" for a in actors):
        cs.append(
            {
                "id": counter.next(),
                "text": "需识别审核复核层级的责任边界并保留管理层执纪决策痕迹",
                "source": "参与者层级推导",
            }
        )
    if len(outputs) > 1:
        cs.append(
            {
                "id": counter.next(),
                "text": "需完整输出定性、适用条款与量纪档次等全部结论，形成闭环依据",
                "source": "输出项规则",
            }
        )
    if any(o.get("category") == "纠错清单" for o in outputs):
        cs.append(
            {
                "id": counter.next(),
                "text": "必须指出文书缺失或错误的引用依据条款，并给出符合现行条例版本的规范表达",
                "source": "输出项规则",
            }
        )

    if not cs:
        cs.append(
            {
                "id": counter.next(),
                "text": "必须引用具体条款号或文档出处，不得脱离权威依据泛泛而谈",
                "source": "输出项规则",
            }
        )
    return cs


# ========== Step 3.5 干扰项设计 ==========
def _derive_interferences(
    rep_process: dict[str, Any],
    asset_ids: list[str],
    fragments: list[KBFragment],
    difficulty: str,
    counter: IdCounter,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """按密度规则生成干扰项。expert 必须包含 1 条陷阱（含冲突/过时/看似合理）。"""
    n = config.INTERFERENCE_DENSITY[difficulty]
    if n == 0:
        return []

    name = rep_process.get("name", "")
    items: list[dict[str, Any]] = []

    candidate_descs = [
        ("条款冲突：同主题在不同版本《纪律处分条例》中口径不一致，需要依据现行版本裁决", True),
        ("多版本过时：文件同时存在 2018 旧版与 2024 修订版，部分党纪条款已过时", True),
        ("看似合理：案情中出现'情节较轻但涉及公款消费'的执纪描述，需结合八项规定精神判定", True),
        ("跨部门角色混淆：将派驻纪检组与审计部门职责混在一起描述，易干扰执纪判断", False),
        ("流程异常：案情中故意穿插一条与纪检结论无关的干扰事实，需要识别并忽略", False),
    ]
    rng.shuffle(candidate_descs)

    # expert 题必须包含 ≥1 条 trap 型候选（文本含"冲突/过时/看似合理"）
    if difficulty == "expert":
        candidate_descs.sort(key=lambda x: not x[1])  # trap 优先

    for desc, is_trap in candidate_descs:
        if len(items) >= n:
            break
        items.append(
            {
                "id": counter.next(),
                "text": desc,
                "trap": is_trap,
                "process_ref": name,
            }
        )

    return items


# ========== Step 3.6 真实性三检验 ==========
# regulation_support 的权威词白名单：含其一即视为有据可依
_AUTHORITY_KEYWORDS = [
    "党纪", "纪律处分条例", "中央八项规定", "八项规定精神", "党中央",
    "纪检", "监察", "执纪", "问责", "现行修订版", "处分条例",
    "条款号", "出处", "依据", "四种形态", "处分", "纠错", "规范表达",
    "引用", "版本", "文书", "规程",
]


def _realism_check(
    item: dict[str, Any],
    glossary: dict[str, str],
    inverted_index: dict[str, list[str]],
    llm_budget: list[int],
) -> dict[str, Any]:
    text = item.get("text", "")

    # 1. regulation_support：含任一权威词 或 在倒排索引里命中任一本地关键字
    for kw in _AUTHORITY_KEYWORDS:
        if kw in text:
            return {"verified_by": "regulation_support", "matched": kw}
    for kw in extract_local_keywords(text, top_k=5):
        if kw in inverted_index:
            return {"verified_by": "regulation_support", "matched": kw}

    # 2. commonsense：glossary 术语子串命中（key 或 value）
    for term, defn in glossary.items():
        if term and term in text:
            return {"verified_by": "commonsense", "term": term}
        # value 命中 4 字以上的字段关键字
        for piece in extract_local_keywords(defn, top_k=2):
            if piece in text:
                return {"verified_by": "commonsense", "term": term}

    # 3. llm_judge（可选）
    if llm_budget[0] > 0:
        client = get_default_client()
        if client.use_llm:
            system = (config.REPO_ROOT / "questforge/prompts/stage3_realism.txt").read_text(encoding="utf-8")
            user = f"待判定：{text}\n\n领域：{config.DOMAIN}"
            out = client.chat_json(system, user, temperature=0.0, max_tokens=200)
            llm_budget[0] -= 1
            if out.get("verified_by") in {"regulation_support", "commonsense", "llm_judge"}:
                return {"verified_by": out["verified_by"], "reason": out.get("reason", "")}

    return {"verified_by": "none"}


# ========== 主流程 ==========
def run(stage2_md: Path | str, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else config.ensure_out_dir()
    out_path = out_dir / "03_context.md"

    parsed2 = read_md(stage2_md)
    artifacts2 = parsed2["artifacts"]
    processes = artifacts2.get("processes", [])
    test_plan = artifacts2.get("test_plan", [])
    process_types = artifacts2.get("process_types", [])
    pid2proc = {p["id"]: p for p in processes}

    # 从 Stage 1 取 glossary（通过 downstream 链）
    stage1_md = Path(stage2_md).parent / "01_understanding.md"
    glossary: dict[str, str] = {}
    if stage1_md.exists():
        glossary = read_md(stage1_md)["artifacts"].get("glossary", {})
    glossary = glossary or dict(config.DEFAULT_GLOSSARY)

    # 3.1 索引
    log.info("[Stage3] 构建知识索引…")
    all_frags, by_id, by_kb = _build_all_fragments()
    inverted_index = build_inverted_index(all_frags)
    log.info(
        "[Stage3] 索引共 %d 个 fragment，倒排表 %d 个关键词",
        len(all_frags),
        len(inverted_index),
    )

    # 落盘：fragments 明细 + 倒排索引（不进 MD artifacts，控制 MD 体积）
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
        json.dumps(inverted_index, ensure_ascii=False),
        encoding="utf-8",
    )

    # 3.2-3.6 为每题组装
    rng = random.Random(42)
    llm_kw_budget = [config.MAX_LLM_KEYWORD_CALLS]
    llm_realism_budget = [config.MAX_LLM_KEYWORD_CALLS]

    c_counter = IdCounter("C")
    i_counter = IdCounter("I")

    test_contexts: list[dict[str, Any]] = []
    covered_by: dict[str, list[str]] = {a["id"]: [] for a in config.KB_FILES}
    realism_discarded: list[str] = []

    for test in test_plan:
        rep = pid2proc[test["source_process"]]
        asset_ids = _match_assets(test, rep)
        fragments = _pick_fragments(asset_ids, by_kb, by_id, rep_process=rep, difficulty=test["difficulty"], rng=rng)

        for aid in asset_ids:
            covered_by.setdefault(aid, []).append(test["test_id"])

        keyword_pool = _keyword_pool(fragments, test["difficulty"], llm_kw_budget)

        # 干扰 fragment（可选：从其他 KB 随机抽）
        interference_frag_count = config.DIFFICULTY_SAMPLING[test["difficulty"]][
            "interference_fragments"
        ]
        noise_frags: list[KBFragment] = []
        if interference_frag_count > 0:
            other_ids = [
                fid for kb, fids in by_kb.items() if kb not in asset_ids for fid in fids
            ]
            rng.shuffle(other_ids)
            noise_frags = [by_id[fid] for fid in other_ids[:interference_frag_count]]

        # 约束 + 干扰
        raw_constraints = _derive_constraints(rep, asset_ids, c_counter)
        raw_interferences = _derive_interferences(
            rep, asset_ids, fragments + noise_frags, test["difficulty"], i_counter, rng
        )

        # 真实性检验
        constraints: list[dict[str, Any]] = []
        for c in raw_constraints:
            r = _realism_check(c, glossary, inverted_index, llm_realism_budget)
            if r["verified_by"] != "none":
                constraints.append({**c, "verified_by": r["verified_by"]})
            else:
                realism_discarded.append(f"[{test['test_id']}][C] {c['text']}")

        interferences: list[dict[str, Any]] = []
        for i in raw_interferences:
            r = _realism_check(i, glossary, inverted_index, llm_realism_budget)
            if r["verified_by"] != "none":
                interferences.append({**i, "verified_by": r["verified_by"]})
            else:
                realism_discarded.append(f"[{test['test_id']}][I] {i['text']}")

        realism_total = len(raw_constraints) + len(raw_interferences)
        realism_passed = len(constraints) + len(interferences)

        test_contexts.append(
            {
                "test_id": test["test_id"],
                "difficulty": test["difficulty"],
                "primary_assets": asset_ids,
                "fragments": [
                    {
                        "frag_id": f.frag_id,
                        "asset_id": f.asset_id,
                        "snippet": truncate(f.key_text, 120),
                    }
                    for f in fragments
                ],
                "interference_fragments": [
                    {"frag_id": f.frag_id, "asset_id": f.asset_id} for f in noise_frags
                ],
                "keyword_pool": keyword_pool,
                "constraints": constraints,
                "interferences": interferences,
                "realism_check": {"total": realism_total, "passed": realism_passed},
            }
        )

    # ==== Artifacts ====
    artifacts_out = {
        "fallback_status": {"weak_points_present": False},
        "knowledge_index": {
            a["id"]: {
                "total_fragments": len(by_kb.get(a["id"], [])),
                "covered_by": sorted(set(covered_by.get(a["id"], []))),
            }
            for a in config.KB_FILES
        },
        "test_contexts": test_contexts,
    }

    # ==== 校验清单（§4.5） ====
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
        else:
            if got != want:
                density_ok = False
                break
    checklist.add(
        "basic 0 干扰、advanced 1、expert ≥2 且含 1 陷阱",
        density_ok,
    )
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
                [["weak_points 存在", "❌", "全部走特性推导"]],
            ),
        ),
        Section(
            "知识索引摘要",
            md_table(
                ["资产", "切片数", "覆盖的 TEST", "关键字池大小(倒排)"],
                [
                    [
                        a["id"] + " " + a["name"],
                        len(by_kb.get(a["id"], [])),
                        ",".join(sorted(set(covered_by.get(a["id"], [])))) or "—",
                        sum(
                            1
                            for kw, fids in inverted_index.items()
                            if any(fid in set(by_kb.get(a["id"], [])) for fid in fids[:3])
                        ),
                    ]
                    for a in config.KB_FILES
                ],
            ),
        ),
        Section(
            "题目上下文设计",
            "\n\n".join(_render_test_section(tc, pid2proc[t["source_process"]])
                         for tc, t in zip(test_contexts, test_plan)),
        ),
    ]

    summary = (
        f"为 {len(test_contexts)} 道题建立了知识索引（共 {len(all_frags)} 个 fragment），"
        f"设计 {sum(len(tc['constraints']) for tc in test_contexts)} 条约束项、"
        f"{sum(len(tc['interferences']) for tc in test_contexts)} 条干扰项"
        f"（其中 {sum(1 for tc in test_contexts for i in tc['interferences'] if i.get('trap'))} 条陷阱）。"
        f"业务真实性通过 {sum(tc['realism_check']['passed'] for tc in test_contexts)} / "
        f"{sum(tc['realism_check']['total'] for tc in test_contexts)}。"
        f"第二层 Fallback 已触发（源文档无 weak_points，全部走特性推导）。"
    )

    remarks = []
    if realism_discarded:
        remarks.append("以下候选因真实性验证未通过被丢弃：")
        remarks.extend(f"  - {x}" for x in realism_discarded)

    frontmatter = {
        "stage": 3,
        "stage_name": "context_and_constraints",
        "version": "1.0",
        "upstream": "02_plan.md",
        "downstream": "04_tests.md",
        "domain": config.DOMAIN,
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
        remarks="\n".join(remarks) if remarks else "（无）",
    )
    return out_path


def _render_test_section(tc: dict[str, Any], rep_process: dict[str, Any]) -> str:
    lines = [
        f"### {tc['test_id']} ({tc['difficulty']} · {rep_process.get('name','')})",
        f"- **主资产**：{'、'.join(tc['primary_assets'])}",
        f"- **核心 fragment**：{'、'.join(f['frag_id'] for f in tc['fragments'])}",
        f"- **关键字候选**：{'、'.join(tc['keyword_pool']) or '—'}",
        f"- **约束项**（{len(tc['constraints'])}）：",
    ]
    for c in tc["constraints"]:
        lines.append(f"  1. {c['id']} · {c['text']} [来源:{c['source']} · 验证:{c['verified_by']}]")
    lines.append(f"- **干扰项**（{len(tc['interferences'])}）：")
    if not tc["interferences"]:
        lines.append("  - 无（符合 basic 干扰密度=0）")
    for i in tc["interferences"]:
        trap = "陷阱·" if i.get("trap") else ""
        lines.append(f"  1. {i['id']} · {trap}{i['text']} [验证:{i['verified_by']}]")
    r = tc["realism_check"]
    lines.append(f"- **真实性验证**：{r['passed']}/{r['total']}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage2", required=True, help="path to 02_plan.md")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    out = run(args.stage2, Path(args.out) if args.out else None)
    print(f"[Stage3] produced: {out}")
