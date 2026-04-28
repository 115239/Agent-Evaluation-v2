---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-23T09:36:55+08:00
created_by: agent-stage3
pass_gate: false
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 6 道题建立了知识索引(共 11089 个 fragment),LLM 生成 19 条约束、2 条干扰(其中 2 条陷阱)。业务真实性通过 21/22。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-001,TEST-002,TEST-003,TEST-004 |
| KB-002 | 1006 | TEST-003,TEST-004 |
| KB-003 | 1235 | TEST-005,TEST-006 |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (basic · 党纪法规语义检索支撑定性量纪建议生成)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0109、FRAG-001-0106、FRAG-001-0418
- **关键字候选**:违反政治纪律、违反工作纪律、中央八项规定、八项规定精神、市场主体提供信息、人民法院工作人员
- **约束项**(3):
  1. C-001 · 引用官方发布的最新版结构化条款作为唯一依据 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 整合知识咨询中提供的具体违纪情形与条款库中的对应片段进行语义匹配 [来源:triggers · 验证:regulation_support]
  1. C-003 · 完整输出定性量纪建议依据清单，不得遗漏任一条款引用项 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-002 (basic · 党纪法规语义检索支撑定性量纪建议生成)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0109、FRAG-001-0106、FRAG-001-0418
- **关键字候选**:违反政治纪律、违反工作纪律、中央八项规定、八项规定精神、市场主体提供信息、人民法院工作人员
- **约束项**(3):
  1. C-004 · 引用官方发布的最新版结构化条款作为唯一依据 [来源:时效性 · 验证:regulation_support]
  1. C-005 · 整合知识咨询中提供的具体违纪情形与条款库中的对应片段进行语义匹配 [来源:triggers · 验证:regulation_support]
  1. C-006 · 完整输出定性量纪建议依据清单，不得遗漏任一条款引用项 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-003 (advanced · 纪检文书纠错闭环处理（以谈话方案及安全预案为例）)
- **主资产**:KB-001、KB-002
- **核心 fragment**:
- **关键字候选**:—
- **约束项**(4):
  1. C-007 · 引用结构化条款库中最新官方版本的条款，排除历史修订稿内容 [来源:时效性 · 验证:regulation_support]
  1. C-008 · 整合结构化条款库与实务问答库中的相关条款，交叉验证谈话方案及安全预案的合规性 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-009 · 依据当前可用资产中最权威、最新的依据，给出文书纠错报告的完整修正建议 [来源:时效性 · 验证:regulation_support]
  1. C-010 · 在纠错报告中明确标注涉及权限边界的管理类要求，不得越权提出执行指令 [来源:actors · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·谈话方案中引用的条款版本与最新实务问答库中的解释存在冲突，需核对时效性。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-004 (advanced · 纪检文书纠错闭环处理（以谈话方案及安全预案为例）)
- **主资产**:KB-001、KB-002
- **核心 fragment**:
- **关键字候选**:—
- **约束项**(4):
  1. C-011 · 引用结构化条款库中最新官方发布版本，排除历史修订稿内容 [来源:时效性 · 验证:regulation_support]
  1. C-012 · 整合结构化条款库与实务问答库中的相关条款，形成交叉验证结论 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-013 · 依据审核复核触发场景，主动识别并标注文书纠错报告中需业务人员复核的修正建议 [来源:triggers · 验证:regulation_support]
  1. C-014 · 完整交付文书纠错报告，确保每条修正建议对应具体条款依据和风险等级说明 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-002 · 陷阱·谈话方案中引用的条款版本与最新实务问答库存在冲突，需核对时效性。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-005 (basic · 总书记讲话精准召回支持政治定性研判)
- **主资产**:KB-003
- **核心 fragment**:FRAG-003-0654、FRAG-003-0658、FRAG-003-0676
- **关键字候选**:中央八项规定、严明政治纪律、中国式现代化甘肃、谱写中国式现代化、中国式现代化湖北
- **约束项**(2):
  1. C-015 · 引用官方发布的讲话摘要+上下文资产，排除非官方渠道内容 [来源:assets_involved · 验证:regulation_support]
  1. C-016 · 依据当前可用的最新官方发布版本生成讲话原文支撑包 [来源:时效性 · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:2/3

### TEST-006 (basic · 总书记讲话精准召回支持政治定性研判)
- **主资产**:KB-003
- **核心 fragment**:FRAG-003-0654、FRAG-003-0658、FRAG-003-0676
- **关键字候选**:中央八项规定、严明政治纪律、中国式现代化甘肃、谱写中国式现代化、中国式现代化湖北
- **约束项**(3):
  1. C-018 · 引用官方发布的最新版本总书记讲话原文支撑包 [来源:时效性 · 验证:regulation_support]
  1. C-019 · 整合讲话摘要与上下文片段，形成完整支撑包 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-020 · 依据知识咨询触发场景，精准召回匹配政治定性所需的讲话内容 [来源:triggers · 验证:llm_judge]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

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
        "TEST-003",
        "TEST-004"
      ]
    },
    "KB-002": {
      "total_fragments": 1006,
      "covered_by": [
        "TEST-003",
        "TEST-004"
      ]
    },
    "KB-003": {
      "total_fragments": 1235,
      "covered_by": [
        "TEST-005",
        "TEST-006"
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
          "frag_id": "FRAG-001-0106",
          "asset_id": "KB-001",
          "snippet": "四种形态, 监督执纪, 疫情防控, 容错纠错, 违纪违法 | 王某某未对排查内蒙古阿拉善盟返京人员工作进行严格细致部署，仅通过微信群转发提醒，未采取有效措施督促镇卫生计生办对社区风险人员的排查工作进行督导检查；杨某在接到区防控办下发的风险人…"
        },
        {
          "frag_id": "FRAG-001-0418",
          "asset_id": "KB-001",
          "snippet": "人民法院工作人员, 廉政准则, 利益冲突, 营利性活动, 兼职 | 接受可能影响公正执行公务的礼金、礼品、宴请以及旅游、健身、娱乐等活动安排，从事营利性活动，为他人的经济活动提供担保，买卖股票或认股权证，利用在办案工作中获取的内幕信息买卖股…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "违反政治纪律",
        "违反工作纪律",
        "中央八项规定",
        "八项规定精神",
        "市场主体提供信息",
        "人民法院工作人员"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "引用官方发布的最新版结构化条款作为唯一依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "整合知识咨询中提供的具体违纪情形与条款库中的对应片段进行语义匹配",
          "source": "triggers",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "完整输出定性量纪建议依据清单，不得遗漏任一条款引用项",
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
          "frag_id": "FRAG-001-0106",
          "asset_id": "KB-001",
          "snippet": "四种形态, 监督执纪, 疫情防控, 容错纠错, 违纪违法 | 王某某未对排查内蒙古阿拉善盟返京人员工作进行严格细致部署，仅通过微信群转发提醒，未采取有效措施督促镇卫生计生办对社区风险人员的排查工作进行督导检查；杨某在接到区防控办下发的风险人…"
        },
        {
          "frag_id": "FRAG-001-0418",
          "asset_id": "KB-001",
          "snippet": "人民法院工作人员, 廉政准则, 利益冲突, 营利性活动, 兼职 | 接受可能影响公正执行公务的礼金、礼品、宴请以及旅游、健身、娱乐等活动安排，从事营利性活动，为他人的经济活动提供担保，买卖股票或认股权证，利用在办案工作中获取的内幕信息买卖股…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "违反政治纪律",
        "违反工作纪律",
        "中央八项规定",
        "八项规定精神",
        "市场主体提供信息",
        "人民法院工作人员"
      ],
      "constraints": [
        {
          "id": "C-004",
          "text": "引用官方发布的最新版结构化条款作为唯一依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-005",
          "text": "整合知识咨询中提供的具体违纪情形与条款库中的对应片段进行语义匹配",
          "source": "triggers",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "完整输出定性量纪建议依据清单，不得遗漏任一条款引用项",
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
      "test_id": "TEST-003",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [],
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
      "keyword_pool": [],
      "constraints": [
        {
          "id": "C-007",
          "text": "引用结构化条款库中最新官方版本的条款，排除历史修订稿内容",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "整合结构化条款库与实务问答库中的相关条款，交叉验证谈话方案及安全预案的合规性",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-009",
          "text": "依据当前可用资产中最权威、最新的依据，给出文书纠错报告的完整修正建议",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-010",
          "text": "在纠错报告中明确标注涉及权限边界的管理类要求，不得越权提出执行指令",
          "source": "actors",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "谈话方案中引用的条款版本与最新实务问答库中的解释存在冲突，需核对时效性。",
          "trap": true,
          "process_ref": "纪检文书纠错闭环处理（以谈话方案及安全预案为例）",
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
      "fragments": [],
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
      "keyword_pool": [],
      "constraints": [
        {
          "id": "C-011",
          "text": "引用结构化条款库中最新官方发布版本，排除历史修订稿内容",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-012",
          "text": "整合结构化条款库与实务问答库中的相关条款，形成交叉验证结论",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-013",
          "text": "依据审核复核触发场景，主动识别并标注文书纠错报告中需业务人员复核的修正建议",
          "source": "triggers",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-014",
          "text": "完整交付文书纠错报告，确保每条修正建议对应具体条款依据和风险等级说明",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-002",
          "text": "谈话方案中引用的条款版本与最新实务问答库存在冲突，需核对时效性。",
          "trap": true,
          "process_ref": "纪检文书纠错闭环处理（以谈话方案及安全预案为例）",
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
      "difficulty": "basic",
      "primary_assets": [
        "KB-003"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-003-0654",
          "asset_id": "KB-003",
          "snippet": "习近平在二十届中央纪委四次全会上发表重要讲话 | 2025-01-06 | 习近平在二十届中央纪委四次全会上发表重要讲话强调 坚持用改革精神和严的标准管党治党 坚决打好反腐败斗争攻坚战持久战总体战 李强赵乐际王沪宁蔡奇丁薛祥出席会议 李希主…"
        },
        {
          "frag_id": "FRAG-003-0658",
          "asset_id": "KB-003",
          "snippet": "习近平在甘肃考察时强调 深化改革勇于创新苦干实干富民兴陇 奋力谱写中国式现代化甘肃篇章 | 2024-09-13 | 习近平在甘肃考察时强调 深化改革勇于创新苦干实干富民兴陇 奋力谱写中国式现代化甘肃篇章 途中在陕西宝鸡考察 蔡奇陪同考察 …"
        },
        {
          "frag_id": "FRAG-003-0676",
          "asset_id": "KB-003",
          "snippet": "习近平在湖北考察时强调 鼓足干劲奋发进取 久久为功善作善成 奋力谱写中国式现代化湖北篇章 | 2024-11-06 | 11月4日至6日，中共中央总书记、国家主席、中央军委主席习近平在湖北考察。这是5日上午，习近平在咸宁市嘉鱼县潘家湾镇十里…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "中央八项规定",
        "严明政治纪律",
        "中国式现代化甘肃",
        "谱写中国式现代化",
        "中国式现代化湖北"
      ],
      "constraints": [
        {
          "id": "C-015",
          "text": "引用官方发布的讲话摘要+上下文资产，排除非官方渠道内容",
          "source": "assets_involved",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-016",
          "text": "依据当前可用的最新官方发布版本生成讲话原文支撑包",
          "source": "时效性",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [],
      "realism_check": {
        "total": 3,
        "passed": 2
      }
    },
    {
      "test_id": "TEST-006",
      "difficulty": "basic",
      "primary_assets": [
        "KB-003"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-003-0654",
          "asset_id": "KB-003",
          "snippet": "习近平在二十届中央纪委四次全会上发表重要讲话 | 2025-01-06 | 习近平在二十届中央纪委四次全会上发表重要讲话强调 坚持用改革精神和严的标准管党治党 坚决打好反腐败斗争攻坚战持久战总体战 李强赵乐际王沪宁蔡奇丁薛祥出席会议 李希主…"
        },
        {
          "frag_id": "FRAG-003-0658",
          "asset_id": "KB-003",
          "snippet": "习近平在甘肃考察时强调 深化改革勇于创新苦干实干富民兴陇 奋力谱写中国式现代化甘肃篇章 | 2024-09-13 | 习近平在甘肃考察时强调 深化改革勇于创新苦干实干富民兴陇 奋力谱写中国式现代化甘肃篇章 途中在陕西宝鸡考察 蔡奇陪同考察 …"
        },
        {
          "frag_id": "FRAG-003-0676",
          "asset_id": "KB-003",
          "snippet": "习近平在湖北考察时强调 鼓足干劲奋发进取 久久为功善作善成 奋力谱写中国式现代化湖北篇章 | 2024-11-06 | 11月4日至6日，中共中央总书记、国家主席、中央军委主席习近平在湖北考察。这是5日上午，习近平在咸宁市嘉鱼县潘家湾镇十里…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "中央八项规定",
        "严明政治纪律",
        "中国式现代化甘肃",
        "谱写中国式现代化",
        "中国式现代化湖北"
      ],
      "constraints": [
        {
          "id": "C-018",
          "text": "引用官方发布的最新版本总书记讲话原文支撑包",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-019",
          "text": "整合讲话摘要与上下文片段，形成完整支撑包",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-020",
          "text": "依据知识咨询触发场景，精准召回匹配政治定性所需的讲话内容",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [],
      "realism_check": {
        "total": 3,
        "passed": 3
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
以下候选因真实性验证未通过被丢弃:
  - [TEST-005][C] 仅交付讲话原文支撑包一项输出，确保包含摘要及必要上下文
