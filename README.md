# QuestForge - AI Agent Evaluation Dataset Pipeline

QuestForge 是一个题目生成 Agent 流水线。它输入业务 PRD/设计文档、业务数据资产和少量人工种子信息，输出可用于评测业务 AI 系统的 benchmark 数据集。

当前主线不是一次性让大模型生成题目，而是把出题过程拆成可审计、可断点续跑、可逐阶段校验的工程流水线：

```text
AgentInput
  -> 00_input_assessment.md
  -> 01_understanding.md
  -> 02_plan.md
  -> 03_context.md
  -> 04_tests.md
  -> 05_report.md
  -> dataset.json / dataset.xlsx / traceability.json
```

可选的 `Stage 6` 会在 `04_tests.md` 之后做先验答题模拟自检，输出 `06_self_eval.md` 和 `dataset_supplementary/self_eval.json`。默认完整流水线只运行到 `Stage 5`。

需要区分两个“五阶段”：

| 名称 | 含义 |
|---|---|
| QuestForge 流水线 Stage 1-5 | 生成题目的工程流程，从业务理解到 benchmark 打包 |
| 题目内五阶段能力 | 被测 Agent 回答题目时需要体现的能力：定义问题、拆解问题、方案生成、执行落地、元认知 |

## 快速开始

### 1. 安装依赖

建议使用 Python 3.10+。

```bash
python -m venv .venv
source .venv/bin/activate
pip install openai pandas openpyxl python-dotenv python-docx pypdf
```

其中 `python-docx`、`pypdf` 只在读取 docx/pdf 资产时需要。

### 2. 配置 LLM

复制环境变量模板：

```bash
cp .env.example .env
```

填写 OpenAI 兼容模型端点：

```env
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
LLM_API_KEY=sk-your-api-key
```

支持 DashScope、DeepSeek、OpenRouter 等 OpenAI 兼容接口。`.env` 会在启动时自动加载；Shell 中已存在的环境变量优先级更高。

常用可选变量：

| 变量 | 作用 | 默认 |
|---|---|---|
| `QUESTFORGE_RUN_ID` | 控制默认产物目录名 `pipeline_run_<RUN_ID>` | 当前时间 |
| `QUESTFORGE_USE_LLM` | 强制开关 LLM，`1` 为启用 | 有 `LLM_API_KEY` 时启用 |
| `QUESTFORGE_TESTS_PER_TYPE` | Stage 2 每类业务类型规划的题目数 | `2` |
| `QUESTFORGE_STAGE6_SAMPLE` | Stage 6 每个难度抽检题目数 | `1` |
| `QUESTFORGE_STAGE6_DIFF_THR` | Stage 6 区分度通过阈值 | `3.0` |
| `QUESTFORGE_LOG` | 日志级别 | `INFO` |

### 3. 运行完整流水线

默认使用纪检场景示例输入：

```bash
python -m questforge.run_pipeline
```

等价于：

```bash
python -m questforge.run_pipeline \
  --input-json datasets/test_agent_2/example_input.json
```

指定 run id 或输出目录：

```bash
python -m questforge.run_pipeline \
  --input-json datasets/test_agent_2/example_input.json \
  --run-id demo

python -m questforge.run_pipeline \
  --input-json datasets/test_agent_2/example_input.json \
  --out questforge/datasets/pipeline_run_demo
```

产物默认写入：

```text
questforge/datasets/pipeline_run_<RUN_ID>/
```

### 4. 断点续跑

`--only` 支持单阶段重跑：

```bash
python -m questforge.run_pipeline --only stage2 --input-json datasets/test_agent_2/example_input.json --run-id demo
python -m questforge.run_pipeline --only stage5 --input-json datasets/test_agent_2/example_input.json --run-id demo
python -m questforge.run_pipeline --only stage6 --input-json datasets/test_agent_2/example_input.json --run-id demo
```

断点续跑时必须复用同一个 `--run-id` 或 `--out`，因为每个阶段会读取同一产物目录里的上游 Markdown。

## 输入契约

入口文件是 `AgentInput` JSON，示例见：

```text
datasets/test_agent_2/example_input.json
```

主要字段：

| 字段 | 说明 |
|---|---|
| `source_channel` | 输入通道；当前完整实现的是 `design_doc` |
| `business_goal` | 一句话业务目标，是整条流水线的主轴 |
| `domain` | 业务领域名称 |
| `docs_dir` | PRD、设计文档、架构文档目录，可为空 |
| `data_dir` | 业务数据资产目录 |
| `samples` | 样例数据读取配置，支持单列类别/内容或多列原样读取 |
| `glossary_seed` | 领域术语种子 |
| `weak_points` | 需要重点测试的薄弱点或能力边界 |
| `business_processes` | 可选人工业务流程；为空时 Stage 2 会尝试由 LLM 推导 |
| `out_dir` | 可选自定义产物目录 |

当前资产读取支持 `xlsx/xls/xlsm/csv/docx/txt/md/pdf`。Excel 资产建议优先使用 `xlsx`。

## 阶段设计

| 阶段 | 入口文件 | 主要职责 | 关键产物 | 是否依赖 LLM |
|---|---|---|---|---|
| Phase 0 | `phase0_preprocess.py` | 检查输入完整性、扫描资产、质量评分 | `00_input_assessment.md` | 否 |
| Stage 1 | `stage1_understanding.py` | 构建业务目标、用户画像、功能、知识资产、术语表 | `01_understanding.md` | 是 |
| Stage 2 | `stage2_plan.py` | 提取业务流程、归纳业务类型、规划题目和覆盖矩阵 | `02_plan.md` | 视输入而定 |
| Stage 3 | `stage3_context.py` | 绑定真实数据片段，设计约束、干扰和关键词池 | `03_context.md`、`stage3_fragments.jsonl`、`stage3_inverted_index.json` | 是 |
| Stage 4 | `stage4_questions.py` | 生成完整题目、参考答案、五阶段期望行为和 10 分 rubric | `04_tests.md`、`stage4_items.jsonl` | 是 |
| Stage 5 | `stage5_finalize.py` | 本地验证、覆盖矩阵对齐、导出 benchmark | `05_report.md`、`dataset.json`、`dataset.xlsx`、`traceability.json` | 否 |
| Stage 6 | `stage6_self_eval.py` | 抽样模拟 perfect/baseline 答题并用 rubric 评分 | `06_self_eval.md`、`dataset_supplementary/self_eval.json` | 是 |

每个阶段的 Markdown 都包含 frontmatter、摘要、业务章节、结构化 JSON artifacts 和下一阶段校验清单。下游通过 `questforge/common.py::read_md` 读取上游 Markdown，不直接依赖上游 Python 内存对象。

## 最终产物

完整通过 Stage 5 后，输出目录通常包含：

```text
00_input_assessment.md
01_understanding.md
02_plan.md
03_context.md
04_tests.md
05_report.md
dataset.json
dataset.xlsx
traceability.json
stage3_fragments.jsonl
stage3_inverted_index.json
stage4_items.jsonl
dataset_supplementary/
```

`dataset.xlsx` 包含以下 sheet：

| Sheet | 内容 |
|---|---|
| `主表` | 评测题目主数据，列名保持为 `问题/答案/实际答案/来源文档/来源片段/标记结果/结果` |
| `评分细则` | 五阶段能力评分点、权重和证据类型 |
| `约束干扰` | 每道题的约束、干扰项和陷阱类型 |
| `元信息` | 数据集版本、领域、业务目标、题量、难度分布等 |

`traceability.json` 和 `dataset_supplementary/traceability.json` 用于回溯每道题来自哪些阶段产物、业务流程、知识资产和数据片段。

当前可参考的已验证运行目录：

```text
questforge/datasets/pipeline_run_review_20260426_stage5_benchmark_v2/
```

该运行的 `05_report.md` 显示 Stage 5 最终 `pass_gate: true`。

## 项目结构

```text
questforge/
├── run_pipeline.py          # CLI 入口
├── config.py                # 环境变量与通用参数
├── input_spec.py            # AgentInput 与 MissingInputError
├── common.py                # Markdown 读写、门禁、表格等通用工具
├── io_utils.py              # 多格式资产读取、Fragment、倒排索引
├── llm_client.py            # OpenAI 兼容 LLM 客户端
├── phase0_preprocess.py     # Phase 0 输入体检
├── stage1_understanding.py  # Stage 1 业务理解
├── stage2_plan.py           # Stage 2 题目规划
├── stage3_context.py        # Stage 3 知识绑定
├── stage4_questions.py      # Stage 4 题目生成
├── stage5_finalize.py       # Stage 5 验证与打包
├── stage6_self_eval.py      # Stage 6 可选先验自检
├── prompts/                 # 各阶段 system prompt
└── datasets/                # 流水线运行产物

datasets/
└── test_agent_2/            # 纪检场景示例输入与业务数据

data/                        # 设计文档、PPT、参考资料
MD文档/                      # 项目流程与设计总结文档
```

## 设计原则

- **阶段 Markdown 是唯一契约**：每个阶段输出一份可读、可解析、可回溯的 Markdown，下游只消费上游 Markdown 中的结构化 artifacts。
- **pass_gate 门禁**：上游 `pass_gate` 不是 `true` 时，流水线中断，避免残缺产物继续滚动生成错误题目。
- **不做静默本地兜底**：输入不足、LLM 输出为空或资产不可读时，抛出 `MissingInputError`，明确告诉用户补什么、为什么补、怎么补。
- **领域无关**：代码不写死业务词汇；领域术语、知识资产和业务流程由 `AgentInput` 与阶段产物传递。
- **可追溯 benchmark**：最终数据集不仅包含题目和答案，还保留覆盖矩阵、评分细则、约束干扰和 traceability。

## 常见问题

### `MissingInputError` 如何处理？

命令退出码为 `2` 时，说明当前阶段缺少必要输入。终端会打印补充清单。补齐 `AgentInput` 或上游阶段产物后，使用同一个 `--run-id` / `--out` 从失败阶段断点续跑。

### 没有配置 `LLM_API_KEY` 能运行吗？

Phase 0 和 Stage 5 不依赖 LLM；Stage 1、Stage 3、Stage 4、Stage 6 需要 LLM。Stage 2 如果 `business_processes` 已经人工提供，可以减少对 LLM 推导流程的依赖。

### Stage 5 失败代表什么？

Stage 5 是本地最终验收。它会检查真实性、闭环性、可量化评分、区分度、预测力、覆盖矩阵和题目独立性。若 `05_report.md` 的 `pass_gate` 为 `false`，应先查看盲区清单和失败项，再回到对应阶段修复。
