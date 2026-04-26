---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-26T19:49:16+08:00
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
| BP-001 | 党纪法规语义检索支撑定性量纪建议生成 | 案件研判 | UG-001 | 3 | 决策建议 | True |
| BP-002 | 纪检文书纠错与政治合规性复核 | 审核复核 | UG-002 | 3 | 问题清单 | True |
| BP-003 | 理论政策语义溯源与权威引用生成 | 知识咨询 | UG-003 | 3 | 结构化条款 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 3 | 审核复核、案件研判、知识咨询 |
| outputs.category | 3 | 决策建议、结构化条款、问题清单 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 | 规划题数 |
|---|---|---|---|---|---|---|
| PT-001 | 案件研判-跨文档类 | BP-001 | BP-001 | 0.46 | advanced | 1 |
| PT-002 | 审核复核-跨文档类 | BP-002 | BP-002 | 0.46 | advanced | 1 |
| PT-003 | 知识咨询-单文档类 | BP-003 | BP-003 | 0.31 | basic | 1 |

## 题目规划
| 题号 | 流程类型 | 来源流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | advanced | 拆解问题、方案生成 |
| TEST-002 | PT-002 | BP-002 | advanced | 定义问题、方案生成 |
| TEST-003 | PT-003 | BP-003 | basic | 定义问题 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 常规 | 重点 | 重点 | 常规 | 常规 |
| TEST-002 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-003 | 重点 | 常规 | 常规 | 常规 | 常规 |

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
          "type": "案件研判",
          "description": "纪检监察员输入违纪事实简述，需快速匹配党纪条款并形成定性量纪建议"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入违纪事实要素（主体、行为、情节、后果）并触发定性量纪建议生成功能"
        },
        {
          "no": 2,
          "name": "系统调用党纪法规语义检索（FEAT-001）匹配相关条款，提取要点词与违纪行为标签"
        },
        {
          "no": 3,
          "name": "融合实务问答知识（KB-002）校验量纪尺度，生成含条款序号、处分档次与理由说明的结构化建议"
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
      "name": "纪检文书纠错与政治合规性复核",
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
          "description": "审理人员上传报批表等正式文书，启动政治表述、依据引用、处分逻辑三重校验"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "解析文书全文，识别关键字段（如‘谈话对象’‘安全措施’‘拟处分档次’）"
        },
        {
          "no": 2,
          "name": "比对KB-001条款效力边界与KB-002实务口径，标出依据缺失、处分档次错误、政治表述偏差项"
        },
        {
          "no": 3,
          "name": "关联总书记讲话（KB-003）与理论文章（KB-004）验证政治定性表述一致性，生成修订批注"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错报告",
          "category": "问题清单"
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
    },
    {
      "id": "BP-003",
      "name": "理论政策语义溯源与权威引用生成",
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
          "description": "政策研究人员需为某理论概念（如‘健全全面从严治党体系’）提供权威出处与阐释脉络"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "输入理论概念或政策表述，启动理论文章摘要检索（FEAT-003）与总书记讲话精准召回（FEAT-002）双通道查询"
        },
        {
          "no": 2,
          "name": "聚合匹配结果，按发布时间、权威层级（中央文件 > 讲话 > 理论文章）、主题覆盖度排序"
        },
        {
          "no": 3,
          "name": "抽取原文片段、标注数据来源与上下文逻辑链，生成可嵌入政策解读材料的引用包"
        }
      ],
      "outputs": [
        {
          "name": "政策引用包",
          "category": "结构化条款"
        }
      ],
      "depends_on": [
        "KB-003",
        "KB-004"
      ],
      "cross_process_dependency": "单流程",
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
      "结构化条款",
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
      "name": "案件研判-跨文档类",
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
      "name": "审核复核-跨文档类",
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
      "name": "知识咨询-单文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.31,
      "assigned_difficulty": "basic",
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
        "拆解问题",
        "方案生成"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-002",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "advanced",
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-003",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "basic",
      "focus_stages": [
        "定义问题"
      ],
      "sample_idx": 0
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
