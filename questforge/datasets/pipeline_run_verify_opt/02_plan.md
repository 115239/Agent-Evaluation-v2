---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-05-08T00:27:09+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 4 条业务流程(LLM 推导);按'触发×跨流程×输出×管理层'组合聚类为 4 个类型,按类型多样性实际规划 4 道(单类最多 2 道):1 basic、2 advanced、1 expert。第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ✗ | 走 LLM 推导 |
| capability_scope.weak_points | ✗ | Stage 3 是否触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 党纪条款语义检索支撑线索初核定性 | 知识咨询 | UG-001 | 3 | 结构化条款 | True |
| BP-002 | 跨知识源定性量纪综合建议生成 | 案件研判 | UG-001 | 3 | 决策建议 | True |
| BP-003 | 纪检文书纠错与多源依据闭环审核 | 审核复核 | UG-001 | 3 | 修正建议 | True |
| BP-004 | 总书记讲话—理论文章—党纪条款三维政策依据整合输出 | 知识咨询 | UG-001 | 6 | 决策建议 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 3 | 审核复核、案件研判、知识咨询 |
| outputs.category | 4 | 修正建议、决策建议、审批结论、结构化条款 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 | 规划题数 |
|---|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001 | BP-001 | 0.31 | basic | 1 |
| PT-002 | 案件研判-跨文档类 | BP-002 | BP-002 | 0.46 | advanced | 1 |
| PT-003 | 审核复核-跨文档类 | BP-003 | BP-003 | 0.46 | advanced | 1 |
| PT-004 | 知识咨询-跨文档类 | BP-004 | BP-004 | 0.72 | expert | 1 |

## 题目规划
| 题号 | 流程类型 | 来源流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-002 | BP-002 | advanced | 拆解问题、方案生成 |
| TEST-003 | PT-003 | BP-003 | advanced | 定义问题、方案生成 |
| TEST-004 | PT-004 | BP-004 | expert | 定义问题、拆解问题、方案生成、执行落地、元认知 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 常规 | 重点 | 重点 | 常规 | 常规 |
| TEST-003 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-004 | 重点 | 重点 | 重点 | 重点 | 重点 |

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
      "name": "党纪条款语义检索支撑线索初核定性",
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
          "description": "纪检监察员输入自然语言问题，如'收受可能影响公正执行公务的礼品如何定性'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "纪检监察员在系统中输入违纪行为描述性查询"
        },
        {
          "no": 2,
          "name": "系统基于语义匹配从 KB-001 检索最相关党纪条款，提取要点词、违纪行为、序号及置信度"
        },
        {
          "no": 3,
          "name": "返回结构化结果：含原文片段、来源行号、依据强度标注，供初核笔录引用"
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
      "expected_difficulty": "basic",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "跨知识源定性量纪综合建议生成",
      "actors": [
        {
          "id": "UG-001",
          "role": "纪检监察员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "案件研判",
          "description": "纪检监察员提交初步核实形成的违纪事实简述，需形成处分建议"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "纪检监察员录入违纪事实（如'接受管理服务对象宴请并收受礼金'）"
        },
        {
          "no": 2,
          "name": "系统并行调用 KB-001（党纪条款）与 KB-002（实务问答）进行双源校验：匹配条款+验证同类案例处理口径"
        },
        {
          "no": 3,
          "name": "融合输出建议定性（如'违反廉洁纪律'）、对应 KB-001 序号、量纪梯度（警告至开除党籍）、从宽/从严情节提示"
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
      "expected_difficulty": "advanced",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "纪检文书纠错与多源依据闭环审核",
      "actors": [
        {
          "id": "UG-001",
          "role": "纪检监察员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "审核复核",
          "description": "对拟上报的谈话方案、立案呈批表等文书开展合规性终审"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "纪检监察员上传待审文书文本（如'报批表(谈话方案及安全预案)'）"
        },
        {
          "no": 2,
          "name": "系统识别错误类型（表达歧义/依据缺失/口径偏差/格式不规范），定位 KB-001 或 KB-002 中对应支撑条目"
        },
        {
          "no": 3,
          "name": "生成带超链接的纠错清单，标注每处问题所援引的知识源（KB-001 序号或 KB-002 来源片段）"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错反馈单",
          "category": "修正建议"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002"
      ],
      "cross_process_dependency": "跨流程",
      "expected_difficulty": "advanced",
      "inferred": true
    },
    {
      "id": "BP-004",
      "name": "总书记讲话—理论文章—党纪条款三维政策依据整合输出",
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
          "description": "纪检监察员需为某类问题（如'政治监督具体化常态化'）准备汇报材料，要求政策高度+理论深度+纪法刚性"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "纪检监察员输入政策命题（如'政治监督具体化常态化'）"
        },
        {
          "no": 2,
          "name": "系统同步检索 KB-003（总书记讲话上下文）、KB-004（理论文章摘要）、KB-001（党纪条款），提取主题标签、核心论点、对应条款"
        },
        {
          "no": 3,
          "name": "交叉比对三源一致性：识别讲话精神→理论阐释→纪法落点映射链"
        },
        {
          "no": 4,
          "name": "生成政策依据整合包：含讲话原文片段（KB-003）、理论支撑摘要（KB-004）、适用党纪条款（KB-001）"
        },
        {
          "no": 5,
          "name": "纪检监察员选择是否触发管理层复核：若用于重大案件汇报，则自动推送至分管副书记"
        },
        {
          "no": 6,
          "name": "分管副书记在系统中确认三源逻辑闭环性，签署‘政策依据完备’意见并归档"
        }
      ],
      "outputs": [
        {
          "name": "三维政策依据整合包",
          "category": "决策建议"
        },
        {
          "name": "管理层复核意见",
          "category": "审批结论"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-003",
        "KB-004"
      ],
      "cross_process_dependency": "跨流程",
      "expected_difficulty": "expert",
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
      "决策建议",
      "审批结论",
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
      "assigned_difficulty": "basic",
      "planned_tests": 1
    },
    {
      "type_id": "PT-002",
      "name": "案件研判-跨文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.46,
      "assigned_difficulty": "advanced",
      "planned_tests": 1
    },
    {
      "type_id": "PT-003",
      "name": "审核复核-跨文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.46,
      "assigned_difficulty": "advanced",
      "planned_tests": 1
    },
    {
      "type_id": "PT-004",
      "name": "知识咨询-跨文档类",
      "members": [
        "BP-004"
      ],
      "representative": "BP-004",
      "complexity_score": 0.72,
      "assigned_difficulty": "expert",
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
        "拆解问题",
        "方案生成"
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
    },
    {
      "test_id": "TEST-004",
      "process_type": "PT-004",
      "source_process": "BP-004",
      "difficulty": "expert",
      "focus_stages": [
        "定义问题",
        "拆解问题",
        "方案生成",
        "执行落地",
        "元认知"
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
      "定义问题": "常规",
      "拆解问题": "重点",
      "方案生成": "重点",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-003": {
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "重点",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-004": {
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
- [x] 每条 BP ≥ 3 个步骤(共 4 条 BP)
- [x] 触发类型取值来自预设词表或 Stage 1 glossary
- [x] test_plan 题目数与按类型多样性规划一致(4 vs 4)
- [x] 覆盖矩阵蓝图中每道题至少 1 个'重点'阶段
- [x] test_plan 非空

## 备注与遗留问题
- 业务流程由 LLM 推导(第一层 Fallback)
- 复杂度梯度自检通过
- 以下类型因缺少可拉开独立性的成员流程,未按配置值重复采样:PT-001(1/2)、PT-002(1/2)、PT-003(1/2)、PT-004(1/2)
