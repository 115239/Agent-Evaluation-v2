---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-05-07T23:38:28+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 3 道题建立了知识索引(共 11089 个 fragment),LLM 生成 10 条约束、1 条干扰(其中 1 条陷阱)。业务真实性通过 11/11。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-001,TEST-003 |
| KB-002 | 1006 | TEST-002 |
| KB-003 | 1235 | TEST-003 |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (basic · 党纪法规语义检索支撑定性量纪建议)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0109、FRAG-001-0006、FRAG-001-0018
- **关键字候选**:违反政治纪律、违反工作纪律、违反廉洁纪律、政治纪律
- **约束项**(3):
  1. C-001 · 引用官方发布的最新党纪条款库中的结构化条款 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 依据知识咨询触发场景，仅输出党纪条款匹配结果一项结构化输出 [来源:outputs_count · 验证:regulation_support]
  1. C-003 · 排除非官方来源或非结构化条款信息 [来源:assets_involved · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-002 (basic · 实务案例问答匹配辅助审查调查决策)
- **主资产**:KB-002
- **核心 fragment**:FRAG-002-0037、FRAG-002-0038、FRAG-002-0039
- **关键字候选**:审查调查人员、核对审查调查
- **约束项**(3):
  1. C-004 · 引用官方发布的实务问答库中最新版本内容作为唯一依据 [来源:时效性 · 验证:regulation_support]
  1. C-005 · 整合案件研判触发的全部要素，匹配对应实务问答条目形成决策支持包 [来源:triggers · 验证:regulation_support]
  1. C-006 · 输出必须包含完整审查调查决策支持包，不得遗漏任一构成要素 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-003 (advanced · 纪检文书纠错辅助与多源口径一致性校验)
- **主资产**:KB-003、KB-001
- **核心 fragment**:FRAG-003-0011、FRAG-003-0101、FRAG-003-0139、FRAG-003-0260、FRAG-003-0395、FRAG-003-0454
- **关键字候选**:严守政治纪律、八项规定这么、八项规定开局、中央八项规定、八项规定精神、严格遵守政治纪律、四种形态、国家监察体制改革
- **约束项**(4):
  1. C-007 · 引用结构化条款与讲话摘要+上下文两类官方资产，整合校验文书表述一致性 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-008 · 依据当前可用的最新官方发布版本，排除历史修订稿或非权威解读内容 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-009 · 识别审核复核场景下需主动标注的模糊表述，并在错误归因摘要中明确推断依据 [来源:triggers · 验证:regulation_support]
  1. C-010 · 完整交付合规文书包与错误归因摘要两项内容，形成闭环处置输出 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·该材料引用的‘四种形态’适用条件与最新中央纪委通报案例中的实践口径存在冲突，需人工复核。 [验证:regulation_support]
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
        "TEST-003"
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
        "TEST-003"
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
      "sample_idx": 0,
      "focus_stages": [
        "定义问题"
      ],
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
          "text": "引用官方发布的最新党纪条款库中的结构化条款",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "依据知识咨询触发场景，仅输出党纪条款匹配结果一项结构化输出",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "排除非官方来源或非结构化条款信息",
          "source": "assets_involved",
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
      "sample_idx": 0,
      "focus_stages": [
        "拆解问题",
        "方案生成"
      ],
      "primary_assets": [
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0037",
          "asset_id": "KB-002",
          "snippet": "调证通知书上扣押物品特征描述的要求是什么？ | 在调取扣押物品来源的相关书证时，如果调证通知书上对扣押物品的特征描述与扣押物品清单的描 述不一致，则无法确定是否为同一件扣押物品，因此关于扣押物品 的特征描述，在不同场合、不同文书上要始终保持…"
        },
        {
          "frag_id": "FRAG-002-0038",
          "asset_id": "KB-002",
          "snippet": "自书材料的标题应如何书写？ | 一般每份自书材料上书标题“关于某问题的交代材料” | 20210513 【实务】避免瑕疵证据的六个妙招.docx | 片段4:被讯问人(被询问人)在(讯  问)询问通知书上的签字日期应与首次(讯问)询问笔录日…"
        },
        {
          "frag_id": "FRAG-002-0039",
          "asset_id": "KB-002",
          "snippet": "自书材料的格式要求是什么？ | 注意自书材料要四周留空不要顶满格，特别是左边留出装  订位置。 | 20210513 【实务】避免瑕疵证据的六个妙招.docx | 片段4:被讯问人(被询问人)在(讯  问)询问通知书上的签字日期应与首次(讯…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "审查调查人员",
        "核对审查调查"
      ],
      "constraints": [
        {
          "id": "C-004",
          "text": "引用官方发布的实务问答库中最新版本内容作为唯一依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-005",
          "text": "整合案件研判触发的全部要素，匹配对应实务问答条目形成决策支持包",
          "source": "triggers",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "输出必须包含完整审查调查决策支持包，不得遗漏任一构成要素",
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
      "sample_idx": 0,
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "primary_assets": [
        "KB-003",
        "KB-001"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-003-0011",
          "asset_id": "KB-003",
          "snippet": "《求是》杂志发表习近平总书记重要文章《在中央和国家机关党的建设工作会议上的讲话》 | 2019-11-01 | 11月1日出版的第21期《求是》杂志发表中共中央总书记、国家主席、中央军委主席习近平的重要文章《在中央和国家机关党的建设工作会议…"
        },
        {
          "frag_id": "FRAG-003-0101",
          "asset_id": "KB-003",
          "snippet": "健全全面从严治党体系 推动新时代党的建设新的伟大工程向纵深发展 | 2023-06-15 | 健全全面从严治党体系 推动新时代党的建设新的伟大工程向纵深发展 习近平 把党的建设作为一项伟大工程来推进，并且始终坚持党要管党、从严治党的原则和方…"
        },
        {
          "frag_id": "FRAG-003-0139",
          "asset_id": "KB-003",
          "snippet": "全面从严治党探索出依靠党的自我革命跳出历史周期率的成功路径 | 2023-01-31 | 全面从严治党探索出依靠党的自我革命跳出历史周期率的成功路径 习近平 2022年1月18日，中共中央总书记、国家主席、中央军委主席习近平在中国共产党第十…"
        },
        {
          "frag_id": "FRAG-003-0260",
          "asset_id": "KB-003",
          "snippet": "习近平：决胜全面建成小康社会 夺取新时代中国特色社会主义伟大胜利 | 2017-10-27 | 决胜全面建成小康社会 夺取新时代中国特色社会主义伟大胜利 ——在中国共产党第十九次全国代表大会上的报告 （2017年10月18日） 习近平 同志…"
        },
        {
          "frag_id": "FRAG-003-0395",
          "asset_id": "KB-003",
          "snippet": "习近平：在新的起点上深化国家监察体制改革 | 2019-02-28 | 中国共产党第十九届中央委员会第三次全体会议，于2018年2月26日至28日在北京举行。中央委员会总书记习近平作重要讲话。 新华社记者 鞠鹏/摄 2018年3月20日，第…"
        },
        {
          "frag_id": "FRAG-003-0454",
          "asset_id": "KB-003",
          "snippet": "习近平代表第十八届中央委员会向大会作的报告摘登 | 2017-10-19 | 中国共产党人的初心和使命就是为中国人民谋幸福为中华民族谋复兴 习近平同志在作十九大报告时说，中国共产党人的初心和使命，就是为中国人民谋幸福，为中华民族谋复兴。 习…"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-004-3371",
          "asset_id": "KB-004"
        },
        {
          "frag_id": "FRAG-004-4824",
          "asset_id": "KB-004"
        }
      ],
      "keyword_pool": [
        "严守政治纪律",
        "八项规定这么",
        "八项规定开局",
        "中央八项规定",
        "八项规定精神",
        "严格遵守政治纪律",
        "四种形态",
        "国家监察体制改革"
      ],
      "constraints": [
        {
          "id": "C-007",
          "text": "引用结构化条款与讲话摘要+上下文两类官方资产，整合校验文书表述一致性",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "依据当前可用的最新官方发布版本，排除历史修订稿或非权威解读内容",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-009",
          "text": "识别审核复核场景下需主动标注的模糊表述，并在错误归因摘要中明确推断依据",
          "source": "triggers",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-010",
          "text": "完整交付合规文书包与错误归因摘要两项内容，形成闭环处置输出",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "该材料引用的‘四种形态’适用条件与最新中央纪委通报案例中的实践口径存在冲突，需人工复核。",
          "trap": true,
          "category": "rule_conflict",
          "process_ref": "纪检文书纠错辅助与多源口径一致性校验",
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
