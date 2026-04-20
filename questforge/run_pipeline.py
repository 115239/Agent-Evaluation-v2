"""QuestForge Pipeline 入口（Stage 1 → Stage 2 → Stage 3）。

用法：
    python -m questforge.run_pipeline               # 默认 offline（USE_LLM 由环境变量控制）
    QUESTFORGE_USE_LLM=1 python -m questforge.run_pipeline
    QUESTFORGE_RUN_ID=demo python -m questforge.run_pipeline
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from . import config, stage1_understanding, stage2_plan, stage3_context

log = logging.getLogger("questforge.pipeline")


def main() -> int:
    parser = argparse.ArgumentParser(description="QuestForge Pipeline · 执行 Stage 1-3")
    parser.add_argument("--run-id", default=None, help="覆盖 config.RUN_ID")
    parser.add_argument("--out", default=None, help="覆盖产物目录")
    parser.add_argument(
        "--only",
        default=None,
        choices=["stage1", "stage2", "stage3"],
        help="仅运行某个阶段（需已有前置产物）",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    if args.run_id:
        config.RUN_ID = args.run_id
        config.OUT_DIR = Path(config.__file__).resolve().parent / "datasets" / f"pipeline_run_{args.run_id}"

    out_dir = Path(args.out) if args.out else config.ensure_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    log.info("[Pipeline] OUT_DIR=%s, USE_LLM=%s", out_dir, config.USE_LLM)

    stage1_path = out_dir / "01_understanding.md"
    stage2_path = out_dir / "02_plan.md"
    stage3_path = out_dir / "03_context.md"

    if args.only in (None, "stage1"):
        log.info("=== Stage 1 · 业务理解 ===")
        stage1_path = stage1_understanding.run(out_dir)
    elif not stage1_path.exists():
        raise FileNotFoundError(f"缺少上游 {stage1_path}，请先跑 stage1")

    if args.only in (None, "stage2"):
        log.info("=== Stage 2 · 业务流程提取 + 题目规划 ===")
        stage2_path = stage2_plan.run(stage1_path, out_dir)
    elif not stage2_path.exists():
        raise FileNotFoundError(f"缺少上游 {stage2_path}，请先跑 stage2")

    if args.only in (None, "stage3"):
        log.info("=== Stage 3 · 仿真数据集构建 + 约束/干扰设计 ===")
        stage3_path = stage3_context.run(stage2_path, out_dir)

    log.info("[Pipeline] 完成，产物：\n  %s\n  %s\n  %s", stage1_path, stage2_path, stage3_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
