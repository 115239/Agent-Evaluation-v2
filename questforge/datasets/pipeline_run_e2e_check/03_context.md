---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-21T23:12:17+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 3 道题建立了知识索引(共 11089 个 fragment),LLM 生成 13 条约束、1 条干扰(其中 1 条陷阱)。业务真实性通过 14/14。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-001,TEST-003 |
| KB-002 | 1006 | TEST-002,TEST-003 |
| KB-003 | 1235 | — |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (basic · 党纪法规语义检索支撑定性量纪建议)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0908、FRAG-001-0193、FRAG-001-2411
- **关键字候选**:食品安全危害调查、拒绝配合食品安全、危害社会行为、实施危害社会、非法买卖外汇、外汇管理部门
- **约束项**(4):
  1. C-001 · 依据KB-001最新官方发布版本引用定性量纪条款 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 仅输出定性量纪参考条款集，不扩展解释或建议 [来源:outputs_count · 验证:regulation_support]
  1. C-003 · 识别并排除KB-001中已废止或标注‘失效’的条款 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-004 · 不整合跨流程资产信息，严格限定于BP-001单流程内条款检索 [来源:cross_process_dependency · 验证:llm_judge]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:4/4

### TEST-002 (basic · 纪检文书纠错闭环处理（报批表专项）)
- **主资产**:KB-002
- **核心 fragment**:FRAG-002-0978、FRAG-002-0039、FRAG-002-0332
- **关键字候选**:第十五条第二款的、此时国家工作人员、审查调查人员、应由审查调查、应对审查调查过程、审查调查过程中
- **约束项**(4):
  1. C-005 · 依据KB-002最新官方实务问答执行审查 [来源:时效性 · 验证:regulation_support]
  1. C-006 · 仅输出《报批表纠错报告》一项修正建议，不得增删或拆分 [来源:outputs_count · 验证:llm_judge]
  1. C-007 · 识别审核复核触发场景，主动校验报批表中必填字段完整性 [来源:triggers · 验证:llm_judge]
  1. C-008 · 引用KB-002中与报批表要素对应的条目进行比对 [来源:cross_process_dependency · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:4/4

### TEST-003 (advanced · 多源知识协同验证实务问答)
- **主资产**:KB-002、KB-001
- **核心 fragment**:FRAG-001-1402、FRAG-001-3660、FRAG-001-2416、FRAG-002-0190、FRAG-001-0487、FRAG-001-2422
- **关键字候选**:未经许可擅自收购、库存量不符合规定、境外举办企业、在境外举办、剽窃他人研究成果、他人研究成果获奖、骗领财政补贴资金、崔某骗领财政补贴
- **约束项**(5):
  1. C-009 · 依据KB-002与KB-001最新发布版本引用权威依据 [来源:时效性 · 验证:regulation_support]
  1. C-010 · 整合KB-002与KB-001内容交叉验证，排除版本不一致信息 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-011 · 识别并标注KB-001中结构化条款对KB-002实务问答的约束效力 [来源:actors_levels · 验证:regulation_support]
  1. C-012 · 完整交付包含条款依据、问答原文、效力说明的权威实务答复包 [来源:outputs_count · 验证:regulation_support]
  1. C-013 · 基于案件研判触发点，主动推断需验证的关键条款维度 [来源:triggers · 验证:llm_judge]
- **干扰项**(1):
  1. I-001 · 陷阱·该材料中引用的条款版本与KB-001最新结构化条款存在表述冲突。 [验证:regulation_support]
- **真实性验证**:6/6

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
        "TEST-003"
      ]
    },
    "KB-002": {
      "total_fragments": 1006,
      "covered_by": [
        "TEST-002",
        "TEST-003"
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
          "frag_id": "FRAG-001-0908",
          "asset_id": "KB-001",
          "snippet": "食品召回, 不安全食品, 食品安全危害, 责令召回, 无害化处理 | 未停止生产销售不安全食品，拒绝配合食品安全危害调查，未及时提交食品安全危害调查、评估报告，未停止生产销售不安全食品，未及时召回"
        },
        {
          "frag_id": "FRAG-001-0193",
          "asset_id": "KB-001",
          "snippet": "刑法第三十条, 单位危害社会行为, 刑事责任, 组织策划实施, 追究刑事责任 | 单位实施危害社会行为，组织、策划、实施危害社会行为"
        },
        {
          "frag_id": "FRAG-001-2411",
          "asset_id": "KB-001",
          "snippet": "骗购外汇, 逃汇, 非法买卖外汇, 伪造单据, 外汇管理 | 骗购外汇，逃汇，非法买卖外汇，伪造、变造海关签发的报关单、进口证明、外汇管理部门核准件等凭证和单据"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "食品安全危害调查",
        "拒绝配合食品安全",
        "危害社会行为",
        "实施危害社会",
        "非法买卖外汇",
        "外汇管理部门"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "依据KB-001最新官方发布版本引用定性量纪条款",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "仅输出定性量纪参考条款集，不扩展解释或建议",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "识别并排除KB-001中已废止或标注‘失效’的条款",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-004",
          "text": "不整合跨流程资产信息，严格限定于BP-001单流程内条款检索",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [],
      "realism_check": {
        "total": 4,
        "passed": 4
      }
    },
    {
      "test_id": "TEST-002",
      "difficulty": "basic",
      "primary_assets": [
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0978",
          "asset_id": "KB-002",
          "snippet": "三万元是指单人还是多人累计？ | 笔者认为，应当以单个人为单位进行衡量。 | 这些情形受贿数额是否累计计算.docx | 片段6:其次 ，对于徐行犯之外的情形 ，可将行贿人提出具体请 托事项作为时间节点 ，在此节点后发生的收受财物行为 ，无…"
        },
        {
          "frag_id": "FRAG-002-0039",
          "asset_id": "KB-002",
          "snippet": "自书材料的格式要求是什么？ | 注意自书材料要四周留空不要顶满格，特别是左边留出装  订位置。 | 20210513 【实务】避免瑕疵证据的六个妙招.docx | 片段4:被讯问人(被询问人)在(讯  问)询问通知书上的签字日期应与首次(讯…"
        },
        {
          "frag_id": "FRAG-002-0332",
          "asset_id": "KB-002",
          "snippet": "安全预案包括哪些内容？ | 细化留置 、“走读式”谈话的安全 预案和对突发事件的应急预案 ，防范各种风险 ，把安全责任 落实到岗 、到人 。要准确掌握被留置对象的动态 ，科学配备 看护人员 ，做好医疗保障 。询问证人及 “走读式”谈话的安 …"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "第十五条第二款的",
        "此时国家工作人员",
        "审查调查人员",
        "应由审查调查",
        "应对审查调查过程",
        "审查调查过程中"
      ],
      "constraints": [
        {
          "id": "C-005",
          "text": "依据KB-002最新官方实务问答执行审查",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "仅输出《报批表纠错报告》一项修正建议，不得增删或拆分",
          "source": "outputs_count",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-007",
          "text": "识别审核复核触发场景，主动校验报批表中必填字段完整性",
          "source": "triggers",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-008",
          "text": "引用KB-002中与报批表要素对应的条目进行比对",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [],
      "realism_check": {
        "total": 4,
        "passed": 4
      }
    },
    {
      "test_id": "TEST-003",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-002",
        "KB-001"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-001-1402",
          "asset_id": "KB-001",
          "snippet": "粮食收购, 粮食储存, 粮食加工, 粮食运输, 粮食市场 | 未经许可擅自收购粮食，以欺骗手段取得粮食收购资格，未执行粮食质量标准，未及时支付售粮款，代扣代缴税、费和其他款项，未建立粮食经营台账，陈粮出库未进行质量鉴定，库存量不符合规定，未…"
        },
        {
          "frag_id": "FRAG-001-3660",
          "asset_id": "KB-001",
          "snippet": "境外企业, 中方投资者, 审批管理, 投资规模, 经济效益 | 不执行本规定自行在境外举办企业"
        },
        {
          "frag_id": "FRAG-001-2416",
          "asset_id": "KB-001",
          "snippet": "研究成果奖励, 学术创新, 弄虚作假, 奖励办法, 人文社会科学 | 弄虚作假或剽窃他人研究成果获奖"
        },
        {
          "frag_id": "FRAG-002-0190",
          "asset_id": "KB-002",
          "snippet": "为什么崔某的行为不属于违反群众纪律？ | 从本案来看，崔某骗领财政补贴资金行为“优”“厚”的是自己，也未导致本村应该领取财政资金补贴的人员领取不到或者比规定的标准领取得低，不属于违反群众纪律性质。 | 20211229 中央纪委国家监委发布…"
        },
        {
          "frag_id": "FRAG-001-0487",
          "asset_id": "KB-001",
          "snippet": "超限检测, 公路管理, 违法行为, 执法人员, 处罚措施 | 未按照规定佩戴标志或者未持证上岗，辱骂、殴打当事人，当场收缴罚款不开具罚款收据或者不如实填写罚款数额，擅自使用扣留车辆、私自处理卸载货物，对未消除违法状态的超限运输车辆予以放行，…"
        },
        {
          "frag_id": "FRAG-001-2422",
          "asset_id": "KB-001",
          "snippet": "煤炭内部审计, 审计证据, 审计工作, 证据管理, 审计取证 | 隐瞒、截留、挪用收入，偷漏税款"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-003-0252",
          "asset_id": "KB-003"
        },
        {
          "frag_id": "FRAG-004-3663",
          "asset_id": "KB-004"
        }
      ],
      "keyword_pool": [
        "未经许可擅自收购",
        "库存量不符合规定",
        "境外举办企业",
        "在境外举办",
        "剽窃他人研究成果",
        "他人研究成果获奖",
        "骗领财政补贴资金",
        "崔某骗领财政补贴"
      ],
      "constraints": [
        {
          "id": "C-009",
          "text": "依据KB-002与KB-001最新发布版本引用权威依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-010",
          "text": "整合KB-002与KB-001内容交叉验证，排除版本不一致信息",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-011",
          "text": "识别并标注KB-001中结构化条款对KB-002实务问答的约束效力",
          "source": "actors_levels",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-012",
          "text": "完整交付包含条款依据、问答原文、效力说明的权威实务答复包",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-013",
          "text": "基于案件研判触发点，主动推断需验证的关键条款维度",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "该材料中引用的条款版本与KB-001最新结构化条款存在表述冲突。",
          "trap": true,
          "process_ref": "多源知识协同验证实务问答",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 6,
        "passed": 6
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
