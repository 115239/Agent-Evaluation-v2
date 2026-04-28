---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-22T00:39:04+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 3 道题建立了知识索引(共 11089 个 fragment),LLM 生成 12 条约束、3 条干扰(其中 3 条陷阱)。业务真实性通过 15/16。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-002 |
| KB-002 | 1006 | TEST-001,TEST-003 |
| KB-003 | 1235 | TEST-003 |
| KB-004 | 4999 | TEST-003 |

## 题目上下文设计
### TEST-001 (basic · 党纪法规语义检索支撑定性量纪决策)
- **主资产**:KB-002
- **核心 fragment**:FRAG-002-0059、FRAG-002-0060、FRAG-002-0061
- **关键字候选**:中央八项规定、八项规定精神
- **约束项**(4):
  1. C-001 · 依据KB-002最新官方版本引用实务问答结论 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 仅基于KB-002开展语义检索，排除其他非官方资产信息 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-003 · 输出必须为完整定性量纪建议初稿，不可省略任一构成要素 [来源:outputs_count > 1 · 验证:regulation_support]
  1. C-004 · 识别知识咨询触发场景，不主动推断未明示的违纪情节 [来源:triggers 含"模糊/推断"类 · 验证:llm_judge]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:4/4

### TEST-002 (advanced · 审查调查文书全流程智能纠错与合规复核)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0071、FRAG-001-0093、FRAG-001-0910、FRAG-001-0195、FRAG-001-2779、FRAG-001-1103
- **关键字候选**:立案审查调查、审查调查、审查调查尚未、接受审查调查、事实的财务会计、的财务会计报告、违反规定扩大权限、拒绝接受监督管理
- **约束项**(4):
  1. C-005 · 依据KB-001最新权威版本引用结构化条款 [来源:时效性 · 验证:regulation_support]
  1. C-006 · 完整交付带定位标记的纠错报告和结构化修正指令 [来源:outputs_count · 验证:llm_judge]
  1. C-007 · 仅基于BP-002单流程内信息开展审查，不整合跨流程资产 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-008 · 识别并排除非官方来源条款，仅使用KB-001中授权条款 [来源:assets_involved · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·文书落款日期早于立案审批日期，看似合理但违反审查调查时间逻辑。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-003 (expert · 总书记讲话与理论文章联合检索支撑政策研判)
- **主资产**:KB-003、KB-004、KB-002
- **核心 fragment**:FRAG-004-2769、FRAG-004-2661、FRAG-004-3420、FRAG-004-4705、FRAG-004-2763、FRAG-004-1628、FRAG-004-1636、FRAG-004-4903、FRAG-002-0585、FRAG-002-0201
- **关键字候选**:纪委严查违规行为、隐身衣问题曝光、全面从严治党强调、叫全面从严治党、八项规定出台、中央八项规定、完成许多学术著作、梁启超故居饮冰
- **约束项**(4):
  1. C-009 · 依据KB-003、KB-004、KB-002中最新发布版本引用权威内容 [来源:时效性 · 验证:regulation_support]
  1. C-010 · 整合KB-003与KB-004内容，交叉比对生成政策对比摘要 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-011 · 识别管理级权限边界，标注KB-002中仅限内部使用的实务问答信息 [来源:actors · 验证:regulation_support]
  1. C-013 · 基于知识咨询触发，主动推断用户未明示的政策适用场景并给出提示 [来源:triggers · 验证:llm_judge]
- **干扰项**(2):
  1. I-002 · 陷阱·KB-003与KB-004中关于‘自我革命’的表述存在版本冲突，需以最新讲话为准。 [验证:regulation_support]
  1. I-003 · 陷阱·KB-002实务问答中引用的案例发生在2021年，属于过时实践参考。 [验证:llm_judge]
- **真实性验证**:6/7

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
        "TEST-002"
      ]
    },
    "KB-002": {
      "total_fragments": 1006,
      "covered_by": [
        "TEST-001",
        "TEST-003"
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
      "covered_by": [
        "TEST-003"
      ]
    }
  },
  "test_contexts": [
    {
      "test_id": "TEST-001",
      "difficulty": "basic",
      "primary_assets": [
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
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "中央八项规定",
        "八项规定精神"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "依据KB-002最新官方版本引用实务问答结论",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "仅基于KB-002开展语义检索，排除其他非官方资产信息",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "输出必须为完整定性量纪建议初稿，不可省略任一构成要素",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-004",
          "text": "识别知识咨询触发场景，不主动推断未明示的违纪情节",
          "source": "triggers 含\"模糊/推断\"类",
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
      "difficulty": "advanced",
      "primary_assets": [
        "KB-001"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-001-0071",
          "asset_id": "KB-001",
          "snippet": "公务员考核规定, 处分执行, 考核结果运用, 年度考核, 违纪行为 | 涉嫌违纪违法被立案审查调查"
        },
        {
          "frag_id": "FRAG-001-0093",
          "asset_id": "KB-001",
          "snippet": "公务员职务与职级并行, 职级晋升, 待遇挂钩, 管理监督, 职数比例 | 受到诫勉、组织处理或者处分等影响期未满或者期满影响使用，涉嫌违纪违法正在接受审查调查尚未作出结论"
        },
        {
          "frag_id": "FRAG-001-0910",
          "asset_id": "KB-001",
          "snippet": "商业银行，信息披露，财务会计报告，风险管理，公司治理 | 提供虚假的或者隐瞒重要事实的财务会计报告"
        },
        {
          "frag_id": "FRAG-001-0195",
          "asset_id": "KB-001",
          "snippet": "统一业务应用系统, 检察工作, 信息填录, 文书制作, 网上业务流转 | 违反网上信息填录、业务流转、文书制作、数据统计、信息发布、电子签章、权限管理、运行维护、安全保密等规定，隐瞒、虚报、迟报业务信息，违反规定扩大权限配置，违反规定将系统…"
        },
        {
          "frag_id": "FRAG-001-2779",
          "asset_id": "KB-001",
          "snippet": "任职回避, 公务回避, 国家公务员, 亲属关系, 回避申请 | 隐瞒应回避的亲属关系，无正当理由拒不服从组织安排"
        },
        {
          "frag_id": "FRAG-001-1103",
          "asset_id": "KB-001",
          "snippet": "重大动物疫情, 应急处理, 疫情报告, 疫区, 动物防疫监督机构 | 瞒报、谎报、迟报重大动物疫情，不采取临时隔离控制措施，不划定疫点、疫区和受威胁区"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-003-1019",
          "asset_id": "KB-003"
        },
        {
          "frag_id": "FRAG-002-0299",
          "asset_id": "KB-002"
        }
      ],
      "keyword_pool": [
        "立案审查调查",
        "审查调查",
        "审查调查尚未",
        "接受审查调查",
        "事实的财务会计",
        "的财务会计报告",
        "违反规定扩大权限",
        "拒绝接受监督管理"
      ],
      "constraints": [
        {
          "id": "C-005",
          "text": "依据KB-001最新权威版本引用结构化条款",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "完整交付带定位标记的纠错报告和结构化修正指令",
          "source": "outputs_count",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-007",
          "text": "仅基于BP-002单流程内信息开展审查，不整合跨流程资产",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-008",
          "text": "识别并排除非官方来源条款，仅使用KB-001中授权条款",
          "source": "assets_involved",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "文书落款日期早于立案审批日期，看似合理但违反审查调查时间逻辑。",
          "trap": true,
          "process_ref": "审查调查文书全流程智能纠错与合规复核",
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
      "difficulty": "expert",
      "primary_assets": [
        "KB-003",
        "KB-004",
        "KB-002"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-004-2769",
          "asset_id": "KB-004",
          "snippet": "晒晒8类“四风”隐身衣 / 徐彩霞 | 八类‘四风’隐身衣问题曝光，包括‘小金库’、公款旅游、电子礼品卡等，纪委严查违规行为。"
        },
        {
          "frag_id": "FRAG-004-2661",
          "asset_id": "KB-004",
          "snippet": "用纪律管住大多数才叫全面从严治党 / 辛 鸣 | 全面从严治党强调全方位、全覆盖，习近平强调反腐无禁区，巡视全覆盖，派驻监督加强。"
        },
        {
          "frag_id": "FRAG-004-3420",
          "asset_id": "KB-004",
          "snippet": "高调豪华不再 隐形奢靡仍存 / 沈叶 | 新年消费回归正常，隐形奢华风盛行。政府机关、国企年会低调，餐饮消费回归正常。中央八项规定出台后，奢靡之风仍存，需常抓不懈。"
        },
        {
          "frag_id": "FRAG-004-4705",
          "asset_id": "KB-004",
          "snippet": "饮冰室书斋：唯有“饮冰”方解“内热” / 周美玲 | 梁启超故居饮冰室书斋，位于天津河北区民族路。梁启超晚年在此完成许多学术著作，启迪民智，对教育和文学影响深远。"
        },
        {
          "frag_id": "FRAG-004-2763",
          "asset_id": "KB-004",
          "snippet": "环保部：向环评“红顶中介”开刀 / 田若饴 | 环保部整治环评‘红顶中介’，2016年底前全国环保系统所属机构与审批部门完全脱钩，违规机构将被取消资质。"
        },
        {
          "frag_id": "FRAG-004-1628",
          "asset_id": "KB-004",
          "snippet": "监督、调查、处置一体推进——保证监察全覆盖的质量和效果 / 余哲西 | 国家监察体制改革推进，强调监督、调查、处置一体推进，解决监督不足、新职责适应等问题。"
        },
        {
          "frag_id": "FRAG-004-1636",
          "asset_id": "KB-004",
          "snippet": "摸清“症状”更要深挖“病根” / 秦皇岛市纪委监委 | 秦皇岛市纪委监委调研分析扶贫领域腐败和作风问题，涉及危房改造、低保五保、产业扶贫、基础设施建设等四方面问题。"
        },
        {
          "frag_id": "FRAG-004-4903",
          "asset_id": "KB-004",
          "snippet": "风清气正守护山清水秀 / 师长青 | 生态环境部开展污染防治攻坚战专项治理，强化政治生态建设，推动干部作风建设，成效显著，空气质量、水质、土壤质量均有所改善。"
        },
        {
          "frag_id": "FRAG-002-0585",
          "asset_id": "KB-002",
          "snippet": "公务员从事营利活动如何处分？ | 从事或者参与营利性活动，在企业或者其他营利性组织中兼任职务的，给予记过或者记大过处分；情节较重的，给予降级或者撤职处分；情节严重的，给予开除处分。 | 第一批精准规范运用“四种形态”典型案例（下）.docx…"
        },
        {
          "frag_id": "FRAG-002-0201",
          "asset_id": "KB-002",
          "snippet": "在扶贫中优亲厚友如何处理？ | 在社会保障、政策扶持、扶贫脱贫、救灾救济款物分配等事项中优亲厚友、明显有失公平的，给予警告或者严重警告处分；情节较重的，给予撤销党内职务或者留党察看处分；情节严重的，给予开除党籍处分。 | 20211229 …"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-001-0344",
          "asset_id": "KB-001"
        },
        {
          "frag_id": "FRAG-001-2721",
          "asset_id": "KB-001"
        },
        {
          "frag_id": "FRAG-001-3212",
          "asset_id": "KB-001"
        }
      ],
      "keyword_pool": [
        "纪委严查违规行为",
        "隐身衣问题曝光",
        "全面从严治党强调",
        "叫全面从严治党",
        "八项规定出台",
        "中央八项规定",
        "完成许多学术著作",
        "梁启超故居饮冰"
      ],
      "constraints": [
        {
          "id": "C-009",
          "text": "依据KB-003、KB-004、KB-002中最新发布版本引用权威内容",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-010",
          "text": "整合KB-003与KB-004内容，交叉比对生成政策对比摘要",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-011",
          "text": "识别管理级权限边界，标注KB-002中仅限内部使用的实务问答信息",
          "source": "actors",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-013",
          "text": "基于知识咨询触发，主动推断用户未明示的政策适用场景并给出提示",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-002",
          "text": "KB-003与KB-004中关于‘自我革命’的表述存在版本冲突，需以最新讲话为准。",
          "trap": true,
          "process_ref": "总书记讲话与理论文章联合检索支撑政策研判",
          "verified_by": "regulation_support"
        },
        {
          "id": "I-003",
          "text": "KB-002实务问答中引用的案例发生在2021年，属于过时实践参考。",
          "trap": true,
          "process_ref": "总书记讲话与理论文章联合检索支撑政策研判",
          "verified_by": "llm_judge"
        }
      ],
      "realism_check": {
        "total": 7,
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
以下候选因真实性验证未通过被丢弃:
  - [TEST-003][C] 完整输出政策对比摘要、政策适用提示、知识图谱更新指令三项结果
