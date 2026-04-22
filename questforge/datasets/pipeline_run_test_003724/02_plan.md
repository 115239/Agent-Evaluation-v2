---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-22T00:38:13+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 3 条业务流程(LLM 推导);按'触发-跨流程'组合聚类为 3 个类型,规划 3 道题:1 basic、1 advanced、1 expert。第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ✗ | 走 LLM 推导 |
| capability_scope.weak_points | ✗ | Stage 3 是否触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 党纪法规语义检索支撑定性量纪决策 | 知识咨询 | UG-001 | 3 | 决策建议 | True |
| BP-002 | 审查调查文书全流程智能纠错与合规复核 | 审核复核 | UG-002 | 4 | 结构化条款 | True |
| BP-003 | 总书记讲话与理论文章联合检索支撑政策研判 | 知识咨询 | UG-003 | 5 | 对比分析 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 2 | 审核复核、知识咨询 |
| outputs.category | 4 | 决策建议、对比分析、操作指令、结构化条款 |
| actors.level | 2 | 业务、管理 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001 | BP-001 | 0.31 | basic |
| PT-002 | 审核复核-单文档类 | BP-002 | BP-002 | 0.51 | advanced |
| PT-003 | 知识咨询-跨文档类 | BP-003 | BP-003 | 0.85 | expert |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-002 | BP-002 | advanced | 定义问题 |
| TEST-003 | PT-003 | BP-003 | expert | 定义问题、拆解问题、方案生成、执行落地、元认知 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-003 | 重点 | 重点 | 重点 | 重点 | 重点 |

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
      "name": "党纪法规语义检索支撑定性量纪决策",
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
          "description": "纪检监察员输入自然语言问题，如'收受可能影响公正执行公务的财物如何定性'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "解析用户查询意图，识别核心违纪行为与纪律类型关键词"
        },
        {
          "no": 2,
          "name": "在结构化条款库（KB-001）中进行语义匹配，召回高置信度条款及关联条文"
        },
        {
          "no": 3,
          "name": "聚合匹配结果生成定性建议初稿，标注要点词、行为要件与适用条款"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪建议初稿",
          "category": "决策建议"
        }
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "审查调查文书全流程智能纠错与合规复核",
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
          "description": "对提交的谈话方案、安全预案、处理意见函等报批类文书启动合规性审查"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "加载待审文书全文，识别文档类型与关键字段（如谈话对象、风险等级、处分依据）"
        },
        {
          "no": 2,
          "name": "并行调用法规条款库（KB-001）与实务问答库（KB-002），检测表达歧义、依据过时、口径不一致、处分档次不当四类错误"
        },
        {
          "no": 3,
          "name": "生成带定位标记的纠错报告，嵌入修正建议及对应法规/案例原文片段"
        },
        {
          "no": 4,
          "name": "输出结构化修正指令供文书起草人回溯修改"
        }
      ],
      "outputs": [
        {
          "name": "带定位标记的纠错报告",
          "category": "结构化条款"
        },
        {
          "name": "结构化修正指令",
          "category": "操作指令"
        }
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "总书记讲话与理论文章联合检索支撑政策研判",
      "actors": [
        {
          "id": "UG-003",
          "role": "政策研究与法规指导人员",
          "level": "管理"
        }
      ],
      "triggers": [
        {
          "type": "知识咨询",
          "description": "输入政策概念或讲话片段，如'健全全面从严治党体系'或'自我革命'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "拆解查询语义，区分政策表述型（匹配KB-004）与讲话引用型（匹配KB-003）"
        },
        {
          "no": 2,
          "name": "跨知识库并行检索，对匹配结果按主题一致性、时效性、权威性加权排序"
        },
        {
          "no": 3,
          "name": "生成对比摘要：讲话上下文段落 vs 理论文章核心观点，标注差异与演进脉络"
        },
        {
          "no": 4,
          "name": "输出政策适用提示，包括最新提法、禁用表述、配套解读路径"
        },
        {
          "no": 5,
          "name": "归档检索日志与研判结论至政策知识图谱更新队列"
        }
      ],
      "outputs": [
        {
          "name": "政策对比摘要",
          "category": "对比分析"
        },
        {
          "name": "政策适用提示",
          "category": "决策建议"
        },
        {
          "name": "知识图谱更新指令",
          "category": "操作指令"
        }
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    }
  ],
  "dimensions": {
    "trigger.type": [
      "审核复核",
      "知识咨询"
    ],
    "outputs.category": [
      "决策建议",
      "对比分析",
      "操作指令",
      "结构化条款"
    ],
    "actors.level": [
      "业务",
      "管理"
    ],
    "cross_process_dependency": [
      "单流程",
      "跨流程"
    ]
  },
  "effective_dimensions": [
    "trigger.type",
    "outputs.category",
    "actors.level",
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
      "name": "审核复核-单文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.51,
      "assigned_difficulty": "advanced"
    },
    {
      "type_id": "PT-003",
      "name": "知识咨询-跨文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.85,
      "assigned_difficulty": "expert"
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
      ]
    },
    {
      "test_id": "TEST-002",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题"
      ]
    },
    {
      "test_id": "TEST-003",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "expert",
      "focus_stages": [
        "定义问题",
        "拆解问题",
        "方案生成",
        "执行落地",
        "元认知"
      ]
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
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "常规",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-003": {
      "定义问题": "重点",
      "拆解问题": "重点",
      "方案生成": "重点",
      "执行落地": "重点",
      "元认知": "重点"
    }
  }
}
```

## 下一阶段校验清单
- [x] 每条 BP ≥ 3 个步骤(共 3 条 BP)
- [x] 触发类型取值来自预设词表或 Stage 1 glossary
- [x] 聚类后的类型数 = test_plan 题目数(3 vs 3)
- [x] 覆盖矩阵蓝图中每道题至少 1 个'重点'阶段
- [x] test_plan 非空

## 备注与遗留问题
- 业务流程由 LLM 推导(第一层 Fallback)
