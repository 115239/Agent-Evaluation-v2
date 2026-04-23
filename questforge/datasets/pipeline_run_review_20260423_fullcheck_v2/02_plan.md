---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-23T13:07:31+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 3 条业务流程(LLM 推导);按'触发×跨流程×输出×管理层'组合聚类为 3 个类型,每类采样 2 题,共规划 6 道:4 basic、2 advanced、0 expert。第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ✗ | 走 LLM 推导 |
| capability_scope.weak_points | ✗ | Stage 3 是否触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 一线纪检监察员获取定性量纪建议 | 案件研判 | UG-001 | 3 | 决策建议 | True |
| BP-002 | 案件审理人员审核报批类文书并纠错 | 审核复核 | UG-002 | 3 | 故障清单 | True |
| BP-003 | 政策研究人员开展多源理论语义检索与整合输出 | 知识咨询 | UG-003 | 3 | 结构化条款 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 3 | 审核复核、案件研判、知识咨询 |
| outputs.category | 3 | 决策建议、故障清单、结构化条款 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 案件研判-单文档类 | BP-001 | BP-001 | 0.31 | basic |
| PT-002 | 审核复核-单文档类 | BP-002 | BP-002 | 0.31 | basic |
| PT-003 | 知识咨询-跨文档类 | BP-003 | BP-003 | 0.46 | advanced |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 拆解问题、方案生成 |
| TEST-002 | PT-001 | BP-001 | basic | 定义问题、方案生成 |
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
      "name": "一线纪检监察员获取定性量纪建议",
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
          "description": "收到违纪事实描述文本，需快速形成初步定性与量纪意见"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入自然语言违纪事实描述（如'违规接受管理服务对象宴请并收受礼品'）"
        },
        {
          "no": 2,
          "name": "系统匹配KB-001结构化条款与KB-002实务问答，识别要点词、违纪行为类型及从宽/从严情节"
        },
        {
          "no": 3,
          "name": "生成含定性结论、援引条款、量纪档次及情节提示的决策建议"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪决策建议",
          "category": "决策建议"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002"
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "案件审理人员审核报批类文书并纠错",
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
          "description": "对拟提交的谈话方案及安全预案等报批表开展合规性审查"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "上传待审文书全文（如'报批表(谈话方案及安全预案)'）"
        },
        {
          "no": 2,
          "name": "系统比对KB-001条款要点词与KB-002实务口径，识别依据引用错误、表述不规范、逻辑矛盾点"
        },
        {
          "no": 3,
          "name": "标注风险位置，推送标准表述、正确援引条款及修正依据片段"
        }
      ],
      "outputs": [
        {
          "name": "文书合规性诊断报告",
          "category": "故障清单"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002"
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "政策研究人员开展多源理论语义检索与整合输出",
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
          "description": "围绕重大政策概念（如'政治监督具体化常态化'）开展跨知识库溯源与阐释支持"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入理论关键词或政策概念，发起跨KB-001、KB-003、KB-004联合检索"
        },
        {
          "no": 2,
          "name": "聚合匹配的党纪条款要点、总书记讲话上下文片段、理论文章核心观点"
        },
        {
          "no": 3,
          "name": "生成结构化对比摘要，标注权威出处、适用层级与实践指向"
        }
      ],
      "outputs": [
        {
          "name": "多源理论整合摘要",
          "category": "结构化条款"
        }
      ],
      "depends_on": [
        "KB-001",
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
      "name": "案件研判-单文档类",
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
      "complexity_score": 0.31,
      "assigned_difficulty": "basic"
    },
    {
      "type_id": "PT-003",
      "name": "知识咨询-跨文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
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
        "拆解问题",
        "方案生成"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-002",
      "process_type": "PT-001",
      "source_process": "BP-001",
      "difficulty": "basic",
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
