---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-22T01:10:57+08:00
created_by: agent-stage3
pass_gate: true
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
### TEST-001 (advanced · 定性量纪建议生成与法规依据校验)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-001-0006、FRAG-001-0031、FRAG-001-0043、FRAG-001-0085、FRAG-001-0097、FRAG-001-0098
- **关键字候选**:违反廉洁纪律、违反政治纪律、党纪处分、处分违纪党员、处分批准权限、按时参加组织生活、党员干部违纪案件、党员干部涉嫌违纪
- **约束项**(4):
  1. C-001 · 引用结构化条款库和实务问答库中最新官方版本的依据 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 整合结构化条款与实务问答两类资产信息，形成完整定性量纪建议 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-003 · 依据案件研判触发条件，主动推断需适用的纪律条款类型并校验匹配性 [来源:triggers · 验证:regulation_support]
  1. C-004 · 输出必须为完整、可直接使用的定性量纪建议终稿，不得缺失结论或依据摘要 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·材料中提及的处分建议与最新修订的《纪律处分条例》条款存在表述差异，需确认是否属于冲突情形。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-002 (advanced · 定性量纪建议生成与法规依据校验)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-001-0006、FRAG-001-0031、FRAG-001-0043、FRAG-001-0085、FRAG-001-0097、FRAG-001-0098
- **关键字候选**:违反廉洁纪律、违反政治纪律、党纪处分、处分违纪党员、处分批准权限、按时参加组织生活、党员干部违纪案件、党员干部涉嫌违纪
- **约束项**(4):
  1. C-005 · 引用结构化条款库和实务问答库中最新官方版本的依据 [来源:时效性 · 验证:regulation_support]
  1. C-006 · 整合结构化条款与实务问答两类资产信息，形成完整定性量纪建议 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-007 · 依据案件研判触发条件，主动推断需适用的纪律条款类型并校验匹配性 [来源:triggers · 验证:regulation_support]
  1. C-008 · 输出必须为完整、可直接使用的定性量纪建议终稿，不得缺失结论或依据摘要 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-002 · 材料中提及的处分建议与最新版《纪律处分条例》第三章第十二条存在表述差异，但实际适用条款未发生实质性变更。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-003 (basic · 总书记讲话精准支撑政策阐释)
- **主资产**:KB-003
- **核心 fragment**:FRAG-003-0031、FRAG-003-0192、FRAG-003-0654
- **关键字候选**:中央八项规定、严明政治纪律、八项规定作为
- **约束项**(3):
  1. C-009 · 引用官方发布的总书记讲话摘要及上下文作为唯一依据 [来源:assets_involved · 验证:regulation_support]
  1. C-010 · 依据当前可用资产中最权威、最新的官方发布版本 [来源:时效性 · 验证:regulation_support]
  1. C-011 · 输出必须为结构化条款形式的政策阐释要点清单 [来源:outputs · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-004 (basic · 总书记讲话精准支撑政策阐释)
- **主资产**:KB-003
- **核心 fragment**:FRAG-003-0031、FRAG-003-0192、FRAG-003-0654
- **关键字候选**:中央八项规定、严明政治纪律、八项规定作为
- **约束项**(3):
  1. C-012 · 引用官方发布的总书记讲话摘要及上下文作为唯一依据 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-013 · 输出必须包含全部政策阐释要点，不得遗漏任一结构化条款 [来源:outputs_count > 1 · 验证:regulation_support]
  1. C-014 · 依据当前可用资产中最权威、最新的官方讲话内容开展审查 [来源:基础约束 · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-005 (advanced · 报批表（谈话方案及安全预案）多维合规审核)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-001-0001、FRAG-001-0106、FRAG-001-0110、FRAG-001-0111、FRAG-001-0149、FRAG-002-0335
- **关键字候选**:八项规定精神、中央八项规定、四种形态、骗取拆迁补偿款、八项规定、党纪处分、审查调查组可以、成立审查调查组
- **约束项**(4):
  1. C-015 · 整合结构化条款库与实务问答库中的最新官方内容，交叉验证谈话方案及安全预案的合规性 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-016 · 引用当前可用的最新官方版本结构化条款和实务问答，排除历史修订稿或非官方解读 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-017 · 识别并标注审核反馈意见中涉及权限边界或管理职责的内容，明确业务层级适用范围 [来源:actors 含"管理"层级 · 验证:llm_judge]
  1. C-018 · 完整交付审核反馈意见，确保覆盖谈话必要性、风险评估、安全措施三类核心要素 [来源:outputs_count > 1 · 验证:regulation_support]
- **干扰项**(1):
  1. I-003 · 陷阱·谈话对象为科级干部时，方案中未体现其所在单位党委意见，看似合理但不符合最新安全预案要求。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-006 (advanced · 报批表（谈话方案及安全预案）多维合规审核)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-001-0001、FRAG-001-0106、FRAG-001-0110、FRAG-001-0111、FRAG-001-0149、FRAG-002-0335
- **关键字候选**:八项规定精神、中央八项规定、四种形态、骗取拆迁补偿款、八项规定、党纪处分、审查调查组可以、成立审查调查组
- **约束项**(4):
  1. C-019 · 引用结构化条款库中最新官方发布版本，排除历史修订稿内容 [来源:时效性 · 验证:regulation_support]
  1. C-020 · 整合结构化条款库与实务问答库中的相关条款，形成交叉验证结论 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-021 · 依据本流程审核复核触发条件，主动识别并标注方案中缺失的安全预案要素 [来源:triggers · 验证:llm_judge]
  1. C-022 · 输出完整审核反馈意见，覆盖谈话方案合规性与安全预案完备性两方面 [来源:outputs_count · 验证:llm_judge]
- **干扰项**(1):
  1. I-004 · 陷阱·谈话对象为退休干部，看似合理应适用普通谈话程序，但实际需按在职干部标准执行安全预案。 [验证:regulation_support]
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
          "frag_id": "FRAG-001-0006",
          "asset_id": "KB-001",
          "snippet": "党纪处分条例、违反政治纪律、违反组织纪律、违反廉洁纪律、违反群众纪律 | 违反政治纪律、违反组织纪律、违反廉洁纪律、违反群众纪律、违反工作纪律、违反生活纪律"
        },
        {
          "frag_id": "FRAG-001-0031",
          "asset_id": "KB-001",
          "snippet": "处分违纪党员, 批准权限, 党纪处分, 党组织, 程序规定 | 违反党纪"
        },
        {
          "frag_id": "FRAG-001-0043",
          "asset_id": "KB-001",
          "snippet": "处分批准权限, 党纪处分, 违纪党员, 批准程序, 处分执行 | 违反处分批准权限和程序"
        },
        {
          "frag_id": "FRAG-001-0085",
          "asset_id": "KB-001",
          "snippet": "党员教育管理, 党组织, 党员义务, 党纪处分, 先锋模范作用 | 不按时参加组织生活, 不交纳党费, 流动到外地工作生活不与党组织主动保持联系, 违反党纪"
        },
        {
          "frag_id": "FRAG-001-0097",
          "asset_id": "KB-001",
          "snippet": "党组讨论, 党员处分, 党纪处分, 纪检监察组, 处分程序 | 司局级党员干部违纪案件，处级及以下党员干部违纪案件"
        },
        {
          "frag_id": "FRAG-001-0098",
          "asset_id": "KB-001",
          "snippet": "党组讨论, 党员处分, 党纪处分, 立案审查, 监督责任 | 党员干部涉嫌违纪问题, 违反党纪"
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
        "违反廉洁纪律",
        "违反政治纪律",
        "党纪处分",
        "处分违纪党员",
        "处分批准权限",
        "按时参加组织生活",
        "党员干部违纪案件",
        "党员干部涉嫌违纪"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "引用结构化条款库和实务问答库中最新官方版本的依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "整合结构化条款与实务问答两类资产信息，形成完整定性量纪建议",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "依据案件研判触发条件，主动推断需适用的纪律条款类型并校验匹配性",
          "source": "triggers",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-004",
          "text": "输出必须为完整、可直接使用的定性量纪建议终稿，不得缺失结论或依据摘要",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "材料中提及的处分建议与最新修订的《纪律处分条例》条款存在表述差异，需确认是否属于冲突情形。",
          "trap": true,
          "process_ref": "定性量纪建议生成与法规依据校验",
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
          "frag_id": "FRAG-001-0006",
          "asset_id": "KB-001",
          "snippet": "党纪处分条例、违反政治纪律、违反组织纪律、违反廉洁纪律、违反群众纪律 | 违反政治纪律、违反组织纪律、违反廉洁纪律、违反群众纪律、违反工作纪律、违反生活纪律"
        },
        {
          "frag_id": "FRAG-001-0031",
          "asset_id": "KB-001",
          "snippet": "处分违纪党员, 批准权限, 党纪处分, 党组织, 程序规定 | 违反党纪"
        },
        {
          "frag_id": "FRAG-001-0043",
          "asset_id": "KB-001",
          "snippet": "处分批准权限, 党纪处分, 违纪党员, 批准程序, 处分执行 | 违反处分批准权限和程序"
        },
        {
          "frag_id": "FRAG-001-0085",
          "asset_id": "KB-001",
          "snippet": "党员教育管理, 党组织, 党员义务, 党纪处分, 先锋模范作用 | 不按时参加组织生活, 不交纳党费, 流动到外地工作生活不与党组织主动保持联系, 违反党纪"
        },
        {
          "frag_id": "FRAG-001-0097",
          "asset_id": "KB-001",
          "snippet": "党组讨论, 党员处分, 党纪处分, 纪检监察组, 处分程序 | 司局级党员干部违纪案件，处级及以下党员干部违纪案件"
        },
        {
          "frag_id": "FRAG-001-0098",
          "asset_id": "KB-001",
          "snippet": "党组讨论, 党员处分, 党纪处分, 立案审查, 监督责任 | 党员干部涉嫌违纪问题, 违反党纪"
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
        "违反廉洁纪律",
        "违反政治纪律",
        "党纪处分",
        "处分违纪党员",
        "处分批准权限",
        "按时参加组织生活",
        "党员干部违纪案件",
        "党员干部涉嫌违纪"
      ],
      "constraints": [
        {
          "id": "C-005",
          "text": "引用结构化条款库和实务问答库中最新官方版本的依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "整合结构化条款与实务问答两类资产信息，形成完整定性量纪建议",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-007",
          "text": "依据案件研判触发条件，主动推断需适用的纪律条款类型并校验匹配性",
          "source": "triggers",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "输出必须为完整、可直接使用的定性量纪建议终稿，不得缺失结论或依据摘要",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-002",
          "text": "材料中提及的处分建议与最新版《纪律处分条例》第三章第十二条存在表述差异，但实际适用条款未发生实质性变更。",
          "trap": false,
          "process_ref": "定性量纪建议生成与法规依据校验",
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
      "fragments": [
        {
          "frag_id": "FRAG-003-0031",
          "asset_id": "KB-003",
          "snippet": "高举中国特色社会主义伟大旗帜 为全面建设社会主义现代化国家而团结奋斗 | 2022-10-26 | 10月16日，习近平在中国共产党第二十次全国代表大会上作报告。 新华社记者 饶爱民摄 同志们： 现在，我代表第十九届中央委员会向大会作报告。…"
        },
        {
          "frag_id": "FRAG-003-0192",
          "asset_id": "KB-003",
          "snippet": "习近平：高举中国特色社会主义伟大旗帜 为全面建设社会主义现代化国家而团结奋斗——在中国共产党第二十次全国代表大会上的报告 | 2022-10-25 | 高举中国特色社会主义伟大旗帜 为全面建设社会主义现代化国家而团结奋斗 ——在中国共产党第…"
        },
        {
          "frag_id": "FRAG-003-0654",
          "asset_id": "KB-003",
          "snippet": "习近平在二十届中央纪委四次全会上发表重要讲话 | 2025-01-06 | 习近平在二十届中央纪委四次全会上发表重要讲话强调 坚持用改革精神和严的标准管党治党 坚决打好反腐败斗争攻坚战持久战总体战 李强赵乐际王沪宁蔡奇丁薛祥出席会议 李希主…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "中央八项规定",
        "严明政治纪律",
        "八项规定作为"
      ],
      "constraints": [
        {
          "id": "C-009",
          "text": "引用官方发布的总书记讲话摘要及上下文作为唯一依据",
          "source": "assets_involved",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-010",
          "text": "依据当前可用资产中最权威、最新的官方发布版本",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-011",
          "text": "输出必须为结构化条款形式的政策阐释要点清单",
          "source": "outputs",
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
      "fragments": [
        {
          "frag_id": "FRAG-003-0031",
          "asset_id": "KB-003",
          "snippet": "高举中国特色社会主义伟大旗帜 为全面建设社会主义现代化国家而团结奋斗 | 2022-10-26 | 10月16日，习近平在中国共产党第二十次全国代表大会上作报告。 新华社记者 饶爱民摄 同志们： 现在，我代表第十九届中央委员会向大会作报告。…"
        },
        {
          "frag_id": "FRAG-003-0192",
          "asset_id": "KB-003",
          "snippet": "习近平：高举中国特色社会主义伟大旗帜 为全面建设社会主义现代化国家而团结奋斗——在中国共产党第二十次全国代表大会上的报告 | 2022-10-25 | 高举中国特色社会主义伟大旗帜 为全面建设社会主义现代化国家而团结奋斗 ——在中国共产党第…"
        },
        {
          "frag_id": "FRAG-003-0654",
          "asset_id": "KB-003",
          "snippet": "习近平在二十届中央纪委四次全会上发表重要讲话 | 2025-01-06 | 习近平在二十届中央纪委四次全会上发表重要讲话强调 坚持用改革精神和严的标准管党治党 坚决打好反腐败斗争攻坚战持久战总体战 李强赵乐际王沪宁蔡奇丁薛祥出席会议 李希主…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "中央八项规定",
        "严明政治纪律",
        "八项规定作为"
      ],
      "constraints": [
        {
          "id": "C-012",
          "text": "引用官方发布的总书记讲话摘要及上下文作为唯一依据",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-013",
          "text": "输出必须包含全部政策阐释要点，不得遗漏任一结构化条款",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-014",
          "text": "依据当前可用资产中最权威、最新的官方讲话内容开展审查",
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
      "test_id": "TEST-005",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-001-0001",
          "asset_id": "KB-001",
          "snippet": "四种形态, 典型案例, 监督执纪, 乡村振兴, 微权力 | 违规收取农村土地经营权流转协调费，侵占、挪用村集体资金，违反中央八项规定精神，挪用农村集体资金"
        },
        {
          "frag_id": "FRAG-001-0106",
          "asset_id": "KB-001",
          "snippet": "四种形态, 监督执纪, 疫情防控, 容错纠错, 违纪违法 | 王某某未对排查内蒙古阿拉善盟返京人员工作进行严格细致部署，仅通过微信群转发提醒，未采取有效措施督促镇卫生计生办对社区风险人员的排查工作进行督导检查；杨某在接到区防控办下发的风险人…"
        },
        {
          "frag_id": "FRAG-001-0110",
          "asset_id": "KB-001",
          "snippet": "四种形态, 违纪行为, 党内纪律, 容错免责, 监督执纪 | 收受监管服务对象礼品、宴请并索取财物；未经规划和施工审批先行开工建设；骗取拆迁补偿款；放贷收息受贿。"
        },
        {
          "frag_id": "FRAG-001-0111",
          "asset_id": "KB-001",
          "snippet": "四种形态, 中央八项规定, 监督执纪, 作风建设, 典型案例 | 梅某组织公款吃喝、违规发放礼品；陈某甲等人统计受灾情况时弄虚作假；华某某吃拿卡要、履职不力；赵某某收受礼金、受贿。"
        },
        {
          "frag_id": "FRAG-001-0149",
          "asset_id": "KB-001",
          "snippet": "四种形态, 违规从事营利活动, 酒驾, 党纪处分, 典型案例 | 黄某某违规从事营利活动，获得分红69.35万元，拒不上交违纪违法所得59.35万元；隆某某饮酒后驾驶机动车，被给予行政处罚。"
        },
        {
          "frag_id": "FRAG-002-0335",
          "asset_id": "KB-002",
          "snippet": "与被审查调查人的谈话应由谁负责？ | 与被审查调查人的谈话、讯问应由本机关干部作为主谈人。 | 制定审查调查方案应注意哪些问题.docx | 片段5:经批准成立审查调查组后 ，要明 确组长和成员及组内分工 ，对于重大 、复杂的案件 ，一般下…"
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
        "八项规定精神",
        "中央八项规定",
        "四种形态",
        "骗取拆迁补偿款",
        "八项规定",
        "党纪处分",
        "审查调查组可以",
        "成立审查调查组"
      ],
      "constraints": [
        {
          "id": "C-015",
          "text": "整合结构化条款库与实务问答库中的最新官方内容，交叉验证谈话方案及安全预案的合规性",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-016",
          "text": "引用当前可用的最新官方版本结构化条款和实务问答，排除历史修订稿或非官方解读",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-017",
          "text": "识别并标注审核反馈意见中涉及权限边界或管理职责的内容，明确业务层级适用范围",
          "source": "actors 含\"管理\"层级",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-018",
          "text": "完整交付审核反馈意见，确保覆盖谈话必要性、风险评估、安全措施三类核心要素",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-003",
          "text": "谈话对象为科级干部时，方案中未体现其所在单位党委意见，看似合理但不符合最新安全预案要求。",
          "trap": true,
          "process_ref": "报批表（谈话方案及安全预案）多维合规审核",
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
          "frag_id": "FRAG-001-0001",
          "asset_id": "KB-001",
          "snippet": "四种形态, 典型案例, 监督执纪, 乡村振兴, 微权力 | 违规收取农村土地经营权流转协调费，侵占、挪用村集体资金，违反中央八项规定精神，挪用农村集体资金"
        },
        {
          "frag_id": "FRAG-001-0106",
          "asset_id": "KB-001",
          "snippet": "四种形态, 监督执纪, 疫情防控, 容错纠错, 违纪违法 | 王某某未对排查内蒙古阿拉善盟返京人员工作进行严格细致部署，仅通过微信群转发提醒，未采取有效措施督促镇卫生计生办对社区风险人员的排查工作进行督导检查；杨某在接到区防控办下发的风险人…"
        },
        {
          "frag_id": "FRAG-001-0110",
          "asset_id": "KB-001",
          "snippet": "四种形态, 违纪行为, 党内纪律, 容错免责, 监督执纪 | 收受监管服务对象礼品、宴请并索取财物；未经规划和施工审批先行开工建设；骗取拆迁补偿款；放贷收息受贿。"
        },
        {
          "frag_id": "FRAG-001-0111",
          "asset_id": "KB-001",
          "snippet": "四种形态, 中央八项规定, 监督执纪, 作风建设, 典型案例 | 梅某组织公款吃喝、违规发放礼品；陈某甲等人统计受灾情况时弄虚作假；华某某吃拿卡要、履职不力；赵某某收受礼金、受贿。"
        },
        {
          "frag_id": "FRAG-001-0149",
          "asset_id": "KB-001",
          "snippet": "四种形态, 违规从事营利活动, 酒驾, 党纪处分, 典型案例 | 黄某某违规从事营利活动，获得分红69.35万元，拒不上交违纪违法所得59.35万元；隆某某饮酒后驾驶机动车，被给予行政处罚。"
        },
        {
          "frag_id": "FRAG-002-0335",
          "asset_id": "KB-002",
          "snippet": "与被审查调查人的谈话应由谁负责？ | 与被审查调查人的谈话、讯问应由本机关干部作为主谈人。 | 制定审查调查方案应注意哪些问题.docx | 片段5:经批准成立审查调查组后 ，要明 确组长和成员及组内分工 ，对于重大 、复杂的案件 ，一般下…"
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
        "八项规定精神",
        "中央八项规定",
        "四种形态",
        "骗取拆迁补偿款",
        "八项规定",
        "党纪处分",
        "审查调查组可以",
        "成立审查调查组"
      ],
      "constraints": [
        {
          "id": "C-019",
          "text": "引用结构化条款库中最新官方发布版本，排除历史修订稿内容",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-020",
          "text": "整合结构化条款库与实务问答库中的相关条款，形成交叉验证结论",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-021",
          "text": "依据本流程审核复核触发条件，主动识别并标注方案中缺失的安全预案要素",
          "source": "triggers",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-022",
          "text": "输出完整审核反馈意见，覆盖谈话方案合规性与安全预案完备性两方面",
          "source": "outputs_count",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-004",
          "text": "谈话对象为退休干部，看似合理应适用普通谈话程序，但实际需按在职干部标准执行安全预案。",
          "trap": true,
          "process_ref": "报批表（谈话方案及安全预案）多维合规审核",
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
