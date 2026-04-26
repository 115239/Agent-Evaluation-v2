---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-23T20:41:12+08:00
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
| KB-001 | 3849 | TEST-001,TEST-002 |
| KB-002 | 1006 | TEST-002 |
| KB-003 | 1235 | TEST-003 |
| KB-004 | 4999 | — |

## 题目上下文设计
### TEST-001 (basic · 党纪法规语义检索支撑定性量纪建议生成)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-0109、FRAG-001-0418、FRAG-001-1031
- **关键字候选**:违反政治纪律、违反廉洁纪律、市场主体提供信息、或者其他市场主体、环境保护违法行为、环境保护专项资金
- **约束项**(3):
  1. C-001 · 引用官方发布的最新版党纪条款集作为唯一依据 [来源:时效性 · 验证:regulation_support]
  1. C-002 · 整合知识咨询中提供的违纪事实要素，精准匹配对应条款 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-003 · 完整输出匹配的党纪条款集，不得遗漏或截断 [来源:outputs_count · 验证:regulation_support]
- **干扰项**(0):
  - 无(符合 basic 干扰密度=0)
- **真实性验证**:3/3

### TEST-002 (advanced · 纪检文书智能纠错与依据闭环验证)
- **主资产**:KB-001、KB-002
- **核心 fragment**:FRAG-002-0624、FRAG-002-0319、FRAG-002-0435、FRAG-002-0320、FRAG-002-0321、FRAG-002-0322
- **关键字候选**:应当受到党纪处分、受到党纪处分的、审查调查部门、相关审查调查、属于审查调查报告、根据党纪处分条例、群众纪律
- **约束项**(4):
  1. C-004 · 引用结构化条款库和实务问答库中最新官方版本的依据，排除历史修订稿内容 [来源:时效性 · 验证:regulation_support]
  1. C-005 · 整合结构化条款与实务问答两类资产信息，完成文书纠错与依据闭环验证 [来源:cross_process_dependency · 验证:regulation_support]
  1. C-006 · 在文书纠错报告中完整呈现问题定位、错误类型、修正建议及对应依据条目 [来源:outputs_count · 验证:regulation_support]
  1. C-007 · 依据审核复核场景要求，对模糊表述或依据缺失处主动标注待确认项 [来源:triggers · 验证:llm_judge]
- **干扰项**(1):
  1. I-001 · 陷阱·该文书引用的条款版本与实务问答库中最新解释存在冲突。 [验证:regulation_support]
- **真实性验证**:5/5

### TEST-003 (basic · 总书记讲话精准召回支撑政策阐释与理论引用)
- **主资产**:KB-003
- **核心 fragment**:FRAG-003-0139、FRAG-003-1104、FRAG-003-0762
- **关键字候选**:中央八项规定、八项规定精神、加强政治纪律、政治纪律和、的政治纪律
- **约束项**(3):
  1. C-008 · 引用官方发布的最新版本总书记讲话摘要及上下文，排除非权威渠道或修订前内容 [来源:时效性 · 验证:regulation_support]
  1. C-009 · 整合讲话原文与政策阐释所需上下文，确保引用包包含完整语义单元 [来源:cross_process_dependency · 验证:llm_judge]
  1. C-010 · 依据知识咨询触发场景，主动识别并补全用户未明示但必需的理论关联点 [来源:triggers · 验证:llm_judge]
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
          "frag_id": "FRAG-001-0418",
          "asset_id": "KB-001",
          "snippet": "人民法院工作人员, 廉政准则, 利益冲突, 营利性活动, 兼职 | 接受可能影响公正执行公务的礼金、礼品、宴请以及旅游、健身、娱乐等活动安排，从事营利性活动，为他人的经济活动提供担保，买卖股票或认股权证，利用在办案工作中获取的内幕信息买卖股…"
        },
        {
          "frag_id": "FRAG-001-1031",
          "asset_id": "KB-001",
          "snippet": "环境保护违法违纪行为, 环境保护法律、法规, 环境保护专项资金, 环境影响评价, 环境保护设施 | 拒不执行环境保护法律、法规以及人民政府关于环境保护的决定、命令，制定或者采取与环境保护法律、法规、规章以及国家环境保护政策相抵触的规定或者措…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "违反政治纪律",
        "违反廉洁纪律",
        "市场主体提供信息",
        "或者其他市场主体",
        "环境保护违法行为",
        "环境保护专项资金"
      ],
      "constraints": [
        {
          "id": "C-001",
          "text": "引用官方发布的最新版党纪条款集作为唯一依据",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-002",
          "text": "整合知识咨询中提供的违纪事实要素，精准匹配对应条款",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-003",
          "text": "完整输出匹配的党纪条款集，不得遗漏或截断",
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
          "frag_id": "FRAG-002-0624",
          "asset_id": "KB-002",
          "snippet": "李某某的行为被认定违反了什么纪律？ | 李某某的行为违反群众纪律 | 第三批准确有效运用“四种形态”典型案例.docx | 片段4:2018年  6月至2020年12月，青光村按照每年 100元/亩的标准收取协调费共计17.11 万余元，用…"
        },
        {
          "frag_id": "FRAG-002-0319",
          "asset_id": "KB-002",
          "snippet": "提出从宽处罚建议的程序是什么？ | 经承办案件的监察机关领导人员集体研究，并报上一级监察机关批准，在移送检察机关时提出从宽处罚的建议。 | 准确适用提出从宽处罚建议制度的思考.docx | 片段6:这不同于检察机关可以提出  精准的或有幅度…"
        },
        {
          "frag_id": "FRAG-002-0435",
          "asset_id": "KB-002",
          "snippet": "审理报告能否直接提出撤销案件意见 | 笔者认为 ，这不符合纪检监察机关依规依纪依法履行职责的  要求。 | 审理报告中可否提出 “撤销案件”意见.docx | 片段1:文档标题: 审理报告中可否提出 “撤销案件”意见 序号: 1872 文档…"
        },
        {
          "frag_id": "FRAG-002-0320",
          "asset_id": "KB-002",
          "snippet": "先行移送审查起诉后还能提出从宽处罚建议吗？ | 实践中，若因留置期限即将届满，在上一级监察机关批准从宽处罚建议之前先行移送审查起诉的，也可以在上一级监察机关批准后另行向检察机关提出从宽处罚建议。 | 准确适用提出从宽处罚建议制度的思考.do…"
        },
        {
          "frag_id": "FRAG-002-0321",
          "asset_id": "KB-002",
          "snippet": "上一级监察机关如何审查从宽处罚建议？ | 上一级监察机关监督检查部门从实体和程序两方面对请示进行实质性审查，并征求本单位案件审理部门的意见，必要时征求本单位相关审查调查部门的意见。 | 准确适用提出从宽处罚建议制度的思考.docx | 片段…"
        },
        {
          "frag_id": "FRAG-002-0322",
          "asset_id": "KB-002",
          "snippet": "上一级监察机关如何审查下一级的请示？ | 上一级监察机关监督检查部门从实体和程序两方面对请示进行实质性审查 ，并征求本单位案件审理部门的意见 ，必要时 征求本单位相关审查调查部门的意见 。 | 准确适用提出从宽处罚建议制度的思考.docx …"
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
        "应当受到党纪处分",
        "受到党纪处分的",
        "审查调查部门",
        "相关审查调查",
        "属于审查调查报告",
        "根据党纪处分条例",
        "群众纪律"
      ],
      "constraints": [
        {
          "id": "C-004",
          "text": "引用结构化条款库和实务问答库中最新官方版本的依据，排除历史修订稿内容",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-005",
          "text": "整合结构化条款与实务问答两类资产信息，完成文书纠错与依据闭环验证",
          "source": "cross_process_dependency",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-006",
          "text": "在文书纠错报告中完整呈现问题定位、错误类型、修正建议及对应依据条目",
          "source": "outputs_count",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-007",
          "text": "依据审核复核场景要求，对模糊表述或依据缺失处主动标注待确认项",
          "source": "triggers",
          "verified_by": "llm_judge"
        }
      ],
      "interferences": [
        {
          "id": "I-001",
          "text": "该文书引用的条款版本与实务问答库中最新解释存在冲突。",
          "trap": true,
          "process_ref": "纪检文书智能纠错与依据闭环验证",
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
          "frag_id": "FRAG-003-0139",
          "asset_id": "KB-003",
          "snippet": "全面从严治党探索出依靠党的自我革命跳出历史周期率的成功路径 | 2023-01-31 | 全面从严治党探索出依靠党的自我革命跳出历史周期率的成功路径 习近平 2022年1月18日，中共中央总书记、国家主席、中央军委主席习近平在中国共产党第十…"
        },
        {
          "frag_id": "FRAG-003-1104",
          "asset_id": "KB-003",
          "snippet": "在中央党校建校90周年庆祝大会暨2023年春季学期开学典礼上的讲话 | 2023-03-31 | 在中央党校建校90周年庆祝大会 暨2023年春季学期开学典礼上的讲话 （2023年3月1日） 习近平 今天，我们在这里集会，庆祝中央党校建校9…"
        },
        {
          "frag_id": "FRAG-003-0762",
          "asset_id": "KB-003",
          "snippet": "习近平在全国党校工作会议上强调 坚持党校姓党根本工作原则 切实做好新形势下党校工作 | 2015-12-12 | 12月11日至12日，全国党校工作会议在北京召开。中共中央总书记、国家主席、中央军委主席习近平发表重要讲话。新华社记者 兰红光…"
        }
      ],
      "interference_fragments": [],
      "keyword_pool": [
        "中央八项规定",
        "八项规定精神",
        "加强政治纪律",
        "政治纪律和",
        "的政治纪律"
      ],
      "constraints": [
        {
          "id": "C-008",
          "text": "引用官方发布的最新版本总书记讲话摘要及上下文，排除非权威渠道或修订前内容",
          "source": "时效性",
          "verified_by": "regulation_support"
        },
        {
          "id": "C-009",
          "text": "整合讲话原文与政策阐释所需上下文，确保引用包包含完整语义单元",
          "source": "cross_process_dependency",
          "verified_by": "llm_judge"
        },
        {
          "id": "C-010",
          "text": "依据知识咨询触发场景，主动识别并补全用户未明示但必需的理论关联点",
          "source": "triggers",
          "verified_by": "llm_judge"
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
