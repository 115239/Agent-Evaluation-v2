---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-21T00:23:29+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 4 条业务流程，全部为本地推导（inferred=true）；按'触发-输出'组合聚类为 4 个类型，规划 4 道题：1 basic、3 advanced、0 expert。第一层 Fallback 已触发（源文档无流程定义段）。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ❌ | 全部走推导路径（LLM+本地兜底） |
| capability_scope.weak_points | ❌ | 将在 Stage 3 触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 党纪法规语义检索与定性支撑流程 | 知识咨询 | UG-001+UG-002 | 3 | 结构化条款 | True |
| BP-002 | 总书记讲话上下文检索与理论阐释支撑流程 | 知识咨询 | UG-003+UG-001 | 3 | 讲话摘要+上下文 | True |
| BP-003 | 纪检文书合规性纠错与法条援引校验流程 | 审核复核 | UG-002+UG-001 | 3 | 纠错清单 | True |
| BP-004 | 定性量纪智能建议生成流程 | 案件研判 | UG-001+UG-002 | 3 | 决策建议 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 3 | 审核复核、案件研判、知识咨询 |
| outputs.category | 4 | 决策建议、纠错清单、结构化条款、讲话摘要+上下文 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001 | BP-001 | 0.31 | basic |
| PT-002 | 知识咨询-跨文档类 | BP-002 | BP-002 | 0.46 | advanced |
| PT-003 | 审核复核-文书纠错类 | BP-003 | BP-003 | 0.46 | advanced |
| PT-004 | 案件研判-综合决策类 | BP-004 | BP-004 | 0.46 | advanced |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-002 | BP-002 | advanced | 定义问题 |
| TEST-003 | PT-003 | BP-003 | advanced | 执行落地、元认知 |
| TEST-004 | PT-004 | BP-004 | advanced | 拆解问题、方案生成 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-003 | 常规 | 常规 | 常规 | 重点 | 重点 |
| TEST-004 | 常规 | 重点 | 重点 | 常规 | 常规 |

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
      "name": "党纪法规语义检索与定性支撑流程",
      "actors": [
        {
          "id": "UG-001",
          "role": "一线纪检监察员",
          "level": "业务"
        },
        {
          "id": "UG-002",
          "role": "案件审理室人员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "知识咨询",
          "description": "用户输入自然语言查询（如'违规公款旅游'）或案情片段，发起党纪条款匹配与定性依据调取"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "解析用户查询语义，提取关键行为要素（主体、行为、情节、金额等）"
        },
        {
          "no": 2,
          "name": "在KB-001中执行多维向量检索，匹配高置信度党纪条款及违纪行为描述"
        },
        {
          "no": 3,
          "name": "关联KB-004中同类实务案例，生成定性逻辑链与条款适用说明"
        }
      ],
      "outputs": [
        {
          "name": "结构化条款匹配结果+定性逻辑链",
          "category": "结构化条款"
        }
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "总书记讲话上下文检索与理论阐释支撑流程",
      "actors": [
        {
          "id": "UG-003",
          "role": "政策研究/理论宣传岗",
          "level": "业务"
        },
        {
          "id": "UG-001",
          "role": "一线纪检监察员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "知识咨询",
          "description": "用户输入主题词（如'政治监督'）或语义相近表述，请求讲话原文与政策语境支持"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "标准化主题意图，映射至KB-002预标主题标签体系"
        },
        {
          "no": 2,
          "name": "检索匹配讲话标题、发布时间、摘要及上下文段落（含起止时间锚点）"
        },
        {
          "no": 3,
          "name": "融合KB-003中相关理论文章观点，生成讲话要义与纪律要求对照阐释"
        }
      ],
      "outputs": [
        {
          "name": "讲话摘要+上下文+理论对照阐释",
          "category": "讲话摘要+上下文"
        }
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "纪检文书合规性纠错与法条援引校验流程",
      "actors": [
        {
          "id": "UG-002",
          "role": "案件审理室人员",
          "level": "业务"
        },
        {
          "id": "UG-001",
          "role": "一线纪检监察员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "审核复核",
          "description": "提交初核报告、审查调查报告或审理报告待审，触发文书规范性自动校验"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "识别文书类型与结构段落（事实陈述、定性分析、条款引用、处理建议）"
        },
        {
          "no": 2,
          "name": "交叉比对KB-001条款要点词与文书定性用词，标记条款缺失、错引、过时风险"
        },
        {
          "no": 3,
          "name": "调用KB-002/KB-004验证政治表述准确性与同类案例适配性，生成修正建议"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错清单与法条援引校验报告",
          "category": "纠错清单"
        }
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    },
    {
      "id": "BP-004",
      "name": "定性量纪智能建议生成流程",
      "actors": [
        {
          "id": "UG-001",
          "role": "一线纪检监察员",
          "level": "业务"
        },
        {
          "id": "UG-002",
          "role": "案件审理室人员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "案件研判",
          "description": "输入结构化案情描述（含时间、主体、行为、金额、情节），启动量纪档次推演"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "结构化解析案情要素，归一化至KB-001违纪行为分类体系"
        },
        {
          "no": 2,
          "name": "基于KB-001条款效力层级与KB-004实务案例判决倾向，计算量纪区间概率分布"
        },
        {
          "no": 3,
          "name": "输出推荐条款、定性结论、量纪档次及3个最邻近实务案例编号与差异提示"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪决策建议",
          "category": "决策建议"
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
      "决策建议",
      "纠错清单",
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
      "assigned_difficulty": "basic"
    },
    {
      "type_id": "PT-002",
      "name": "知识咨询-跨文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.46,
      "assigned_difficulty": "advanced"
    },
    {
      "type_id": "PT-003",
      "name": "审核复核-文书纠错类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.46,
      "assigned_difficulty": "advanced"
    },
    {
      "type_id": "PT-004",
      "name": "案件研判-综合决策类",
      "members": [
        "BP-004"
      ],
      "representative": "BP-004",
      "complexity_score": 0.46,
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
      "difficulty": "advanced",
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
        "执行落地",
        "元认知"
      ]
    },
    {
      "test_id": "TEST-004",
      "process_type": "PT-004",
      "source_process": "BP-004",
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
      "拆解问题": "常规",
      "方案生成": "常规",
      "执行落地": "重点",
      "元认知": "重点"
    },
    "TEST-004": {
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
- [x] 每条 BP ≥ 3 个步骤（共 4 条 BP）
- [x] 触发类型取值来自预设词表或 Stage 1 glossary
- [x] 聚类后的类型数 = test_plan 题目数（4 vs 4）
- [x] 难度分配覆盖 ≥ 2 级（实际 ['advanced', 'basic']）
- [x] 覆盖矩阵蓝图中每道题至少 1 个'重点'阶段
- [x] process_types 同时包含'知识咨询'类与'文书纠错'类

## 备注与遗留问题
（无）
