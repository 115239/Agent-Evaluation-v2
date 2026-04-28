---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-22T00:25:04+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 3 条业务流程(LLM 推导);按'触发-跨流程'组合聚类为 2 个类型,规划 2 道题:1 basic、1 advanced、0 expert。第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| business_processes 段存在 | ✗ | 走 LLM 推导 |
| capability_scope.weak_points | ✗ | Stage 3 是否触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出类别 | inferred |
|---|---|---|---|---|---|---|
| BP-001 | 党纪法规条款匹配与定性量纪建议生成 | 知识咨询 | UG-001 | 3 | 决策建议 | True |
| BP-002 | 纪检文书纠错与政治口径一致性校验 | 审核复核 | UG-001+UG-002 | 4 | 问题清单 | True |
| BP-003 | 总书记讲话精准定位与政策语境还原 | 知识咨询 | UG-002 | 3 | 结构化摘要 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 2 | 审核复核、知识咨询 |
| outputs.category | 3 | 决策建议、结构化摘要、问题清单 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001,BP-003 | BP-001 | 0.31 | basic |
| PT-002 | 审核复核-跨文档类 | BP-002 | BP-002 | 0.52 | advanced |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-002 | BP-002 | advanced | 定义问题 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 重点 | 常规 | 常规 | 常规 | 常规 |

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
      "name": "党纪法规条款匹配与定性量纪建议生成",
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
          "description": "用户输入违纪行为描述（如'违规接受管理服务对象宴请'）发起语义检索"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "一线纪检监察员输入自然语言形式的违纪行为描述或关键词"
        },
        {
          "no": 2,
          "name": "系统基于KB-001执行语义匹配，识别对应要点词、违纪行为类型及适用条款"
        },
        {
          "no": 3,
          "name": "融合从宽/从严情节等术语规则，生成含处分档次提示的定性量纪建议"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪建议书",
          "category": "决策建议"
        }
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "纪检文书纠错与政治口径一致性校验",
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
          "description": "案件审理人员对一线人员提交的报批表(谈话方案及安全预案)开展合规性审查"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "一线纪检监察员上传待审纪检文书（如谈话方案及安全预案）"
        },
        {
          "no": 2,
          "name": "系统调用KB-001/KB-002/KB-003/KB-004进行多源交叉校验：条款引用、实务问答依据、讲话精神契合度、理论口径一致性"
        },
        {
          "no": 3,
          "name": "标注表达不规范、依据错误、政治表述偏差等具体问题并提供修正建议"
        },
        {
          "no": 4,
          "name": "案件审理人员确认问题清单并决定是否退回修改或签批通过"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错报告",
          "category": "问题清单"
        }
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "总书记讲话精准定位与政策语境还原",
      "actors": [
        {
          "id": "UG-002",
          "role": "案件审理人员",
          "level": "业务"
        }
      ],
      "triggers": [
        {
          "type": "知识咨询",
          "description": "用户输入政策表述或主题词（如'反腐败斗争关系民心'），需支撑审查结论的政治正当性"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "案件审理人员输入政策关键词或完整引述句"
        },
        {
          "no": 2,
          "name": "系统在KB-003中执行上下文敏感检索，匹配原始讲话标题、发布时间与主题"
        },
        {
          "no": 3,
          "name": "提取原文片段及前后段落逻辑，生成含语境说明的摘要卡片"
        }
      ],
      "outputs": [
        {
          "name": "讲话语境摘要卡",
          "category": "结构化摘要"
        }
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
      "结构化摘要",
      "问题清单"
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
        "BP-001",
        "BP-003"
      ],
      "representative": "BP-001",
      "complexity_score": 0.31,
      "assigned_difficulty": "basic"
    },
    {
      "type_id": "PT-002",
      "name": "审核复核-跨文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
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
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题"
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
    }
  }
}
```

## 下一阶段校验清单
- [x] 每条 BP ≥ 3 个步骤(共 3 条 BP)
- [x] 触发类型取值来自预设词表或 Stage 1 glossary
- [x] 聚类后的类型数 = test_plan 题目数(2 vs 2)
- [x] 覆盖矩阵蓝图中每道题至少 1 个'重点'阶段
- [x] test_plan 非空

## 备注与遗留问题
- 业务流程由 LLM 推导(第一层 Fallback)
- 聚类数 2 < 3,可回头补次优流程
