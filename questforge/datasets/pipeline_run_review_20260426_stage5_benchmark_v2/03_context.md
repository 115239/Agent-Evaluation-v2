---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-26T19:56:10+08:00
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
| KB-001 | 3849 | TEST-001,TEST-003 |
| KB-002 | 1006 | TEST-001 |
| KB-003 | 1235 | TEST-002 |
| KB-004 | 4999 | TEST-003 |

## 题目上下文设计
### TEST-001 (advanced · 党纪法规语义驱动的定性量纪建议生成)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-001-0109、FRAG-002-0033、FRAG-002-0034、FRAG-002-0667、FRAG-001-0418、FRAG-002-0104
- **关键字候选**:违反政治纪律、违反工作纪律、八项规定范畴、属于八项规定、应当受到党纪处分、受到党纪处分的、影响公正执行公务、市场主体提供信息
- **约束项**(4):
  1. C-001 · 引用结构化条款库中最新官方发布版本的党纪条文 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 整合结构化条款库与实务问答库中的对应片段，形成完整定性依据 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-003 · 排除非官方来源及历史修订稿中的过时解释 [来源:时效性 · 验证:regulation_support]
  1. C-004 · 输出必须包含违纪行为定性、量纪情节分析、建议处分档次三项内容 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·材料中提及的处分建议与最新修订的《中国共产党纪律处分条例》条款存在表述差异，需核对是否属于冲突情形。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-002 (basic · 总书记讲话上下文支撑的文书口径校验)
- **主资产**:KB-003
- **核心 fragment**:FRAG-003-0402、FRAG-003-0903、FRAG-003-0260
- **关键字候选**:严明政治纪律、政治纪律和、严格遵守政治纪律、中央八项规定
- **约束项**(3):
  1. C-005 · 引用官方发布的讲话摘要及上下文作为唯一依据 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-006 · 标注校验报告中每一项口径偏差所对应的讲话原文片段 [来源:outputs_count > 1 · 验证:llm_judge]
  1. C-007 · 依据审核复核触发场景，主动识别并提示需人工复核的模糊表述 [来源:triggers 含"模糊/推断"类 · 验证:llm_judge]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-003 (advanced · 纪检文书全要素智能纠错与依据回溯)
- **主资产**:KB-004、KB-001
- **核心 fragment**:FRAG-004-1346、FRAG-004-1611、FRAG-004-2028、FRAG-004-2045、FRAG-004-2105、FRAG-004-4690
- **关键字候选**:审查调查工作、实现审查调查、加强审查调查、审查调查安全、审查调查、确保审查调查、审查调查依法、审查调查质量
- **约束项**(4):
  1. C-008 · 引用结构化条款中最新官方版本作为纠错依据 [来源:时效性 · 验证:regulation_support]
  1. C-009 · 整合理论文章摘要与结构化条款，交叉验证表述合规性 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-010 · 依据审核复核场景，主动识别并标注需人工复核的模糊表述 [来源:triggers · 验证:llm_judge]
  1. C-011 · 完整交付纠错修订包，确保每处修改均附带对应条款出处 [来源:outputs_count · 验证:llm_judge]
- **干扰项**(1):
  1. I-002 · 陷阱·纪检文书引用的理论文章摘要与结构化条款在处分尺度上存在表述冲突。 [验证:regulation_support]
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
        "TEST-001"
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
      "covered_by": [
        "TEST-003"
      ]
    }
  },
  "test_contexts": [
    {
      "test_id": "TEST-001",
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
          "frag_id": "FRAG-001-0109",
          "asset_id": "KB-001",
          "snippet": "违反政治纪律, 违反廉洁纪律, 违反群众纪律, 违反工作纪律, 违反生活纪律 | 违反政治纪律和政治规矩，利用职权或者职务上的影响为他人谋取利益，收受可能影响公正执行公务的财物，违反办公用房管理规定，违反会议活动管理规定"
        },
        {
          "frag_id": "FRAG-002-0033",
          "asset_id": "KB-002",
          "snippet": "违规收送名贵特产和礼品礼金问题包含哪些情形？ | 违规收送名贵特产和礼品礼金问题分为'两收两送'四种情形：收受可能影响公正执行公务的财物、收受明显超出正常礼尚往来的财物、违规送礼、违规公款赠送发放礼品。 | 20210315 违规收送名贵特…"
        },
        {
          "frag_id": "FRAG-002-0034",
          "asset_id": "KB-002",
          "snippet": "特定关系人收受财物是否属于八项规定范畴？ | 特定关系人收受财物情形不属于八项规定范畴。 | 20210315 违规收送名贵特产和礼品礼金问题.docx | 片段11:文档标题: 20210315 违规收送名贵特产和礼品礼金问题 片段12:…"
        },
        {
          "frag_id": "FRAG-002-0667",
          "asset_id": "KB-002",
          "snippet": "收受可能影响公正执行公务的财物如何处理？ | 收受可能影响公正执行公务的礼品、礼金、消费卡和有价证券、股权、其他金融产品等财物，情节较轻的，给予警告或者严重警告处分；情节较重的，给予撤销党内职务或者留党察看处分；情节严重的，给予开除党籍处分…"
        },
        {
          "frag_id": "FRAG-001-0418",
          "asset_id": "KB-001",
          "snippet": "人民法院工作人员, 廉政准则, 利益冲突, 营利性活动, 兼职 | 接受可能影响公正执行公务的礼金、礼品、宴请以及旅游、健身、娱乐等活动安排，从事营利性活动，为他人的经济活动提供担保，买卖股票或认股权证，利用在办案工作中获取的内幕信息买卖股…"
        },
        {
          "frag_id": "FRAG-002-0104",
          "asset_id": "KB-002",
          "snippet": "王某违规吃喝行为有哪些表现？ | 一是按照《中国共产党纪律处分条例》第一百零三条的规定，王某“违反有关规定组织、参加用公款支付的宴请”;二是按照《中国共产党纪律处分条例》第九十二条的规定，王某“接受可能影响公正执行公务的宴请”。 | 202…"
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
        "违反政治纪律",
        "违反工作纪律",
        "八项规定范畴",
        "属于八项规定",
        "应当受到党纪处分",
        "受到党纪处分的",
        "影响公正执行公务",
        "市场主体提供信息"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "引用结构化条款库中最新官方发布版本的党纪条文",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "整合结构化条款库与实务问答库中的对应片段，形成完整定性依据",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "排除非官方来源及历史修订稿中的过时解释",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-004",
          "text": "输出必须包含违纪行为定性、量纪情节分析、建议处分档次三项内容",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "材料中提及的处分建议与最新修订的《中国共产党纪律处分条例》条款存在表述差异，需核对是否属于冲突情形。",
          "trap": true,
          "process_ref": "党纪法规语义驱动的定性量纪建议生成",
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
          "frag_id": "FRAG-003-0402",
          "asset_id": "KB-003",
          "snippet": "习近平：增强推进党的政治建设的自觉性和坚定性 | 2019-07-15 | 中国共产党第十八届中央委员会第六次全体会议，于2016年10月24日至27日在北京举行。中央委员会总书记习近平作重要讲话。 新华社记者 李学仁/摄 今天，我们进行十…"
        },
        {
          "frag_id": "FRAG-003-0903",
          "asset_id": "KB-003",
          "snippet": "习近平在中共中央政治局第六次集体学习时强调  把党的政治建设作为党的根本性建设  为党不断从胜利走向胜利提供重要保证 | 2018-06-30 | 中共中央政治局6月29日下午就加强党的政治建设举行第六次集体学习。中共中央总书记习近平在主持…"
        },
        {
          "frag_id": "FRAG-003-0260",
          "asset_id": "KB-003",
          "snippet": "习近平：决胜全面建成小康社会 夺取新时代中国特色社会主义伟大胜利 | 2017-10-27 | 决胜全面建成小康社会 夺取新时代中国特色社会主义伟大胜利 ——在中国共产党第十九次全国代表大会上的报告 （2017年10月18日） 习近平 同志…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "严明政治纪律",
        "政治纪律和",
        "严格遵守政治纪律",
        "中央八项规定"
      ],
      "constraints": [
        {
          "id": "C-005",
          "text": "引用官方发布的讲话摘要及上下文作为唯一依据",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "标注校验报告中每一项口径偏差所对应的讲话原文片段",
          "source": "outputs_count > 1",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-007",
          "text": "依据审核复核触发场景，主动识别并提示需人工复核的模糊表述",
          "source": "triggers 含\"模糊/推断\"类",
          "verified_by": "llm_judge"
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
        "KB-004",
        "KB-001"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-004-1346",
          "asset_id": "KB-004",
          "snippet": "在全面融合中实现“三个提升” / 高广才 | 转隶干部高广才提出实现审查调查工作‘三个提升’：战术思维向战略思维、单纯执法向纪法衔接、‘烂树’向护‘森林’。"
        },
        {
          "frag_id": "FRAG-004-1611",
          "asset_id": "KB-004",
          "snippet": "地方简讯 | 多地区纪委加强审查调查安全，注重隐患排查、风险提醒，提升执纪审查能力。"
        },
        {
          "frag_id": "FRAG-004-2028",
          "asset_id": "KB-004",
          "snippet": "不折不扣落实《意见》部署要求 推动国资央企全面从严治党向纵深发展 / 陈超英 | 落实《意见》部署，国资央企深化全面从严治党，强化政治监督，加强审查调查，提升纪检监察队伍能力。"
        },
        {
          "frag_id": "FRAG-004-2045",
          "asset_id": "KB-004",
          "snippet": "湖北：强化法治思维善用法治方式反腐败 / 杨宏斌 张定 | 湖北深化监察体制改革，强化法治思维，运用法治方式反腐败，注重制度建设，确保审查调查依法依规开展。"
        },
        {
          "frag_id": "FRAG-004-2105",
          "asset_id": "KB-004",
          "snippet": "一线传真 | 甘肃：巡视整改完成，省直机关干部住房超标清退工作结束。湖南常德：加强内部监督，严防‘灯下黑’。山东曲阜：旁听庭审检视审查调查质量。海南海口：权限清单规范权力行使。河北邯郸丛台区：抓细抓实党风廉政宣传教育。"
        },
        {
          "frag_id": "FRAG-004-4690",
          "asset_id": "KB-004",
          "snippet": "严格依规依纪依法开展审查调查 / 王薇 | 纪检监察审查调查严格依规依纪依法开展，强化党委领导，规范立案审批，外查工作需严格执行，重要取证全程录音录像，突出监管责任。"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-003-0134",
          "asset_id": "KB-003"
        },
        {
          "frag_id": "FRAG-003-0494",
          "asset_id": "KB-003"
        }
      ],
      "keyword_pool": [
        "审查调查工作",
        "实现审查调查",
        "加强审查调查",
        "审查调查安全",
        "审查调查",
        "确保审查调查",
        "审查调查依法",
        "审查调查质量"
      ],
      "constraints": [
        {
          "id": "C-008",
          "text": "引用结构化条款中最新官方版本作为纠错依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-009",
          "text": "整合理论文章摘要与结构化条款，交叉验证表述合规性",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-010",
          "text": "依据审核复核场景，主动识别并标注需人工复核的模糊表述",
          "source": "triggers",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-011",
          "text": "完整交付纠错修订包，确保每处修改均附带对应条款出处",
          "source": "outputs_count",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-002",
          "text": "纪检文书引用的理论文章摘要与结构化条款在处分尺度上存在表述冲突。",
          "trap": true,
          "process_ref": "纪检文书全要素智能纠错与依据回溯",
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
