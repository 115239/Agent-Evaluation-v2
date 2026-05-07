---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-05-07T23:38:05+08:00
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
| BP-001 | 党纪法规语义检索支撑定性量纪建议 | 知识咨询 | UG-001 | 3 | 结构化条款 | True |
| BP-002 | 实务案例问答匹配辅助审查调查决策 | 案件研判 | UG-001 | 4 | 决策建议 | True |
| BP-003 | 纪检文书纠错辅助与多源口径一致性校验 | 审核复核 | UG-001 | 5 | 故障清单 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 3 | 审核复核、案件研判、知识咨询 |
| outputs.category | 3 | 决策建议、故障清单、结构化条款 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 | 规划题数 |
|---|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001 | BP-001 | 0.31 | basic | 1 |
| PT-002 | 案件研判-单文档类 | BP-002 | BP-002 | 0.37 | basic | 1 |
| PT-003 | 审核复核-跨文档类 | BP-003 | BP-003 | 0.58 | advanced | 1 |

## 题目规划
| 题号 | 流程类型 | 来源流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-002 | BP-002 | basic | 拆解问题、方案生成 |
| TEST-003 | PT-003 | BP-003 | advanced | 定义问题、方案生成 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 常规 | 重点 | 重点 | 常规 | 常规 |
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
          "description": "纪检监察员输入自然语言问题，如'收受可能影响公正执行公务的财物如何定性'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "解析用户查询中的违纪行为关键词与政治语境（如'收受财物''公正执行公务'），识别潜在纪律类型（廉洁纪律/政治纪律）"
        },
        {
          "no": 2,
          "name": "在KB-001中进行多粒度语义匹配：条款要点词、行为描述、适用情形，并排除时效性失效条款"
        },
        {
          "no": 3,
          "name": "生成结构化输出：匹配条款原文、核心要点、相似度排序及引用依据（含条、款、项）"
        }
      ],
      "outputs": [
        {
          "name": "党纪条款匹配结果",
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
      "name": "实务案例问答匹配辅助审查调查决策",
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
          "description": "纪检监察员就具体审查调查场景提问，如'被审查人主动交代组织未掌握的问题，是否一律认定为主动投案？'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "提取问题中的关键要素：行为主体、行为阶段（初核/立案后）、信息属性（组织已掌握/未掌握）"
        },
        {
          "no": 2,
          "name": "在KB-002中检索高度匹配的实务问答对，校验来源文档权威性（中央纪委文件/指导性案例）及时间有效性"
        },
        {
          "no": 3,
          "name": "比对标准答案与实际答案差异，标注适用前提、例外情形及政策演进提示"
        },
        {
          "no": 4,
          "name": "输出带溯源标记的决策支持包：结论、依据片段、风险提示"
        }
      ],
      "outputs": [
        {
          "name": "审查调查决策支持包",
          "category": "决策建议"
        }
      ],
      "depends_on": [
        "KB-002"
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "纪检文书纠错辅助与多源口径一致性校验",
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
          "description": "纪检监察员上传待报批文书（如谈话方案及安全预案），启动合规性终审前校验"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "识别文书类型与所处流程阶段，提取关键字段（如适用‘四种形态’层级、引用条款编号、政治表述措辞）"
        },
        {
          "no": 2,
          "name": "并行调用KB-001（条款引用准确性）、KB-002（实务口径一致性）、KB-003（总书记讲话政治表述规范性）进行交叉验证"
        },
        {
          "no": 3,
          "name": "定位三类错误：条款引用错位、形态适用逻辑矛盾、政治术语表述偏差（如将‘自我革命’误写为‘自我革新’）"
        },
        {
          "no": 4,
          "name": "生成带位置锚点的修正建议集，按紧急程度分级（必须修改/建议优化/存疑待人工确认）"
        },
        {
          "no": 5,
          "name": "聚合输出含修订痕迹的合规文书包及错误归因分析摘要"
        }
      ],
      "outputs": [
        {
          "name": "合规文书包与错误归因摘要",
          "category": "故障清单"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002",
        "KB-003"
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
      "name": "案件研判-单文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.37,
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
      "complexity_score": 0.58,
      "assigned_difficulty": "advanced",
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
      "difficulty": "basic",
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
