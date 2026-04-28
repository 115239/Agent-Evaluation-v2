---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-21T09:23:51+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 2 道题建立了知识索引(共 11089 个 fragment),LLM 生成 8 条约束、1 条干扰(其中 0 条陷阱)。业务真实性通过 9/9。第二层 Fallback 触发(无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|---|---|---|
| weak_points 存在 | ✗ | 全部走流程特性推导(LLM) |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST |
|---|---|---|
| KB-001 | 3849 | TEST-002 |
| KB-002 | 1006 | TEST-001,TEST-002 |
| KB-003 | 1235 | — |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (basic · 定性量纪建议生成与依据验证)
- **主资产**:KB-002
- **核心 fragment**:FRAG-002-0059、FRAG-002-0060、FRAG-002-0061
- **关键字候选**:中央八项规定、八项规定精神
- **约束项**(4):
  1. C-001 · 依据KB-002最新官方版本生成定性量纪建议 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 仅基于BP-001单流程内信息生成建议，不整合跨流程资产 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-003 · 输出必须为结构化建议，且完整包含定性与量纪两部分结论 [来源:outputs_count · 验证:commonsense]
  1. C-004 · 识别知识咨询触发场景，不主动追问或推断未明示事实 [来源:triggers · 验证:llm_judge]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:4/4

### TEST-002 (advanced · 纪检文书全流程智能纠错与依据回溯)
- **主资产**:KB-002、KB-001
- **核心 fragment**:FRAG-001-2932、FRAG-001-1903、FRAG-001-1680、FRAG-001-1559、FRAG-001-1945、FRAG-002-0225
- **关键字候选**:测绘计量器具、计量器具检定、工程设计图纸进行、领取建设工程施工、交易系统办理柜台、投资人办理转托管、瞒报家庭住房、家庭住房情况
- **约束项**(4):
  1. C-005 · 依据当前可用资产中最新版本的KB-001和KB-002进行纠错与溯源 [来源:时效性 · 验证:regulation_support]
  1. C-006 · 整合KB-001结构化条款与KB-002实务问答，交叉验证纠错结论 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-007 · 完整输出修订版文书和纠错依据溯源清单两项结果，缺一不可 [来源:outputs_count · 验证:llm_judge]
  1. C-008 · 识别审核复核触发场景，对模糊表述主动标注待确认项 [来源:triggers · 验证:llm_judge]
- **干扰项**(1):
  1. I-001 · 纪检文书纠错应优先引用KB-002实务问答，因其更新频率高于KB-001结构化条款。 [验证:regulation_support]
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
          "text": "依据KB-002最新官方版本生成定性量纪建议",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "仅基于BP-001单流程内信息生成建议，不整合跨流程资产",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-003",
          "text": "输出必须为结构化建议，且完整包含定性与量纪两部分结论",
          "source": "outputs_count",
          "verified_by": "commonsense"
        },
        {
          "id": "C-004",
          "text": "识别知识咨询触发场景，不主动追问或推断未明示事实",
          "source": "triggers",
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
        "KB-002",
        "KB-001"
      ],
      "fragments": [
        {
          "frag_id": "FRAG-001-2932",
          "asset_id": "KB-001",
          "snippet": "测绘计量管理, 测绘计量器具, 检定, 型式批准, 计量标准 | 使用未经考核合格的计量标准，未经授权开展测绘计量器具检定，进口未经型式批准的测绘计量器具，使用未经检定或检定不合格的测绘计量器具"
        },
        {
          "frag_id": "FRAG-001-1903",
          "asset_id": "KB-001",
          "snippet": "城市地下空间, 开发利用, 规划管理, 工程建设, 违法行为 | 未领取建设工程施工许可证擅自开工，设计文件未按照规定进行设计审查，不按照工程设计图纸进行施工，在使用或者装饰装修中擅自改变地下工程结构设计，地下工程的专用设备、器材的定型、生…"
        },
        {
          "frag_id": "FRAG-001-1680",
          "asset_id": "KB-001",
          "snippet": "商业银行, 柜台交易, 记账式国债, 托管, 结算 | 未经批准从事柜台交易业务，不按规定公布买卖双边价格，卖空债券，未通过交易系统办理柜台交易业务，不按所报价格满足投资人的买卖要求，无正当理由暂停交易，挪用投资人债券，伪造债券账务记录，不…"
        },
        {
          "frag_id": "FRAG-001-1559",
          "asset_id": "KB-001",
          "snippet": "易地调动干部, 住房管理, 购房补贴, 周转住房, 住房档案 | 瞒报家庭住房情况，多占住房，骗取购房补贴"
        },
        {
          "frag_id": "FRAG-001-1945",
          "asset_id": "KB-001",
          "snippet": "渔业资源, 捕捞业, 养殖业, 水产苗种, 渔政监督管理 | 使用炸鱼、毒鱼、电鱼等破坏渔业资源的方法进行捕捞，偷捕、抢夺他人养殖的水产品，无证捕捞，涂改、买卖捕捞许可证"
        },
        {
          "frag_id": "FRAG-002-0225",
          "asset_id": "KB-002",
          "snippet": "违纪行为的客体是什么？ | 本行为的客体是复杂客体，既包括我国的社会主义道德，又包括婚姻家庭关系。 | 与他人发生不正当性关系行为的证据收集与运用.docx | 片段3:本⾏为的主观⽅⾯只能是故意，即有配偶的党员 与他⼈⾃愿发⽣性关系，或者…"
        }
      ],
      "interference_fragments": [
        {
          "frag_id": "FRAG-003-1147",
          "asset_id": "KB-003"
        },
        {
          "frag_id": "FRAG-004-2308",
          "asset_id": "KB-004"
        }
      ],
      "keyword_pool": [
        "测绘计量器具",
        "计量器具检定",
        "工程设计图纸进行",
        "领取建设工程施工",
        "交易系统办理柜台",
        "投资人办理转托管",
        "瞒报家庭住房",
        "家庭住房情况"
      ],
      "constraints": [
        {
          "id": "C-005",
          "text": "依据当前可用资产中最新版本的KB-001和KB-002进行纠错与溯源",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "整合KB-001结构化条款与KB-002实务问答，交叉验证纠错结论",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-007",
          "text": "完整输出修订版文书和纠错依据溯源清单两项结果，缺一不可",
          "source": "outputs_count",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-008",
          "text": "识别审核复核触发场景，对模糊表述主动标注待确认项",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "纪检文书纠错应优先引用KB-002实务问答，因其更新频率高于KB-001结构化条款。",
          "trap": false,
          "process_ref": "纪检文书全流程智能纠错与依据回溯",
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
