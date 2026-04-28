---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-26T19:55:35+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 3 条业务流程(LLM 推导);按'触发×跨流程×输出×管理层'组合聚类为 3 个类型,按类型多样性实际规划 3 道(单类最多 2 道):1 basic、2 advanced、0 expert。第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ✗ | 走 LLM 推导 |
| capability_scope.weak_points | ✗ | Stage 3 是否触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 党纪法规语义驱动的定性量纪建议生成 | 知识咨询 | UG-001 | 3 | 决策建议 | True |
| BP-002 | 总书记讲话上下文支撑的文书口径校验 | 审核复核 | UG-002 | 3 | 合规清单 | True |
| BP-003 | 纪检文书全要素智能纠错与依据回溯 | 审核复核 | UG-001+UG-002 | 4 | 结构化条款 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 2 | 审核复核、知识咨询 |
| outputs.category | 3 | 决策建议、合规清单、结构化条款 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 | 规划题数 |
|---|---|---|---|---|---|---|
| PT-001 | 知识咨询-跨文档类 | BP-001 | BP-001 | 0.46 | advanced | 1 |
| PT-002 | 审核复核-单文档类 | BP-002 | BP-002 | 0.31 | basic | 1 |
| PT-003 | 审核复核-跨文档类 | BP-003 | BP-003 | 0.52 | advanced | 1 |

## 题目规划
| 题号 | 流程类型 | 来源流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | advanced | 定义问题、方案生成 |
| TEST-002 | PT-002 | BP-002 | basic | 定义问题 |
| TEST-003 | PT-003 | BP-003 | advanced | 定义问题、方案生成 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-002 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-003 | 重点 | 常规 | 重点 | 常规 | 常规 |

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
      "name": "党纪法规语义驱动的定性量纪建议生成",
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
          "description": "一线纪检监察员输入自然语言问题，如'收受可能影响公正执行公务的财物如何定性'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "解析用户查询中的违纪行为关键词与政治语境（如'收受财物''影响公正执行公务'）"
        },
        {
          "no": 2,
          "name": "在KB-001中进行多粒度语义匹配，检索匹配条款、要点词、序号及权威来源标识"
        },
        {
          "no": 3,
          "name": "融合KB-002实务问答结果，生成含条款引用、从宽/从严情节提示、定性量纪建议的结构化输出"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪建议书",
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
      "name": "总书记讲话上下文支撑的文书口径校验",
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
          "description": "案件审理人员上传报批表(谈话方案及安全预案)，要求核查政治表述与总书记讲话口径一致性"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "提取文书中的政策性表述、政治术语（如'反腐败斗争关系民心这个最大的政治'）"
        },
        {
          "no": 2,
          "name": "调用KB-003进行原文片段比对与上下文溯源，识别出处标题、发布时间、主题标签"
        },
        {
          "no": 3,
          "name": "标记表述偏差位置，输出修正建议及对应讲话原文依据"
        }
      ],
      "outputs": [
        {
          "name": "口径校验报告",
          "category": "合规清单"
        }
      ],
      "depends_on": [
        "KB-003"
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "纪检文书全要素智能纠错与依据回溯",
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
          "description": "对拟提交的审查调查类文书（如谈话方案、立案呈批报告）发起合规性终审纠错"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "对文书全文进行三重校验：表达规范性（语法/术语）、依据准确性（条款引用有效性）、口径一致性（与总书记讲话/理论文章精神）"
        },
        {
          "no": 2,
          "name": "并行调用KB-001（条款）、KB-002（实务问答）、KB-003（讲话）、KB-004（理论摘要）定位错误所涉知识源"
        },
        {
          "no": 3,
          "name": "生成带错误类型标签、位置锚点、修正建议及多源依据链接的交互式纠错视图"
        },
        {
          "no": 4,
          "name": "支持一键导出含修订痕迹与依据索引的正式版文书"
        }
      ],
      "outputs": [
        {
          "name": "纠错修订包",
          "category": "结构化条款"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002",
        "KB-003",
        "KB-004"
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
      "合规清单",
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
      "name": "知识咨询-跨文档类",
      "members": [
        "BP-001"
      ],
      "representative": "BP-001",
      "complexity_score": 0.46,
      "assigned_difficulty": "advanced",
      "planned_tests": 1
    },
    {
      "type_id": "PT-002",
      "name": "审核复核-单文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.31,
      "assigned_difficulty": "basic",
      "planned_tests": 1
    },
    {
      "type_id": "PT-003",
      "name": "审核复核-跨文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.52,
      "assigned_difficulty": "advanced",
      "planned_tests": 1
    }
  ],
  "test_plan": [
    {
      "test_id": "TEST-001",
      "process_type": "PT-001",
      "source_process": "BP-001",
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-002",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "basic",
      "focus_stages": [
        "定义问题"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-003",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "sample_idx": 0
    }
  ],
  "coverage_matrix_plan": {
    "TEST-001": {
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "重点",
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
      "拆解问题": "常规",
      "方案生成": "重点",
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
