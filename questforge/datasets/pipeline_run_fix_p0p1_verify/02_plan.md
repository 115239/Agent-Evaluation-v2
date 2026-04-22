---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-22T01:09:57+08:00
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
| BP-001 | 定性量纪建议生成与法规依据校验 | 案件研判 | UG-001 | 3 | 决策建议 | True |
| BP-002 | 总书记讲话精准支撑政策阐释 | 知识咨询 | UG-003 | 3 | 结构化条款 | True |
| BP-003 | 报批表（谈话方案及安全预案）多维合规审核 | 审核复核 | UG-002 | 4 | 决策建议 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 3 | 审核复核、案件研判、知识咨询 |
| outputs.category | 2 | 决策建议、结构化条款 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 案件研判-跨文档类 | BP-001 | BP-001 | 0.46 | advanced |
| PT-002 | 知识咨询-单文档类 | BP-002 | BP-002 | 0.31 | basic |
| PT-003 | 审核复核-跨文档类 | BP-003 | BP-003 | 0.52 | advanced |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | advanced | 拆解问题、方案生成 |
| TEST-002 | PT-001 | BP-001 | advanced | 定义问题、方案生成 |
| TEST-003 | PT-002 | BP-002 | basic | 定义问题 |
| TEST-004 | PT-002 | BP-002 | basic | 执行落地 |
| TEST-005 | PT-003 | BP-003 | advanced | 定义问题、方案生成 |
| TEST-006 | PT-003 | BP-003 | advanced | 拆解问题、执行落地 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 常规 | 重点 | 重点 | 常规 | 常规 |
| TEST-002 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-003 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-004 | 常规 | 常规 | 常规 | 重点 | 常规 |
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
      "name": "定性量纪建议生成与法规依据校验",
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
          "description": "收到线索初核报告后需拟制党纪处分建议"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入案件要素（如违纪行为、从宽/从严情节、岗位性质）发起实务案例类比推理"
        },
        {
          "no": 2,
          "name": "基于初步定性，调用党纪法规语义检索匹配具体条款及要点词"
        },
        {
          "no": 3,
          "name": "将拟制的定性量纪建议段落送入纪检文书智能纠错模块进行依据一致性与表述合规性校验"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪建议终稿",
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
      "id": "BP-002",
      "name": "总书记讲话精准支撑政策阐释",
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
          "description": "为起草理论阐释材料或答复下级咨询，需权威讲话原文支撑"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入主题词（如'政治监督具体化常态化'）触发总书记讲话精准召回"
        },
        {
          "no": 2,
          "name": "筛选匹配结果中发布时间最近、主题最聚焦的3篇讲话，提取关键段落"
        },
        {
          "no": 3,
          "name": "结合理论文章观点支撑检索结果，交叉验证并生成带出处标注的政策阐释要点"
        }
      ],
      "outputs": [
        {
          "name": "政策阐释要点清单",
          "category": "结构化条款"
        }
      ],
      "depends_on": [
        "KB-003",
        "KB-004"
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "报批表（谈话方案及安全预案）多维合规审核",
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
          "description": "对审查调查组提交的谈话方案及安全预案开展形式与实质审核"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "上传报批表全文，启动纪检文书智能纠错，识别表达歧义、安全风险表述缺失、程序依据过时等问题"
        },
        {
          "no": 2,
          "name": "针对纠错提示中涉及的‘四种形态’适用、‘谈话函询’程序条款等，自动关联党纪法规语义检索获取最新条款原文"
        },
        {
          "no": 3,
          "name": "调取同类已审结案件中的实务问答，比对当前方案中风险等级判定、审批权限设置是否符合口径"
        },
        {
          "no": 4,
          "name": "整合纠错建议、法规条款、实务口径，生成带修订痕迹与依据索引的审核反馈意见"
        }
      ],
      "outputs": [
        {
          "name": "审核反馈意见",
          "category": "决策建议"
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
      "name": "案件研判-跨文档类",
      "members": [
        "BP-001"
      ],
      "representative": "BP-001",
      "complexity_score": 0.46,
      "assigned_difficulty": "advanced"
    },
    {
      "type_id": "PT-002",
      "name": "知识咨询-单文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.31,
      "assigned_difficulty": "basic"
    },
    {
      "type_id": "PT-003",
      "name": "审核复核-跨文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.52,
      "assigned_difficulty": "advanced"
    }
  ],
  "test_plan": [
    {
      "test_id": "TEST-001",
      "process_type": "PT-001",
      "source_process": "BP-001",
      "difficulty": "advanced",
      "focus_stages": [
        "拆解问题",
        "方案生成"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-002",
      "process_type": "PT-001",
      "source_process": "BP-001",
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "sample_idx": 1
    },
    {
      "test_id": "TEST-003",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "basic",
      "focus_stages": [
        "定义问题"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-004",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "basic",
      "focus_stages": [
        "执行落地"
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
      "定义问题": "常规",
      "拆解问题": "重点",
      "方案生成": "重点",
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
    },
    "TEST-004": {
      "定义问题": "常规",
      "拆解问题": "常规",
      "方案生成": "常规",
      "执行落地": "重点",
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
