---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-21T01:26:32+08:00
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
| BP-001 | 党纪法规语义检索支撑定性量纪建议生成 | 知识咨询 | UG-001 | 3 | 决策建议 | True |
| BP-002 | 纪检文书纠错闭环处理 | 审核复核 | UG-002 | 3 | 问题清单 | True |
| BP-003 | 多源理论素材协同检索与政策阐释 | 知识咨询 | UG-003 | 4 | 综合摘要 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 2 | 审核复核、知识咨询 |
| outputs.category | 3 | 决策建议、综合摘要、问题清单 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-跨文档类 | BP-001,BP-003 | BP-003 | 0.52 | advanced |
| PT-002 | 审核复核-单文档类 | BP-002 | BP-002 | 0.31 | basic |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-003 | advanced | 定义问题 |
| TEST-002 | PT-002 | BP-002 | basic | 定义问题 |

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
          "description": "一线纪检监察员输入自然语言描述违纪事实，请求匹配适用党纪条款及量纪建议"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "用户提交违纪事实简述（如'违规接受管理服务对象宴请并收受礼品'）"
        },
        {
          "no": 2,
          "name": "系统调用FEAT-001进行党纪法规语义检索，定位KB-001中匹配条款（含要点词、违纪行为、条款序号）"
        },
        {
          "no": 3,
          "name": "融合KB-002实务问答，生成含定性依据、处分档次建议、从宽/从严情节提示的结构化建议"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪建议书",
          "category": "决策建议"
        }
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    },
    {
      "id": "BP-002",
      "name": "纪检文书纠错闭环处理",
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
          "description": "案件审理人员上传待审报批表（谈话方案及安全预案）等正式文书启动合规性审查"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "系统解析文书全文，识别关键字段（如‘谈话对象’‘风险点’‘审批依据’）"
        },
        {
          "no": 2,
          "name": "并行比对KB-001（条款时效性）、KB-002（口径一致性）、KB-003（政治表述准确性）"
        },
        {
          "no": 3,
          "name": "标注错误类型（表达歧义/依据过时/口径偏差/逻辑矛盾），定位原文位置，输出修正建议及知识锚点"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错报告",
          "category": "问题清单"
        }
      ],
      "cross_process_dependency": "单流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "多源理论素材协同检索与政策阐释",
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
          "description": "政策研究人员输入理论概念（如'健全全面从严治党体系'）请求跨知识库关联阐释"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "系统同步触发FEAT-003（理论文章摘要检索）、FEAT-002（总书记讲话精准召回）、FEAT-001（相关党纪条款映射）"
        },
        {
          "no": 2,
          "name": "对KB-004摘要、KB-003讲话片段、KB-001条款要点进行语义对齐与主题聚类"
        },
        {
          "no": 3,
          "name": "生成带来源标注的综合阐释包，含核心论点、权威引述、制度衔接说明"
        },
        {
          "no": 4,
          "name": "支持导出为政策答疑模板或培训课件素材"
        }
      ],
      "outputs": [
        {
          "name": "政策阐释包",
          "category": "综合摘要"
        }
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
      "综合摘要",
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
      "name": "知识咨询-跨文档类",
      "members": [
        "BP-001",
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.52,
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
    }
  ],
  "test_plan": [
    {
      "test_id": "TEST-001",
      "process_type": "PT-001",
      "source_process": "BP-003",
      "difficulty": "advanced",
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
