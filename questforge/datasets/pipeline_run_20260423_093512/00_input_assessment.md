---
stage: 0
stage_name: input_assessment
version: 1.0
upstream: AgentInput(用户提供)
downstream: 01_understanding.md
domain: 纪检材料智能审查
created_at: 2026-04-23T09:35:13+08:00
created_by: agent-phase0
pass_gate: true
---

# Phase 0 · 输入预处理

## 摘要
通道 = `design_doc`。
完整性 8/8 通过,质量评分 1.0(0-1)。
推荐策略:derive(源文档无 business_processes,Stage 2 触发第一层 Fallback,由 LLM 推导)。
✅ 输入满足最小要求,可进入 Stage 1。

## 完整性检查
| 项 | 状态 |
|---|---|
| source_channel ∈ {design_doc, gui, code, user_log} | ✓ |
| source_channel 已在当前 Pipeline 实现(design_doc) | ✓ |
| business_goal 一句话业务目标(≥10 字) | ✓ |
| domain 业务领域名 | ✓ |
| data_dir 业务数据资产目录存在 | ✓ |
| data_dir 至少含 1 个资产文件(xlsx/docx/csv) | ✓ |
| docs_dir(若提供)应为目录 | ✓ |
| samples 所声明的文件均存在 | ✓ |

## 质量评分明细
| 维度 | 贡献 |
|---|---|
| business_goal 字数 ≥ 20 | +0.30 |
| data_dir 资产数 ≥ 2 | +0.30(4 个) |
| samples 非空 | +0.20 |
| glossary_seed ≥ 3 条 | +0.20 |

## 资产扫描
| 文件 | 扩展名 |
|---|---|
| 党纪法规.xlsx | .xlsx |
| 实务测试集.xlsx | .xlsx |
| 总书记讲话.xlsx | .xlsx |
| 理论文章.xlsx | .xlsx |

## 推荐策略
**derive(源文档无 business_processes,Stage 2 触发第一层 Fallback,由 LLM 推导)**

## 补充建议
- 未提供 `business_processes`。Stage 2 将由 LLM 推导流程;若有现成的流程定义,建议提供以避免 LLM 幻觉。
- 未提供 `weak_points`(能力边界/已知短板)。Stage 3 将通过流程特性推导约束;若有明确短板(如'版本区分/权限边界'),建议提供,可显著提升题目靶向性。
- 未提供 `docs_dir`(PRD/架构文档目录)。Stage 1 将仅从 business_goal + 资产列头推导用户画像与功能;有 PRD 则更精确。
- 未指定 `out_dir`,默认使用 /Users/sin/Documents/Data/ccic/0418_智能体评测实现/questforge/datasets/pipeline_run_20260423_093512。

## 结构化数据
```json
{
  "agent_input": {
    "source_channel": "design_doc",
    "business_goal": "为纪检监察员提供党纪法规、总书记讲话、理论文章、实务案例的 AI 语义检索与文书纠错辅助",
    "domain": "纪检材料智能审查",
    "docs_dir": null,
    "data_dir": "/Users/sin/Documents/Data/ccic/0418_智能体评测实现/datasets/test_agent_2/纪检项目业务数据+样例数据/纪检项目业务数据+样例数据/业务数据",
    "samples": [
      {
        "label": "retrieval_usecase",
        "file": "/Users/sin/Documents/Data/ccic/0418_智能体评测实现/datasets/test_agent_2/纪检项目业务数据+样例数据/纪检项目业务数据+样例数据/样例数据/AI测试-语义和定性量纪检索用例.xlsx",
        "sheet": "Sheet1",
        "category_col": "样例类别",
        "content_col": "样例内容",
        "columns": []
      },
      {
        "label": "doc_correction",
        "file": "/Users/sin/Documents/Data/ccic/0418_智能体评测实现/datasets/test_agent_2/纪检项目业务数据+样例数据/纪检项目业务数据+样例数据/样例数据/文书纠错样例.xlsx",
        "sheet": "Sheet1",
        "category_col": null,
        "content_col": null,
        "columns": [
          "测试文书",
          "测试样例",
          "纠正答案"
        ]
      }
    ],
    "glossary_seed": {
      "八项规定": "中央八项规定精神,聚焦公务接待、差旅、公款消费等纪律要求",
      "四种形态": "监督执纪的四种递进形态(红脸出汗—轻处分—重处分—立案审查)",
      "定性量纪": "对违纪行为进行定性并决定处分档次",
      "从宽情节": "主动交代、配合调查、退赔挽损等可以从轻从宽的情节",
      "从严情节": "对抗组织审查、隐瞒不报、转移赃款等应当从重从严的情节",
      "廉洁纪律": "党员干部在廉洁从政方面必须遵守的纪律要求",
      "政治纪律": "维护党中央权威和集中统一领导的纪律",
      "工作纪律": "履行岗位职责、遵守工作规程的纪律",
      "党纪处分": "对违纪党员作出的处分,含警告、严重警告、撤销党内职务、留党察看、开除党籍",
      "审查调查": "纪检监察机关对涉嫌违纪违法党员干部的调查核实",
      "谈话函询": "党组织对党员干部反映问题的沟通方式",
      "文书纠错": "对纪检文书中表达、依据、口径等错误进行识别与修正"
    },
    "weak_points": [],
    "business_processes": [],
    "out_dir": null
  },
  "completeness": {
    "source_channel ∈ {design_doc, gui, code, user_log}": true,
    "source_channel 已在当前 Pipeline 实现(design_doc)": true,
    "business_goal 一句话业务目标(≥10 字)": true,
    "domain 业务领域名": true,
    "data_dir 业务数据资产目录存在": true,
    "data_dir 至少含 1 个资产文件(xlsx/docx/csv)": true,
    "docs_dir(若提供)应为目录": true,
    "samples 所声明的文件均存在": true
  },
  "quality_score": 1.0,
  "recommended_strategy": "derive(源文档无 business_processes,Stage 2 触发第一层 Fallback,由 LLM 推导)",
  "suggestions": [
    "未提供 `business_processes`。Stage 2 将由 LLM 推导流程;若有现成的流程定义,建议提供以避免 LLM 幻觉。",
    "未提供 `weak_points`(能力边界/已知短板)。Stage 3 将通过流程特性推导约束;若有明确短板(如'版本区分/权限边界'),建议提供,可显著提升题目靶向性。",
    "未提供 `docs_dir`(PRD/架构文档目录)。Stage 1 将仅从 business_goal + 资产列头推导用户画像与功能;有 PRD 则更精确。",
    "未指定 `out_dir`,默认使用 /Users/sin/Documents/Data/ccic/0418_智能体评测实现/questforge/datasets/pipeline_run_20260423_093512。"
  ],
  "missing_required": []
}
```

## 下一阶段校验清单
- [x] source_channel ∈ {design_doc, gui, code, user_log}
- [x] source_channel 已在当前 Pipeline 实现(design_doc)
- [x] business_goal 一句话业务目标(≥10 字)
- [x] domain 业务领域名
- [x] data_dir 业务数据资产目录存在
- [x] data_dir 至少含 1 个资产文件(xlsx/docx/csv)
- [x] docs_dir(若提供)应为目录
- [x] samples 所声明的文件均存在

## 备注与遗留问题
(无)
