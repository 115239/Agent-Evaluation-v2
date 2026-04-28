"""QuestForge Pipeline 入口(Phase 0 + Stage 1-5)。

用法:
    # 默认示例(纪检示例输入):
    python -m questforge.run_pipeline --input-json datasets/test_agent_2/example_input.json

    # 自定义输出目录 / run-id:
    python -m questforge.run_pipeline --input-json X.json --run-id demo --out /tmp/out

    # 单阶段断点续跑(上游 MD 必须已存在):
    python -m questforge.run_pipeline --input-json X.json --only stage2

退出码:
    0 正常完成
    1 其他异常
    2 MissingInputError(用户需补充输入)
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import (
    config,
    phase0_preprocess,
    stage1_understanding,
    stage2_plan,
    stage3_context,
    stage4_questions,
    stage5_finalize,
)
from .common import read_md
from .input_spec import AgentInput, MissingField, MissingInputError

log = logging.getLogger("questforge.pipeline")

EXIT_OK = 0
EXIT_GENERIC_ERROR = 1
EXIT_MISSING_INPUT = 2


def _require_pass_gate(md_path: Path, stage_name: str) -> None:
    """检查阶段 MD frontmatter 的 pass_gate。false → MissingInputError,阻止推进。"""
    parsed = read_md(md_path)
    fm = parsed["frontmatter"]
    if fm.get("pass_gate") is True:
        return
    raise MissingInputError(
        stage=stage_name,
        report=[
            MissingField(
                field_name=f"{md_path.name} 的校验清单",
                why_needed=(
                    "该阶段部分校验项未通过,后续阶段会基于残缺产物滚动错误;"
                    "请阅读 MD 末尾的'下一阶段校验清单'找到失败项"
                ),
                suggested_format=(
                    "根据失败项补充 example_input.json 中对应字段(如 business_processes、"
                    "weak_points、features 细节),或调整 LLM_MODEL 后重跑该阶段"
                ),
                example=f"python -m questforge.run_pipeline --only {fm.get('stage_name','stageN')} --input-json <path>",
            )
        ],
    )


def _default_input_json() -> Path:
    return config.REPO_ROOT / "datasets" / "test_agent_2" / "example_input.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="QuestForge Pipeline · Phase 0 + Stage 1-5")
    parser.add_argument(
        "--input-json",
        default=None,
        help="AgentInput JSON 路径;缺省使用 datasets/test_agent_2/example_input.json",
    )
    parser.add_argument("--run-id", default=None, help="覆盖 config.RUN_ID")
    parser.add_argument("--out", default=None, help="覆盖产物目录")
    parser.add_argument(
        "--only",
        default=None,
        choices=["stage0", "stage1", "stage2", "stage3", "stage4", "stage5"],
        help="仅运行指定阶段(上游 MD 必须已存在)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    # --- 载入 AgentInput ---
    input_path = Path(args.input_json) if args.input_json else _default_input_json()
    if not input_path.exists():
        log.error("输入 JSON 不存在:%s", input_path)
        return EXIT_GENERIC_ERROR
    try:
        agent_input = AgentInput.from_json(input_path)
    except Exception as e:
        log.error("AgentInput 解析失败:%s", e)
        return EXIT_GENERIC_ERROR

    # --- 决定产物目录 ---
    if args.run_id:
        config.RUN_ID = args.run_id
        config.OUT_DIR = (
            Path(config.__file__).resolve().parent / "datasets" / f"pipeline_run_{args.run_id}"
        )
    effective_out = (
        Path(args.out) if args.out else config.ensure_out_dir(agent_input.out_dir)
    )
    effective_out.mkdir(parents=True, exist_ok=True)
    log.info("[Pipeline] OUT_DIR=%s, USE_LLM=%s", effective_out, config.USE_LLM)

    phase0_path = effective_out / "00_input_assessment.md"
    stage1_path = effective_out / "01_understanding.md"
    stage2_path = effective_out / "02_plan.md"
    stage3_path = effective_out / "03_context.md"
    stage4_path = effective_out / "04_tests.md"
    stage5_path = effective_out / "05_report.md"

    try:
        only = args.only  # None 表示跑全链

        if only in (None, "stage0"):
            log.info("=== Phase 0 · 输入预处理 ===")
            phase0_path, _ = phase0_preprocess.run(agent_input, effective_out)

        if only in (None, "stage1"):
            if not phase0_path.exists():
                raise FileNotFoundError(f"缺少上游 {phase0_path},请先跑 stage0")
            _require_pass_gate(phase0_path, "Stage 1 前置校验")
            log.info("=== Stage 1 · 业务理解 ===")
            stage1_path = stage1_understanding.run(agent_input, effective_out)

        if only in (None, "stage2"):
            if not stage1_path.exists():
                raise FileNotFoundError(f"缺少上游 {stage1_path},请先跑 stage1")
            _require_pass_gate(stage1_path, "Stage 2 前置校验")
            log.info("=== Stage 2 · 业务流程提取 + 题目规划 ===")
            stage2_path = stage2_plan.run(stage1_path, effective_out, agent_input)

        if only in (None, "stage3"):
            if not stage2_path.exists():
                raise FileNotFoundError(f"缺少上游 {stage2_path},请先跑 stage2")
            _require_pass_gate(stage2_path, "Stage 3 前置校验")
            log.info("=== Stage 3 · 仿真数据集构建 + 约束/干扰设计 ===")
            stage3_path = stage3_context.run(stage2_path, effective_out, agent_input)

        if only in (None, "stage4"):
            if not stage3_path.exists():
                raise FileNotFoundError(f"缺少上游 {stage3_path},请先跑 stage3")
            _require_pass_gate(stage3_path, "Stage 4 前置校验")
            log.info("=== Stage 4 · 题目 + 期望 + 评分细则 ===")
            stage4_path = stage4_questions.run(stage3_path, effective_out, agent_input)

        if only in (None, "stage5"):
            if not stage4_path.exists():
                raise FileNotFoundError(f"缺少上游 {stage4_path},请先跑 stage4")
            _require_pass_gate(stage4_path, "Stage 5 前置校验")
            log.info("=== Stage 5 · 验证 + benchmark ===")
            stage5_path = stage5_finalize.run(stage4_path, effective_out, agent_input)
            if read_md(stage5_path)["frontmatter"].get("pass_gate") is not True:
                log.error("[Pipeline] Stage 5 最终验收未通过,请查看 %s", stage5_path)
                return EXIT_GENERIC_ERROR

        log.info(
            "[Pipeline] 完成,产物:\n  %s\n  %s\n  %s\n  %s\n  %s\n  %s",
            phase0_path,
            stage1_path,
            stage2_path,
            stage3_path,
            stage4_path,
            stage5_path,
        )
        return EXIT_OK

    except MissingInputError as e:
        print("\n" + "=" * 72)
        print(e.format_for_user())
        print("=" * 72 + "\n")
        log.error("[Pipeline] %s", e)
        return EXIT_MISSING_INPUT

    except Exception as e:  # pragma: no cover
        log.exception("[Pipeline] 异常终止:%s", e)
        return EXIT_GENERIC_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
