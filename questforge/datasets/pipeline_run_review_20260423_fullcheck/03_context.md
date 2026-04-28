---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-23T13:02:10+08:00
created_by: agent-stage3
pass_gate: false
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 6 道题建立了知识索引(共 11089 个 fragment),LLM 生成 22 条约束、4 条干扰(其中 3 条陷阱)。业务真实性通过 26/26。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-001,TEST-002,TEST-005,TEST-006 |
| KB-002 | 1006 | TEST-001,TEST-002,TEST-005,TEST-006 |
| KB-003 | 1235 | TEST-003,TEST-004 |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (advanced · 党纪法规语义检索支撑定性量纪建议生成)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0286、FRAG-002-0287、FRAG-002-0288、FRAG-002-0289、FRAG-002-0290、FRAG-002-0291
- **关键字候选**:违反工作纪律、廉洁纪律问题、违反廉洁纪律、违规从事营利活动
- **约束项**(4):
  1. C-001 · 引用结构化条款库和实务问答库中最新发布的官方版本 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 整合结构化条款与实务问答两类资产信息，形成统一的定性量纪依据 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-003 · 依据知识咨询触发场景，主动识别并标注建议书中所涉条款的适用边界 [来源:triggers · 验证:llm_judge]
  1. C-004 · 完整生成定性量纪建议书，确保结论可直接用于纪检决策环节 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·该材料中引用的实务问答库内容与最新党纪处分条例条款存在表述差异，看似合理但需核验时效性。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-002 (advanced · 党纪法规语义检索支撑定性量纪建议生成)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0286、FRAG-002-0287、FRAG-002-0288、FRAG-002-0289、FRAG-002-0290、FRAG-002-0291
- **关键字候选**:违反工作纪律、廉洁纪律问题、违反廉洁纪律、违规从事营利活动
- **约束项**(4):
  1. C-005 · 引用结构化条款库和实务问答库中最新发布的官方版本 [来源:时效性 · 验证:regulation_support]
  1. C-006 · 整合结构化条款与实务问答两类资产信息，形成统一的定性量纪依据 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-007 · 依据党纪法规语义检索结果，完整生成定性量纪建议书，不得遗漏结论、依据和适用情形 [来源:outputs_count · 验证:regulation_support]
  1. C-008 · 对知识咨询类触发场景，需主动识别并标注建议中涉及的模糊表述或需人工复核的推断点 [来源:triggers · 验证:llm_judge]
- **干扰项**(1):
  1. I-002 · 陷阱·纪检材料审查中，实务问答库对‘主动交代’的认定标准与最新党纪处分条例存在表述差异，可能引发定性冲突。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-003 (basic · 总书记讲话精准召回支持政治表述合规审查)
- **主资产**:KB-003
- **核心 fragment**:
- **关键字候选**:—
- **约束项**(3):
  1. C-009 · 引用官方发布的讲话摘要及上下文作为唯一依据 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-010 · 整合讲话原文与上下文片段，确保政治表述审查结论完整覆盖报告要求 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-011 · 依据当前可用资产中最权威、最新的官方发布版本开展审查 [来源:基础约束 · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-004 (basic · 总书记讲话精准召回支持政治表述合规审查)
- **主资产**:KB-003
- **核心 fragment**:
- **关键字候选**:—
- **约束项**(3):
  1. C-012 · 引用官方发布的总书记讲话摘要及上下文作为唯一依据 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-013 · 整合讲话原文与上下文语义，确保政治表述审查结论不脱离原始语境 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-014 · 输出完整政治表述合规报告，不得遗漏任一合规项判定结果 [来源:outputs_count > 1 · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-005 (advanced · 纪检文书全量纠错与多源知识协同验证)
- **主资产**:KB-001、KB-002
- **核心 fragment**:
- **关键字候选**:—
- **约束项**(4):
  1. C-015 · 引用结构化条款库和实务问答库中的最新官方版本进行协同验证 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-016 · 排除结构化条款库和实务问答库中非官方发布或已废止的条目 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-017 · 识别管理级人员权限边界，对涉及内部管理规则的内容标注‘需管理级复核’ [来源:actors 含"管理"层级 · 验证:llm_judge]
  1. C-018 · 完整交付文书纠错意见书，包含错误定位、依据条款、修正建议三项要素 [来源:outputs_count > 1 · 验证:regulation_support]
- **干扰项**(1):
  1. I-003 · 纪检文书纠错需同步比对结构化条款和实务问答，二者权威性相同，可直接交叉验证。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-006 (advanced · 纪检文书全量纠错与多源知识协同验证)
- **主资产**:KB-001、KB-002
- **核心 fragment**:
- **关键字候选**:—
- **约束项**(4):
  1. C-019 · 引用结构化条款库与实务问答库中最新官方版本，排除过时条目 [来源:时效性 · 验证:regulation_support]
  1. C-020 · 整合结构化条款与实务问答两类知识源，协同验证文书表述合规性 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-021 · 识别管理级权限要求，对涉及处分建议等受限内容标注权限提示 [来源:actors · 验证:regulation_support]
  1. C-022 · 依据审核复核触发场景，主动推断需补正的隐含事实依据并列明 [来源:triggers · 验证:llm_judge]
- **干扰项**(1):
  1. I-004 · 陷阱·文书纠错意见书需同步抄送组织部门，看似合理但实际超出该流程职责范围 [验证:regulation_support]
- **真实性验证**:5/5

## 结构化数据
```json
{
  "fallback_status": {
    "weak_points_present": false
  },
  "authority_keywords_count": 14,
  "knowledge_index": {
    "KB-001": {
      "total_fragments": 3849,
      "covered_by": [
        "TEST-001",
        "TEST-002",
        "TEST-005",
        "TEST-006"
      ]
    },
    "KB-002": {
      "total_fragments": 1006,
      "covered_by": [
        "TEST-001",
        "TEST-002",
        "TEST-005",
        "TEST-006"
      ]
    },
    "KB-003": {
      "total_fragments": 1235,
      "covered_by": [
        "TEST-003",
        "TEST-004"
      ]
    },
    "KB-004": {
      "total_fragments": 4999,
      "covered_by": []
    }
  },
  "test_contexts": [
    {
      "test_id": "TEST-001",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0286",
          "asset_id": "KB-002",
          "snippet": "营利活动合规但方式不当可能违反哪些纪律？ | 党员领导干部炒股但未按要求进行个人事项报告可能违反组织纪律；工作时间从事营利活动造成损失或不良影响可能违反工作纪律等。 | 党员干部从事营利活动的纪法罪认定.docx | 片段3:区分 营利活动…"
        },
        {
          "frag_id": "FRAG-002-0287",
          "asset_id": "KB-002",
          "snippet": "党政机关领导干部在营利活动方面有何限制？ | 党政机关领导干部不得经商办企业。 | 党员干部从事营利活动的纪法罪认定.docx | 片段3:区分 营利活动合规还是违纪 ，既要贯彻民法典的法治精神和法治 理念 ，尊重和保护党员干部个人合法财产…"
        },
        {
          "frag_id": "FRAG-002-0288",
          "asset_id": "KB-002",
          "snippet": "违规从事营利活动的违纪和职务违法认定依据有何不同？ | 党纪党规对违规从事营利活动的违纪行为进行规范；政务处分法、公务员法和事业单位工作人员处分暂行规定等法律法规对违规从事营利活动的违法行为进行规范。 | 党员干部从事营利活动的纪法罪认定.…"
        },
        {
          "frag_id": "FRAG-002-0289",
          "asset_id": "KB-002",
          "snippet": "事业单位工作人员违规从事营利活动如何认定？ | 事业单位工作人员的情况则相对复杂，需要考虑其是否属于参照公务员法管理人员、管理岗位还是专业技术岗位人员等情况，根据国家、地区、行业、系统等相关规定进行具体分析。 | 党员干部从事营利活动的纪法…"
        },
        {
          "frag_id": "FRAG-002-0290",
          "asset_id": "KB-002",
          "snippet": "判断投资营利是否违纪的关键是什么？ | 投资营利是否违纪，关键在于判断党员领导干部从事营利活动是否“违反有关规定”。 | 党员干部从事营利活动的纪法罪认定.docx | 片段3:区分 营利活动合规还是违纪 ，既要贯彻民法典的法治精神和法治 …"
        },
        {
          "frag_id": "FRAG-002-0291",
          "asset_id": "KB-002",
          "snippet": "违规从事营利活动的违纪点是什么？ | 其违纪点在于市场本不可进入而违规进入 | 党员干部从事营利活动的纪法罪认定.docx | 片段3:区分 营利活动合规还是违纪 ，既要贯彻民法典的法治精神和法治 理念 ，尊重和保护党员干部个人合法财产 ，…"
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
        "违反工作纪律",
        "廉洁纪律问题",
        "违反廉洁纪律",
        "违规从事营利活动"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "引用结构化条款库和实务问答库中最新发布的官方版本",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "整合结构化条款与实务问答两类资产信息，形成统一的定性量纪依据",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "依据知识咨询触发场景，主动识别并标注建议书中所涉条款的适用边界",
          "source": "triggers",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-004",
          "text": "完整生成定性量纪建议书，确保结论可直接用于纪检决策环节",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "该材料中引用的实务问答库内容与最新党纪处分条例条款存在表述差异，看似合理但需核验时效性。",
          "trap": true,
          "process_ref": "党纪法规语义检索支撑定性量纪建议生成",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 5,
        "passed": 5
      }
    },
    {
      "test_id": "TEST-002",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0286",
          "asset_id": "KB-002",
          "snippet": "营利活动合规但方式不当可能违反哪些纪律？ | 党员领导干部炒股但未按要求进行个人事项报告可能违反组织纪律；工作时间从事营利活动造成损失或不良影响可能违反工作纪律等。 | 党员干部从事营利活动的纪法罪认定.docx | 片段3:区分 营利活动…"
        },
        {
          "frag_id": "FRAG-002-0287",
          "asset_id": "KB-002",
          "snippet": "党政机关领导干部在营利活动方面有何限制？ | 党政机关领导干部不得经商办企业。 | 党员干部从事营利活动的纪法罪认定.docx | 片段3:区分 营利活动合规还是违纪 ，既要贯彻民法典的法治精神和法治 理念 ，尊重和保护党员干部个人合法财产…"
        },
        {
          "frag_id": "FRAG-002-0288",
          "asset_id": "KB-002",
          "snippet": "违规从事营利活动的违纪和职务违法认定依据有何不同？ | 党纪党规对违规从事营利活动的违纪行为进行规范；政务处分法、公务员法和事业单位工作人员处分暂行规定等法律法规对违规从事营利活动的违法行为进行规范。 | 党员干部从事营利活动的纪法罪认定.…"
        },
        {
          "frag_id": "FRAG-002-0289",
          "asset_id": "KB-002",
          "snippet": "事业单位工作人员违规从事营利活动如何认定？ | 事业单位工作人员的情况则相对复杂，需要考虑其是否属于参照公务员法管理人员、管理岗位还是专业技术岗位人员等情况，根据国家、地区、行业、系统等相关规定进行具体分析。 | 党员干部从事营利活动的纪法…"
        },
        {
          "frag_id": "FRAG-002-0290",
          "asset_id": "KB-002",
          "snippet": "判断投资营利是否违纪的关键是什么？ | 投资营利是否违纪，关键在于判断党员领导干部从事营利活动是否“违反有关规定”。 | 党员干部从事营利活动的纪法罪认定.docx | 片段3:区分 营利活动合规还是违纪 ，既要贯彻民法典的法治精神和法治 …"
        },
        {
          "frag_id": "FRAG-002-0291",
          "asset_id": "KB-002",
          "snippet": "违规从事营利活动的违纪点是什么？ | 其违纪点在于市场本不可进入而违规进入 | 党员干部从事营利活动的纪法罪认定.docx | 片段3:区分 营利活动合规还是违纪 ，既要贯彻民法典的法治精神和法治 理念 ，尊重和保护党员干部个人合法财产 ，…"
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
        "违反工作纪律",
        "廉洁纪律问题",
        "违反廉洁纪律",
        "违规从事营利活动"
      ],
      "constraints": [
        {
          "id": "C-005",
          "text": "引用结构化条款库和实务问答库中最新发布的官方版本",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "整合结构化条款与实务问答两类资产信息，形成统一的定性量纪依据",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-007",
          "text": "依据党纪法规语义检索结果，完整生成定性量纪建议书，不得遗漏结论、依据和适用情形",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "对知识咨询类触发场景，需主动识别并标注建议中涉及的模糊表述或需人工复核的推断点",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-002",
          "text": "纪检材料审查中，实务问答库对‘主动交代’的认定标准与最新党纪处分条例存在表述差异，可能引发定性冲突。",
          "trap": true,
          "process_ref": "党纪法规语义检索支撑定性量纪建议生成",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 5,
        "passed": 5
      }
    },
    {
      "test_id": "TEST-003",
      "difficulty": "basic",
      "primary_assets": [
        "KB-003"
      ],
      "fragments": [],
      "interference_fragments": [],
      "keyword_pool": [],
      "constraints": [
        {
          "id": "C-009",
          "text": "引用官方发布的讲话摘要及上下文作为唯一依据",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-010",
          "text": "整合讲话原文与上下文片段，确保政治表述审查结论完整覆盖报告要求",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-011",
          "text": "依据当前可用资产中最权威、最新的官方发布版本开展审查",
          "source": "基础约束",
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
      "test_id": "TEST-004",
      "difficulty": "basic",
      "primary_assets": [
        "KB-003"
      ],
      "fragments": [],
      "interference_fragments": [],
      "keyword_pool": [],
      "constraints": [
        {
          "id": "C-012",
          "text": "引用官方发布的总书记讲话摘要及上下文作为唯一依据",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-013",
          "text": "整合讲话原文与上下文语义，确保政治表述审查结论不脱离原始语境",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-014",
          "text": "输出完整政治表述合规报告，不得遗漏任一合规项判定结果",
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
      "test_id": "TEST-005",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [],
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
      "keyword_pool": [],
      "constraints": [
        {
          "id": "C-015",
          "text": "引用结构化条款库和实务问答库中的最新官方版本进行协同验证",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-016",
          "text": "排除结构化条款库和实务问答库中非官方发布或已废止的条目",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-017",
          "text": "识别管理级人员权限边界，对涉及内部管理规则的内容标注‘需管理级复核’",
          "source": "actors 含\"管理\"层级",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-018",
          "text": "完整交付文书纠错意见书，包含错误定位、依据条款、修正建议三项要素",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-003",
          "text": "纪检文书纠错需同步比对结构化条款和实务问答，二者权威性相同，可直接交叉验证。",
          "trap": false,
          "process_ref": "纪检文书全量纠错与多源知识协同验证",
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
      "fragments": [],
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
      "keyword_pool": [],
      "constraints": [
        {
          "id": "C-019",
          "text": "引用结构化条款库与实务问答库中最新官方版本，排除过时条目",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-020",
          "text": "整合结构化条款与实务问答两类知识源，协同验证文书表述合规性",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-021",
          "text": "识别管理级权限要求，对涉及处分建议等受限内容标注权限提示",
          "source": "actors",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-022",
          "text": "依据审核复核触发场景，主动推断需补正的隐含事实依据并列明",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-004",
          "text": "文书纠错意见书需同步抄送组织部门，看似合理但实际超出该流程职责范围",
          "trap": true,
          "process_ref": "纪检文书全量纠错与多源知识协同验证",
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
- [ ] 每道 TEST 的 keyword_pool ≥ 1
- [ ] 每道 TEST 的 fragments ≥ 1

## 备注与遗留问题
(无)
