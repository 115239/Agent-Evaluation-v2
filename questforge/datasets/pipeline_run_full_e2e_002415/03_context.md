---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-22T00:25:33+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 2 道题建立了知识索引(共 11089 个 fragment),LLM 生成 9 条约束、1 条干扰(其中 0 条陷阱)。业务真实性通过 10/10。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-001 |
| KB-002 | 1006 | TEST-002 |
| KB-003 | 1235 | TEST-002 |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (basic · 党纪法规条款匹配与定性量纪建议生成)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0908、FRAG-001-0193、FRAG-001-2411
- **关键字候选**:食品安全危害调查、及时提交食品安全、危害社会行为、实施危害社会、非法买卖外汇、签发的报关单
- **约束项**(4):
  1. C-001 · 依据KB-001最新官方发布版本引用党纪法规条款 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 仅基于KB-001结构化条款进行匹配，排除非官方解释或案例类资产 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-003 · 输出必须为完整定性量纪建议书，不可省略结论、依据条款及量纪建议三要素 [来源:outputs_count > 1 · 验证:regulation_support]
  1. C-004 · 识别并标注KB-001中条款的适用前提与限制条件，不得直接套用无前提条款 [来源:actors 含"管理"层级 · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:4/4

### TEST-002 (advanced · 纪检文书纠错与政治口径一致性校验)
- **主资产**:KB-002、KB-003
- **核心 fragment**:FRAG-003-0074、FRAG-003-0822、FRAG-002-0125、FRAG-002-0685、FRAG-002-0521、FRAG-003-0931
- **关键字候选**:全球应对气候变化、气候变化作出更大、圆满完成各项工作、详细了解武器弹药、八项规定精神、中央八项规定、适用于证据不足、于证据不足情形
- **约束项**(5):
  1. C-005 · 依据KB-002和KB-003最新官方版本开展校验 [来源:时效性 · 验证:regulation_support]
  1. C-006 · 整合KB-002实务问答与KB-003讲话摘要上下文进行跨流程一致性比对 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-007 · 排除非官方来源或未标注权威性的政治表述引用 [来源:时效性 · 验证:regulation_support]
  1. C-008 · 在纠错报告中标注所有政治口径偏差项及其对应KB-003原文依据 [来源:actors_levels · 验证:regulation_support]
  1. C-009 · 完整交付文书纠错报告，不得遗漏任一问题清单条目 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 文书引用了2021年版《监督执纪工作规则》条款，但未注明是否适配最新政治表述口径。 [验证:regulation_support]
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
        "TEST-001"
      ]
    },
    "KB-002": {
      "total_fragments": 1006,
      "covered_by": [
        "TEST-002"
      ]
    },
    "KB-003": {
      "total_fragments": 1235,
      "covered_by": [
        "TEST-002"
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
        "及时提交食品安全",
        "危害社会行为",
        "实施危害社会",
        "非法买卖外汇",
        "签发的报关单"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "依据KB-001最新官方发布版本引用党纪法规条款",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "仅基于KB-001结构化条款进行匹配，排除非官方解释或案例类资产",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "输出必须为完整定性量纪建议书，不可省略结论、依据条款及量纪建议三要素",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-004",
          "text": "识别并标注KB-001中条款的适用前提与限制条件，不得直接套用无前提条款",
          "source": "actors 含\"管理\"层级",
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
      "test_id": "TEST-002",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-002",
        "KB-003"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-003-0074",
          "asset_id": "KB-003",
          "snippet": "继往开来，开启全球应对气候变化新征程 | 2020-12-13 | 尊敬的古特雷斯秘书长先生， 尊敬的各位同事： 很高兴出席今天的气候雄心峰会。5年前，各国领导人以最大的政治决心和智慧推动达成应对气候变化《巴黎协定》。5年来，《巴黎协定》进…"
        },
        {
          "frag_id": "FRAG-003-0822",
          "asset_id": "KB-003",
          "snippet": "习近平在视察北部战区海军时强调  贯彻转型建设要求 锻造海上精兵劲旅 | 2018-06-15 | 中共中央总书记、国家主席、中央军委主席习近平11日下午视察北部战区海军，强调要坚决贯彻新时代党的强军思想，坚持政治建军、改革强军、科技兴军、…"
        },
        {
          "frag_id": "FRAG-002-0125",
          "asset_id": "KB-002",
          "snippet": "最终认定张某行为违纪的依据是什么？ | 张某的退休时间在党的十九大之后，中央对于严格落实中央八项规定精神、毫不松懈纠治“四风”的要求已经非常明确，但其仍然不知敬畏，多次接受退休前管理服务对象的宴请。为严肃党的纪律，应将张某的上述行为认定为违…"
        },
        {
          "frag_id": "FRAG-002-0685",
          "asset_id": "KB-002",
          "snippet": "全面从严治党的关键是什么？ | 全面从严治党关键在严、要害在治 | 第三批准确有效运用“四种形态”典型案例.docx | 片段24:制定实 施中央八项规定是党在新时代的徙木立 信之举，是以习近平同志为核心的党中 央作出的庄严承诺。党的十八大…"
        },
        {
          "frag_id": "FRAG-002-0521",
          "asset_id": "KB-002",
          "snippet": "登记上交适用于什么情形？ | 登记上交适用于证据不足情形 | 涉案财物如何查扣和处理.docx | 片段7:文档标题: 涉案财物如何查扣和处理 片段8:序号: 1888 片段9:文档名称: 202103 中纪委网站“业务探讨”汇编（更新至2…"
        },
        {
          "frag_id": "FRAG-003-0931",
          "asset_id": "KB-003",
          "snippet": "习近平在中国共产党第十九次全国代表大会上的报告 | 2017-10-28 | 10月18日，习近平在中国共产党第十九次全国代表大会上作报告。 新华社记者 鞠 鹏摄 决胜全面建成小康社会 夺取新时代中国特色社会主义伟大胜利 ——在中国共产党第…"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-004-4701",
          "asset_id": "KB-004"
        },
        {
          "frag_id": "FRAG-001-0439",
          "asset_id": "KB-001"
        }
      ],
      "keyword_pool": [
        "全球应对气候变化",
        "气候变化作出更大",
        "圆满完成各项工作",
        "详细了解武器弹药",
        "八项规定精神",
        "中央八项规定",
        "适用于证据不足",
        "于证据不足情形"
      ],
      "constraints": [
        {
          "id": "C-005",
          "text": "依据KB-002和KB-003最新官方版本开展校验",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "整合KB-002实务问答与KB-003讲话摘要上下文进行跨流程一致性比对",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-007",
          "text": "排除非官方来源或未标注权威性的政治表述引用",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "在纠错报告中标注所有政治口径偏差项及其对应KB-003原文依据",
          "source": "actors_levels",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-009",
          "text": "完整交付文书纠错报告，不得遗漏任一问题清单条目",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "文书引用了2021年版《监督执纪工作规则》条款，但未注明是否适配最新政治表述口径。",
          "trap": false,
          "process_ref": "纪检文书纠错与政治口径一致性校验",
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
