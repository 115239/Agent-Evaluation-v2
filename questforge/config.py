"""QuestForge 全局配置

所有路径、模型、并发、难度阈值集中在本文件最前端，符合用户偏好：
简单独立脚本将配置项作为全局变量集中定义。
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path


# ========== .env 自动加载 ==========
def _load_dotenv(repo_root: Path) -> None:
    """启动时从 repo 根目录的 .env 载入环境变量。

    优先使用 python-dotenv；不可用则走内置的简易解析：
      - 支持 KEY=VALUE、# 注释、前后空白、带/不带引号
      - 已存在的 os.environ 不会被覆盖（让用户 shell export 优先）
    """
    env_path = repo_root / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(env_path, override=False)
        return
    except Exception:
        pass
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


_REPO_ROOT = Path(__file__).resolve().parent.parent
_load_dotenv(_REPO_ROOT)


# ========== 项目路径 ==========
REPO_ROOT = _REPO_ROOT
DATASET_ROOT = (
    REPO_ROOT
    / "datasets"
    / "test_agent_2"
    / "纪检项目业务数据+样例数据"
    / "纪检项目业务数据+样例数据"
)
BUSINESS_DIR = DATASET_ROOT / "业务数据"
SAMPLE_DIR = DATASET_ROOT / "样例数据"

# 产物目录（每次运行一个子目录）
RUN_ID = os.environ.get("QUESTFORGE_RUN_ID") or datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = REPO_ROOT / "save" / f"pipeline_run_{RUN_ID}"

# ========== 业务域 ==========
DOMAIN = "纪检材料智能审查"
ONE_LINER_GOAL = (
    "为纪检监察员提供党纪法规、总书记讲话、理论文章、实务案例的 "
    "AI 语义检索与文书纠错辅助"
)

# ========== 四大知识库资产（Stage 1 直接登记，不走 LLM） ==========
# 每项：id / file / sheet / key_fields(拼接 key_text) / authority / category
KB_FILES = [
    {
        "id": "KB-001",
        "name": "党纪法规",
        "file": BUSINESS_DIR / "党纪法规.xlsx",
        "sheet": "党纪法规",
        "key_fields": ["要点词", "违纪行为"],
        "authority": "官方",
        "category": "结构化条款",
    },
    {
        "id": "KB-002",
        "name": "总书记讲话",
        "file": BUSINESS_DIR / "总书记讲话.xlsx",
        "sheet": "Sheet1",
        "key_fields": ["标题", "摘要", "主题"],
        "authority": "官方",
        "category": "讲话摘要+上下文",
    },
    {
        "id": "KB-003",
        "name": "理论文章",
        "file": BUSINESS_DIR / "理论文章.xlsx",
        "sheet": "理论文章",
        "key_fields": ["标题", "摘要"],
        "authority": "权威刊物",
        "category": "理论洞察",
    },
    {
        "id": "KB-004",
        "name": "实务测试集",
        "file": BUSINESS_DIR / "实务测试集.xlsx",
        "sheet": "Sheet1",
        "key_fields": ["问题", "答案", "来源文档"],
        "authority": "历史案例",
        "category": "实务问答",
    },
]

# ========== 样例数据（用于识别典型诉求、功能边界） ==========
SAMPLE_FILES = {
    "retrieval_usecase": {
        "file": SAMPLE_DIR / "AI测试-语义和定性量纪检索用例.xlsx",
        "sheet": "Sheet1",
        "category_col": "样例类别",
        "content_col": "样例内容",
    },
    "doc_correction": {
        "file": SAMPLE_DIR / "文书纠错样例.xlsx",
        "sheet": "Sheet1",
        "columns": ["测试文书", "测试样例", "纠正答案"],
    },
}

# ========== LLM 配置 ==========
# 优先读通用变量 LLM_*，其次兼容旧的 DEEPSEEK_*；默认阿里云千问（OpenAI 兼容接口）。
LLM_BASE_URL = os.environ.get(
    "LLM_BASE_URL",
    os.environ.get("DEEPSEEK_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
)
LLM_API_KEY = os.environ.get("LLM_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))
LLM_MODEL = os.environ.get("LLM_MODEL", os.environ.get("DEEPSEEK_MODEL", "qwen-plus"))
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 2000
LLM_MAX_RETRY = 3
LLM_RETRY_SLEEP = 1.5
LLM_CONCURRENCY = 4

# 是否调用 LLM；默认自动：API_KEY 存在即启用。环境变量 QUESTFORGE_USE_LLM 可强制覆盖
def _resolve_use_llm() -> bool:
    override = os.environ.get("QUESTFORGE_USE_LLM")
    if override is not None:
        return override == "1"
    return bool(LLM_API_KEY)


USE_LLM = _resolve_use_llm()

# ========== Stage 2 规划参数 ==========
DIFFICULTY_THRESHOLDS = {"basic": 0.4, "advanced": 0.7}  # 上限，>advanced 即 expert
TRIGGER_VOCAB = ["知识咨询", "案件研判", "审核复核", "批量处理"]
OUTPUT_CATEGORY_VOCAB = [
    "结构化条款",
    "讲话摘要+上下文",
    "理论洞察",
    "实务问答",
    "决策建议",
    "纠错清单",
]

# ========== Stage 3 采样参数 ==========
# 按难度控制主资产 / 候选 fragment / 干扰 fragment 数量
DIFFICULTY_SAMPLING = {
    "basic": {"primary_assets": 1, "candidate_fragments": 3, "interference_fragments": 0},
    "advanced": {"primary_assets": 2, "candidate_fragments": 6, "interference_fragments": 2},
    "expert": {"primary_assets": 3, "candidate_fragments": 10, "interference_fragments": 3},
}
INTERFERENCE_DENSITY = {"basic": 0, "advanced": 1, "expert": 2}
TRAP_KEYWORDS = ["冲突", "过时", "看似合理"]
MAX_LLM_KEYWORD_CALLS = 20  # Stage 3 关键字抽取 LLM 调用上限（offline 也能有合理输出）

# ========== 预置领域术语表（Fallback 使用） ==========
DEFAULT_GLOSSARY = {
    "八项规定": "中央八项规定精神，聚焦公务接待、差旅、公款消费等纪律要求",
    "四种形态": "监督执纪的四种递进形态（红脸出汗—轻处分—重处分—立案审查）",
    "定性量纪": "对违纪行为进行定性并决定处分档次",
    "从宽情节": "主动交代、配合调查、退赔挽损等可以从轻从宽的情节",
    "从严情节": "对抗组织审查、隐瞒不报、转移赃款等应当从重从严的情节",
    "廉洁纪律": "党员干部在廉洁从政方面必须遵守的纪律要求",
    "政治纪律": "维护党中央权威和集中统一领导的纪律",
    "工作纪律": "履行岗位职责、遵守工作规程的纪律",
    "党纪处分": "对违纪党员作出的处分，含警告、严重警告、撤销党内职务、留党察看、开除党籍",
    "审查调查": "纪检监察机关对涉嫌违纪违法党员干部的调查核实",
    "谈话函询": "党组织对党员干部反映问题的沟通方式",
    "文书纠错": "对纪检文书中表达、依据、口径等错误进行识别与修正",
}

# ========== 日志 ==========
LOG_LEVEL = os.environ.get("QUESTFORGE_LOG", "INFO")


def ensure_out_dir() -> Path:
    """创建产物目录（幂等）。"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUT_DIR
