"""Stage 1 · 业务理解 → 01_understanding.md

输入：config.KB_FILES + 样例数据 + ONE_LINER_GOAL
输出：OUT_DIR / 01_understanding.md

不做流程提取，只做：业务目标识别 + 用户画像抽取 + 核心功能枚举 +
业务数据资产登记 + 领域术语表沉淀。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, IdCounter, Section, iso_now, md_table, truncate, write_md
from .io_utils import load_sample_usecases, summarize_kb
from .llm_client import get_default_client

log = logging.getLogger("questforge.stage1")


# ========== 本地兜底：当 LLM 不可用时的默认"业务理解" ==========
def _fallback_business_goal() -> dict[str, str]:
    return {
        "one_liner": config.ONE_LINER_GOAL,
        "success_metric": "知识库检索召回率 ≥ 85%，文书纠错准确率 ≥ 90%",
        "business_value": "替代大部分人工条款查阅工作，缩短纪检材料审查时间",
    }


def _fallback_user_groups(samples: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """从样例数据兜底出两个用户画像。"""
    ret_samples = samples.get("语义检索", []) + samples.get("定性量纪", [])
    correct_samples = samples.get("文书纠错", [])

    groups = []
    if ret_samples:
        groups.append(
            {
                "id": "UG-001",
                "role": "纪检监察员",
                "responsibility": "审查违纪案件、查询党纪法规与讲话/理论依据",
                "typical_query": truncate(ret_samples[0].get("样例内容", ""), 80)
                or "这种情形适用哪条纪律处分条例?",
            }
        )
    else:
        groups.append(
            {
                "id": "UG-001",
                "role": "纪检监察员",
                "responsibility": "审查违纪案件、查询党纪法规",
                "typical_query": "这种情形适用哪条纪律处分条例?",
            }
        )

    if correct_samples:
        groups.append(
            {
                "id": "UG-002",
                "role": "纪检文书审核人员",
                "responsibility": "审核纪检文书表达与依据引用是否规范",
                "typical_query": truncate(correct_samples[0].get("测试样例", ""), 80)
                or "这份文书有哪些表述或依据问题需要纠正？",
            }
        )
    else:
        groups.append(
            {
                "id": "UG-002",
                "role": "纪检部门负责人",
                "responsibility": "定性量纪决策、审核文书",
                "typical_query": "类似案件历史上是怎么量纪的?",
            }
        )
    return groups


def _fallback_features() -> list[dict[str, Any]]:
    """6 个功能：对齐"知识库检索四大类 + 定性量纪 + 文书纠错"。"""
    return [
        {
            "id": "FEAT-001",
            "name": "党纪法规语义检索",
            "input": "违纪情形的自然语言描述",
            "output": "匹配条款号+要点词+违纪行为原文",
            "depends_on": ["KB-001"],
            "inferred": True,
        },
        {
            "id": "FEAT-002",
            "name": "总书记讲话主题定位",
            "input": "主题关键词或自然语言问题",
            "output": "相关讲话标题+摘要+时间+出处",
            "depends_on": ["KB-002"],
            "inferred": True,
        },
        {
            "id": "FEAT-003",
            "name": "理论文章检索",
            "input": "理论主题或关键词",
            "output": "相关理论文章标题+摘要",
            "depends_on": ["KB-003"],
            "inferred": True,
        },
        {
            "id": "FEAT-004",
            "name": "实务案例检索",
            "input": "违纪情形描述或实务问题",
            "output": "类似实务问答+来源文档+来源片段",
            "depends_on": ["KB-004"],
            "inferred": True,
        },
        {
            "id": "FEAT-005",
            "name": "定性量纪建议",
            "input": "案情描述",
            "output": "适用条款+量纪档次+类案参考",
            "depends_on": ["KB-001", "KB-004"],
            "inferred": True,
        },
        {
            "id": "FEAT-006",
            "name": "纪检文书纠错",
            "input": "待审核的纪检文书片段",
            "output": "纠错建议+依据条款+对应规范表达",
            "depends_on": ["KB-001", "KB-004"],
            "inferred": True,
        },
    ]


def _fallback_glossary() -> dict[str, str]:
    return dict(config.DEFAULT_GLOSSARY)


# ========== LLM 抽取 ==========
_JSON_SCHEMA_HINT = """
请按以下 JSON Schema 输出:
{
  "business_goal": {"one_liner":"string","success_metric":"string","business_value":"string"},
  "user_groups": [{"id":"UG-xxx","role":"string","responsibility":"string","typical_query":"string"}],
  "features":    [{"id":"FEAT-xxx","name":"string","input":"string","output":"string","depends_on":["KB-xxx"]}],
  "glossary":    {"term":"definition"}
}
"""


def _llm_extract(
    one_liner: str,
    kb_cards: list[dict[str, Any]],
    sample_usecases: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """LLM 推导 business_goal / user_groups / features / glossary。"""
    client = get_default_client()
    if not client.use_llm:
        return {}

    system = (config.REPO_ROOT / "questforge/prompts/stage1_business.txt").read_text(encoding="utf-8")

    # 资产卡片摘要（精简避免 prompt 爆炸）
    kb_brief = [
        {
            "id": c["id"],
            "name": c["name"],
            "rows": c["rows"],
            "key_fields": c["key_fields"],
            "authority": c["authority"],
            "category": c["category"],
            "columns": c["columns"],
        }
        for c in kb_cards
    ]

    # 样例诉求池（每类各取前 10 条原文）
    sample_brief = {k: [x.get("样例内容") or x.get("测试样例", "") for x in v[:10]] for k, v in sample_usecases.items()}

    user = (
        f"<business_goal_hint>{one_liner}</business_goal_hint>\n"
        f"<knowledge_assets>{json.dumps(kb_brief, ensure_ascii=False)}</knowledge_assets>\n"
        f"<sample_queries>{json.dumps(sample_brief, ensure_ascii=False)}</sample_queries>\n"
        f"<domain>{config.DOMAIN}</domain>\n"
        f"{_JSON_SCHEMA_HINT}"
    )
    result = client.chat_json(system, user)
    return result


# ========== 主流程 ==========
def run(out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else config.ensure_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "01_understanding.md"

    # 1. 业务数据资产登记（代码确定性产出）
    log.info("[Stage1] 登记 %d 个知识库资产", len(config.KB_FILES))
    kb_cards = [summarize_kb(a) for a in config.KB_FILES]

    # 2. 样例数据加载（驱动 typical_query）
    sample_usecases = load_sample_usecases()
    log.info("[Stage1] 样例数据类别：%s", {k: len(v) for k, v in sample_usecases.items()})

    # 3. LLM 抽取其余字段（失败自动 fallback）
    llm_out = _llm_extract(config.ONE_LINER_GOAL, kb_cards, sample_usecases)

    remarks_lines: list[str] = []

    business_goal = llm_out.get("business_goal") or _fallback_business_goal()
    if not llm_out.get("business_goal"):
        remarks_lines.append("business_goal 走本地兜底（LLM 未启用或解析失败）")

    user_groups = llm_out.get("user_groups") or _fallback_user_groups(sample_usecases)
    if not llm_out.get("user_groups"):
        remarks_lines.append("user_groups 走本地兜底，typical_query 从样例数据取")

    features = llm_out.get("features") or _fallback_features()
    if not llm_out.get("features"):
        remarks_lines.append("features 走本地兜底（6 项：知识库检索四大类 + 定性量纪 + 文书纠错）")

    glossary = llm_out.get("glossary") or _fallback_glossary()
    if not llm_out.get("glossary"):
        remarks_lines.append("glossary 使用预置术语表")

    # 4. 统一补 ID / inferred 标记
    user_groups = _normalize_user_groups(user_groups)
    features = _normalize_features(features, kb_ids={c["id"] for c in kb_cards})

    # 5. 组装 artifacts
    knowledge_assets = [
        {
            "id": c["id"],
            "file": c["file"],
            "sheet": c["sheet"],
            "rows": c["rows"],
            "key_fields": c["key_fields"],
            "authority": c["authority"],
            "category": c["category"],
        }
        for c in kb_cards
    ]

    artifacts = {
        "business_goal": business_goal,
        "user_groups": user_groups,
        "features": features,
        "knowledge_assets": knowledge_assets,
        "glossary": glossary,
    }

    # 6. 校验清单
    checklist = Checklist()
    one_liner_len = len(business_goal.get("one_liner", ""))
    checklist.add(
        f"业务目标 one_liner 字数 20-100（实际 {one_liner_len}）",
        20 <= one_liner_len <= 100,
    )
    checklist.add(
        f"至少识别 1 个用户画像，每个有 typical_query 原文示例（实际 {len(user_groups)}）",
        bool(user_groups) and all(u.get("typical_query") for u in user_groups),
    )
    checklist.add(
        f"至少识别 1 个核心功能，每个标注 input/output/depends_on（实际 {len(features)}）",
        bool(features)
        and all(f.get("input") and f.get("output") and f.get("depends_on") for f in features),
    )
    checklist.add(
        "每个核心功能关联 ≥ 1 个 knowledge_asset",
        all(f.get("depends_on") for f in features),
    )
    checklist.add(
        f"领域术语表 ≥ 5 条（实际 {len(glossary)}）",
        len(glossary) >= 5,
    )

    # 7. 渲染 MD
    summary = (
        f"基于 {config.DOMAIN} 的业务目标与样例数据，识别出 "
        f"{len(user_groups)} 类核心用户、{len(features)} 项核心功能、"
        f"{len(knowledge_assets)} 类业务数据资产。"
        f"业务目标聚焦知识库检索（四大类）与文书纠错两大能力。"
        f"领域术语表已沉淀 {len(glossary)} 条。"
    )

    sections = [
        Section(
            "业务目标",
            md_table(
                ["字段", "值"],
                [[k, business_goal.get(k, "")] for k in ("one_liner", "success_metric", "business_value")],
            ),
        ),
        Section(
            "用户画像",
            md_table(
                ["ID", "角色", "职责", "典型诉求（原文示例）"],
                [[u["id"], u["role"], u["responsibility"], truncate(u["typical_query"], 60)] for u in user_groups],
            ),
        ),
        Section(
            "核心功能清单",
            md_table(
                ["ID", "功能名", "输入", "输出", "依赖资产"],
                [
                    [f["id"], f["name"], f["input"], f["output"], ",".join(f["depends_on"])]
                    for f in features
                ],
            ),
        ),
        Section(
            "业务数据资产",
            md_table(
                ["资产 ID", "文件", "行数", "关键字段", "权威性", "类别"],
                [
                    [a["id"], a["file"], a["rows"], ",".join(a["key_fields"]), a["authority"], a["category"]]
                    for a in knowledge_assets
                ],
            ),
        ),
        Section(
            "领域术语表(节选)",
            "\n".join(f"- **{k}**：{v}" for k, v in glossary.items()),
        ),
    ]

    frontmatter = {
        "stage": 1,
        "stage_name": "business_understanding",
        "version": "1.0",
        "upstream": "源文档",
        "downstream": "02_plan.md",
        "domain": config.DOMAIN,
        "created_at": iso_now(),
        "created_by": "agent-stage1",
        "pass_gate": checklist.all_passed(),
    }

    write_md(
        out_path,
        frontmatter=frontmatter,
        title="Stage 1 · 业务理解",
        summary=summary,
        sections=sections,
        artifacts=artifacts,
        checklist=checklist,
        remarks="\n".join(f"- {r}" for r in remarks_lines) if remarks_lines else "（无）",
    )
    return out_path


# ========== 辅助：ID 归一化 ==========
def _normalize_user_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = IdCounter("UG")
    normalized = []
    for g in groups:
        normalized.append(
            {
                "id": g.get("id") or counter.next(),
                "role": g.get("role", "未命名角色"),
                "responsibility": g.get("responsibility", ""),
                "typical_query": g.get("typical_query", ""),
            }
        )
    # 若原 id 为空或重复，强制顺序重排
    used = set()
    for g in normalized:
        if g["id"] in used or not g["id"].startswith("UG-"):
            g["id"] = counter.next()
        used.add(g["id"])
    return normalized


def _normalize_features(features: list[dict[str, Any]], kb_ids: set[str]) -> list[dict[str, Any]]:
    counter = IdCounter("FEAT")
    used = set()
    normalized = []
    for f in features:
        dep = [x for x in f.get("depends_on", []) if x in kb_ids]
        fid = f.get("id")
        if not fid or not fid.startswith("FEAT-") or fid in used:
            fid = counter.next()
        used.add(fid)
        normalized.append(
            {
                "id": fid,
                "name": f.get("name", "未命名功能"),
                "input": f.get("input", ""),
                "output": f.get("output", ""),
                "depends_on": dep or sorted(kb_ids)[:1],  # 至少关联 1 个
                "inferred": bool(f.get("inferred", True)),
            }
        )
    return normalized


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    out = run(Path(args.out) if args.out else None)
    print(f"[Stage1] produced: {out}")
