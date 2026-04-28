---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-23T09:36:04+08:00
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
| BP-001 | 党纪法规语义检索支撑定性量纪建议生成 | 知识咨询 | UG-001 | 3 | 结构化条款 | True |
| BP-002 | 纪检文书纠错闭环处理（以谈话方案及安全预案为例） | 审核复核 | UG-002 | 4 | 修正建议 | True |
| BP-003 | 总书记讲话精准召回支持政治定性研判 | 知识咨询 | UG-003 | 3 | 讲话摘要+上下文 | True |

## 分类维度扫描
| 维度 | 取值数 | 取值 |
|---|---|---|
| trigger.type | 2 | 审核复核、知识咨询 |
| outputs.category | 3 | 修正建议、结构化条款、讲话摘要+上下文 |
| actors.level | 1 | 业务 |
| cross_process_dependency | 2 | 单流程、跨流程 |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---|---|---|---|---|---|
| PT-001 | 知识咨询-单文档类 | BP-001 | BP-001 | 0.31 | basic |
| PT-002 | 审核复核-跨文档类 | BP-002 | BP-002 | 0.52 | advanced |
| PT-003 | 知识咨询-单文档类 | BP-003 | BP-003 | 0.31 | basic |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | focus_stages |
|---|---|---|---|---|
| TEST-001 | PT-001 | BP-001 | basic | 定义问题 |
| TEST-002 | PT-001 | BP-001 | basic | 执行落地 |
| TEST-003 | PT-002 | BP-002 | advanced | 定义问题、方案生成 |
| TEST-004 | PT-002 | BP-002 | advanced | 拆解问题、执行落地 |
| TEST-005 | PT-003 | BP-003 | basic | 定义问题 |
| TEST-006 | PT-003 | BP-003 | basic | 执行落地 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|---|---|---|---|---|---|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 常规 | 常规 | 常规 | 重点 | 常规 |
| TEST-003 | 重点 | 常规 | 重点 | 常规 | 常规 |
| TEST-004 | 常规 | 重点 | 常规 | 重点 | 常规 |
| TEST-005 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-006 | 常规 | 常规 | 常规 | 重点 | 常规 |

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
          "description": "一线纪检监察员输入自然语言问题，如'收受可能影响公正执行公务的财物如何定性'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "解析用户查询中的违纪行为关键词与纪律类型（如'收受财物''廉洁纪律'）"
        },
        {
          "no": 2,
          "name": "在KB-001中进行语义匹配，召回相关条款并标注要点词、违纪行为及条款序号"
        },
        {
          "no": 3,
          "name": "按相关性排序输出结构化条款结果，并附合规性提示（如是否属‘四种形态’第一种形态适用情形）"
        }
      ],
      "outputs": [
        {
          "name": "定性量纪建议依据清单",
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
      "name": "纪检文书纠错闭环处理（以谈话方案及安全预案为例）",
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
          "description": "案件审理人员上传待审报批表(谈话方案及安全预案)，启动合规性审查"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "识别文书中的关键字段（如谈话对象、风险等级、安全措施、审批路径）"
        },
        {
          "no": 2,
          "name": "交叉比对KB-001（纪律条款）、KB-002（实务问答）、KB-003（总书记讲话）校验依据引用准确性与政治表述规范性"
        },
        {
          "no": 3,
          "name": "定位错误类型（表达/依据/口径），标记错误位置并生成带来源锚点的修正建议"
        },
        {
          "no": 4,
          "name": "输出含修订痕迹与依据溯源的纠错报告，支持一键插入或人工复核"
        }
      ],
      "outputs": [
        {
          "name": "文书纠错报告",
          "category": "修正建议"
        }
      ],
      "depends_on": [
        "KB-001",
        "KB-002",
        "KB-003"
      ],
      "cross_process_dependency": "跨流程",
      "inferred": true
    },
    {
      "id": "BP-003",
      "name": "总书记讲话精准召回支持政治定性研判",
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
          "description": "政策研究人员输入主题关键词或上下文片段，如'整治形式主义为基层减负'"
        }
      ],
      "steps": [
        {
          "no": 1,
          "name": "提取查询中的政治主题、时间隐含线索与语义焦点（如'减负''整治''形式主义'）"
        },
        {
          "no": 2,
          "name": "在KB-003中执行多粒度召回（标题匹配+段落语义+发布时间窗口过滤）"
        },
        {
          "no": 3,
          "name": "聚合匹配结果，输出标题、发布时间、主题、摘要及高亮原文片段，并标注数据来源（如《求是》2023年第X期）"
        }
      ],
      "outputs": [
        {
          "name": "讲话原文支撑包",
          "category": "讲话摘要+上下文"
        }
      ],
      "depends_on": [
        "KB-003"
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
      "修正建议",
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
      "name": "审核复核-跨文档类",
      "members": [
        "BP-002"
      ],
      "representative": "BP-002",
      "complexity_score": 0.52,
      "assigned_difficulty": "advanced"
    },
    {
      "type_id": "PT-003",
      "name": "知识咨询-单文档类",
      "members": [
        "BP-003"
      ],
      "representative": "BP-003",
      "complexity_score": 0.31,
      "assigned_difficulty": "basic"
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
      "process_type": "PT-001",
      "source_process": "BP-001",
      "difficulty": "basic",
      "focus_stages": [
        "执行落地"
      ],
      "sample_idx": 1
    },
    {
      "test_id": "TEST-003",
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
      "test_id": "TEST-004",
      "process_type": "PT-002",
      "source_process": "BP-002",
      "difficulty": "advanced",
      "focus_stages": [
        "拆解问题",
        "执行落地"
      ],
      "sample_idx": 1
    },
    {
      "test_id": "TEST-005",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "basic",
      "focus_stages": [
        "定义问题"
      ],
      "sample_idx": 0
    },
    {
      "test_id": "TEST-006",
      "process_type": "PT-003",
      "source_process": "BP-003",
      "difficulty": "basic",
      "focus_stages": [
        "执行落地"
      ],
      "sample_idx": 1
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
      "拆解问题": "常规",
      "方案生成": "常规",
      "执行落地": "重点",
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
      "定义问题": "常规",
      "拆解问题": "重点",
      "方案生成": "常规",
      "执行落地": "重点",
      "元认知": "常规"
    },
    "TEST-005": {
      "定义问题": "重点",
      "拆解问题": "常规",
      "方案生成": "常规",
      "执行落地": "常规",
      "元认知": "常规"
    },
    "TEST-006": {
      "定义问题": "常规",
      "拆解问题": "常规",
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
