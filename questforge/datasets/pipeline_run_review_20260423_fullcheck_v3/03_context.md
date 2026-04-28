---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-23T13:17:59+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 6 道题建立了知识索引(共 11089 个 fragment),LLM 生成 22 条约束、4 条干扰(其中 4 条陷阱)。业务真实性通过 26/26。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-001,TEST-002,TEST-003,TEST-004,TEST-005,TEST-006 |
| KB-002 | 1006 | TEST-003,TEST-004,TEST-005,TEST-006 |
| KB-003 | 1235 | — |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (basic · 党纪法规语义检索支撑定性量纪建议)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0109、FRAG-001-0006、FRAG-001-0018
- **关键字候选**:违反政治纪律、违反工作纪律、违反廉洁纪律、政治纪律
- **约束项**(3):
  1. C-001 · 引用官方发布的最新版党纪条款作为唯一依据 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 整合知识咨询中提供的违纪事实要素，完成条款匹配并输出完整报告 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-003 · 报告必须包含条款原文、适用情形说明及定性结论三项内容 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-002 (basic · 党纪法规语义检索支撑定性量纪建议)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0109、FRAG-001-0006、FRAG-001-0018
- **关键字候选**:违反政治纪律、违反工作纪律、违反廉洁纪律、政治纪律
- **约束项**(3):
  1. C-004 · 引用官方发布的最新版党纪条款作为唯一依据 [来源:时效性 · 验证:regulation_support]
  1. C-005 · 排除非官方渠道或历史修订版本中的条款内容 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-006 · 完整生成党纪条款匹配报告，不得遗漏结构化要素 [来源:outputs_count > 1 · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-003 (advanced · 实务案例问答匹配驱动定性量纪智能建议)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0059、FRAG-002-0060、FRAG-002-0061、FRAG-002-0062、FRAG-002-0063、FRAG-002-0064
- **关键字候选**:八项规定精神、中央八项规定、违反八项规定
- **约束项**(4):
  1. C-007 · 引用党纪条款和实务问答两类官方资产，整合形成定性量纪综合建议 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-008 · 依据当前可用的最新官方发布版本党纪条款和实务问答开展审查 [来源:时效性 · 验证:regulation_support]
  1. C-009 · 识别案件研判触发点，对模糊事实描述主动追问必要信息以支撑定性 [来源:triggers · 验证:llm_judge]
  1. C-010 · 完整交付定性量纪综合建议，不得遗漏决策建议类输出项 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·该材料中提及的2021年某省纪委内部问答口径，与中央纪委最新实务问答存在表述差异，看似合理但可能影响定性结论。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-004 (advanced · 实务案例问答匹配驱动定性量纪智能建议)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0059、FRAG-002-0060、FRAG-002-0061、FRAG-002-0062、FRAG-002-0063、FRAG-002-0064
- **关键字候选**:八项规定精神、中央八项规定、违反八项规定
- **约束项**(4):
  1. C-011 · 引用党纪条款和实务问答两类官方资产，整合形成定性量纪综合建议 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-012 · 依据当前可用的最新官方发布版本党纪条款和实务问答开展审查 [来源:时效性 · 验证:regulation_support]
  1. C-013 · 识别案件研判触发点，对模糊事实描述主动追问必要信息以支撑定性 [来源:triggers · 验证:llm_judge]
  1. C-014 · 完整交付定性量纪综合建议，不得遗漏决策建议类输出项 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-002 · 陷阱·该案例中被审查人主动交代问题，看似合理地应予从轻处理，但需结合具体时间节点和交代内容完整性综合判断。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-005 (advanced · 纪检文书纠错辅助与多源知识协同审核)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0624、FRAG-002-0741、FRAG-002-0435、FRAG-002-0740、FRAG-002-0742、FRAG-002-0757
- **关键字候选**:应当受到党纪处分、受到党纪处分的、处置审查调查过程、审查调查过程中、根据党纪处分条例、属于审查调查报告、四种形态、具体问题具体分析
- **约束项**(4):
  1. C-015 · 引用党纪条款和实务问答两类官方资产，整合形成知识锚定依据 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-016 · 依据当前可用的最新官方发布版本，排除过时条款或问答内容 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-017 · 完整交付文书纠错分析报告与知识锚定修订版文书两项输出，缺一不可 [来源:outputs_count > 1 · 验证:regulation_support]
  1. C-018 · 在审核复核触发场景下，对模糊表述主动标注存疑点并提示需人工确认 [来源:triggers · 验证:llm_judge]
- **干扰项**(1):
  1. I-003 · 陷阱·该文书引用的党纪条款版本与实务问答库中最新解读存在表述差异，看似合理但需核对时效性。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-006 (advanced · 纪检文书纠错辅助与多源知识协同审核)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0624、FRAG-002-0741、FRAG-002-0435、FRAG-002-0740、FRAG-002-0742、FRAG-002-0757
- **关键字候选**:应当受到党纪处分、受到党纪处分的、处置审查调查过程、审查调查过程中、根据党纪处分条例、属于审查调查报告、四种形态、具体问题具体分析
- **约束项**(4):
  1. C-019 · 引用党纪条款和实务问答两类官方资产，整合形成知识锚定依据 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-020 · 依据当前可用的最新官方发布版本，排除过时条款或问答内容 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-021 · 完整交付文书纠错分析报告和知识锚定修订版文书两项输出 [来源:outputs_count · 验证:regulation_support]
  1. C-022 · 在审核复核触发场景下，主动识别并标注需人工复核的模糊表述条目 [来源:triggers · 验证:llm_judge]
- **干扰项**(1):
  1. I-004 · 陷阱·该文书引用的党纪条款版本与实务问答库中最新解读存在表述差异，看似合理但需核验时效性。 [验证:regulation_support]
- **真实性验证**:5/5

## 结构化数据
```json
{
  "fallback_status": {
    "weak_points_present": false
  },
  "authority_keywords_count": 32,
  "knowledge_index": {
    "KB-001": {
      "total_fragments": 3849,
      "covered_by": [
        "TEST-001",
        "TEST-002",
        "TEST-003",
        "TEST-004",
        "TEST-005",
        "TEST-006"
      ]
    },
    "KB-002": {
      "total_fragments": 1006,
      "covered_by": [
        "TEST-003",
        "TEST-004",
        "TEST-005",
        "TEST-006"
      ]
    },
    "KB-003": {
      "total_fragments": 1235,
      "covered_by": []
    },
    "KB-004": {
      "total_fragments": 4999,
      "covered_by": []
    }
  },
  "test_contexts": [
    {
      "test_id": "TEST-001",
      "difficulty": "basic",
      "primary_assets": [
        "KB-001"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-001-0109",
          "asset_id": "KB-001",
          "snippet": "违反政治纪律, 违反廉洁纪律, 违反群众纪律, 违反工作纪律, 违反生活纪律 | 违反政治纪律和政治规矩，利用职权或者职务上的影响为他人谋取利益，收受可能影响公正执行公务的财物，违反办公用房管理规定，违反会议活动管理规定"
        },
        {
          "frag_id": "FRAG-001-0006",
          "asset_id": "KB-001",
          "snippet": "党纪处分条例、违反政治纪律、违反组织纪律、违反廉洁纪律、违反群众纪律 | 违反政治纪律、违反组织纪律、违反廉洁纪律、违反群众纪律、违反工作纪律、违反生活纪律"
        },
        {
          "frag_id": "FRAG-001-0018",
          "asset_id": "KB-001",
          "snippet": "纪律处分, 党员, 党组织, 违纪行为, 政治纪律 | 违反政治纪律、组织纪律、廉洁纪律、群众纪律、工作纪律、生活纪律"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "违反政治纪律",
        "违反工作纪律",
        "违反廉洁纪律",
        "政治纪律"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "引用官方发布的最新版党纪条款作为唯一依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "整合知识咨询中提供的违纪事实要素，完成条款匹配并输出完整报告",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-003",
          "text": "报告必须包含条款原文、适用情形说明及定性结论三项内容",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [],
      "realism_check": {
        "total": 3,
        "passed": 3
      }
    },
    {
      "test_id": "TEST-002",
      "difficulty": "basic",
      "primary_assets": [
        "KB-001"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-001-0109",
          "asset_id": "KB-001",
          "snippet": "违反政治纪律, 违反廉洁纪律, 违反群众纪律, 违反工作纪律, 违反生活纪律 | 违反政治纪律和政治规矩，利用职权或者职务上的影响为他人谋取利益，收受可能影响公正执行公务的财物，违反办公用房管理规定，违反会议活动管理规定"
        },
        {
          "frag_id": "FRAG-001-0006",
          "asset_id": "KB-001",
          "snippet": "党纪处分条例、违反政治纪律、违反组织纪律、违反廉洁纪律、违反群众纪律 | 违反政治纪律、违反组织纪律、违反廉洁纪律、违反群众纪律、违反工作纪律、违反生活纪律"
        },
        {
          "frag_id": "FRAG-001-0018",
          "asset_id": "KB-001",
          "snippet": "纪律处分, 党员, 党组织, 违纪行为, 政治纪律 | 违反政治纪律、组织纪律、廉洁纪律、群众纪律、工作纪律、生活纪律"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "违反政治纪律",
        "违反工作纪律",
        "违反廉洁纪律",
        "政治纪律"
      ],
      "constraints": [
        {
          "id": "C-004",
          "text": "引用官方发布的最新版党纪条款作为唯一依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-005",
          "text": "排除非官方渠道或历史修订版本中的条款内容",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "完整生成党纪条款匹配报告，不得遗漏结构化要素",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [],
      "realism_check": {
        "total": 3,
        "passed": 3
      }
    },
    {
      "test_id": "TEST-003",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0059",
          "asset_id": "KB-002",
          "snippet": "第一批执纪执法指导性案例聚焦什么问题？ | 此次发布的案例，聚焦违反中央八项规定精神典型问题 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 20210804 中央纪委国家…"
        },
        {
          "frag_id": "FRAG-002-0060",
          "asset_id": "KB-002",
          "snippet": "指导性案例针对哪些实践中的问题？ | 针对实践中存在的性质认定、条规适用、处理处分不精准不恰当等问题 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 20210804 中央…"
        },
        {
          "frag_id": "FRAG-002-0061",
          "asset_id": "KB-002",
          "snippet": "指导性案例阐释了哪些内容？ | 阐释执纪执法要旨、政策策略把握、定性量纪理由、纪法条规适用等内容 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 20210804 中央纪委…"
        },
        {
          "frag_id": "FRAG-002-0062",
          "asset_id": "KB-002",
          "snippet": "指导性案例释放了什么信号？ | 持续释放整治违反中央八项规定精神问题“越往后越严”的强烈信号 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 20210804 中央纪委国家…"
        },
        {
          "frag_id": "FRAG-002-0063",
          "asset_id": "KB-002",
          "snippet": "建立执纪执法指导性案例制度的依据是什么？ | 为深入贯彻落实十九届中央纪委五次全会精神和中央纪委办公厅《关于加强和改进案件审理工作的意见》等规定 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx |…"
        },
        {
          "frag_id": "FRAG-002-0064",
          "asset_id": "KB-002",
          "snippet": "各级纪检监察机关应如何对待指导性案例？ | 各级纪检监察机关在办理同类案件、处理同类问题时，应当参照指导性案例 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 202108…"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-004-2196",
          "asset_id": "KB-004"
        },
        {
          "frag_id": "FRAG-003-1132",
          "asset_id": "KB-003"
        }
      ],
      "keyword_pool": [
        "八项规定精神",
        "中央八项规定",
        "违反八项规定"
      ],
      "constraints": [
        {
          "id": "C-007",
          "text": "引用党纪条款和实务问答两类官方资产，整合形成定性量纪综合建议",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "依据当前可用的最新官方发布版本党纪条款和实务问答开展审查",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-009",
          "text": "识别案件研判触发点，对模糊事实描述主动追问必要信息以支撑定性",
          "source": "triggers",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-010",
          "text": "完整交付定性量纪综合建议，不得遗漏决策建议类输出项",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "该材料中提及的2021年某省纪委内部问答口径，与中央纪委最新实务问答存在表述差异，看似合理但可能影响定性结论。",
          "trap": true,
          "process_ref": "实务案例问答匹配驱动定性量纪智能建议",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 5,
        "passed": 5
      }
    },
    {
      "test_id": "TEST-004",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0059",
          "asset_id": "KB-002",
          "snippet": "第一批执纪执法指导性案例聚焦什么问题？ | 此次发布的案例，聚焦违反中央八项规定精神典型问题 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 20210804 中央纪委国家…"
        },
        {
          "frag_id": "FRAG-002-0060",
          "asset_id": "KB-002",
          "snippet": "指导性案例针对哪些实践中的问题？ | 针对实践中存在的性质认定、条规适用、处理处分不精准不恰当等问题 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 20210804 中央…"
        },
        {
          "frag_id": "FRAG-002-0061",
          "asset_id": "KB-002",
          "snippet": "指导性案例阐释了哪些内容？ | 阐释执纪执法要旨、政策策略把握、定性量纪理由、纪法条规适用等内容 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 20210804 中央纪委…"
        },
        {
          "frag_id": "FRAG-002-0062",
          "asset_id": "KB-002",
          "snippet": "指导性案例释放了什么信号？ | 持续释放整治违反中央八项规定精神问题“越往后越严”的强烈信号 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 20210804 中央纪委国家…"
        },
        {
          "frag_id": "FRAG-002-0063",
          "asset_id": "KB-002",
          "snippet": "建立执纪执法指导性案例制度的依据是什么？ | 为深入贯彻落实十九届中央纪委五次全会精神和中央纪委办公厅《关于加强和改进案件审理工作的意见》等规定 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx |…"
        },
        {
          "frag_id": "FRAG-002-0064",
          "asset_id": "KB-002",
          "snippet": "各级纪检监察机关应如何对待指导性案例？ | 各级纪检监察机关在办理同类案件、处理同类问题时，应当参照指导性案例 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段1:文档标题: 202108…"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-004-4127",
          "asset_id": "KB-004"
        },
        {
          "frag_id": "FRAG-004-4971",
          "asset_id": "KB-004"
        }
      ],
      "keyword_pool": [
        "八项规定精神",
        "中央八项规定",
        "违反八项规定"
      ],
      "constraints": [
        {
          "id": "C-011",
          "text": "引用党纪条款和实务问答两类官方资产，整合形成定性量纪综合建议",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-012",
          "text": "依据当前可用的最新官方发布版本党纪条款和实务问答开展审查",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-013",
          "text": "识别案件研判触发点，对模糊事实描述主动追问必要信息以支撑定性",
          "source": "triggers",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-014",
          "text": "完整交付定性量纪综合建议，不得遗漏决策建议类输出项",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-002",
          "text": "该案例中被审查人主动交代问题，看似合理地应予从轻处理，但需结合具体时间节点和交代内容完整性综合判断。",
          "trap": true,
          "process_ref": "实务案例问答匹配驱动定性量纪智能建议",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 5,
        "passed": 5
      }
    },
    {
      "test_id": "TEST-005",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0624",
          "asset_id": "KB-002",
          "snippet": "李某某的行为被认定违反了什么纪律？ | 李某某的行为违反群众纪律 | 第三批准确有效运用“四种形态”典型案例.docx | 片段4:2018年  6月至2020年12月，青光村按照每年 100元/亩的标准收取协调费共计17.11 万余元，用…"
        },
        {
          "frag_id": "FRAG-002-0741",
          "asset_id": "KB-002",
          "snippet": "王某某受到什么处分？ | 给予王某某党内严重警告处分，并予以免职、调离原单位处理 | 第二批准确有效运用“四种形态”典型案例.docx | 片段4:09 |光风廉政建设宁夏：王某某对监管服务对象吃拿索要案(2023年典型案例第1号，总第5号…"
        },
        {
          "frag_id": "FRAG-002-0435",
          "asset_id": "KB-002",
          "snippet": "审理报告能否直接提出撤销案件意见 | 笔者认为 ，这不符合纪检监察机关依规依纪依法履行职责的  要求。 | 审理报告中可否提出 “撤销案件”意见.docx | 片段1:文档标题: 审理报告中可否提出 “撤销案件”意见 序号: 1872 文档…"
        },
        {
          "frag_id": "FRAG-002-0740",
          "asset_id": "KB-002",
          "snippet": "本案的处理依据是什么？ | 运用“四种形态”,应当坚持宽严相济、区别处理，做到纪法情理贯通融合，具体问题具体分析，综合考虑错误性质、情节后果、主观态度等因素，依规依纪依法提出处理意见，确保严之有据、宽之有度。 | 第二批准确有效运用“四种形…"
        },
        {
          "frag_id": "FRAG-002-0742",
          "asset_id": "KB-002",
          "snippet": "王某某的违纪行为有哪些？ | 2017年、2018年、2020年春节前，王某某多次接受辖区监管服务对象所送的米面油、熟食品等供自己、亲属以及单位工作人员食用，价值716元；2020年春节前，王某某召集市场监管所工作人员约10人，接受辖区某餐…"
        },
        {
          "frag_id": "FRAG-002-0757",
          "asset_id": "KB-002",
          "snippet": "富拉尔基区纪委对违建问题的处理意见是什么？ | 2021年4月，富拉尔基区纪委经核 查后对奋斗社区服务中心违建问题所涉 王某某等4名同志提出拟容错免责的意 见，报送齐齐哈尔市纪委审批。 | 第二批准确有效运用“四种形态”典型案例.docx …"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-004-4356",
          "asset_id": "KB-004"
        },
        {
          "frag_id": "FRAG-003-0473",
          "asset_id": "KB-003"
        }
      ],
      "keyword_pool": [
        "应当受到党纪处分",
        "受到党纪处分的",
        "处置审查调查过程",
        "审查调查过程中",
        "根据党纪处分条例",
        "属于审查调查报告",
        "四种形态",
        "具体问题具体分析"
      ],
      "constraints": [
        {
          "id": "C-015",
          "text": "引用党纪条款和实务问答两类官方资产，整合形成知识锚定依据",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-016",
          "text": "依据当前可用的最新官方发布版本，排除过时条款或问答内容",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-017",
          "text": "完整交付文书纠错分析报告与知识锚定修订版文书两项输出，缺一不可",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-018",
          "text": "在审核复核触发场景下，对模糊表述主动标注存疑点并提示需人工确认",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-003",
          "text": "该文书引用的党纪条款版本与实务问答库中最新解读存在表述差异，看似合理但需核对时效性。",
          "trap": true,
          "process_ref": "纪检文书纠错辅助与多源知识协同审核",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 5,
        "passed": 5
      }
    },
    {
      "test_id": "TEST-006",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0624",
          "asset_id": "KB-002",
          "snippet": "李某某的行为被认定违反了什么纪律？ | 李某某的行为违反群众纪律 | 第三批准确有效运用“四种形态”典型案例.docx | 片段4:2018年  6月至2020年12月，青光村按照每年 100元/亩的标准收取协调费共计17.11 万余元，用…"
        },
        {
          "frag_id": "FRAG-002-0741",
          "asset_id": "KB-002",
          "snippet": "王某某受到什么处分？ | 给予王某某党内严重警告处分，并予以免职、调离原单位处理 | 第二批准确有效运用“四种形态”典型案例.docx | 片段4:09 |光风廉政建设宁夏：王某某对监管服务对象吃拿索要案(2023年典型案例第1号，总第5号…"
        },
        {
          "frag_id": "FRAG-002-0435",
          "asset_id": "KB-002",
          "snippet": "审理报告能否直接提出撤销案件意见 | 笔者认为 ，这不符合纪检监察机关依规依纪依法履行职责的  要求。 | 审理报告中可否提出 “撤销案件”意见.docx | 片段1:文档标题: 审理报告中可否提出 “撤销案件”意见 序号: 1872 文档…"
        },
        {
          "frag_id": "FRAG-002-0740",
          "asset_id": "KB-002",
          "snippet": "本案的处理依据是什么？ | 运用“四种形态”,应当坚持宽严相济、区别处理，做到纪法情理贯通融合，具体问题具体分析，综合考虑错误性质、情节后果、主观态度等因素，依规依纪依法提出处理意见，确保严之有据、宽之有度。 | 第二批准确有效运用“四种形…"
        },
        {
          "frag_id": "FRAG-002-0742",
          "asset_id": "KB-002",
          "snippet": "王某某的违纪行为有哪些？ | 2017年、2018年、2020年春节前，王某某多次接受辖区监管服务对象所送的米面油、熟食品等供自己、亲属以及单位工作人员食用，价值716元；2020年春节前，王某某召集市场监管所工作人员约10人，接受辖区某餐…"
        },
        {
          "frag_id": "FRAG-002-0757",
          "asset_id": "KB-002",
          "snippet": "富拉尔基区纪委对违建问题的处理意见是什么？ | 2021年4月，富拉尔基区纪委经核 查后对奋斗社区服务中心违建问题所涉 王某某等4名同志提出拟容错免责的意 见，报送齐齐哈尔市纪委审批。 | 第二批准确有效运用“四种形态”典型案例.docx …"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-004-2012",
          "asset_id": "KB-004"
        },
        {
          "frag_id": "FRAG-004-0809",
          "asset_id": "KB-004"
        }
      ],
      "keyword_pool": [
        "应当受到党纪处分",
        "受到党纪处分的",
        "处置审查调查过程",
        "审查调查过程中",
        "根据党纪处分条例",
        "属于审查调查报告",
        "四种形态",
        "具体问题具体分析"
      ],
      "constraints": [
        {
          "id": "C-019",
          "text": "引用党纪条款和实务问答两类官方资产，整合形成知识锚定依据",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-020",
          "text": "依据当前可用的最新官方发布版本，排除过时条款或问答内容",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-021",
          "text": "完整交付文书纠错分析报告和知识锚定修订版文书两项输出",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-022",
          "text": "在审核复核触发场景下，主动识别并标注需人工复核的模糊表述条目",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-004",
          "text": "该文书引用的党纪条款版本与实务问答库中最新解读存在表述差异，看似合理但需核验时效性。",
          "trap": true,
          "process_ref": "纪检文书纠错辅助与多源知识协同审核",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 5,
        "passed": 5
      }
    }
  ]
}
```

## 下一阶段校验清单
- [x] 每道 TEST 至少 1 个约束项
- [x] basic 0 干扰、advanced 1、expert ≥2 且含 1 陷阱
- [x] 每条约束/干扰通过真实性三检验之一
- [x] 每道 TEST 的 keyword_pool ≥ 1
- [x] 每道 TEST 的 fragments ≥ 1

## 备注与遗留问题
(无)
