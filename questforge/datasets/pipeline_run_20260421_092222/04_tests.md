---
stage: 4
stage_name: test_items
version: 1.0
upstream: 03_context.md
downstream: 05_report.md
domain: 纪检材料智能审查
created_at: 2026-04-22T00:20:51+08:00
created_by: agent-stage4
pass_gate: true
---

# Stage 4 · 题目 + 期望 + 评分细则

## 摘要
共生成 2/2 道题(失败 0);难度一致 1 道、偏移 1 道;平均 difficulty_score 2.00。

## 题目一览
| ID | 难度 | difficulty_score | 约束 | 干扰 | 主资产 | 对应流程 |
|---|---|---|---|---|---|---|
| TEST-001 | advanced | 1.83 | 4 | 0 | KB-002 | BP-001 |
| TEST-002 | advanced | 2.17 | 4 | 1 | KB-002+KB-001 | BP-002 |

## 难度自校准一致性
| TEST | Stage 2 规划 | Stage 4 校准 | difficulty_score |
|---|---|---|---|
| TEST-001 | basic | advanced | 1.83 |

## 逐题详情
## TEST-001 · 单一知识查询(advanced)

### prompt
> 我是一名刚接手线索初核的纪检监察员，手头有一份反映某干部在公务接待中违规提供高档酒水的材料，需要快速给出定性量纪建议——依据KB-002最新官方版本生成定性量纪建议，输出必须为结构化建议，且完整包含定性与量纪两部分结论，不整合跨流程资产，也不主动追问未明示事实，这该怎么操作？

### 约束与干扰
- 约束:依据KB-002最新官方版本生成定性量纪建议、仅基于BP-001单流程内信息生成建议，不整合跨流程资产、输出必须为结构化建议，且完整包含定性与量纪两部分结论、识别知识咨询触发场景，不主动追问或推断未明示事实
- 干扰:无

### 五阶段期望
| 阶段 | 期望 |
|---|---|
| 定义问题 | {'intent_understanding': '定性量纪建议生成与依据验证：针对公务接待中违规提供高档酒水行为，生成符合最新权威依据的定性与量纪结构化建议', 'implicit_needs': ['定性量纪建议'], 'problem… |
| 拆解问题 | {'expected_steps': ['调用党纪法规语义检索（FEAT-001）获取匹配条款及要点词', '叠加实务问答验证辅助（FEAT-004）比对标准答案与来源文档', '整合条款要点、违纪行为定义与实务结论，生成结构化定性量纪建议… |
| 方案生成 | {'information_sources': ['KB-002/FRAG-002-0059：第一批执纪执法指导性案例聚焦违反中央八项规定精神典型问题（20210804发布）', 'KB-002/FRAG-002-0060：针对实践中存在的… |
| 执行落地 | {'output_format': "结构化建议，含两个强制字段：'定性结论'（如'违反中央八项规定精神，构成廉洁纪律违纪'）和'量纪建议'（如'建议给予党内警告处分'），无自由发挥段落", 'exception_handling': '若… |
| 元认知 | {'source_annotation': '所有结论须标注出处为KB-002（20210804中央纪委国家监委发布第一批执纪执法指导性案例），并强调其为最新官方版本', 'uncertainty_acknowledgment': '不虚构… |

### 评分细则
| 阶段 | 满分 | 权重 | scoring_points |
|---|---|---|---|
| 定义问题 | 2 | 0.2 | 准确识别用户核心诉求为生成‘定性+量纪’双要素结构化建议，而非单纯解释八项规定或列举案例(1.0, llm_judge) · 显性识别约束‘依据KB-002最新官方版本’和‘不整合跨流程资产’，并在问题理解中排除BP-001外信息源(1.0, keyword_match) |
| 拆解问题 | 2 | 0.2 | 正确列出BP-001全部三个步骤名称，顺序与<source_process>.steps完全一致，无增删改(1.0, keyword_match) · 指出步骤执行必须严格遵循编号顺序，不得合并、跳过或调换(1.0, semantic_match) |
| 方案生成 | 3 | 0.3 | 引用FRAG-002-0059确认行为定性锚点为‘违反中央八项规定精神’(1.0, keyword_match) · 引用FRAG-002-0060支撑‘性质认定、条规适用、处理处分’三环节需同步覆盖(1.0, keyword_match) · 引用FRAG-002-0061明确输出须含‘定性量纪理由、纪法条规适用’，… |
| 执行落地 | 2 | 0.2 | 输出格式严格满足‘结构化建议’且含‘定性结论’与‘量纪建议’两个独立字段，无额外解释性文字(1.0, semantic_match) · 所有结论均标注KB-002出处（含20210804日期），未混入其他版本或外部条规(1.0, keyword_match) |
| 元认知 | 1 | 0.1 | 明确声明本建议边界：仅限BP-001流程内输出，不延伸至审查调查、谈话函询等环节(1.0, semantic_match) |

### 致命扣分项 / 一票否决项
- **致命扣分**:输出中出现‘四种形态’‘从宽情节’‘从严情节’等<glossary>中定义但KB-002未提及的术语，视为擅自引入外部知识 → llm_judge detects presence of glossary terms not appearing in KB-002 fragments
- **一票否决**:未在输出中标注‘20210804’或未指明‘KB-002’来源，即判定为未满足‘依据KB-002最新官方版本’约束 → keyword_match misses '20210804' or 'KB-002'

## TEST-002 · 多意图综合决策(advanced)

### prompt
> 我们刚收到一份关于干部瞒报家庭住房情况的立案呈批表，其中引用了KB-001中‘易地调动干部’条款，但未标注版本号；另有一处将‘未领取建设工程施工许可证擅自开工’错误套用于住房违规场景，还混入了KB-002里关于不正当性关系客体的表述。请依据当前可用资产中最新版本的KB-001和KB-002进行纠错与溯源，整合KB-001结构化条款与KB-002实务问答交叉验证，并完整输出修订版文书和纠错依据溯源清单两项结果——审核复核触发时对‘工程设计图纸进行’这类模糊引述是否需主动标注待确认？

### 约束与干扰
- 约束:依据当前可用资产中最新版本的KB-001和KB-002进行纠错与溯源、整合KB-001结构化条款与KB-002实务问答，交叉验证纠错结论、完整输出修订版文书和纠错依据溯源清单两项结果，缺一不可、识别审核复核触发场景，对模糊表述主动标注待确认项
- 干扰:纪检文书纠错应优先引用KB-002实务问答，因其更新频率高于KB-001结构化条款。

### 五阶段期望
| 阶段 | 期望 |
|---|---|
| 定义问题 | {'intent_understanding': '纪检文书全流程智能纠错与依据回溯：对立案呈批表中条款误引、跨域套用、出处缺失等问题开展合规性复核', 'implicit_needs': ['修订版文书', '纠错依据溯源清单'], 'p… |
| 拆解问题 | {'expected_steps': ['上传文书文本，触发纪检文书智能纠错（FEAT-005）识别依据错误与表述偏差', '自动关联KB-001（党纪条款）、KB-002（实务问答）、KB-003（总书记讲话）定位修正依据原文', '生成… |
| 方案生成 | {'information_sources': ['KB-001/FRAG-001-1559：易地调动干部, 住房管理, 购房补贴, 周转住房, 住房档案 \| 瞒报家庭住房情况，多占住房，骗取购房补贴', 'KB-001/FRAG-001-… |
| 执行落地 | {'output_format': '修订版文书为Word格式，含Track Changes修订痕迹+红色批注框标注错误类型（如‘跨领域误引’‘出处缺失’）及KB-001/FRAG-001-1559条款号；纠错依据溯源清单为Excel，列含… |
| 元认知 | {'source_annotation': '所有引用均标注KB-001（v2023.12）与KB-002（v2024.03）版本号，FRAG-ID精确到末位数字（如FRAG-001-1559）', 'uncertainty_acknowl… |

### 评分细则
| 阶段 | 满分 | 权重 | scoring_points |
|---|---|---|---|
| 定义问题 | 2 | 0.2 | 准确识别核心诉求为审核复核场景下的纪检文书纠错与依据回溯，而非单纯知识查询(1.0, llm_judge) · 显性指出‘瞒报家庭住房情况’为事实锚点，隐性覆盖‘修订版文书’和‘纠错依据溯源清单’双输出需求(1.0, keyword_match) |
| 拆解问题 | 2 | 0.2 | 严格按BP-002.steps顺序列出全部4个步骤名称，文字与顺序零偏差(1.0, keyword_match) · 明确步骤间依赖关系，指出步骤2必须同步调用KB-001与KB-002(1.0, semantic_match) |
| 方案生成 | 3 | 0.3 | 正确选用KB-001/FRAG-001-1559作为‘瞒报家庭住房’唯一依据源，并排除FRAG-001-1903与FRAG-002-0225(1.0, keyword_match) · 说明KB-002仅用于构成要件验证，不替代KB-001定性效力，体现跨资产权限边界(1.0, semantic_match) · 提出… |
| 执行落地 | 2 | 0.2 | 修订版文书格式要求含Track Changes与红色批注框，且明确标注KB版本号与FRAG-ID(1.0, keyword_match) · 纠错依据溯源清单字段完整（错误位置/原句/修正句/FRAG-ID/snippet摘要/KB版本号）(1.0, semantic_match) |
| 元认知 | 1 | 0.1 | 明确声明KB-002不得替代KB-001定性，且指出KB-002/FRAG-002-0225在此案中属越权引用(1.0, keyword_match) |

### 致命扣分项 / 一票否决项
- **致命扣分**:未在参考答案中体现‘审核复核触发场景’这一关键上下文，导致问题定位失焦 → reference.define_problem.intent_understanding 中缺失‘审核复核’关键词
- **一票否决**:未完整输出‘修订版文书’和‘纠错依据溯源清单’两项结果，任缺其一即整题零分 → reference.execution.output_format 中未同时描述两项输出格式

## 结构化数据
```json
{
  "generation_summary": {
    "total_planned": 2,
    "generated": 2,
    "failed": []
  },
  "items": [
    {
      "test_id": "TEST-001",
      "difficulty": "advanced",
      "difficulty_score": 1.83,
      "domain": "纪检材料智能审查",
      "prompt": "我是一名刚接手线索初核的纪检监察员，手头有一份反映某干部在公务接待中违规提供高档酒水的材料，需要快速给出定性量纪建议——依据KB-002最新官方版本生成定性量纪建议，输出必须为结构化建议，且完整包含定性与量纪两部分结论，不整合跨流程资产，也不主动追问未明示事实，这该怎么操作？",
      "context": {
        "user_role": "一线纪检监察员",
        "intent_type": "单一知识查询",
        "constraints": [
          "依据KB-002最新官方版本生成定性量纪建议",
          "仅基于BP-001单流程内信息生成建议，不整合跨流程资产",
          "输出必须为结构化建议，且完整包含定性与量纪两部分结论",
          "识别知识咨询触发场景，不主动追问或推断未明示事实"
        ],
        "interference_items": [],
        "success_criteria": [
          "准确识别‘中央八项规定精神’为违纪行为核心指向",
          "明确诉求是生成含定性+量纪两要素的结构化建议，而非解释、溯源或扩展建议"
        ]
      },
      "reference": {
        "define_problem": {
          "intent_understanding": "定性量纪建议生成与依据验证：针对公务接待中违规提供高档酒水行为，生成符合最新权威依据的定性与量纪结构化建议",
          "implicit_needs": [
            "定性量纪建议"
          ],
          "problem_essence": "在不越权、不跨流程、不增补事实前提下，基于KB-002片段精准输出定性（违反廉洁纪律/中央八项规定精神）与量纪（如警告至严重警告）的结构化结论"
        },
        "decompose": {
          "expected_steps": [
            "调用党纪法规语义检索（FEAT-001）获取匹配条款及要点词",
            "叠加实务问答验证辅助（FEAT-004）比对标准答案与来源文档",
            "整合条款要点、违纪行为定义与实务结论，生成结构化定性量纪建议草稿"
          ],
          "priority_ordering": "严格按步骤编号顺序执行，不可跳步或倒置"
        },
        "solution": {
          "information_sources": [
            "KB-002/FRAG-002-0059：第一批执纪执法指导性案例聚焦违反中央八项规定精神典型问题（20210804发布）",
            "KB-002/FRAG-002-0060：针对实践中存在的性质认定、条规适用、处理处分不精准不恰当等问题",
            "KB-002/FRAG-002-0061：阐释执纪执法要旨、政策策略把握、定性量纪理由、纪法条规适用等内容"
          ],
          "cross_doc_integration": "禁止。本题限定仅使用KB-002内三个片段，不引入BP-001以外任何资产"
        },
        "execution": {
          "output_format": "结构化建议，含两个强制字段：'定性结论'（如'违反中央八项规定精神，构成廉洁纪律违纪'）和'量纪建议'（如'建议给予党内警告处分'），无自由发挥段落",
          "exception_handling": "若输入未体现具体行为细节（如未说明是否首次、是否退赔），则默认不引入从宽/从严情节，仅基于基础情形作建议"
        },
        "metacognition": {
          "source_annotation": "所有结论须标注出处为KB-002（20210804中央纪委国家监委发布第一批执纪执法指导性案例），并强调其为最新官方版本",
          "uncertainty_acknowledgment": "不虚构、不推测未在KB-002中明确表述的裁量细则（如未提‘高档酒水’对应具体金额阈值，则不自行设定）",
          "boundary_awareness": "本流程仅输出定性量纪建议，不涉及审查调查程序启动、谈话函询安排、文书纠错等BP-001范围外职能"
        }
      },
      "rubric": {
        "total_max_score": 10,
        "stages": [
          {
            "stage_name": "定义问题",
            "max_score": 2,
            "weight": 0.2,
            "scoring_points": [
              {
                "description": "准确识别用户核心诉求为生成‘定性+量纪’双要素结构化建议，而非单纯解释八项规定或列举案例",
                "score": 1.0,
                "evidence_type": "llm_judge",
                "keywords": []
              },
              {
                "description": "显性识别约束‘依据KB-002最新官方版本’和‘不整合跨流程资产’，并在问题理解中排除BP-001外信息源",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "KB-002最新官方版本",
                  "不整合跨流程资产"
                ]
              }
            ]
          },
          {
            "stage_name": "拆解问题",
            "max_score": 2,
            "weight": 0.2,
            "scoring_points": [
              {
                "description": "正确列出BP-001全部三个步骤名称，顺序与<source_process>.steps完全一致，无增删改",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "调用党纪法规语义检索（FEAT-001）获取匹配条款及要点词",
                  "叠加实务问答验证辅助（FEAT-004）比对标准答案与来源文档",
                  "整合条款要点、违纪行为定义与实务结论，生成结构化定性量纪建议草稿"
                ]
              },
              {
                "description": "指出步骤执行必须严格遵循编号顺序，不得合并、跳过或调换",
                "score": 1.0,
                "evidence_type": "semantic_match",
                "keywords": [
                  "严格按步骤编号顺序执行"
                ]
              }
            ]
          },
          {
            "stage_name": "方案生成",
            "max_score": 3,
            "weight": 0.3,
            "scoring_points": [
              {
                "description": "引用FRAG-002-0059确认行为定性锚点为‘违反中央八项规定精神’",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "违反中央八项规定精神"
                ]
              },
              {
                "description": "引用FRAG-002-0060支撑‘性质认定、条规适用、处理处分’三环节需同步覆盖",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "性质认定、条规适用、处理处分"
                ]
              },
              {
                "description": "引用FRAG-002-0061明确输出须含‘定性量纪理由、纪法条规适用’，确保建议非空泛结论",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "定性量纪理由",
                  "纪法条规适用"
                ]
              }
            ]
          },
          {
            "stage_name": "执行落地",
            "max_score": 2,
            "weight": 0.2,
            "scoring_points": [
              {
                "description": "输出格式严格满足‘结构化建议’且含‘定性结论’与‘量纪建议’两个独立字段，无额外解释性文字",
                "score": 1.0,
                "evidence_type": "semantic_match",
                "keywords": [
                  "结构化建议",
                  "定性结论",
                  "量纪建议"
                ]
              },
              {
                "description": "所有结论均标注KB-002出处（含20210804日期），未混入其他版本或外部条规",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "20210804",
                  "KB-002"
                ]
              }
            ]
          },
          {
            "stage_name": "元认知",
            "max_score": 1,
            "weight": 0.1,
            "scoring_points": [
              {
                "description": "明确声明本建议边界：仅限BP-001流程内输出，不延伸至审查调查、谈话函询等环节",
                "score": 1.0,
                "evidence_type": "semantic_match",
                "keywords": [
                  "仅限BP-001流程内",
                  "不延伸至审查调查"
                ]
              }
            ]
          }
        ],
        "fatal_deductions": [
          {
            "description": "输出中出现‘四种形态’‘从宽情节’‘从严情节’等<glossary>中定义但KB-002未提及的术语，视为擅自引入外部知识",
            "detection_rule": "llm_judge detects presence of glossary terms not appearing in KB-002 fragments"
          }
        ],
        "veto_items": [
          {
            "description": "未在输出中标注‘20210804’或未指明‘KB-002’来源，即判定为未满足‘依据KB-002最新官方版本’约束",
            "detection_rule": "keyword_match misses '20210804' or 'KB-002'"
          }
        ]
      },
      "source_process": "BP-001",
      "inferred": true,
      "tags": [
        "中央八项规定",
        "定性量纪",
        "KB-002"
      ]
    },
    {
      "test_id": "TEST-002",
      "difficulty": "advanced",
      "difficulty_score": 2.17,
      "domain": "纪检材料智能审查",
      "prompt": "我们刚收到一份关于干部瞒报家庭住房情况的立案呈批表，其中引用了KB-001中‘易地调动干部’条款，但未标注版本号；另有一处将‘未领取建设工程施工许可证擅自开工’错误套用于住房违规场景，还混入了KB-002里关于不正当性关系客体的表述。请依据当前可用资产中最新版本的KB-001和KB-002进行纠错与溯源，整合KB-001结构化条款与KB-002实务问答交叉验证，并完整输出修订版文书和纠错依据溯源清单两项结果——审核复核触发时对‘工程设计图纸进行’这类模糊引述是否需主动标注待确认？",
      "context": {
        "user_role": "案件审理人员",
        "intent_type": "多意图综合决策",
        "constraints": [
          "依据当前可用资产中最新版本的KB-001和KB-002进行纠错与溯源",
          "整合KB-001结构化条款与KB-002实务问答，交叉验证纠错结论",
          "完整输出修订版文书和纠错依据溯源清单两项结果，缺一不可",
          "识别审核复核触发场景，对模糊表述主动标注待确认项"
        ],
        "interference_items": [
          "纪检文书纠错应优先引用KB-002实务问答，因其更新频率高于KB-001结构化条款。"
        ],
        "success_criteria": [
          "修订版文书准确替换错误条款并标注出处",
          "纠错依据溯源清单逐条对应FRAG-ID与原文片段摘要",
          "对‘工程设计图纸进行’等跨领域误引明确标注‘待确认：非住房管理适用条款’"
        ]
      },
      "reference": {
        "define_problem": {
          "intent_understanding": "纪检文书全流程智能纠错与依据回溯：对立案呈批表中条款误引、跨域套用、出处缺失等问题开展合规性复核",
          "implicit_needs": [
            "修订版文书",
            "纠错依据溯源清单"
          ],
          "problem_essence": "在审核复核场景下，识别并修正纪检文书中因混淆监管领域（如住房/工程/计量）、错配法规层级、遗漏版本标注导致的定性偏差与依据失当"
        },
        "decompose": {
          "expected_steps": [
            "上传文书文本，触发纪检文书智能纠错（FEAT-005）识别依据错误与表述偏差",
            "自动关联KB-001（党纪条款）、KB-002（实务问答）、KB-003（总书记讲话）定位修正依据原文",
            "生成带标注的修订版文书，含错误类型标签、修正建议及对应条款/讲话/问答出处",
            "输出纠错报告供审理人员交叉验证并决定是否退回修改"
          ],
          "priority_ordering": "步骤1→2→3→4为线性依赖链，步骤2必须同步调用KB-001与KB-002完成交叉验证"
        },
        "solution": {
          "information_sources": [
            "KB-001/FRAG-001-1559：易地调动干部, 住房管理, 购房补贴, 周转住房, 住房档案 | 瞒报家庭住房情况，多占住房，骗取购房补贴",
            "KB-001/FRAG-001-1903：城市地下空间, 开发利用, 规划管理, 工程建设, 违法行为 | 未领取建设工程施工许可证擅自开工，设计文件未按照规定进行设计审查…",
            "KB-002/FRAG-002-0225：违纪行为的客体是什么？ | 本行为的客体是复杂客体，既包括我国的社会主义道德，又包括婚姻家庭关系。"
          ],
          "cross_doc_integration": "以‘瞒报家庭住房情况’为锚点，在KB-001中锁定FRAG-001-1559作为唯一适用条款；排除FRAG-001-1903（工程建设类）与FRAG-002-0225（婚姻伦理类）的误引；KB-002仅用于验证‘客体’表述逻辑，不替代KB-001住房条款效力"
        },
        "execution": {
          "output_format": "修订版文书为Word格式，含Track Changes修订痕迹+红色批注框标注错误类型（如‘跨领域误引’‘出处缺失’）及KB-001/FRAG-001-1559条款号；纠错依据溯源清单为Excel，列含：错误位置、原句、修正句、FRAG-ID、snippet摘要、KB版本号",
          "exception_handling": "对‘工程设计图纸进行’等明显超出住房管理范畴的表述，自动触发‘待确认’标签并附说明：‘该表述源自KB-001/FRAG-001-1903（工程建设），与当前住房违规事项无法律适用关联，建议删除或由审理人员书面确认扩展解释依据’"
        },
        "metacognition": {
          "source_annotation": "所有引用均标注KB-001（v2023.12）与KB-002（v2024.03）版本号，FRAG-ID精确到末位数字（如FRAG-001-1559）",
          "uncertainty_acknowledgment": "‘未领取建设工程施工许可证擅自开工’在住房违规语境中是否存在类推适用可能？当前无KB资产支持，标注为‘待审理组书面确认’",
          "boundary_awareness": "KB-002仅提供客体/主观方面等构成要件解释，不得直接替代KB-001条款作为定性依据；本案中KB-002/FRAG-002-0225属越权引用，须剔除"
        }
      },
      "rubric": {
        "total_max_score": 10,
        "stages": [
          {
            "stage_name": "定义问题",
            "max_score": 2,
            "weight": 0.2,
            "scoring_points": [
              {
                "description": "准确识别核心诉求为审核复核场景下的纪检文书纠错与依据回溯，而非单纯知识查询",
                "score": 1.0,
                "evidence_type": "llm_judge"
              },
              {
                "description": "显性指出‘瞒报家庭住房情况’为事实锚点，隐性覆盖‘修订版文书’和‘纠错依据溯源清单’双输出需求",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "修订版文书",
                  "纠错依据溯源清单"
                ]
              }
            ]
          },
          {
            "stage_name": "拆解问题",
            "max_score": 2,
            "weight": 0.2,
            "scoring_points": [
              {
                "description": "严格按BP-002.steps顺序列出全部4个步骤名称，文字与顺序零偏差",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "上传文书文本，触发纪检文书智能纠错（FEAT-005）识别依据错误与表述偏差",
                  "自动关联KB-001（党纪条款）、KB-002（实务问答）、KB-003（总书记讲话）定位修正依据原文",
                  "生成带标注的修订版文书，含错误类型标签、修正建议及对应条款/讲话/问答出处",
                  "输出纠错报告供审理人员交叉验证并决定是否退回修改"
                ]
              },
              {
                "description": "明确步骤间依赖关系，指出步骤2必须同步调用KB-001与KB-002",
                "score": 1.0,
                "evidence_type": "semantic_match"
              }
            ]
          },
          {
            "stage_name": "方案生成",
            "max_score": 3,
            "weight": 0.3,
            "scoring_points": [
              {
                "description": "正确选用KB-001/FRAG-001-1559作为‘瞒报家庭住房’唯一依据源，并排除FRAG-001-1903与FRAG-002-0225",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "KB-001/FRAG-001-1559",
                  "瞒报家庭住房情况"
                ]
              },
              {
                "description": "说明KB-002仅用于构成要件验证，不替代KB-001定性效力，体现跨资产权限边界",
                "score": 1.0,
                "evidence_type": "semantic_match"
              },
              {
                "description": "提出对‘工程设计图纸进行’等误引字段的处理策略：标注‘待确认’并附法律适用说明",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "待确认",
                  "工程设计图纸进行"
                ]
              }
            ]
          },
          {
            "stage_name": "执行落地",
            "max_score": 2,
            "weight": 0.2,
            "scoring_points": [
              {
                "description": "修订版文书格式要求含Track Changes与红色批注框，且明确标注KB版本号与FRAG-ID",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "Track Changes",
                  "红色批注框",
                  "KB-001（v2023.12）",
                  "FRAG-001-1559"
                ]
              },
              {
                "description": "纠错依据溯源清单字段完整（错误位置/原句/修正句/FRAG-ID/snippet摘要/KB版本号）",
                "score": 1.0,
                "evidence_type": "semantic_match"
              }
            ]
          },
          {
            "stage_name": "元认知",
            "max_score": 1,
            "weight": 0.1,
            "scoring_points": [
              {
                "description": "明确声明KB-002不得替代KB-001定性，且指出KB-002/FRAG-002-0225在此案中属越权引用",
                "score": 1.0,
                "evidence_type": "keyword_match",
                "keywords": [
                  "越权引用",
                  "KB-002/FRAG-002-0225"
                ]
              }
            ]
          }
        ],
        "fatal_deductions": [
          {
            "description": "未在参考答案中体现‘审核复核触发场景’这一关键上下文，导致问题定位失焦",
            "detection_rule": "reference.define_problem.intent_understanding 中缺失‘审核复核’关键词"
          }
        ],
        "veto_items": [
          {
            "description": "未完整输出‘修订版文书’和‘纠错依据溯源清单’两项结果，任缺其一即整题零分",
            "detection_rule": "reference.execution.output_format 中未同时描述两项输出格式"
          }
        ]
      },
      "source_process": "BP-002",
      "inferred": true,
      "tags": [
        "住房纪律",
        "文书纠错",
        "跨资产验证"
      ]
    }
  ],
  "difficulty_mismatches": [
    {
      "test_id": "TEST-001",
      "planned": "basic",
      "calibrated": "advanced",
      "difficulty_score": 1.83
    }
  ]
}
```

## 下一阶段校验清单
- [x] items 数 == test_plan 数(2)
- [x] 每道 TEST 的 prompt 长度 20-300 字
- [x] 每道 TEST 的 reference 覆盖 5 阶段
- [x] 每道 TEST 的 decompose.expected_steps 与 source_process.steps 一致
- [x] 每道 TEST 的 rubric 总分=10 且权重 2/2/3/2/1
- [x] 每道 TEST ≥1 fatal_deduction + ≥1 veto_item
- [x] 每道 TEST 的 prompt 与 Stage 3 约束字符重叠 ≥ 30%

## 备注与遗留问题
难度自校准与 Stage 2 规划不一致(本阶段不覆盖 Stage 2,留待 Stage 5 裁决):
  - TEST-001: 规划=basic,校准=advanced(score=1.83)
