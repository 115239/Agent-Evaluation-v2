# QuestForge - AI Agent Evaluation Pipeline

五阶段评测数据集生成流水线：输入业务 PRD/设计文档 + 业务数据（xlsx），输出可用于评测业务 AI 系统的完整测试数据集。

## 工作原理

采用**五阶段心智模型**，从抽象到具体逐步落地：

```
原始文档 → Stage 1 认知表 → Stage 2 题目骨架 → Stage 3 知识绑定 → Stage 4 完整题目 → Stage 5 可执行数据集
```

| 阶段 | 职责 | 产物 |
|------|------|------|
| Phase 0 | 输入完整性体检 + 质量打分 | `00_input_assessment.md` |
| Stage 1 | 扫描资产，构建业务认知五表（目标/用户/功能/知识资产/术语） | `01_understanding.md` |
| Stage 2 | 流程提取 → 动态分类 → 聚类 → 难度梯度 → 覆盖矩阵蓝图 | `02_plan.md` |
| Stage 3 | 加载 xlsx 建 Fragment 索引，按难度匹配资产/约束/干扰 | `03_context.md` + `stage3_fragments.jsonl` |
| Stage 4 | 基于 Stage 3 生成完整题目、五阶段期望行为与评分细则 | `04_tests.md` + `stage4_items.jsonl` |
| Stage 5 | 本地验证 + 覆盖矩阵对齐 + 最终打包 | `dataset.json` + `dataset.xlsx` + `traceability.json` |

每个阶段只产出一份 MD 文件，下一阶段只消费上一阶段的 MD —— **阶段产物是唯一契约**。

## 快速开始

### 环境要求

- Python 3.10+
- 依赖：`openpyxl`, `openai`, `pandas`, `tqdm`, `jieba`（可选）

### 配置

复制 `.env.example` 为 `.env` 并填入 LLM 凭证：

```bash
cp .env.example .env
```

```env
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
LLM_API_KEY=sk-your-api-key
```

支持任何 OpenAI 兼容的 LLM 端点（阿里云 DashScope、DeepSeek、OpenRouter 等）。

### 运行

```bash
# 跑通完整流水线（使用内置示例输入）
python -m questforge.run_pipeline

# 指定自定义输入与产物目录
python -m questforge.run_pipeline --input-json datasets/test/xxx/input.json --run-id demo --out /tmp/out

# 单阶段断点续跑
python -m questforge.run_pipeline --only stage2 --input-json <path>
```

## 项目结构

```
questforge/
├── run_pipeline.py          # 流水线入口 & CLI
├── config.py                # 环境变量配置
├── input_spec.py            # AgentInput 数据类
├── common.py                # ID 生成、MD 读写等通用工具
├── io_utils.py              # KBFragment、关键字提取、倒排索引
├── llm_client.py            # OpenAI 兼容 LLM 客户端
├── phase0_preprocess.py     # Phase 0 输入预处理
├── stage1_understanding.py  # Stage 1 业务理解
├── stage2_plan.py           # Stage 2 题目规划
├── stage3_context.py        # Stage 3 知识绑定
├── stage4_questions.py      # Stage 4 题目生成
├── stage5_finalize.py       # Stage 5 验证与打包
└── prompts/                 # 各阶段 system prompt

datasets/
├── test_agent_2/            # 纪检场景示例输入
│   ├── example_input.json
│   └── 纪检项目业务数据+样例数据/
└── test/                    # 安监场景测试资料

data/                        # 设计文档、PPT 等参考资料
```

## 设计特点

- **领域无关**：框架不预设业务词汇，领域术语由 Stage 1 的 glossary 动态注入
- **pass_gate 门禁**：每个阶段产物含 `pass_gate: true/false`，未通过不进入下一阶段
- **不做本地兜底**：LLM 输出缺失时抛出明确异常，提示用户用 `--only stageN` 补跑
- **单一初始 commit，无历史泄漏**
