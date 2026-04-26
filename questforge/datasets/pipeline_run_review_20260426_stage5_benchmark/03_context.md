---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-26T19:49:51+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 3 道题建立了知识索引(共 11089 个 fragment),LLM 生成 11 条约束、2 条干扰(其中 2 条陷阱)。业务真实性通过 13/13。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-001,TEST-002 |
| KB-002 | 1006 | TEST-001,TEST-002 |
| KB-003 | 1235 | TEST-003 |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (advanced · 党纪法规语义检索支撑定性量纪建议生成)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0059、FRAG-002-0060、FRAG-002-0061、FRAG-002-0062、FRAG-002-0063、FRAG-002-0064
- **关键字候选**:中央八项规定、八项规定精神、违反八项规定
- **约束项**(4):
  1. C-001 · 引用结构化条款库和实务问答库中最新官方发布版本的全部相关条款 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 整合结构化条款库与实务问答库内容，形成统一的定性量纪依据支撑 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-003 · 依据案件研判触发条件，主动推断需适用的党纪法规条款类型及适用情形 [来源:triggers · 验证:regulation_support]
  1. C-004 · 完整生成定性量纪建议书，确保结论明确、依据可追溯、逻辑闭环 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·该材料中引用的党纪条款版本与最新修订版存在表述差异，看似合理但可能影响定性结论。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-002 (advanced · 纪检文书纠错与政治合规性复核)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0079、FRAG-002-0083、FRAG-002-0075、FRAG-002-0080、FRAG-002-0081、FRAG-002-0082
- **关键字候选**:违反政治纪律、中央八项规定、八项规定精神、形式主义官僚主义
- **约束项**(4):
  1. C-005 · 引用结构化条款库中最新官方发布版本进行政治合规性比对 [来源:时效性 · 验证:regulation_support]
  1. C-006 · 整合结构化条款库与实务问答库中的官方信息，交叉验证纠错依据 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-007 · 依据本流程输出要求，完整生成文书纠错报告问题清单 [来源:outputs_count · 验证:regulation_support]
  1. C-008 · 在审核复核触发场景下，主动识别并标注需业务人员确认的模糊表述项 [来源:triggers · 验证:llm_judge]
- **干扰项**(1):
  1. I-002 · 陷阱·该文书引用的2021年版《监督执纪工作规则》条款，与2023年修订版存在表述差异，需注意版本冲突。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-003 (basic · 理论政策语义溯源与权威引用生成)
- **主资产**:KB-003
- **核心 fragment**:FRAG-003-0031、FRAG-003-0101、FRAG-003-0154
- **关键字候选**:中央八项规定、严明政治纪律、八项规定开局、中国特色社会主义、伟大社会革命实践
- **约束项**(3):
  1. C-009 · 引用官方发布的讲话摘要及上下文作为唯一政策依据 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-010 · 整合讲话摘要与其原始上下文片段，确保语义完整性 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-011 · 输出政策引用包须包含条款原文、出处层级与适用场景说明 [来源:outputs_count > 1 · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

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
        "TEST-002"
      ]
    },
    "KB-002": {
      "total_fragments": 1006,
      "covered_by": [
        "TEST-001",
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
      "difficulty": "advanced",
      "sample_idx": 0,
      "focus_stages": [
        "拆解问题",
        "方案生成"
      ],
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
        "中央八项规定",
        "八项规定精神",
        "违反八项规定"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "引用结构化条款库和实务问答库中最新官方发布版本的全部相关条款",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "整合结构化条款库与实务问答库内容，形成统一的定性量纪依据支撑",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "依据案件研判触发条件，主动推断需适用的党纪法规条款类型及适用情形",
          "source": "triggers",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-004",
          "text": "完整生成定性量纪建议书，确保结论明确、依据可追溯、逻辑闭环",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "该材料中引用的党纪条款版本与最新修订版存在表述差异，看似合理但可能影响定性结论。",
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
      "sample_idx": 0,
      "focus_stages": [
        "定义问题",
        "方案生成"
      ],
      "primary_assets": [
        "KB-001",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-002-0079",
          "asset_id": "KB-002",
          "snippet": "哪些条例列举的情形可认定为形式主义、官僚主义？ | 《中国共产党纪律处分条例》第五十条、第一百一十二条、第一百一十三条、第一百一十六条、第一百一十七条、第一百三十三条等条款列举的情形 | 20210804 中央纪委国家监委发布第一批执纪执法…"
        },
        {
          "frag_id": "FRAG-002-0083",
          "asset_id": "KB-002",
          "snippet": "违反群众纪律等问题如何认定为形式主义、官僚主义？ | 如果将违反群众纪律、工作纪律等问题认定为形式主义、官僚主义，应该在纪检监察文书的'违反中央八项规定精神'问题中予以单列表述 | 20210804 中央纪委国家监委发布第一批执纪执法指导性…"
        },
        {
          "frag_id": "FRAG-002-0075",
          "asset_id": "KB-002",
          "snippet": "什么是形式主义、官僚主义？ | 形式主义、官僚主义与党的优良传统、优良作风背道而驰，为广大干部群众所深恶痛绝。 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段4:1.贺某在新冠肺炎疫情防…"
        },
        {
          "frag_id": "FRAG-002-0080",
          "asset_id": "KB-002",
          "snippet": "形式主义背后的根源是什么？ | 形式主义背后是功利主义、实用主义作祟，政绩观错位、责任心缺失，只想当官不想干事，只想出彩不想担责，满足于做表面文章，重显绩不重潜绩，重包装不重实效 | 20210804 中央纪委国家监委发布第一批执纪执法指导…"
        },
        {
          "frag_id": "FRAG-002-0081",
          "asset_id": "KB-002",
          "snippet": "官僚主义背后的根源是什么？ | 官僚主义背后是官本位思想，价值观走偏、权力观扭曲，盲目依赖个人经验和主观判断，严重脱离实际、脱离群众 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段9:从…"
        },
        {
          "frag_id": "FRAG-002-0082",
          "asset_id": "KB-002",
          "snippet": "贺某存在哪些突出问题？ | 贺某政绩观错位、责任心缺失、满足于做表面文章等突出问题 | 20210804 中央纪委国家监委发布第一批执纪执法指导性案例-中央纪委网站.docx | 片段9:从本案所表现出来的现象看，贺某确实存在不   正确履…"
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
        "违反政治纪律",
        "中央八项规定",
        "八项规定精神",
        "形式主义官僚主义"
      ],
      "constraints": [
        {
          "id": "C-005",
          "text": "引用结构化条款库中最新官方发布版本进行政治合规性比对",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "整合结构化条款库与实务问答库中的官方信息，交叉验证纠错依据",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-007",
          "text": "依据本流程输出要求，完整生成文书纠错报告问题清单",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "在审核复核触发场景下，主动识别并标注需业务人员确认的模糊表述项",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-002",
          "text": "该文书引用的2021年版《监督执纪工作规则》条款，与2023年修订版存在表述差异，需注意版本冲突。",
          "trap": true,
          "process_ref": "纪检文书纠错与政治合规性复核",
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
      "sample_idx": 0,
      "focus_stages": [
        "定义问题"
      ],
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
          "frag_id": "FRAG-003-0101",
          "asset_id": "KB-003",
          "snippet": "健全全面从严治党体系 推动新时代党的建设新的伟大工程向纵深发展 | 2023-06-15 | 健全全面从严治党体系 推动新时代党的建设新的伟大工程向纵深发展 习近平 把党的建设作为一项伟大工程来推进，并且始终坚持党要管党、从严治党的原则和方…"
        },
        {
          "frag_id": "FRAG-003-0154",
          "asset_id": "KB-003",
          "snippet": "深入推进党的自我革命 | 2024-12-15 | 深入推进党的自我革命 习近平 我们党作为世界上最大的马克思主义执政党，如何成功跳出治乱兴衰历史周期率、确保党永远不变质不变色不变味？这是摆在全党同志面前的一个战略性问题。党的十八大以来，在…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "中央八项规定",
        "严明政治纪律",
        "八项规定开局",
        "中国特色社会主义",
        "伟大社会革命实践"
      ],
      "constraints": [
        {
          "id": "C-009",
          "text": "引用官方发布的讲话摘要及上下文作为唯一政策依据",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-010",
          "text": "整合讲话摘要与其原始上下文片段，确保语义完整性",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-011",
          "text": "输出政策引用包须包含条款原文、出处层级与适用场景说明",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
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
- [x] 每道 TEST 的 keyword_pool ≥ 1
- [x] 每道 TEST 的 fragments ≥ 1

## 备注与遗留问题
(无)
