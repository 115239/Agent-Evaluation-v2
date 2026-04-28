---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-23T20:40:39+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 3 条业务流程(LLM 推导);按'触发×跨流程×输出×管理层'组合聚类为 3 个类型,按类型多样性实际规划 3 道(单类最多 2 道):2 basic、1 advanced、0 expert。第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ✗ | 走 LLM 推导 |
| capability_scope.weak_points | ✗ | Stage 3 是否触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 党纪法规语义检索支撑定性量纪建议生成 | 知识咨询 | UG-001 | 3 | 结构化条款 | True |
| BP-002 | 纪检文书智能纠错与依据闭环验证 | 审核复核 | UG-001+UG-002 | 4 | 决策建议 | True |
| BP-003 | 总书记讲话精准召回支撑政策阐释与理论引用 | 知识咨询 | UG-003 | 3 | 讲话摘要+上下文 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 2 | 审核复核、知识咨询 |
| outputs.category | 3 | 决策建议、结构化条款、讲话摘要+上下文 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 | 规划题数 |
|---|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001 | BP-001 | 0.31 | basic | 1 |
| PT-002 | 审核复核-跨文档类 | BP-002 | BP-002 | 0.52 | advanced | 1 |
| PT-003 | 知识咨询-单文档类 | BP-003 | BP-003 | 0.31 | basic | 1 |

## 题目规划
| 题号 | 流程类型 | 来源流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-002 | BP-002 | advanced | 定义问题、方案生成 |
| TEST-003 | PT-003 | BP-003 | basic | 定义问题 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-003 | 重点 | 常规 | 常规 | 常规 | 常规 |

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
      "name": "党纪法规语义检索支撑定性量纪建议生成",
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
          "description": "一线纪检监察员在拟制定性量纪建议时，需快速定位适用党纪条款及违纪行为要点"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入自然语言问题（如'收受可能影响公正执行公务的财物如何定性'）或关键词组合"
        },
        {
          "no": 2,
          "name": "系统基于KB-001进行语义匹配与相关度排序，提取要点词、违纪行为及原文上下文片段"
        },
        {
          "no": 3,
          "name": "返回结构化条款结果，供纪检监察员嵌入定性量纪建议初稿"
        }
      ],
      "outputs": [
        {
          "name": "匹配党纪条款集",
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
      "name": "纪检文书智能纠错与依据闭环验证",
      "actors": [
        {
          "id": "UG-001",
          "role": "一线纪检监察员",
          "level": "业务"
        },
        {
          "id": "UG-002",
          "role": "案件审理人员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "审核复核",
          "description": "案件审理人员对一线提交的报批表、函件等文书开展合规性审查时触发纠错需求"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "上传待审纪检文书文本（如谈话方案及安全预案）"
        },
        {
          "no": 2,
          "name": "系统联合KB-001（条款）、KB-002（实务问答）、KB-003（讲话）进行多源依据比对与错误标注"
        },
        {
          "no": 3,
          "name": "生成含错误类型、修正建议及对应法规/讲话/实务依据的纠错报告"
        },
        {
          "no": 4,
          "name": "审理人员依据报告反馈修改意见，纪检监察员完成修订并重新提交"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错报告",
          "category": "决策建议"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002",
        "KB-003"
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "总书记讲话精准召回支撑政策阐释与理论引用",
      "actors": [
        {
          "id": "UG-003",
          "role": "政策研究与法规指导人员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "知识咨询",
          "description": "政策研究人员为撰写理论阐释材料或答复基层咨询，需精准定位总书记相关讲话原文及上下文"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入主题词（如'自我革命'）或模糊语义查询（如'新时代全面从严治党根本遵循'）"
        },
        {
          "no": 2,
          "name": "系统基于KB-003进行时间加权与主题聚类召回，提取标题、发布时间、关键段落及摘要"
        },
        {
          "no": 3,
          "name": "输出可直接引用的讲话片段，并标记政治语境适配性提示（如'适用于警示教育场景'）"
        }
      ],
      "outputs": [
        {
          "name": "精准讲话引用包",
          "category": "讲话摘要+上下文"
        }
      ],
      "depends_on": [
        "KB-003"
      ],
      "cross_process_dependency": "单流程",
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
      "结构化条款",
      "讲话摘要+上下文"
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
      "assigned_difficulty": "basic",
      "planned_tests": 1
    },
    {
      "type_id": "PT-002",
      "name": "审核复核-跨文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.52,
      "assigned_difficulty": "advanced",
      "planned_tests": 1
    },
    {
      "type_id": "PT-003",
      "name": "知识咨询-单文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.31,
      "assigned_difficulty": "basic",
      "planned_tests": 1
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
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-003",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "basic",
      "focus_stages": [
        "定义问题"
      ],
      "sample_idx": 0
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
      "方案生成": "重点",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-003": {
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "常规",
      "执行落地": "常规",
      "元认知": "常规"
    }
  }
}
```

## 下一阶段校验清单
- [x] 每条 BP ≥ 3 个步骤(共 3 条 BP)
- [x] 触发类型取值来自预设词表或 Stage 1 glossary
- [x] test_plan 题目数与按类型多样性规划一致(3 vs 3)
- [x] 覆盖矩阵蓝图中每道题至少 1 个'重点'阶段
- [x] test_plan 非空

## 备注与遗留问题
- 业务流程由 LLM 推导(第一层 Fallback)
- 以下类型因缺少可拉开独立性的成员流程,未按配置值重复采样:PT-001(1/2)、PT-002(1/2)、PT-003(1/2)
