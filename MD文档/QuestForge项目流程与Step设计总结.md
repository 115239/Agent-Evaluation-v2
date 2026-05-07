# QuestForge 项目流程与 Step 设计总结

## 1. 项目定位

QuestForge 是一个“题目生成 Agent”流水线：输入业务 PRD/设计文档、业务数据资产和少量人工种子信息，输出可用于评测业务 AI 系统的测试数据集。当前仓库实现的主线是：

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

核心目标不是“直接让大模型生成几道题”，而是把出题拆成可审计、可断点续跑、可逐阶段校验的流水线。每一阶段都输出 Markdown，下一阶段只读取上一阶段 Markdown 中的结构化 JSON artifacts。

## 2. 项目建设路线

从当前仓库和历史产物看，QuestForge 的建设路线大致分成 5 个阶段：

| 建设阶段 | 目标 | 结果 |
|---|---|---|
| 设计重构 | 把原来的题目生成逻辑改成“阶段产物驱动”的流水线 | 形成 `题目生成Agent设计文档.md` 中的 Stage 1-5 设计，并规定每阶段输出 MD |
| Stage 1-3 实现 | 先完成正式出题前的准备工作 | 实现业务理解、流程规划、知识绑定、约束/干扰设计 |
| Stage 4 实现 | 把知识后台转成完整题目 | 生成 prompt、五阶段期望行为、10 分制 rubric |
| Stage 5 实现 | 对题目集做验证并打包 benchmark | 输出 `05_report.md`、`dataset.json`、`dataset.xlsx`、`traceability.json` |
| 全流程修复 | 跑完整 Phase 0 + Stage 1-5，修复数据格式和质量门禁问题 | 最新可参考运行目录 `questforge/datasets/pipeline_run_review_20260426_stage5_benchmark_v2/`，最终 `pass_gate: true` |

需要区分两个“五阶段”：

| 名称 | 含义 |
|---|---|
| QuestForge 流水线 Stage 1-5 | 生成题目的工程流程，从业务理解到 benchmark 打包 |
| 题目内的五阶段能力 | 被评测对象回答题目时应体现的能力：定义问题、拆解问题、方案生成、执行落地、元认知 |

## 3. 全局设计原则

### 3.1 阶段 MD 是唯一契约

每个阶段都用 `questforge/common.py::write_md` 输出统一骨架：

````text
YAML frontmatter
# 阶段标题
## 摘要
## 若干业务章节
## 结构化数据
```json
{ artifacts }
```
## 下一阶段校验清单
## 备注与遗留问题
````

下游通过 `questforge/common.py::read_md` 解析 frontmatter 和 artifacts，不直接读上游 Python 内存对象。

### 3.2 pass_gate 门禁

每份阶段 MD 的 frontmatter 都有：

```yaml
pass_gate: true | false
```

`questforge/run_pipeline.py::_require_pass_gate()` 会在跨阶段前检查该字段。只要上游 `pass_gate` 不是 true，流水线就中断，并用 `MissingInputError` 告诉用户缺什么、为什么缺、怎么补、补充示例是什么。

### 3.3 不做静默本地兜底

当前框架的原则是：如果 LLM 输出为空、输入字段不足、数据资产不可读，不用模板数据偷偷补齐，而是中断并要求用户补输入。这样可以避免后续阶段基于残缺数据继续滚动生成错误题目。

### 3.4 领域无关

代码里的 `config.py`、`io_utils.py` 等通用模块不应写死“纪检/党纪/条款”等领域词。领域信息由 `AgentInput`、Stage 1 的 `glossary`、`knowledge_assets` 往下传。

## 4. 输入契约

入口数据结构是 `AgentInput`，定义在 `questforge/input_spec.py`。

| 字段 | 当前作用 |
|---|---|
| `source_channel` | 输入通道。当前实际完整支持 `design_doc`，`gui/code/user_log` 仍是占位 |
| `business_goal` | 一句话业务目标，是整条流水线的主轴 |
| `domain` | 业务领域名 |
| `docs_dir` | PRD/架构文档目录。设计上用于业务理解；当前实现主要做路径检查和补充建议，Stage 1 主体仍依赖 business_goal、data_dir、samples |
| `data_dir` | 业务数据资产目录，主要读取 xlsx/docx |
| `samples` | 样例数据配置，可按类别列或多列原样读取 |
| `glossary_seed` | 领域术语种子，Stage 1/3 使用 |
| `weak_points` | 能力边界/薄弱点，Stage 3 设计约束和干扰时使用 |
| `business_processes` | 用户可直接提供业务流程。若为空，Stage 2 走 LLM 推导 |
| `out_dir` | 可选产物目录 |

参考输入文件是：

```text
datasets/test_agent_2/example_input.json
```

## 5. Step 0: Phase 0 输入预处理

对应文件：

```text
questforge/phase0_preprocess.py
```

输出：

```text
00_input_assessment.md
```

设计目标：先判断输入是否满足进入流水线的最低条件，避免 Stage 1 才发现缺业务目标、数据目录或通道不支持。

| 子步骤 | 设计 |
|---|---|
| Step 0.1 载入 AgentInput | 从 JSON 解析输入，路径字段按输入文件所在目录解析成绝对路径 |
| Step 0.2 完整性检查 | 检查 `source_channel`、`business_goal`、`domain`、`data_dir` 等必要字段 |
| Step 0.3 数据资产扫描 | 扫描 `data_dir` 下的可用业务数据文件，目前重点是 xlsx/docx |
| Step 0.4 质量评分 | 按 business_goal 长度、资产数量、samples、glossary_seed 给 0-1 分 |
| Step 0.5 推荐策略 | 如果已有 `business_processes`，Stage 2 可直接转录；否则 Stage 2 触发流程推导 |
| Step 0.6 输出门禁 | 生成 `00_input_assessment.md`，`pass_gate` 决定能否进入 Stage 1 |

核心 artifacts：

```json
{
  "agent_input": "...",
  "completeness": "...",
  "quality_score": 0.0,
  "recommended_strategy": "...",
  "suggestions": [],
  "missing_required": []
}
```

## 6. Step 1: 业务理解

对应文件：

```text
questforge/stage1_understanding.py
```

输出：

```text
01_understanding.md
```

设计目标：把原始业务目标、样例和数据资产整理成“认知五表”：业务目标、用户画像、核心功能、知识资产、领域术语。Stage 1 不做业务流程抽取，只做理解和登记。

| 子步骤 | 设计 |
|---|---|
| Step 1.1 LLM 可用性检查 | Stage 1 需要 LLM 做资产分类、用户画像、功能和术语抽取；无 LLM 就中断 |
| Step 1.2 扫描业务资产 | 读取 `data_dir` 下可用文件，xlsx 通过 openpyxl 选择行数最多的 sheet |
| Step 1.3 资产分类 | LLM 为每个资产判断 `key_fields`、`authority`、`category`，生成 `KB-001` 这类资产 ID |
| Step 1.4 加载样例数据 | 根据 `samples` 配置加载真实样例，用作用户诉求和功能识别依据 |
| Step 1.5 抽取认知五表 | LLM 输出 `business_goal` 补充信息、`user_groups`、`features`、`glossary` |
| Step 1.6 归一化和校验 | 用户画像必须有 `typical_query`，功能必须有 input/output/depends_on，术语表至少 5 条 |
| Step 1.7 输出阶段 MD | 写入业务目标、用户画像、功能清单、知识资产、术语表 |

核心 artifacts：

```json
{
  "business_goal": {
    "one_liner": "...",
    "success_metric": "...",
    "business_value": "..."
  },
  "user_groups": [],
  "features": [],
  "knowledge_assets": [],
  "glossary": {}
}
```

Stage 1 的价值：它把后续所有推导都固定在业务目标和真实数据资产上，避免 Stage 2 直接凭空“想流程”。

## 7. Step 2: 业务流程提取与题目规划

对应文件：

```text
questforge/stage2_plan.py
```

输出：

```text
02_plan.md
```

设计目标：把 Stage 1 的业务认知转成题目骨架。它决定“出几道题、每道题考哪个流程、难度是什么、五阶段哪个能力是重点”。

| 子步骤 | 设计 |
|---|---|
| Step 2.1 流程提取 | 如果 `AgentInput.business_processes` 存在，直接转录；否则 LLM 从 Stage 1 artifacts 推导流程，这是第一层 Fallback |
| Step 2.2 动态分类维度扫描 | 从流程中抽取触发类型、参与角色、输出类别、是否跨流程等维度；至少有 2 种取值才算有效维度 |
| Step 2.3 聚类与复杂度计算 | 按流程相似度和复杂度聚类，避免固定套用“查询/决策/审核”这类死分类 |
| Step 2.4 业务类型归纳 | 为每个 cluster 生成 `PT-xxx` 业务类型，选出代表流程 |
| Step 2.5 题目数量规划 | 每个业务类型规划若干题，受 `QUESTFORGE_TESTS_PER_TYPE` 控制，默认每类最多 2 道 |
| Step 2.6 难度分配 | 根据 complexity 分为 `basic/advanced/expert`，文书纠错/审核类会避免被压成 basic |
| Step 2.7 focus_stages 规划 | 给每道题标注五阶段中的重点考察阶段 |
| Step 2.8 覆盖矩阵蓝图 | 输出 `coverage_matrix_plan`，作为 Stage 5 覆盖验证基线 |

核心 artifacts：

```json
{
  "fallback_status": {
    "business_processes_present": false,
    "capability_scope_present": false,
    "llm_path_taken": true
  },
  "processes": [],
  "dimensions": {},
  "effective_dimensions": [],
  "process_types": [],
  "test_plan": [],
  "coverage_matrix_plan": {}
}
```

Stage 2 的关键变化：题目数量不是固定 3 道，而是由业务类型数量和成员流程独立性决定；题目难度不是由覆盖范围决定，而是由约束、跨资产、干扰和流程复杂度共同决定。

## 8. Step 3: 知识绑定与约束/干扰设计

对应文件：

```text
questforge/stage3_context.py
```

输出：

```text
03_context.md
stage3_fragments.jsonl
stage3_inverted_index.json
```

设计目标：把 Stage 2 的题目骨架绑定到真实业务数据片段，并为每道题设计约束项、干扰项和关键字池。

| 子步骤 | 设计 |
|---|---|
| Step 3.1 读取上游 | 读取 `02_plan.md`，并回读同目录下的 `01_understanding.md` 获取 glossary、features、knowledge_assets |
| Step 3.2 构建权威词 | 从 glossary、知识资产类别、weak_points 中构建 authority keywords，用于真实性验证 |
| Step 3.3 数据切片 | 读取每个 xlsx，按 Stage 1 识别出的 `key_fields` 构建 `KBFragment` |
| Step 3.4 倒排索引 | 通过 `io_utils.build_inverted_index()` 建立关键词到 fragment 的索引 |
| Step 3.5 匹配主资产 | 按题目来源流程、功能依赖、难度和已覆盖资产选择 primary assets；后续修复过资产重复导致独立性低的问题 |
| Step 3.6 抽取核心片段 | 按流程字段、focus_stages 和难度抽取候选 fragments |
| Step 3.7 生成 keyword_pool | 从 fragment 中提取 4-8 字专业短语，供 Stage 4 组织 prompt |
| Step 3.8 生成约束项 | LLM 根据流程、资产、weak_points 或流程特性生成 constraints |
| Step 3.9 生成干扰项 | 按难度控制干扰密度：basic 0、advanced 1、expert 至少 2 且包含陷阱 |
| Step 3.10 真实性三检验 | 约束/干扰必须通过权威词匹配、倒排索引支持或 LLM 真实性判定之一，否则丢弃 |
| Step 3.11 输出上下文 | 写入每道题的 `test_contexts`，同时落盘 fragment JSONL 和倒排索引 |

核心 artifacts：

```json
{
  "fallback_status": {
    "weak_points_present": false
  },
  "authority_keywords_count": 0,
  "knowledge_index": {},
  "test_contexts": [
    {
      "test_id": "TEST-001",
      "difficulty": "advanced",
      "primary_assets": [],
      "fragments": [],
      "interference_fragments": [],
      "keyword_pool": [],
      "constraints": [],
      "interferences": [],
      "realism_check": {
        "total": 0,
        "passed": 0
      }
    }
  ]
}
```

Stage 3 是区分“真实业务题”和“空泛大模型题”的关键。没有 fragment、keyword_pool、constraints，就不能进入 Stage 4。

## 9. Step 4: 题目、五阶段期望与评分细则生成

对应文件：

```text
questforge/stage4_questions.py
```

输出：

```text
04_tests.md
stage4_items.jsonl
```

设计目标：把 Stage 3 的知识后台转成完整可执行题目，每道题都必须包含用户 prompt、参考答案结构、五阶段期望行为和 10 分制评分细则。

| 子步骤 | 设计 |
|---|---|
| Step 4.1 读取上下文 | 读取 `03_context.md` 的 `test_contexts`，并回读 Stage 1/2 获取流程和术语 |
| Step 4.2 构建生成任务 | 每个 `test_context` 对应一个 LLM 任务 |
| Step 4.3 支持断点续传 | 已写入 `stage4_items.jsonl` 的 `test_id` 会跳过，失败后可只重跑 Stage 4 |
| Step 4.4 并发调用 LLM | 用 `ThreadPoolExecutor` 按 `STAGE4_MAX_WORKERS` 并发生成 |
| Step 4.5 schema 校验 | 校验 prompt、reference、rubric、fatal_deductions、veto_items 等结构 |
| Step 4.6 五阶段一致性校验 | `reference.decompose.expected_steps` 必须等于来源业务流程的 `steps.name` |
| Step 4.7 rubric 权重校验 | 总分固定 10，五阶段权重固定为 2/2/3/2/1 |
| Step 4.8 难度自校准 | 本地计算 `difficulty_score`，与 Stage 2 规划不一致时记入 remarks，留给 Stage 5 裁决 |
| Step 4.9 输出题目集 | 写入 `04_tests.md` 和 `stage4_items.jsonl` |

每道 item 的核心结构：

```json
{
  "test_id": "TEST-001",
  "difficulty": "advanced",
  "difficulty_score": 2.33,
  "prompt": "...",
  "reference": {
    "define": {},
    "decompose": {},
    "plan": {},
    "execute": {},
    "metacognition": {}
  },
  "rubric": {
    "total_max_score": 10,
    "stages": [],
    "fatal_deductions": [],
    "veto_items": []
  }
}
```

Stage 4 产出的不是单纯“题目文本”，而是一套可以跑批评测的题目对象：题干、答案模板、证据要求、评分规则、否决项都在同一个 item 内。

## 10. Step 5: 验证与 benchmark 打包

对应文件：

```text
questforge/stage5_finalize.py
```

输出：

```text
05_report.md
dataset.json
dataset.xlsx
traceability.json
dataset_supplementary/
```

设计目标：Stage 5 不再调用 LLM，而是对 Stage 4 的题目集做本地验证、覆盖矩阵对齐、区分度估计、独立性检查和最终数据集导出。

| 子步骤 | 设计 |
|---|---|
| Step 5.1 读取全链路 artifacts | 读取 Stage 1-4 的 artifacts，用于验证和溯源 |
| Step 5.2 5 设计原则验证 | 每道题检查真实性、闭环性、可量化、区分度、预测力 |
| Step 5.3 覆盖矩阵对齐 | 将 Stage 4 实际 reference/rubric 覆盖情况与 Stage 2 蓝图对比 |
| Step 5.4 盲区识别 | 对覆盖不足的阶段生成 high/medium/low 盲区 |
| Step 5.5 先验区分度估计 | 基于约束密度、干扰设计、跨资产整合、难度等估算题目区分度 |
| Step 5.6 独立性评分 | 计算题目之间资产、关键词、流程步骤重合度，要求 `independence_score >= 0.5` |
| Step 5.7 traceability 构建 | 将 test item 回链到业务流程、用户画像、功能、知识资产、fragment |
| Step 5.8 dataset.json 导出 | 输出标准 JSON 数据集 |
| Step 5.9 dataset.xlsx 导出 | 输出兼容人工查看/纪检样例格式的 Excel |
| Step 5.10 最终门禁 | 所有 TEST passed、无 high 盲区、独立性达标、JSON/XLSX 结构校验通过 |

最终 JSON 顶层结构：

```json
{
  "dataset_meta": {},
  "coverage_matrix": {},
  "items": []
}
```

Excel workbook 固定包含 4 个 sheet：

| Sheet | 内容 |
|---|---|
| `主表` | 兼容样例格式的题目主数据，核心列为 `问题/答案/实际答案/来源文档/来源片段/标记结果/结果` |
| `评分细则` | 每道题五阶段 rubric、分值、证据类型 |
| `约束干扰` | constraints、interferences、trap 标记和验证来源 |
| `元信息` | 数据集版本、领域、题目数、难度分布、创建时间 |

## 11. 已验证样例结果

当前仓库里可参考的完整运行目录：

```text
questforge/datasets/pipeline_run_review_20260426_stage5_benchmark_v2/
```

该目录包含：

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
dataset_supplementary/
stage3_fragments.jsonl
stage3_inverted_index.json
stage4_items.jsonl
```

其中 `05_report.md` 显示：

| 指标 | 结果 |
|---|---|
| Stage 5 `pass_gate` | true |
| 题目数 | 3 |
| 5 设计原则通过数 | 3/3 |
| 覆盖矩阵 high/medium/low 问题 | 0/0/0 |
| 先验区分度 | 2 道优秀，1 道待改进 |
| 独立性评分 | 0.83 |

这说明当前主链路已经能从纪检示例输入跑到最终 benchmark 包。

## 12. 运行方式

默认运行纪检示例：

```bash
python -m questforge.run_pipeline
```

指定输入、run id 和输出目录：

```bash
python -m questforge.run_pipeline \
  --input-json datasets/test_agent_2/example_input.json \
  --run-id demo \
  --out /tmp/questforge_demo
```

断点续跑某一阶段：

```bash
python -m questforge.run_pipeline \
  --input-json datasets/test_agent_2/example_input.json \
  --only stage4
```

退出码含义：

| 退出码 | 含义 |
|---|---|
| 0 | 正常完成 |
| 1 | 通用异常或 Stage 5 最终验收失败 |
| 2 | `MissingInputError`，需要按提示补输入后续跑 |

## 13. 当前边界与后续可优化点

| 边界 | 说明 |
|---|---|
| 输入通道 | 当前完整实现是 `design_doc` 通道；GUI、code、user_log 仍是输入契约层面的占位 |
| 测试工程 | 仓库没有 pyproject、Makefile、正式测试 runner，主要靠端到端 pipeline 运行验证 |
| LLM 依赖 | Stage 1、Stage 3、Stage 4 必须有 LLM；Stage 2 在无 `business_processes` 时也必须有 LLM |
| 领域迁移 | 代码保持领域无关，但换领域时必须补 `business_goal`、数据资产、glossary_seed、weak_points 或流程定义 |
| 题目独立性 | Stage 5 会卡 `independence_score`，资产重复使用过多会导致最终失败，需要回 Stage 3 或 Stage 2 调整 |

## 14. 一句话总结

QuestForge 的路线是：先把业务目标、用户、功能和知识资产变成稳定认知，再从认知中抽取业务流程和题目骨架，然后把题目骨架绑定到真实数据片段，生成带五阶段期望和评分细则的完整题目，最后用本地验证器打包成可跑批的 benchmark 数据集。它的关键不是某一次 LLM 出题，而是每个阶段都有可审计的 MD 产物、结构化 JSON 契约和 pass_gate 门禁。
