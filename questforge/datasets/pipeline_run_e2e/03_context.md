---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-21T01:27:07+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 2 道题建立了知识索引(共 11089 个 fragment),LLM 生成 9 条约束、1 条干扰(其中 1 条陷阱)。业务真实性通过 10/10。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | — |
| KB-002 | 1006 | TEST-002 |
| KB-003 | 1235 | TEST-001 |
| KB-004 | 4999 | TEST-001 |

## 题目上下文设计
### TEST-001 (advanced · 多源理论素材协同检索与政策阐释)
- **主资产**:KB-004、KB-003
- **核心 fragment**:FRAG-004-3431、FRAG-004-1132、FRAG-004-3755、FRAG-003-0060、FRAG-004-3248、FRAG-004-1214
- **关键字候选**:纪律审查呈现、提升纪律审查、中央纪委二次全会、全面从严治党一刻、强调共产党不可、反腐和从严治党、支持多边贸易体制、绿水青山就是金山
- **约束项**(5):
  1. C-001 · 依据KB-003与KB-004中最新发布版本的权威内容生成政策阐释包 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 整合KB-003（讲话摘要+上下文）与KB-004（理论文章摘要）跨资产信息，形成统一阐释 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-003 · 引用KB-003中官方标注的讲话上下文，排除未经官方确认的延伸解读 [来源:资产存在多版本或时效性维度 · 验证:regulation_support]
  1. C-004 · 识别并标注政策阐释包中所有源自KB-003的讲话原文引述段落 [来源:actors 含"管理"层级 · 验证:regulation_support]
  1. C-005 · 完整交付政策阐释包，不得遗漏理论依据、讲话要点及二者逻辑映射关系 [来源:outputs_count > 1 · 验证:regulation_support]
- **干扰项**(1):
  1. I-001 · 陷阱·KB-004理论文章摘要与KB-003讲话摘要+上下文在‘两个维护’表述上存在版本冲突 [验证:regulation_support]
- **真实性验证**:6/6

### TEST-002 (basic · 纪检文书纠错闭环处理)
- **主资产**:KB-002
- **核心 fragment**:FRAG-002-0700、FRAG-002-0571、FRAG-002-0196
- **关键字候选**:运用第四种形态、第四种形态处理、四种形态、第一批精准规范、履行职责若干规定、廉洁履行职责若干
- **约束项**(4):
  1. C-006 · 依据KB-002最新官方版本引用实务问答依据 [来源:时效性 · 验证:regulation_support]
  1. C-007 · 仅输出1份完整文书纠错报告，不得遗漏问题清单任一要素 [来源:outputs_count · 验证:regulation_support]
  1. C-008 · 识别审核复核触发场景，主动确认待审文书类型及适用规则 [来源:triggers · 验证:llm_judge]
  1. C-009 · 排除非官方KB-002以外的任何实务问答来源 [来源:时效性 · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:4/4

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
      "covered_by": []
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
        "TEST-001"
      ]
    },
    "KB-004": {
      "total_fragments": 4999,
      "covered_by": [
        "TEST-001"
      ]
    }
  },
  "test_contexts": [
    {
      "test_id": "TEST-001",
      "difficulty": "advanced",
      "primary_assets": [
        "KB-004",
        "KB-003"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-004-3431",
          "asset_id": "KB-004",
          "snippet": "“三审一评”助力挺纪在前 / 黄继鹏 | 江苏省推行‘三审一评’审理体系，提升纪律审查质效，实现案件审理‘全覆盖’，纪律审查呈现量质齐升态势。"
        },
        {
          "frag_id": "FRAG-004-1132",
          "asset_id": "KB-004",
          "snippet": "科学判断严峻复杂形势——全面从严治党一刻也不能松 / 余哲西 | 习近平总书记在十九届中央纪委二次全会上强调全面从严治党要持之以恒。当前反腐败形势依然严峻复杂，需继续深化。但全党上下对夺取最后胜利有充足信心。"
        },
        {
          "frag_id": "FRAG-004-3755",
          "asset_id": "KB-004",
          "snippet": "狮子只怕身上长虱子 / 高深 | 毛泽东与冒鹤亭对话，以狮子怕虱子为例，强调共产党不可自生祸患。强调反腐和从严治党，防止腐败滋生。"
        },
        {
          "frag_id": "FRAG-003-0060",
          "asset_id": "KB-003",
          "snippet": "还行不行？习近平这样回应外界对中国经济的三个疑问 | 2016-09-03 | 人民日报客户端9月3日报道：随着中国经济发展进入新常态，很多人都关心，中国经济能否实现持续稳定增长？中国能否把改革开放推进下去？中国能否避免陷入“中等收入陷阱”…"
        },
        {
          "frag_id": "FRAG-004-3248",
          "asset_id": "KB-004",
          "snippet": "关键时期的重大决策——写在全面建成小康社会进入决胜阶段之际 | 决胜全面建成小康社会，五中全会明确目标，强调党的领导，注重共享发展，全党砥砺奋进，向复兴伟业迈进。"
        },
        {
          "frag_id": "FRAG-004-1214",
          "asset_id": "KB-004",
          "snippet": "深刻理解和把握新时代党的建设总要求 / 王彦坤 王 菲 | 新时代党的建设总要求：加强党的领导，建设坚强核心，推进伟大事业，实现伟大梦想。"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-001-1750",
          "asset_id": "KB-001"
        },
        {
          "frag_id": "FRAG-002-0156",
          "asset_id": "KB-002"
        }
      ],
      "keyword_pool": [
        "纪律审查呈现",
        "提升纪律审查",
        "中央纪委二次全会",
        "全面从严治党一刻",
        "强调共产党不可",
        "反腐和从严治党",
        "支持多边贸易体制",
        "绿水青山就是金山"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "依据KB-003与KB-004中最新发布版本的权威内容生成政策阐释包",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "整合KB-003（讲话摘要+上下文）与KB-004（理论文章摘要）跨资产信息，形成统一阐释",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-003",
          "text": "引用KB-003中官方标注的讲话上下文，排除未经官方确认的延伸解读",
          "source": "资产存在多版本或时效性维度",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-004",
          "text": "识别并标注政策阐释包中所有源自KB-003的讲话原文引述段落",
          "source": "actors 含\"管理\"层级",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-005",
          "text": "完整交付政策阐释包，不得遗漏理论依据、讲话要点及二者逻辑映射关系",
          "source": "outputs_count > 1",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "KB-004理论文章摘要与KB-003讲话摘要+上下文在‘两个维护’表述上存在版本冲突",
          "trap": true,
          "process_ref": "多源理论素材协同检索与政策阐释",
          "verified_by": "regulation_support"
        }
      ],
      "realism_check": {
        "total": 6,
        "passed": 6
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
          "frag_id": "FRAG-002-0700",
          "asset_id": "KB-002",
          "snippet": "陈某某担任什么职务？ | 陈某某作为孝顺镇农村集体“三资”代理服务中心副主任 | 第三批准确有效运用“四种形态”典型案例.docx | 片段32:【经验做法】1.坚持严的基调，突出政治效果案件查办过程中，金东区纪委监委  始终把政治效果放在…"
        },
        {
          "frag_id": "FRAG-002-0571",
          "asset_id": "KB-002",
          "snippet": "案例发布时间是什么时候？ | 2022-12-01 | 第一批精准规范运用“四种形态”典型案例（上）.docx | 片段22:文档标题: 第一批精准规范运用“四种形态”典型案例（上） 片段23:序号: 1840 片段24:文档名称: 1.第…"
        },
        {
          "frag_id": "FRAG-002-0196",
          "asset_id": "KB-002",
          "snippet": "纪委监委在村干部受处分后应做好什么工作？ | 县（市、区、旗）纪委监委应当协助同级党委做好基层群众性自治组织中从事管理的人员受处分后的相关处理工作 | 20211229 中央纪委国家监委发布第二批执纪执法指导性案例.docx | 片段30:…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "运用第四种形态",
        "第四种形态处理",
        "四种形态",
        "第一批精准规范",
        "履行职责若干规定",
        "廉洁履行职责若干"
      ],
      "constraints": [
        {
          "id": "C-006",
          "text": "依据KB-002最新官方版本引用实务问答依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-007",
          "text": "仅输出1份完整文书纠错报告，不得遗漏问题清单任一要素",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-008",
          "text": "识别审核复核触发场景，主动确认待审文书类型及适用规则",
          "source": "triggers",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-009",
          "text": "排除非官方KB-002以外的任何实务问答来源",
          "source": "时效性",
          "verified_by": "regulation_support"
        }
      ],
      "interferences": [],
      "realism_check": {
        "total": 4,
        "passed": 4
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
