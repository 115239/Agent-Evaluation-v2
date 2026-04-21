"""QuestForge 框架级配置

**本文件只保留与领域无关的通用常量。**
所有领域专属信息(业务目标、知识库、术语等)均通过 `AgentInput` 在运行时传入。
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path


# ========== .env 自动加载 ==========
def _load_dotenv(repo_root: Path) -> None:
    """启动时从 repo 根目录的 .env 载入环境变量。

    优先使用 python-dotenv;不可用则走内置的简易解析。
    已存在的 os.environ 不会被覆盖(让用户 shell export 优先)。
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


REPO_ROOT = Path(__file__).resolve().parent.parent
_load_dotenv(REPO_ROOT)


# ========== 产物目录 ==========
RUN_ID = os.environ.get("QUESTFORGE_RUN_ID") or datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = Path(__file__).resolve().parent / "datasets" / f"pipeline_run_{RUN_ID}"


def ensure_out_dir(override: Path | None = None) -> Path:
    """创建产物目录(幂等)。用户可通过 `AgentInput.out_dir` 覆盖默认路径。"""
    target = Path(override) if override else OUT_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


# ========== LLM 配置 ==========
# 优先读通用变量 LLM_*,其次兼容旧的 DEEPSEEK_*
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


def _resolve_use_llm() -> bool:
    override = os.environ.get("QUESTFORGE_USE_LLM")
    if override is not None:
        return override == "1"
    return bool(LLM_API_KEY)


USE_LLM = _resolve_use_llm()


# ========== 五阶段固定名称(设计文档 §3.3) ==========
FIVE_STAGES = ["定义问题", "拆解问题", "方案生成", "执行落地", "元认知"]


# ========== Stage 2 规划参数(与领域无关) ==========
DIFFICULTY_THRESHOLDS = {"basic": 0.4, "advanced": 0.7}  # 上限,>advanced 即 expert

# §4.4 触发类型示例词表(LLM 可扩充)
TRIGGER_VOCAB = ["知识咨询", "案件研判", "审核复核", "批量处理"]


# ========== Stage 3 采样/密度参数(与领域无关) ==========
# 按难度控制主资产 / 候选 fragment / 干扰 fragment 数量(设计文档 §4.5 Step 3.2)
DIFFICULTY_SAMPLING = {
    "basic": {"primary_assets": 1, "candidate_fragments": 3, "interference_fragments": 0},
    "advanced": {"primary_assets": 2, "candidate_fragments": 6, "interference_fragments": 2},
    "expert": {"primary_assets": 3, "candidate_fragments": 10, "interference_fragments": 3},
}

# 干扰密度硬规则(§4.5 Step 3.5)
INTERFERENCE_DENSITY = {"basic": 0, "advanced": 1, "expert": 2}

# expert 必须包含的"陷阱"标记词
TRAP_KEYWORDS = ["冲突", "过时", "看似合理"]

# LLM 预算上限(Stage 3 关键字抽取 + 真实性判定合计,避免 offline 场景下爆调用)
MAX_LLM_KEYWORD_CALLS = 20


# ========== Stage 4 参数(与领域无关) ==========
# 单条题目 LLM 调用并发上限(每题一次调用)
STAGE4_MAX_WORKERS = LLM_CONCURRENCY

# prompt 长度硬约束(设计文档 §4.6 Step 4.1)
STAGE4_PROMPT_LEN = (20, 300)

# 五阶段满分权重(设计文档 §4.6 Step 4.3, 固定 2/2/3/2/1)
STAGE4_STAGE_WEIGHTS: dict[str, float] = {
    "定义问题": 2.0,
    "拆解问题": 2.0,
    "方案生成": 3.0,
    "执行落地": 2.0,
    "元认知": 1.0,
}

# 难度自校准分档(设计文档 §4.6 Step 4.4)
STAGE4_DIFFICULTY_SCORE_THRESHOLDS = {"basic": 1.5, "advanced": 2.3}

# Stage 4 单题 LLM 最大 token(reference/rubric 较长, 需要比默认更大)
STAGE4_LLM_MAX_TOKENS = 6000


# ========== 日志 ==========
LOG_LEVEL = os.environ.get("QUESTFORGE_LOG", "INFO")


__all__ = [
    "REPO_ROOT",
    "RUN_ID",
    "OUT_DIR",
    "ensure_out_dir",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "LLM_MAX_RETRY",
    "LLM_RETRY_SLEEP",
    "LLM_CONCURRENCY",
    "USE_LLM",
    "FIVE_STAGES",
    "DIFFICULTY_THRESHOLDS",
    "TRIGGER_VOCAB",
    "DIFFICULTY_SAMPLING",
    "INTERFERENCE_DENSITY",
    "TRAP_KEYWORDS",
    "MAX_LLM_KEYWORD_CALLS",
    "STAGE4_MAX_WORKERS",
    "STAGE4_PROMPT_LEN",
    "STAGE4_STAGE_WEIGHTS",
    "STAGE4_DIFFICULTY_SCORE_THRESHOLDS",
    "STAGE4_LLM_MAX_TOKENS",
    "LOG_LEVEL",
]
