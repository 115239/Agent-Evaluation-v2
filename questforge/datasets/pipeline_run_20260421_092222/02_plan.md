---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-21T09:23:13+08:00
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
| BP-001 | 定性量纪建议生成与依据验证 | 知识咨询 | UG-001 | 3 | 结构化建议 | True |
| BP-002 | 纪检文书全流程智能纠错与依据回溯 | 审核复核 | UG-001+UG-002 | 4 | 标注修订稿 | True |
| BP-003 | 理论政策支撑型材料智能编研 | 知识咨询 | UG-003 | 3 | 观点整合包 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 2 | 审核复核、知识咨询 |
| outputs.category | 4 | 依据引用清单、标注修订稿、结构化建议、观点整合包 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001,BP-003 | BP-001 | 0.31 | basic |
| PT-002 | 审核复核-跨文档类 | BP-002 | BP-002 | 0.66 | advanced |

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
      "name": "定性量纪建议生成与依据验证",
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
          "description": "纪检监察员输入定性量纪类自然语言问题，如'收受可能影响公正执行公务的财物如何定性'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "调用党纪法规语义检索（FEAT-001）获取匹配条款及要点词"
        },
        {
          "no": 2,
          "name": "叠加实务问答验证辅助（FEAT-004）比对标准答案与来源文档"
        },
        {
          "no": 3,
          "name": "整合条款要点、违纪行为定义与实务结论，生成结构化定性量纪建议草稿"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪建议",
          "category": "结构化建议"
        }
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "纪检文书全流程智能纠错与依据回溯",
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
          "description": "案件审理人员对一线人员提交的报批表、谈话方案等文书启动合规性复核"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "上传文书文本，触发纪检文书智能纠错（FEAT-005）识别依据错误与表述偏差"
        },
        {
          "no": 2,
          "name": "自动关联KB-001（党纪条款）、KB-002（实务问答）、KB-003（总书记讲话）定位修正依据原文"
        },
        {
          "no": 3,
          "name": "生成带标注的修订版文书，含错误类型标签、修正建议及对应条款/讲话/问答出处"
        },
        {
          "no": 4,
          "name": "输出纠错报告供审理人员交叉验证并决定是否退回修改"
        }
      ],
      "outputs": [
        {
          "name": "修订版文书",
          "category": "标注修订稿"
        },
        {
          "name": "纠错依据溯源清单",
          "category": "依据引用清单"
        }
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "理论政策支撑型材料智能编研",
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
          "description": "政策研究人员围绕理论概念（如'政治监督具体化常态化'）发起深度支撑材料编研需求"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "并行调用理论文章观点支撑检索（FEAT-003）与总书记讲话精准召回（FEAT-002）"
        },
        {
          "no": 2,
          "name": "融合摘要、核心论点、讲话主题与发布时间，构建多源观点矩阵"
        },
        {
          "no": 3,
          "name": "按逻辑脉络组织输出，标注各观点在党纪法规（KB-001）中的制度映射关系"
        }
      ],
      "outputs": [
        {
          "name": "理论政策编研包",
          "category": "观点整合包"
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
      "依据引用清单",
      "标注修订稿",
      "结构化建议",
      "观点整合包"
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
      "complexity_score": 0.66,
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
