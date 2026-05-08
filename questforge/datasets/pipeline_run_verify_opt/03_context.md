---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-05-08T00:46:22+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 4 道题建立了知识索引(共 11089 个 fragment),LLM 生成 11 条约束、4 条干扰(其中 4 条陷阱)。业务真实性通过 15/15。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-001,TEST-002,TEST-003,TEST-004 |
| KB-002 | 1006 | TEST-002,TEST-003 |
| KB-003 | 1235 | TEST-004 |
| KB-004 | 4999 | TEST-004 |

## 题目上下文设计
### TEST-001 (basic · 党纪条款语义检索支撑线索初核定性)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0109、FRAG-001-0418、FRAG-001-0041
- **关键字候选**:违反政治纪律、违反工作纪律、其他市场主体提供、影响公正执行公务、造成不良后果或者、不良后果或者影响
- **约束项**(2):
  1. C-001 · 必须引用结构化条款资产中的最新权威条目 → authority [来源:assets_involved · 验证:regulation_support]
  1. C-002 · 必须标注每条匹配依据的来源文档及具体片段 → 未标注依据来源文档及片段 [来源:user_personas · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:2/2

### TEST-002 (advanced · 跨知识源定性量纪综合建议生成)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0059、FRAG-002-0060、FRAG-002-0061、FRAG-002-0062、FRAG-002-0063、FRAG-002-0064
- **关键字候选**:中央八项规定、八项规定精神、违反八项规定
- **约束项**(3):
  1. C-003 · 必须整合结构化条款与实务问答两类资产生成建议 → 跨流程 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-004 · 必须引用最新发布的执纪执法指导性案例内容 → KB-002 [来源:assets_involved · 验证:regulation_support]
  1. C-005 · 必须标注每条定性量纪依据所来源的文档名称及具体片段 → UG-001 [来源:user_personas · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·[version_conflict]·某基层纪委内部培训材料提到‘对首次轻微违反八项规定者可免予处分’，该说法与中央纪委网站发布的指导性案例精神不一致。 [验证:regulation_support]
- **真实性验证**:4/4

### TEST-003 (advanced · 纪检文书纠错与多源依据闭环审核)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0624、FRAG-002-0335、FRAG-002-0336、FRAG-002-0337、FRAG-002-0338、FRAG-002-0339
- **关键字候选**:应当受到党纪处分、受到党纪处分的、成立审查调查组、审查调查组可以、群众纪律
- **约束项**(3):
  1. C-006 · 必须整合结构化条款与实务问答两类资产依据 → 跨流程 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-007 · 必须标注每条依据所来源的文档名称及片段位置 → 未标注依据来源文档及片段 [来源:user_personas.frustration_triggers · 验证:regulation_support]
  1. C-008 · 必须排除‘四种形态’适用阶段与党纪处分档次的混淆表述 → 混淆‘四种形态’适用阶段与处分档次 [来源:user_personas.frustration_triggers · 验证:regulation_support]
- **干扰项**(1):
  1. I-002 · 陷阱·[scope_creep]·青光村协调费案例中，李某某被立案审查时间是2021年1月，但同期另一份材料称其2020年12月已受诫勉处理，二者存在事实冲突。 [验证:llm_judge]
- **真实性验证**:4/4

### TEST-004 (expert · 总书记讲话—理论文章—党纪条款三维政策依据整合输出)
- **主资产**:KB-001、KB-003、KB-004
- **核心 fragment**:FRAG-004-4861、FRAG-003-0031、FRAG-003-0192、FRAG-003-0654、FRAG-004-2161、FRAG-003-0652、FRAG-003-0653、FRAG-003-0092、FRAG-003-0395、FRAG-003-0819
- **关键字候选**:政治监督具体化、工作高质量发展、中央八项规定、严明政治纪律、内蒙古自治区纪委、内蒙古高质量发展、八项规定、中国特色社会主义
- **约束项**(3):
  1. C-009 · 必须整合总书记讲话、理论文章、党纪条款三类资产形成三维依据包 → cross_process_dependency [来源:process.name · 验证:llm_judge]
  1. C-010 · 必须引用最新版本的中央纪委全会讲话，排除2023年及以前的旧版全会精神 → weak_point 名 或 维度名 [来源:profile.assets_involved · 验证:regulation_support]
  1. C-012 · 必须标注每条依据所来源的资产类别及具体片段内容，拒绝无来源摘要 → frustration_triggers [来源:user_personas.UG-001 · 验证:regulation_support]
- **干扰项**(2):
  1. I-003 · 陷阱·[version_conflict]·内蒙古自治区纪委监委将党中央决策部署落实情况作为监督重点——该表述出自理论文章摘要，但被误标为二十届中央纪委四次全会讲话原文。 [验证:regulation_support]
  1. I-004 · 陷阱·[emotional_pressure]·提问者强调‘只要结论，不要解释’，并称‘再给长篇大论就直接退单’，情绪急迫且明确拒绝过程说明。 [验证:llm_judge]
- **真实性验证**:5/5

## 结构化数据
```json
{
  "fallback_status": {
    "weak_points_present": false
  },
  "authority_keywords_count": 17,
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
        "TEST-002",
        "TEST-003"
      ]
    },
    "KB-003": {
      "total_fragments": 1235,
      "covered_by": [
        "TEST-004"
      ]
    },
    "KB-004": {
      "total_fragments": 4999,
      "covered_by": [
        "TEST-004"
      ]
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
          "frag_id": "FRAG-001-0418",
          "asset_id": "KB-001",
          "snippet": "人民法院工作人员, 廉政准则, 利益冲突, 营利性活动, 兼职 | 接受可能影响公正执行公务的礼金、礼品、宴请以及旅游、健身、娱乐等活动安排，从事营利性活动，为他人的经济活动提供担保，买卖股票或认股权证，利用在办案工作中获取的内幕信息买卖股…"
        },
        {
          "frag_id": "FRAG-001-0041",
          "asset_id": "KB-001",
          "snippet": "政务处分, 违纪行为, 公职人员, 处分管理, 违法行为 | 散布有损宪法权威、中国共产党领导和国家声誉的言论，参加旨在反对宪法、中国共产党领导和国家的集会、游行、示威等活动，拒不执行或者变相不执行中国共产党和国家的路线方针政策、重大决策部…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "违反政治纪律",
        "违反工作纪律",
        "其他市场主体提供",
        "影响公正执行公务",
        "造成不良后果或者",
        "不良后果或者影响"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "必须引用结构化条款资产中的最新权威条目",
          "source": "assets_involved",
          "targets": [
            "authority"
          ],
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "必须标注每条匹配依据的来源文档及具体片段",
          "source": "user_personas",
          "targets": [
            "未标注依据来源文档及片段"
          ],
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [],
      "realism_check": {
        "total": 2,
        "passed": 2,
        "raw_total": 2,
        "filtered_out": 0
      }
    },
    {
      "test_id": "TEST-002",
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
          "id": "C-003",
          "text": "必须整合结构化条款与实务问答两类资产生成建议",
          "source": "cross_process_dependency",
          "targets": [
            "跨流程"
          ],
          "verified_by": "regulation_support"
        },
        {
          "id": "C-004",
          "text": "必须引用最新发布的执纪执法指导性案例内容",
          "source": "assets_involved",
          "targets": [
            "KB-002"
          ],
          "verified_by": "regulation_support"
        },
        {
          "id": "C-005",
          "text": "必须标注每条定性量纪依据所来源的文档名称及具体片段",
          "source": "user_personas",
          "targets": [
            "UG-001"
          ],
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "某基层纪委内部培训材料提到‘对首次轻微违反八项规定者可免予处分’，该说法与中央纪委网站发布的指导性案例精神不一致。",
          "trap": true,
          "trap_kind": "version_conflict",
          "category": "实务问答",
          "process_ref": "跨知识源定性量纪综合建议生成",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 4,
        "passed": 4,
        "raw_total": 4,
        "filtered_out": 0
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
          "frag_id": "FRAG-002-0335",
          "asset_id": "KB-002",
          "snippet": "与被审查调查人的谈话应由谁负责？ | 与被审查调查人的谈话、讯问应由本机关干部作为主谈人。 | 制定审查调查方案应注意哪些问题.docx | 片段5:经批准成立审查调查组后 ，要明 确组长和成员及组内分工 ，对于重大 、复杂的案件 ，一般下…"
        },
        {
          "frag_id": "FRAG-002-0336",
          "asset_id": "KB-002",
          "snippet": "后勤保障包括哪些内容？ | 要与办公室、案管等部门协调，保障办案车辆和设备、办公用品、生活用品等，并配备必要的急救药品，与相关医院建立医疗绿色通道，做好医疗保障。 | 制定审查调查方案应注意哪些问题.docx | 片段5:经批准成立审查调查…"
        },
        {
          "frag_id": "FRAG-002-0337",
          "asset_id": "KB-002",
          "snippet": "措施保障包括哪些内容？ | 要加强与公安机关的协作配合，提请协助采取搜查、留置、通缉、限制出境和技术侦查等措施。 | 制定审查调查方案应注意哪些问题.docx | 片段5:经批准成立审查调查组后 ，要明 确组长和成员及组内分工 ，对于重大 …"
        },
        {
          "frag_id": "FRAG-002-0338",
          "asset_id": "KB-002",
          "snippet": "取证保障包括哪些内容？ | 要与案发单位多沟通协调，做好相关人员的陪护交接，提供有关证据材料等工作。 | 制定审查调查方案应注意哪些问题.docx | 片段5:经批准成立审查调查组后 ，要明 确组长和成员及组内分工 ，对于重大 、复杂的案件…"
        },
        {
          "frag_id": "FRAG-002-0339",
          "asset_id": "KB-002",
          "snippet": "办案人员的具体任务如何明确？ | 办案人员承担的具体任务可在谈话方案和外查方案中进一步细化和明确。 | 制定审查调查方案应注意哪些问题.docx | 片段5:经批准成立审查调查组后 ，要明 确组长和成员及组内分工 ，对于重大 、复杂的案件 …"
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
        "应当受到党纪处分",
        "受到党纪处分的",
        "成立审查调查组",
        "审查调查组可以",
        "群众纪律"
      ],
      "constraints": [
        {
          "id": "C-006",
          "text": "必须整合结构化条款与实务问答两类资产依据",
          "source": "cross_process_dependency",
          "targets": [
            "跨流程"
          ],
          "verified_by": "regulation_support"
        },
        {
          "id": "C-007",
          "text": "必须标注每条依据所来源的文档名称及片段位置",
          "source": "user_personas.frustration_triggers",
          "targets": [
            "未标注依据来源文档及片段"
          ],
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "必须排除‘四种形态’适用阶段与党纪处分档次的混淆表述",
          "source": "user_personas.frustration_triggers",
          "targets": [
            "混淆‘四种形态’适用阶段与处分档次"
          ],
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-002",
          "text": "青光村协调费案例中，李某某被立案审查时间是2021年1月，但同期另一份材料称其2020年12月已受诫勉处理，二者存在事实冲突。",
          "trap": true,
          "trap_kind": "scope_creep",
          "category": "scope_creep",
          "process_ref": "纪检文书纠错与多源依据闭环审核",
          "verified_by": "llm_judge"
        }
      ],
      "realism_check": {
        "total": 4,
        "passed": 4,
        "raw_total": 4,
        "filtered_out": 0
      }
    },
    {
      "test_id": "TEST-004",
      "difficulty": "expert",
      "sample_idx": 0,
      "focus_stages": [
        "定义问题",
        "拆解问题",
        "方案生成",
        "执行落地",
        "元认知"
      ],
      "primary_assets": [
        "KB-001",
        "KB-003",
        "KB-004"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-004-4861",
          "asset_id": "KB-004",
          "snippet": "如何理解全国巡视工作会议部署要求 / 刘来宾 | 全国巡视工作会议部署要求：聚焦‘两个维护’，推进政治监督具体化常态化，推动巡视工作高质量发展。"
        },
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
        },
        {
          "frag_id": "FRAG-004-2161",
          "asset_id": "KB-004",
          "snippet": "把党中央各项决策部署落实情况作为 | 内蒙古自治区纪委监委将党中央决策部署落实情况作为监督重点，通过政治监督具体化、精准化、常态化，护航内蒙古高质量发展。"
        },
        {
          "frag_id": "FRAG-003-0652",
          "asset_id": "KB-003",
          "snippet": "习近平在二十届中央纪委二次全会上发表重要讲话 | 2023-01-09 | 习近平在二十届中央纪委二次全会上发表重要讲话强调 一刻不停推进全面从严治党 保障党的二十大决策部署贯彻落实 李强赵乐际王沪宁蔡奇丁薛祥出席会议　李希主持会议 新华社…"
        },
        {
          "frag_id": "FRAG-003-0653",
          "asset_id": "KB-003",
          "snippet": "习近平在二十届中央纪委二次全会上发表重要讲话强调 一刻不停推进全面从严治党 保障党的二十大决策部署贯彻落实 | 2023-01-09 | 习近平在二十届中央纪委二次全会上发表重要讲话强调 一刻不停推进全面从严治党 保障党的二十大决策部署贯彻…"
        },
        {
          "frag_id": "FRAG-003-0092",
          "asset_id": "KB-003",
          "snippet": "坚定不移走中国特色社会主义法治道路 为全面建设社会主义现代化国家提供有力法治保障 | 2021-02-28 | 坚定不移走中国特色社会主义法治道路 为全面建设社会主义现代化国家提供有力法治保障 习近平 这次中央全面依法治国工作会议的主要任务…"
        },
        {
          "frag_id": "FRAG-003-0395",
          "asset_id": "KB-003",
          "snippet": "习近平：在新的起点上深化国家监察体制改革 | 2019-02-28 | 中国共产党第十九届中央委员会第三次全体会议，于2018年2月26日至28日在北京举行。中央委员会总书记习近平作重要讲话。 新华社记者 鞠鹏/摄 2018年3月20日，第…"
        },
        {
          "frag_id": "FRAG-003-0819",
          "asset_id": "KB-003",
          "snippet": "习近平在十九届中央纪委五次全会上发表重要讲话强调 充分发挥全面从严治党引领保障作用 确保“十四五”时期目标任务落到实处 李克强栗战书汪洋王沪宁韩正出席会议 赵乐际主持会议 | 2021-01-22 | 1月22日，中共中央总书记、国家主席、…"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-002-0876",
          "asset_id": "KB-002"
        },
        {
          "frag_id": "FRAG-002-0733",
          "asset_id": "KB-002"
        },
        {
          "frag_id": "FRAG-002-0551",
          "asset_id": "KB-002"
        }
      ],
      "keyword_pool": [
        "政治监督具体化",
        "工作高质量发展",
        "中央八项规定",
        "严明政治纪律",
        "内蒙古自治区纪委",
        "内蒙古高质量发展",
        "八项规定",
        "中国特色社会主义"
      ],
      "constraints": [
        {
          "id": "C-009",
          "text": "必须整合总书记讲话、理论文章、党纪条款三类资产形成三维依据包",
          "source": "process.name",
          "targets": [
            "cross_process_dependency"
          ],
          "verified_by": "llm_judge"
        },
        {
          "id": "C-010",
          "text": "必须引用最新版本的中央纪委全会讲话，排除2023年及以前的旧版全会精神",
          "source": "profile.assets_involved",
          "targets": [
            "weak_point 名 或 维度名"
          ],
          "verified_by": "regulation_support"
        },
        {
          "id": "C-012",
          "text": "必须标注每条依据所来源的资产类别及具体片段内容，拒绝无来源摘要",
          "source": "user_personas.UG-001",
          "targets": [
            "frustration_triggers"
          ],
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-003",
          "text": "内蒙古自治区纪委监委将党中央决策部署落实情况作为监督重点——该表述出自理论文章摘要，但被误标为二十届中央纪委四次全会讲话原文。",
          "trap": true,
          "trap_kind": "version_conflict",
          "category": "version_conflict",
          "process_ref": "总书记讲话—理论文章—党纪条款三维政策依据整合输出",
          "verified_by": "regulation_support"
        },
        {
          "id": "I-004",
          "text": "提问者强调‘只要结论，不要解释’，并称‘再给长篇大论就直接退单’，情绪急迫且明确拒绝过程说明。",
          "trap": true,
          "trap_kind": "emotional_pressure",
          "category": "emotional_pressure",
          "process_ref": "总书记讲话—理论文章—党纪条款三维政策依据整合输出",
          "verified_by": "llm_judge"
        }
      ],
      "realism_check": {
        "total": 5,
        "passed": 5,
        "raw_total": 6,
        "filtered_out": 1
      }
    }
  ]
}
```

## 下一阶段校验清单
- [x] 每道 TEST 至少 1 个约束项
- [x] basic 0 干扰、advanced ≥1、expert ≥2 且含 1 陷阱
- [x] trap_kind 取值合法且 expert 至少 1 条 trap_kind ≠ none
- [x] 每条约束/干扰通过真实性三检验之一
- [x] 每道 TEST 的 keyword_pool ≥ 1
- [x] 每道 TEST 的 fragments ≥ 1

## 备注与遗留问题
以下候选因真实性验证未通过被丢弃:
  - [TEST-004][C] 必须完整交付三维政策依据整合包与管理层复核意见两项输出
