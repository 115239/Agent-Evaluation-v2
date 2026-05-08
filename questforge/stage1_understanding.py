"""Stage 1 · 业务理解 → 01_understanding.md

输入:AgentInput(Phase 0 已通过验证)
输出:OUT_DIR / 01_understanding.md

通过 MissingInputError 请求用户补充。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from . import config
from .common import Checklist, IdCounter, Section, iso_now, md_table, read_md, truncate, write_md
from .input_spec import AgentInput, MissingField, MissingInputError, SampleFileConfig
from .io_utils import (
    SUPPORTED_EXTS,
    UnsupportedFormatError,
    load_kb,
    load_sample_usecases,
    summarize_kb,
)
from .llm_client import LLMClient, get_default_client

log = logging.getLogger("questforge.stage1")


# ========== 资产扫描 & 识别 ==========
_ASSET_EXTS = set(SUPPORTED_EXTS)


def _probe_best_sheet(path: Path) -> str:
    try:
        import openpyxl  # type: ignore

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        best_sheet = None
        best_rows = -1
        for s in wb.sheetnames:
            ws = wb[s]
            if ws.max_row > best_rows:
                best_rows = ws.max_row
                best_sheet = s
        wb.close()
        return best_sheet or "Sheet1"
    except Exception as e:
        log.warning("探测 sheet 失败(%s):%s;默认使用 Sheet1", path.name, e)
        return "Sheet1"


def _probe_asset(path: Path) -> dict[str, Any]:
    """读取资产文件头,输出不带 LLM 推断字段的原始描述。"""
    info: dict[str, Any] = {
        "name": path.stem,
        "file": path,
        "file_display": path.name,
        "suffix": path.suffix.lower(),
        "sheet": "",
        "rows": 0,
        "columns": [],
        "sample_rows": [],
        "load_error": "",
    }
    ext = path.suffix.lower()
    if ext in {".xlsx", ".xls", ".xlsm"}:
        sheet = _probe_best_sheet(path)
    else:
        sheet = "main"

    try:
        df = load_kb(path, sheet)
    except UnsupportedFormatError as e:
        info["sheet"] = sheet
        info["load_error"] = str(e)
        return info
    except Exception as e:
        log.warning("加载资产失败 %s:%s", path.name, e)
        info["sheet"] = sheet
        info["load_error"] = f"加载失败: {e}"
        return info

    sample_rows = df.head(3).to_dict(orient="records")
    for row in sample_rows:
        for k, v in list(row.items()):
            if isinstance(v, str) and len(v) > 150:
                row[k] = v[:150] + "…"
    info.update(
        sheet=sheet,
        rows=int(len(df)),
        columns=list(df.columns),
        sample_rows=sample_rows,
    )
    return info


def _scan_data_dir(data_dir: Path) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for p in sorted(data_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in _ASSET_EXTS:
            assets.append(_probe_asset(p))
    return assets


# ========== LLM 调用封装 ==========
_JSON_SCHEMA_HINT_MAIN = """
请严格按以下 JSON Schema 输出(仅一个 JSON 对象,不含 markdown 围栏):
{
  "business_goal": {"success_metric": "string", "business_value": "string"},
  "user_groups": [{
    "id": "UG-xxx",
    "role": "string",
    "responsibility": "string",
    "typical_query": "string",
    "language_profile": {"formality": "formal|casual|mixed", "vocabulary": "simple|technical|mixed"},
    "knowledge_domain": {"expert_areas": ["string"], "novice_areas": ["string"], "misconceptions": ["string"]},
    "behavioral_pattern": {"interaction_style": "direct|exploratory|methodical", "info_need": "minimal|moderate|comprehensive"},
    "emotional_baseline": {"stress_level": "low|medium|high", "frustration_triggers": ["string"]},
    "goal_motivation": {"primary_goal": "solve|learn|validate|explore", "time_pressure": "urgent|moderate|none"}
  }],
  "features":    [{"id": "FEAT-xxx", "name": "string", "input": "string", "output": "string", "depends_on": ["KB-xxx"]}],
  "glossary":    {"term": "definition"}
}
注意:
- business_goal.one_liner 已由用户提供,不必再输出;只输出 success_metric 与 business_value
- depends_on 只能引用输入中给出的 KB ID
- 若 samples 里有真实用户原话,user_groups.typical_query 必须引用原文
- user_groups 的 5 个 persona 子字段(language_profile/knowledge_domain/behavioral_pattern/emotional_baseline/goal_motivation)均为枚举值,
  无明确证据时用 "NOT_SPECIFIED"(对枚举字段)或空数组(对列表字段)
- emotional_baseline.frustration_triggers 与 knowledge_domain.misconceptions 是后续阶段干扰生成与 prompt 风格化的种子,尽量给出 1-3 条具体描述
"""


def _asset_classify_prompt(asset: dict[str, Any], domain: str) -> str:
    brief = {
        "file": asset["file_display"],
        "sheet": asset["sheet"],
        "rows": asset["rows"],
        "columns": asset["columns"],
        "sample_rows": asset["sample_rows"],
    }
    return (
        f"<domain>{domain}</domain>\n"
        f"<asset>{json.dumps(brief, ensure_ascii=False)}</asset>\n\n"
        "请为该资产推断以下三个字段,输出 JSON:\n"
        "{\n"
        '  "key_fields": ["<2-4 个最能代表该资产业务信息的列名,必须来自 columns>"],\n'
        '  "authority": "官方 | 权威刊物 | 历史案例 | 社区内容 | 其他",\n'
        '  "category": "<一句 4-10 字的资产类别,例:结构化条款/讲话摘要+上下文/实务问答>"\n'
        "}\n"
        "仅输出 JSON。"
    )


def _llm_classify_asset(client: LLMClient, asset: dict[str, Any], domain: str) -> dict[str, Any]:
    system_path = config.REPO_ROOT / "questforge/prompts/stage1_asset_classify.txt"
    system = system_path.read_text(encoding="utf-8") if system_path.exists() else (
        "你是数据资产分类员,负责基于资产的列头与样例行推断其 key_fields / authority / category。"
    )
    raw = client.chat_json(system, _asset_classify_prompt(asset, domain), max_tokens=400)
    if not isinstance(raw, dict):
        return {}
    kf = raw.get("key_fields") or []
    columns = set(asset["columns"])
    kf = [k for k in kf if k in columns]
    if not kf:
        return {}
    return {
        "key_fields": kf[:4],
        "authority": (raw.get("authority") or "").strip() or "未知",
        "category": (raw.get("category") or "").strip() or "未分类",
    }


def _llm_extract(
    client: LLMClient,
    agent_input: AgentInput,
    kb_cards: list[dict[str, Any]],
    sample_usecases: dict[str, list[dict[str, Any]]],
    docs_excerpt: str = "",
) -> dict[str, Any]:
    system_path = config.REPO_ROOT / "questforge/prompts/stage1_business.txt"
    system = system_path.read_text(encoding="utf-8")

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
    sample_brief = {
        label: [
            next((v for k, v in item.items() if isinstance(v, str) and v.strip()), "")
            for item in items[:10]
        ]
        for label, items in sample_usecases.items()
    }

    prd_block = docs_excerpt.strip() or "(未提供 docs_dir,无 PRD 节选)"

    user = (
        f"<domain>{agent_input.domain}</domain>\n"
        f"<business_goal>{agent_input.business_goal}</business_goal>\n"
        f"<weak_points>{json.dumps(agent_input.weak_points, ensure_ascii=False)}</weak_points>\n"
        f"<prd_excerpt>\n{prd_block}\n</prd_excerpt>\n"
        f"<knowledge_assets>{json.dumps(kb_brief, ensure_ascii=False)}</knowledge_assets>\n"
        f"<sample_queries>{json.dumps(sample_brief, ensure_ascii=False)}</sample_queries>\n"
        f"<glossary_seed>{json.dumps(agent_input.glossary_seed, ensure_ascii=False)}</glossary_seed>\n"
        f"{_JSON_SCHEMA_HINT_MAIN}"
    )
    return client.chat_json(system, user)


# ========== 归一化 ==========
_PERSONA_ENUMS: dict[str, set[str]] = {
    "language_profile.formality": {"formal", "casual", "mixed"},
    "language_profile.vocabulary": {"simple", "technical", "mixed"},
    "behavioral_pattern.interaction_style": {"direct", "exploratory", "methodical"},
    "behavioral_pattern.info_need": {"minimal", "moderate", "comprehensive"},
    "emotional_baseline.stress_level": {"low", "medium", "high"},
    "goal_motivation.primary_goal": {"solve", "learn", "validate", "explore"},
    "goal_motivation.time_pressure": {"urgent", "moderate", "none"},
}


def _enum_or_unspecified(value: Any, allowed: set[str]) -> str:
    s = (str(value or "")).strip().lower()
    return s if s in allowed else "NOT_SPECIFIED"


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(x).strip() for x in value if str(x).strip()]


def _normalize_persona(raw: dict[str, Any]) -> dict[str, Any]:
    """把 user_group 的 5 个 persona 子字段归一化到稳定枚举/列表。"""
    lp = raw.get("language_profile") or {}
    kd = raw.get("knowledge_domain") or {}
    bp = raw.get("behavioral_pattern") or {}
    eb = raw.get("emotional_baseline") or {}
    gm = raw.get("goal_motivation") or {}
    return {
        "language_profile": {
            "formality": _enum_or_unspecified(lp.get("formality"), _PERSONA_ENUMS["language_profile.formality"]),
            "vocabulary": _enum_or_unspecified(lp.get("vocabulary"), _PERSONA_ENUMS["language_profile.vocabulary"]),
        },
        "knowledge_domain": {
            "expert_areas": _str_list(kd.get("expert_areas")),
            "novice_areas": _str_list(kd.get("novice_areas")),
            "misconceptions": _str_list(kd.get("misconceptions")),
        },
        "behavioral_pattern": {
            "interaction_style": _enum_or_unspecified(
                bp.get("interaction_style"), _PERSONA_ENUMS["behavioral_pattern.interaction_style"]
            ),
            "info_need": _enum_or_unspecified(
                bp.get("info_need"), _PERSONA_ENUMS["behavioral_pattern.info_need"]
            ),
        },
        "emotional_baseline": {
            "stress_level": _enum_or_unspecified(
                eb.get("stress_level"), _PERSONA_ENUMS["emotional_baseline.stress_level"]
            ),
            "frustration_triggers": _str_list(eb.get("frustration_triggers")),
        },
        "goal_motivation": {
            "primary_goal": _enum_or_unspecified(
                gm.get("primary_goal"), _PERSONA_ENUMS["goal_motivation.primary_goal"]
            ),
            "time_pressure": _enum_or_unspecified(
                gm.get("time_pressure"), _PERSONA_ENUMS["goal_motivation.time_pressure"]
            ),
        },
    }


def _normalize_user_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = IdCounter("UG")
    normalized: list[dict[str, Any]] = []
    for g in groups:
        normalized.append(
            {
                "id": g.get("id") or counter.next(),
                "role": (g.get("role") or "").strip() or "未命名角色",
                "responsibility": (g.get("responsibility") or "").strip(),
                "typical_query": (g.get("typical_query") or "").strip(),
                "persona": _normalize_persona(g),
            }
        )
    used: set[str] = set()
    for g in normalized:
        if g["id"] in used or not g["id"].startswith("UG-"):
            g["id"] = counter.next()
        used.add(g["id"])
    return normalized


def _normalize_features(features: list[dict[str, Any]], kb_ids: set[str]) -> list[dict[str, Any]]:
    counter = IdCounter("FEAT")
    used: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for f in features:
        dep = [x for x in (f.get("depends_on") or []) if x in kb_ids]
        fid = f.get("id")
        if not fid or not fid.startswith("FEAT-") or fid in used:
            fid = counter.next()
        used.add(fid)
        normalized.append(
            {
                "id": fid,
                "name": (f.get("name") or "").strip() or "未命名功能",
                "input": (f.get("input") or "").strip(),
                "output": (f.get("output") or "").strip(),
                "depends_on": dep,
                "inferred": bool(f.get("inferred", True)),
            }
        )
    return normalized


# ========== 主流程 ==========
def _render_personas(user_groups: list[dict[str, Any]]) -> str:
    if not user_groups:
        return "(无 user_groups)"
    rows = []
    for u in user_groups:
        p = u.get("persona") or {}
        lp = p.get("language_profile") or {}
        bp = p.get("behavioral_pattern") or {}
        eb = p.get("emotional_baseline") or {}
        gm = p.get("goal_motivation") or {}
        kd = p.get("knowledge_domain") or {}
        rows.append(
            [
                u["id"],
                f"{lp.get('formality','-')}/{lp.get('vocabulary','-')}",
                f"{bp.get('interaction_style','-')}/{bp.get('info_need','-')}",
                f"{eb.get('stress_level','-')}",
                "、".join((eb.get("frustration_triggers") or [])[:3]) or "—",
                f"{gm.get('primary_goal','-')}/{gm.get('time_pressure','-')}",
                "、".join((kd.get("misconceptions") or [])[:2]) or "—",
            ]
        )
    return md_table(
        ["ID", "语言风格", "行为", "压力", "情绪触发(摘录)", "目标/紧迫", "常见误解(摘录)"],
        rows,
    )


def run(agent_input: AgentInput, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "01_understanding.md"

    # --- 1. LLM 必须可用 ---
    client = get_default_client()
    if not client.use_llm:
        raise MissingInputError(
            stage="Stage 1 · 业务理解",
            report=[
                MissingField(
                    field_name="LLM_API_KEY",
                    why_needed=(
                        "Stage 1 的用户画像、核心功能、资产分类、术语抽取均需 LLM;"
                        "本 Pipeline 不提供领域默认值。"
                    ),
                    suggested_format="在 repo 根目录 `.env` 中设置环境变量",
                    example="LLM_API_KEY=<YOUR_API_KEY>\nLLM_BASE_URL=https://...\nLLM_MODEL=qwen-plus",
                )
            ],
            hint="检测到 LLM 客户端不可用。请配置 API key 后重跑。",
        )

    # --- 2. 扫描资产 ---
    assets_raw = _scan_data_dir(Path(agent_input.data_dir))
    if not assets_raw:
        raise MissingInputError(
            stage="Stage 1 · 业务理解",
            report=[
                MissingField(
                    field_name="data_dir",
                    why_needed="Stage 1 资产登记需要至少 1 个可读文件",
                    suggested_format=f"目录内放置扩展名 ∈ {sorted(_ASSET_EXTS)} 的文件",
                    example=f"data_dir = {agent_input.data_dir}(当前为空或无匹配扩展名)",
                )
            ],
        )

    # 2.1 过滤加载失败的资产(load_error 非空意味着扩展名不支持/编码错误/依赖缺失)
    load_failures = [a for a in assets_raw if a.get("load_error")]
    if load_failures:
        raise MissingInputError(
            stage="Stage 1 · 业务理解",
            report=[
                MissingField(
                    field_name=f"data_dir/{a['file_display']}",
                    why_needed=f"资产解析失败:{a['load_error']}",
                    suggested_format=(
                        "确认扩展名 ∈ "
                        f"{sorted(_ASSET_EXTS)};必要时安装可选依赖(python-docx / pypdf)"
                        " 或将老 .doc 另存为 .docx"
                    ),
                    example=f"加载失败:{a['file_display']}",
                )
                for a in load_failures
            ],
            hint=f"共 {len(load_failures)} 个资产加载失败。",
        )

    # 2.2 排除 rows=0 的空资产(LLM 也无法基于空列头分类)
    empty_assets = [a for a in assets_raw if a["rows"] == 0]
    if empty_assets:
        raise MissingInputError(
            stage="Stage 1 · 业务理解",
            report=[
                MissingField(
                    field_name=f"data_dir/{a['file_display']}",
                    why_needed="资产读取后 0 行,无法用于建索引(可能正文为空、PDF 为扫描版、或 docx 全为短碎片)",
                    suggested_format="确认文件含有实际内容;扫描版 PDF 需 OCR 处理后转文本",
                    example=f"空资产:{a['file_display']}",
                )
                for a in empty_assets
            ],
            hint=f"共 {len(empty_assets)} 个资产 rows=0。",
        )

    # --- 3. LLM 分类每个资产 ---
    kb_cards: list[dict[str, Any]] = []
    failed_assets: list[str] = []
    id_counter = IdCounter("KB")
    for asset in assets_raw:
        classify = _llm_classify_asset(client, asset, agent_input.domain)
        if not classify:
            failed_assets.append(asset["file_display"])
            continue
        kb_cards.append(
            {
                "id": id_counter.next(),
                "name": asset["name"],
                "file": asset["file_display"],
                "sheet": asset["sheet"],
                "rows": asset["rows"],
                "key_fields": classify["key_fields"],
                "authority": classify["authority"],
                "category": classify["category"],
                "columns": asset["columns"],
                "sample_rows": asset["sample_rows"],
                "_path": str(asset["file"]),
            }
        )

    if failed_assets:
        raise MissingInputError(
            stage="Stage 1 · 业务理解",
            report=[
                MissingField(
                    field_name=f"data_dir/{fn}",
                    why_needed=(
                        "LLM 未能推断该资产的 key_fields/authority/category(可能因列头含噪或 LLM 返回格式问题)"
                    ),
                    suggested_format=(
                        "两种选择:(a)重命名/清理列头后重跑;"
                        "(b)在 example_input.json 增加 asset_overrides 明确指定"
                    ),
                    example=(
                        '"asset_overrides": [{"file": "'
                        + fn
                        + '", "key_fields": ["列A","列B"], "authority": "官方", "category": "结构化条款"}]'
                    ),
                )
                for fn in failed_assets
            ],
            hint=f"共 {len(failed_assets)} 个资产未能自动分类。",
        )

    # --- 4. 加载样例数据 ---
    sample_usecases: dict[str, list[dict[str, Any]]] = load_sample_usecases(agent_input.samples)
    log.info("[Stage1] 样例数据:%s", {k: len(v) for k, v in sample_usecases.items()})

    # --- 5. LLM 抽取 user_groups / features / glossary ---
    docs_excerpt = ""
    phase0_path = Path(out_dir) / "00_input_assessment.md"
    if phase0_path.exists():
        try:
            phase0_doc = read_md(phase0_path)
            docs_excerpt = str(phase0_doc["artifacts"].get("docs_text_excerpt") or "")
        except Exception as e:
            log.warning("读取 00_input_assessment.md 的 docs_text_excerpt 失败:%s", e)
    llm_out = _llm_extract(client, agent_input, kb_cards, sample_usecases, docs_excerpt=docs_excerpt)
    if not isinstance(llm_out, dict) or not llm_out:
        raise MissingInputError(
            stage="Stage 1 · 业务理解",
            report=[
                MissingField(
                    field_name="LLM 响应",
                    why_needed="LLM 未返回可解析的 JSON,无法继续推断用户/功能/术语",
                    suggested_format="确认 LLM_MODEL 支持 JSON 输出;或提供备用模型",
                    example="LLM_MODEL=qwen-plus / gpt-4o-mini / deepseek-chat",
                )
            ],
        )

    user_groups_raw = llm_out.get("user_groups") or []
    features_raw = llm_out.get("features") or []
    glossary_llm: dict[str, str] = llm_out.get("glossary") or {}

    # business_goal 一句话来自用户,success_metric / business_value 来自 LLM(可空)
    goal_extra = llm_out.get("business_goal") or {}
    business_goal = {
        "one_liner": agent_input.business_goal,
        "success_metric": (goal_extra.get("success_metric") or "").strip() or "NOT_SPECIFIED",
        "business_value": (goal_extra.get("business_value") or "").strip() or "NOT_SPECIFIED",
    }

    # --- 6. 校验 & 归一化 ---
    missing: list[MissingField] = []
    if not user_groups_raw:
        missing.append(
            MissingField(
                field_name="user_groups",
                why_needed="下一阶段以'用户角色 × 核心功能'推导业务流程,缺用户画像无法推导",
                suggested_format="在 example_input.json 添加 user_groups 覆盖,或补充更详细的 PRD/samples",
                example='"user_groups": [{"role": "客服主管", "responsibility": "...", "typical_query": "..."}]',
            )
        )
    if not features_raw:
        missing.append(
            MissingField(
                field_name="features",
                why_needed="核心功能是流程推导的另一个乘数,缺失则 Stage 2 无法进行",
                suggested_format="确认 Architecture/架构设计类文档已放入 docs_dir;或手工在 example_input.json 提供 features",
                example='"features": [{"name": "对话质检", "input": "对话文本", "output": "质检评分"}]',
            )
        )
    glossary = {**agent_input.glossary_seed, **(glossary_llm or {})}
    if len(glossary) < 5:
        missing.append(
            MissingField(
                field_name="glossary_seed",
                why_needed="Stage 3 的真实性三检验依赖 ≥5 条领域术语表;LLM 抽取数量不足",
                suggested_format="在 example_input.json 的 glossary_seed 至少补到 5 条",
                example='"glossary_seed": {"术语A": "定义", "术语B": "定义", ...}',
            )
        )
    if missing:
        raise MissingInputError(stage="Stage 1 · 业务理解", report=missing)

    user_groups = _normalize_user_groups(user_groups_raw)
    features = _normalize_features(features_raw, kb_ids={c["id"] for c in kb_cards})

    # --- 7. 组装 artifacts ---
    knowledge_assets = [
        {
            "id": c["id"],
            "file": c["file"],
            "path": c["_path"],
            "sheet": c["sheet"],
            "rows": c["rows"],
            "key_fields": c["key_fields"],
            "authority": c["authority"],
            "category": c["category"],
            "columns": list(c.get("columns") or [])[:30],
            "sample_rows": [
                {k: truncate(str(v), 80) for k, v in (row or {}).items()}
                for row in (c.get("sample_rows") or [])[:3]
            ],
        }
        for c in kb_cards
    ]

    # 截断到 ~4KB,供 Stage 2/3 复用原始文档摘要而无需重读 docs_dir
    docs_digest = truncate(docs_excerpt, 4000) if docs_excerpt else ""

    artifacts = {
        "business_goal": business_goal,
        "user_groups": user_groups,
        "features": features,
        "knowledge_assets": knowledge_assets,
        "glossary": glossary,
        "docs_digest": docs_digest,
    }

    # --- 8. 校验清单 ---
    checklist = Checklist()
    one_liner_len = len(business_goal["one_liner"])
    checklist.add(
        f"业务目标 one_liner 字数 20-100(实际 {one_liner_len})",
        20 <= one_liner_len <= 100,
    )
    checklist.add(
        f"至少识别 1 个用户画像,每个有 typical_query(实际 {len(user_groups)})",
        bool(user_groups) and all(u["typical_query"] for u in user_groups),
    )
    checklist.add(
        f"至少识别 1 个核心功能,每个标注 input/output/depends_on(实际 {len(features)})",
        bool(features)
        and all(f["input"] and f["output"] and f["depends_on"] for f in features),
    )
    checklist.add(
        "每个核心功能关联 ≥ 1 个 knowledge_asset",
        all(f["depends_on"] for f in features),
    )
    checklist.add(f"领域术语表 ≥ 5 条(实际 {len(glossary)})", len(glossary) >= 5)

    # --- 9. 渲染 MD ---
    summary = (
        f"基于领域 {agent_input.domain} 的 business_goal 与 {len(knowledge_assets)} 个业务数据资产,"
        f"LLM 识别出 {len(user_groups)} 类用户、{len(features)} 项核心功能,"
        f"沉淀术语表 {len(glossary)} 条(含种子 {len(agent_input.glossary_seed)} 条)。"
    )

    sections = [
        Section(
            "业务目标",
            md_table(
                ["字段", "值"],
                [[k, business_goal[k]] for k in ("one_liner", "success_metric", "business_value")],
            ),
        ),
        Section(
            "用户画像",
            md_table(
                ["ID", "角色", "职责", "典型诉求(原文示例)"],
                [[u["id"], u["role"], u["responsibility"], truncate(u["typical_query"], 60)] for u in user_groups],
            ),
        ),
        Section(
            "用户画像 · Persona 细分",
            _render_personas(user_groups),
        ),
        Section(
            "核心功能清单",
            md_table(
                ["ID", "功能名", "输入", "输出", "依赖资产"],
                [[f["id"], f["name"], f["input"], f["output"], ",".join(f["depends_on"])] for f in features],
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
            "\n".join(f"- **{k}**:{v}" for k, v in list(glossary.items())[:20]),
        ),
    ]

    frontmatter = {
        "stage": 1,
        "stage_name": "business_understanding",
        "version": "1.0",
        "upstream": "00_input_assessment.md",
        "downstream": "02_plan.md",
        "domain": agent_input.domain,
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
        remarks="(无,Pipeline 无本地兜底)",
    )
    return out_path


__all__ = ["run"]
