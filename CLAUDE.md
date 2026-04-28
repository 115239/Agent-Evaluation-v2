# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

QuestForge 是一个"题目生成 Agent"流水线:输入 PRD/设计文档 + 业务数据(xlsx),输出可用于评测业务 AI 系统的测试数据集。设计文档权威版本:`题目生成Agent设计文档.md`(根目录,~100 KB)。

当前实现覆盖 **Phase 0 + Stage 1-5**。Stage 4 负责题目、五阶段期望和 rubric 扩写;Stage 5 负责验证、最终 benchmark 打包和 `dataset.{json,xlsx}` 输出.

## 常用命令

```bash
# 跑通完整流水线(默认使用 datasets/test_agent_2/example_input.json)
python -m questforge.run_pipeline

# 指定自定义输入与产物目录
python -m questforge.run_pipeline --input-json datasets/test/xxx/input.json --run-id demo --out /tmp/out

# 单阶段断点续跑(上游 MD 必须已存在于产物目录)
python -m questforge.run_pipeline --only stage2 --input-json <path>

# 退出码:0=正常, 1=通用异常, 2=MissingInputError(需补输入)
```

无 pyproject.toml、无测试 runner、无 Makefile。`questforge/tests/` 仅有 schemas 占位目录,没有真实测试。

## LLM 凭证

`.env`(根目录,已 gitignore)载入以下变量,`questforge/config.py` 自动读取:

```
LLM_BASE_URL=<OpenAI 兼容 endpoint>
LLM_API_KEY=<key>
LLM_MODEL=<model id,如 qwen-plus、claude-opus-4.6、gpt-5.4>
```

设置 `QUESTFORGE_USE_LLM=0` 可强制关 LLM(仅跑本地启发式)。默认若 `LLM_API_KEY` 为空则自动切 offline。

## 架构核心(必读)

**五阶段心智模型**:原始文档 → 5 张"认知表"(S1)→ 题目骨架(S2)→ 知识绑定(S3)→ 完整题目(S4)→ 可执行数据集(S5)。

**阶段产物是唯一契约**:每个阶段只产出一份 MD 文件到 `OUT_DIR`,下一阶段只吃上一阶段的 MD。MD 骨架由 `common.write_md` 强制统一:YAML frontmatter + 摘要 + 若干 Section + `## 结构化数据` JSON 代码块 + `## 下一阶段校验清单` + 备注。下游通过 `common.read_md` 解析 frontmatter 与 artifacts JSON。

**pass_gate 门禁**:每份 MD 的 frontmatter 含 `pass_gate: true/false`。`run_pipeline._require_pass_gate` 在跨阶段之前强校验;false 即抛 `MissingInputError`,不自动兜底。

**不做本地兜底**是框架硬原则。LLM 输出为空 / 输入字段缺失时,统一包成 `MissingInputError`(见 `input_spec.py`),`format_for_user()` 产出"缺什么 / 为什么 / 怎么补 / 例子"四元组列表,告诉用户用 `--only stageN` 补跑。不要给 LLM 调用加"静默默认值"补救——违背设计意图。

**关键模块分工**:

- `input_spec.py` — `AgentInput` dataclass(通道 + 业务目标 + docs_dir + data_dir + samples + glossary_seed + weak_points + business_processes)。当前只实现 `design_doc` 通道;其他三种(gui/code/user_log)是占位。
- `phase0_preprocess.py` — 完整性体检 + 质量打分 + 策略推荐;pass_gate 决定是否放行到 Stage 1。
- `stage1_understanding.py` — 扫资产、调 LLM 产"认知五表"(business_goal / user_groups / features / knowledge_assets / glossary)。资产探测用 openpyxl 取行数最多的 sheet。
- `stage2_plan.py` — 流程提取(LLM 推导或转录用户提供的 `business_processes`)→ 动态分类维度(至少 2 取值才算有效)→ 聚类 → 按 complexity 分难度梯度(`DIFFICULTY_THRESHOLDS`)→ 覆盖矩阵蓝图。
- `stage3_context.py` — 加载全部 xlsx 建 Fragment + 倒排索引(`io_utils.build_fragments` + `build_inverted_index`);按难度决定主资产数/候选/干扰(`DIFFICULTY_SAMPLING`);约束/干扰由 LLM 生成,过"三检验"过滤合成幻觉。产出 `03_context.md` + `stage3_fragments.jsonl` + `stage3_inverted_index.json`。
- `stage4_questions.py` — 基于 `03_context.md` 生成完整题目、五阶段期望行为与 10 分制评分细则,产出 `04_tests.md` + `stage4_items.jsonl`。
- `stage5_finalize.py` — 本地执行 5 设计原则验证、覆盖矩阵对齐、先验区分度和独立性评估,产出 `05_report.md`、`dataset.json`、`dataset.xlsx`、`traceability.json` 与 `dataset_supplementary/`。
- `io_utils.py` — 领域无关;`KBFragment` 数据类、`extract_local_keywords`(jieba 可选,不可用自动降级)。对应 `datasets/test_agent_2/0311构建.py` 的"原始片段→关键字→用户提问"三步。
- `llm_client.py` — OpenAI 兼容 SDK 的最小封装,`chat_json` 强制 JSON 输出,解析失败返空 dict 让上层走 offline。
- `prompts/*.txt` — 每个阶段的 system prompt,领域无关。修改 prompt 是调优主入口,代码里基本只负责组装 user payload。

**产物路径**:默认写到 `questforge/datasets/pipeline_run_<RUN_ID>/`(RUN_ID 可通过 `--run-id` 或 `QUESTFORGE_RUN_ID` 覆盖)。`AgentInput.out_dir` 或 `--out` 可强制改目录。`save/pipeline_run_*` 是旧手工实验目录,`.gitignore` 已屏蔽。

## 设计硬约束

- **领域无关**:`io_utils`、`config` 不得出现"纪检/党纪/条款"等业务词汇;领域词统一由 Stage 1 产出的 `glossary` 往下游注入。
- **ID 规范**:`common.IdCounter` 统一产 `UG-001` / `BP-001` / `PT-001` / `FRAG-<asset尾三位>-<4位row>` 等 ID。跨阶段引用必须走 ID。
- **Python 规范**(遵从 `~/.claude/CLAUDE.md`):优先用 Python;独立脚本把输入/输出路径、model、并发数等配置项作为全局变量放最前。
- **关键字提取长度区间**是 4-8 字(`io_utils.extract_local_keywords`),与 `0311构建.py` 的 `MIN/MAX_KEYWORD_LENGTH` 对齐,改动前要确认下游 Stage 4 的 prompt 种子不会被破坏。

## 输入 JSON 示例位置

`datasets/test_agent_2/example_input.json` 是纪检场景的参考输入。`datasets/test/安监的组件/` 是新的安监场景测试资料(未完成 input.json)。`datasets/test_agent_2/0311构建.py` 是 Pipeline 化之前的一次性合成脚本,调 DeepSeek 直接出题,保留作 Stage 4 的参考实现。
