---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-23T13:17:10+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 3 条业务流程(LLM 推导);按'触发×跨流程×输出×管理层'组合聚类为 3 个类型,每类采样 2 题,共规划 6 道:2 basic、4 advanced、0 expert。第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ✗ | 走 LLM 推导 |
| capability_scope.weak_points | ✗ | Stage 3 是否触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 党纪法规语义检索支撑定性量纪建议 | 知识咨询 | UG-001 | 3 | 结构化条款 | True |
| BP-002 | 实务案例问答匹配驱动定性量纪智能建议 | 案件研判 | UG-001 | 3 | 决策建议 | True |
| BP-003 | 纪检文书纠错辅助与多源知识协同审核 | 审核复核 | UG-002 | 4 | 故障清单 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 3 | 审核复核、案件研判、知识咨询 |
| outputs.category | 4 | 决策建议、故障清单、结构化文档、结构化条款 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001 | BP-001 | 0.31 | basic |
| PT-002 | 案件研判-跨文档类 | BP-002 | BP-002 | 0.46 | advanced |
| PT-003 | 审核复核-跨文档类 | BP-003 | BP-003 | 0.66 | advanced |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-001 | BP-001 | basic | 执行落地 |
| TEST-003 | PT-002 | BP-002 | advanced | 拆解问题、方案生成 |
| TEST-004 | PT-002 | BP-002 | advanced | 定义问题、方案生成 |
| TEST-005 | PT-003 | BP-003 | advanced | 定义问题、方案生成 |
| TEST-006 | PT-003 | BP-003 | advanced | 拆解问题、执行落地 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 常规 | 常规 | 常规 | 重点 | 常规 |
| TEST-003 | 常规 | 重点 | 重点 | 常规 | 常规 |
| TEST-004 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-005 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-006 | 常规 | 重点 | 常规 | 重点 | 常规 |

## 结构化数据
```json
{
  "fallback_status": {
    "business_processes_present": false,
    "capability_scope_present": false,
    "llm_path_taken": true
  },
  "processes": [
    {
      "id": "BP-001",
      "name": "党纪法规语义检索支撑定性量纪建议",
      "actors": [
        {
          "id": "UG-001",
          "role": "一线纪检监察员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "知识咨询",
          "description": "纪检监察员输入自然语言问题，如'收受可能影响公正执行公务的财物如何定性？'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "解析用户问题中的违纪行为要素、纪律类型（如廉洁纪律）及情节关键词"
        },
        {
          "no": 2,
          "name": "在党纪条款库（KB-001）中进行语义匹配，召回匹配度最高的3条条款及要点词"
        },
        {
          "no": 3,
          "name": "生成结构化输出：条款原文+违纪行为描述+关联条文链接，并标注适用情形说明"
        }
      ],
      "outputs": [
        {
          "name": "党纪条款匹配报告",
          "category": "结构化条款"
        }
      ],
      "depends_on": [
        "KB-001"
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "实务案例问答匹配驱动定性量纪智能建议",
      "actors": [
        {
          "id": "UG-001",
          "role": "一线纪检监察员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "案件研判",
          "description": "纪检监察员提交违纪事实简述（含主体、行为、情节、后果等要素）"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "提取事实简述中的关键实体（如‘主动交代’‘同案人’）与行为模式"
        },
        {
          "no": 2,
          "name": "在实务问答库（KB-002）中检索相似问题及标准答案，同步调用党纪条款库（KB-001）校验处分档次逻辑"
        },
        {
          "no": 3,
          "name": "融合检索结果生成定性建议：推荐条款、行为定性、从宽/从严识别、处分档次及依据链"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪综合建议",
          "category": "决策建议"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002"
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "纪检文书纠错辅助与多源知识协同审核",
      "actors": [
        {
          "id": "UG-002",
          "role": "案件审理人员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "审核复核",
          "description": "案件审理人员上传待审报批表或处理意见函文本"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "对文书进行格式合规性初筛（如标题、签发栏、附件标识）"
        },
        {
          "no": 2,
          "name": "调用党纪条款库（KB-001）校验引用条款有效性，调用实务问答库（KB-002）验证定性结论一致性"
        },
        {
          "no": 3,
          "name": "识别并标记四类问题：表达不规范、依据引用错误、处分档次不匹配、口径不一致，附修正建议与知识锚点"
        },
        {
          "no": 4,
          "name": "生成带可点击知识溯源的修订版文书与问题清单"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错分析报告",
          "category": "故障清单"
        },
        {
          "name": "知识锚定修订版文书",
          "category": "结构化文档"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002"
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    }
  ],
  "dimensions": {
    "trigger.type": [
      "审核复核",
      "案件研判",
      "知识咨询"
    ],
    "outputs.category": [
      "决策建议",
      "故障清单",
      "结构化文档",
      "结构化条款"
    ],
    "actors.level": [
      "业务"
    ],
    "cross_process_dependency": [
      "单流程",
      "跨流程"
    ]
  },
  "effective_dimensions": [
    "trigger.type",
    "outputs.category",
    "cross_process_dependency"
  ],
  "process_types": [
    {
      "type_id": "PT-001",
      "name": "知识咨询-单文档类",
      "members": [
        "BP-001"
      ],
      "representative": "BP-001",
      "complexity_score": 0.31,
      "assigned_difficulty": "basic"
    },
    {
      "type_id": "PT-002",
      "name": "案件研判-跨文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.46,
      "assigned_difficulty": "advanced"
    },
    {
      "type_id": "PT-003",
      "name": "审核复核-跨文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.66,
      "assigned_difficulty": "advanced"
    }
  ],
  "test_plan": [
    {
      "test_id": "TEST-001",
      "process_type": "PT-001",
      "source_process": "BP-001",
      "difficulty": "basic",
      "focus_stages": [
        "定义问题"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-002",
      "process_type": "PT-001",
      "source_process": "BP-001",
      "difficulty": "basic",
      "focus_stages": [
        "执行落地"
      ],
      "sample_idx": 1
    },
    {
      "test_id": "TEST-003",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "advanced",
      "focus_stages": [
        "拆解问题",
        "方案生成"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-004",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "sample_idx": 1
    },
    {
      "test_id": "TEST-005",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-006",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "advanced",
      "focus_stages": [
        "拆解问题",
        "执行落地"
      ],
      "sample_idx": 1
    }
  ],
  "coverage_matrix_plan": {
    "TEST-001": {
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "常规",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-002": {
      "定义问题": "常规",
      "拆解问题": "常规",
      "方案生成": "常规",
      "执行落地": "重点",
      "元认知": "常规"
    },
    "TEST-003": {
      "定义问题": "常规",
      "拆解问题": "重点",
      "方案生成": "重点",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-004": {
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "重点",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-005": {
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "重点",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-006": {
      "定义问题": "常规",
      "拆解问题": "重点",
      "方案生成": "常规",
      "执行落地": "重点",
      "元认知": "常规"
    }
  }
}
```

## 下一阶段校验清单
- [x] 每条 BP ≥ 3 个步骤(共 3 条 BP)
- [x] 触发类型取值来自预设词表或 Stage 1 glossary
- [x] test_plan 题目数 = 类型数×每类采样数(3×2=6 vs 6)
- [x] 覆盖矩阵蓝图中每道题至少 1 个'重点'阶段
- [x] test_plan 非空

## 备注与遗留问题
- 业务流程由 LLM 推导(第一层 Fallback)
