---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-21T23:11:29+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 3 条业务流程(LLM 推导);按'触发-跨流程'组合聚类为 3 个类型,规划 3 道题:2 basic、1 advanced、0 expert。第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ✗ | 走 LLM 推导 |
| capability_scope.weak_points | ✗ | Stage 3 是否触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 党纪法规语义检索支撑定性量纪建议 | 知识咨询 | UG-001 | 3 | 结构化条款 | True |
| BP-002 | 纪检文书纠错闭环处理（报批表专项） | 审核复核 | UG-002 | 4 | 修正建议 | True |
| BP-003 | 多源知识协同验证实务问答 | 案件研判 | UG-003 | 4 | 结构化问答 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 3 | 审核复核、案件研判、知识咨询 |
| outputs.category | 3 | 修正建议、结构化条款、结构化问答 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001 | BP-001 | 0.31 | basic |
| PT-002 | 审核复核-单文档类 | BP-002 | BP-002 | 0.37 | basic |
| PT-003 | 案件研判-跨文档类 | BP-003 | BP-003 | 0.52 | advanced |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-002 | BP-002 | basic | 定义问题 |
| TEST-003 | PT-003 | BP-003 | advanced | 拆解问题、方案生成 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-003 | 常规 | 重点 | 重点 | 常规 | 常规 |

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
          "role": "纪检监察员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "知识咨询",
          "description": "纪检监察员在初步核实或审查调查中需对具体违纪行为进行定性量纪判断"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入自然语言问题（如'收受可能影响公正执行公务的财物如何定性'）"
        },
        {
          "no": 2,
          "name": "系统匹配KB-001中结构化条款，提取要点词、违纪行为及依据出处"
        },
        {
          "no": 3,
          "name": "生成含相关度排序的条款列表，标注适用情形与排除条件"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪参考条款集",
          "category": "结构化条款"
        }
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "纪检文书纠错闭环处理（报批表专项）",
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
          "description": "案件审理人员对审查调查组提交的谈话方案及安全预案等报批类文书开展合规性审核"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "上传待审报批表全文至纠错模块"
        },
        {
          "no": 2,
          "name": "系统调用KB-001（条款）与KB-002（实务问答）联合校验依据引用、口径一致性与定性量纪逻辑"
        },
        {
          "no": 3,
          "name": "输出带定位标记的错误清单及逐条修正建议"
        },
        {
          "no": 4,
          "name": "审理人员确认/修改建议并归档纠错记录"
        }
      ],
      "outputs": [
        {
          "name": "报批表纠错报告",
          "category": "修正建议"
        }
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "多源知识协同验证实务问答",
      "actors": [
        {
          "id": "UG-003",
          "role": "政策研究/法规处人员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "案件研判",
          "description": "法规处需对基层报送的疑难执纪场景问题（如从宽情节认定）提供权威答复"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "接收实务问题输入（如'被审查人主动交代未掌握问题，是否构成从宽情节？'）"
        },
        {
          "no": 2,
          "name": "并行检索KB-001（条款依据）、KB-002（既有问答）、KB-004（理论文章）交叉印证"
        },
        {
          "no": 3,
          "name": "聚合输出结构化问答结果，标注知识冲突点与推荐口径"
        },
        {
          "no": 4,
          "name": "生成可下发的政策答复模板及配套依据索引包"
        }
      ],
      "outputs": [
        {
          "name": "权威实务答复包",
          "category": "结构化问答"
        }
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
      "修正建议",
      "结构化条款",
      "结构化问答"
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
      "name": "审核复核-单文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.37,
      "assigned_difficulty": "basic"
    },
    {
      "type_id": "PT-003",
      "name": "案件研判-跨文档类",
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
      "difficulty": "basic",
      "focus_stages": [
        "定义问题"
      ]
    },
    {
      "test_id": "TEST-002",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "basic",
      "focus_stages": [
        "定义问题"
      ]
    },
    {
      "test_id": "TEST-003",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "advanced",
      "focus_stages": [
        "拆解问题",
        "方案生成"
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
      "定义问题": "常规",
      "拆解问题": "重点",
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
- [x] 聚类后的类型数 = test_plan 题目数(3 vs 3)
- [x] 覆盖矩阵蓝图中每道题至少 1 个'重点'阶段
- [x] test_plan 非空

## 备注与遗留问题
- 业务流程由 LLM 推导(第一层 Fallback)
