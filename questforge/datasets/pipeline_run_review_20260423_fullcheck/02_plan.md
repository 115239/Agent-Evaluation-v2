---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-23T13:01:15+08:00
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
| BP-001 | 党纪法规语义检索支撑定性量纪建议生成 | 知识咨询 | UG-001 | 3 | 决策建议 | True |
| BP-002 | 总书记讲话精准召回支持政治表述合规审查 | 审核复核 | UG-002 | 3 | 合规清单 | True |
| BP-003 | 纪检文书全量纠错与多源知识协同验证 | 审核复核 | UG-002+UG-003 | 4 | 修正指令 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 2 | 审核复核、知识咨询 |
| outputs.category | 3 | 修正指令、决策建议、合规清单 |
| actors.level | 2 | 业务、管理 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-跨文档类 | BP-001 | BP-001 | 0.46 | advanced |
| PT-002 | 审核复核-单文档类 | BP-002 | BP-002 | 0.31 | basic |
| PT-003 | 审核复核-跨文档类 | BP-003 | BP-003 | 0.67 | advanced |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | advanced | 定义问题、方案生成 |
| TEST-002 | PT-001 | BP-001 | advanced | 拆解问题、执行落地 |
| TEST-003 | PT-002 | BP-002 | basic | 定义问题 |
| TEST-004 | PT-002 | BP-002 | basic | 执行落地 |
| TEST-005 | PT-003 | BP-003 | advanced | 定义问题、方案生成 |
| TEST-006 | PT-003 | BP-003 | advanced | 拆解问题、执行落地 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-002 | 常规 | 重点 | 常规 | 重点 | 常规 |
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
          "description": "一线纪检监察员输入自然语言违纪事实描述，请求定性依据与处分建议"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "解析违纪事实简述，提取关键行为要素（如'接受宴请''收受礼品''管理服务对象'）"
        },
        {
          "no": 2,
          "name": "基于KB-001执行党纪法规语义检索，匹配廉洁纪律、工作纪律等条款及要点词"
        },
        {
          "no": 3,
          "name": "融合KB-002中同类实务问答，生成含条款引用、处分档次、从宽/从严提示的结构化建议"
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
      "name": "总书记讲话精准召回支持政治表述合规审查",
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
          "description": "审理人员对报批表中政治表述（如'两个维护''国之大者'使用场景）开展口径一致性核查"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "识别文书中的政治术语及上下文语境"
        },
        {
          "no": 2,
          "name": "调用KB-003进行主题+上下文联合检索，召回总书记最新权威表述原文片段"
        },
        {
          "no": 3,
          "name": "比对原文发布时间、语义边界与文书使用场景，输出口径偏差定位与修正依据"
        }
      ],
      "outputs": [
        {
          "name": "政治表述合规报告",
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
      "name": "纪检文书全量纠错与多源知识协同验证",
      "actors": [
        {
          "id": "UG-002",
          "role": "案件审理人员",
          "level": "业务"
        },
        {
          "id": "UG-003",
          "role": "政策研究与法规指导人员",
          "level": "管理"
        }
      ],
      "triggers": [
        {
          "type": "审核复核",
          "description": "审理人员提交待审报批表(谈话方案及安全预案)，触发多维度合规性扫描"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "对文书全文进行分层解析：程序要素（审批节点）、实体要素（定性依据）、政治要素（表述口径）"
        },
        {
          "no": 2,
          "name": "并行调用KB-001（条款时效性）、KB-002（实务口径）、KB-003（讲话原文）进行交叉验证"
        },
        {
          "no": 3,
          "name": "聚合三类知识冲突点，生成错误类型标签、位置锚点、修正建议及对应知识源片段"
        },
        {
          "no": 4,
          "name": "由政策研究人员对高风险逻辑矛盾类错误进行人工复核并签发终版纠错意见"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错意见书",
          "category": "修正指令"
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
      "知识咨询"
    ],
    "outputs.category": [
      "修正指令",
      "决策建议",
      "合规清单"
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
      "name": "知识咨询-跨文档类",
      "members": [
        "BP-001"
      ],
      "representative": "BP-001",
      "complexity_score": 0.46,
      "assigned_difficulty": "advanced"
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
      "name": "审核复核-跨文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.67,
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
        "定义问题",
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
        "拆解问题",
        "执行落地"
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
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "重点",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-002": {
      "定义问题": "常规",
      "拆解问题": "重点",
      "方案生成": "常规",
      "执行落地": "重点",
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
