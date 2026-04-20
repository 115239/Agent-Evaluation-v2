# 题目生成Agent设计文档

**版本**：V2.0  

**日期**：2026-04-16  

**状态**：待审核  

**更新说明**：V2.0新增四通道输入、评分细则、题目质量保障体系、跑批评测流程、评测报告设计  

---

## 一、概述

### 1.1 设计目标

题目生成Agent负责基于智能系统设计文档，自动生成评测统一题。

**核心职责**：

- 从设计文档提取或推导业务流程（基于 GUI 挖掘业务流程、基于 code 挖掘业务流程）

- 动态分类流程类型

- 为每个流程类型生成一个统一题

- 生成五阶段期望行为

- 验证题目满足设计原则

### 1.2 核心设计原则

| 原则 | 说明 |
| --- | --- |
| 从设计意图出发 | 评测应验证系统是否达成了设计意图，而非验证历史数据pattern |
| 覆盖范围≠题目难度 | 题目数量由流程类型数量动态决定，难度由约束项/干扰项调节 |
| 双层Fallback机制 | 流程定义不存在→从PRD推导；能力边界不存在→从流程特性推导 |
| 业务闭环 | 每个题目都走完完整的业务流程 |
| 业务真实性验证 | 所有推导必须验证是否符合真实业务场景 |

---

## 二、输入定义

### 2.1 四通道输入来源

题目生成Agent支持四种输入通道，适应不同评测场景：

| 通道 | 输入物 | 适用场景 | 说明 |
| --- | --- | --- | --- |
| 设计文档通道 | PRD + Architecture + 流程定义 | 上线前评测（标准路径） | 最完整的信息来源，优先使用 |
| GUI挖掘通道 | 系统URL + 用户凭证 + 页面截图 | 已有系统但缺少文档 | 通过Playwright自动遍历挖掘业务流程 |
| 代码挖掘通道 | 源码仓库 + API接口文档 | 后端AI组件评测 | 通过AST解析和API扫描提取功能点 |
| 用户日志通道 | 生产环境query log + 高频/失败case | 上线后持续评测 | 从真实用户行为中挖掘评测场景 |

### 2.2 各通道最小输入集

#### 设计文档通道（标准路径）

```plaintext
必须：PRD（含业务目标、用户群体、核心功能）
必须：Architecture（含核心功能定义列表）
可选：业务流程定义（无 → 从PRD推导，见Fallback机制）
可选：能力边界定义（无 → 从流程特性推导，见Fallback机制）
可选：领域知识库（规程/制度文档，用于填充题目细节）
```

#### GUI挖掘通道

```plaintext
必须：系统访问URL + 登录凭证
必须：业务目标描述（1-3句话，明确"系统上线后要解决什么问题"）
可选：核心页面/功能列表（无则Agent自动遍历发现）
```

#### 代码挖掘通道

```plaintext
必须：源码目录路径或Git仓库地址
必须：入口文件/主要API端点标识
可选：API文档（Swagger/OpenAPI spec）
```

#### 用户日志通道

```plaintext
必须：query log文件（含用户输入、系统输出、时间戳）
必须：业务目标描述
可选：人工标注的失败case（用于定向生成高区分度题目）
```

### 2.3 输入数据结构

```plaintext
class AgentInput:
    """
    题目生成Agent的输入
    """
    
    # 输入通道标识
    source_channel: str  # "design_doc" / "gui" / "code" / "user_log"
    
    # 核心：智能系统设计文档（设计文档通道必须）
    system_design_docs: SystemDesignDocs
    
    # 辅助：业务域知识（用于填充题目细节，可选）
    domain_knowledge: DomainKnowledge
    
    # 目标：业务目标 （所有通道必须，需要人工确认）
    business_goal: BusinessGoal
    
    # GUI通道专用
    gui_config: GUIConfig  # Optional
    
    # 代码通道专用
    code_config: CodeConfig  # Optional
    
    # 用户日志通道专用
    log_config: LogConfig  # Optional


class SystemDesignDocs:
    """
    智能系统设计文档
    
    最小输入：PRD + Architecture
    """
    
    # 产品需求文档（必须存在）
    prd: PRD
    
    # 系统架构设计（必须存在）
    architecture: ArchitectureDesign
    
    # 业务流程定义（可能不存在 → Fallback）
    business_processes: List[BusinessProcess]  # Optional
    
    # 能力边界定义（可能不存在 → Fallback）
    capability_scope: CapabilityScope  # Optional


class PRD:
    """产品需求文档"""
    business_objective: str       # 业务目标
    target_users: List[TargetUser] # 用户群体
    core_features: List[Feature]   # 核心功能


class ArchitectureDesign:
    """系统架构设计"""
    core_features: List[Feature]           # 核心功能列表
    feature_definitions: List[FeatureDefinition]  # 功能详细定义


class GUIConfig:
    """GUI挖掘通道配置"""
    system_url: str             # 系统访问URL
    credentials: dict           # 登录凭证
    target_pages: List[str]     # 核心页面列表（可选，空则自动遍历）

class CodeConfig:
    """代码挖掘通道配置"""
    repo_path: str              # 源码路径或Git URL
    entry_points: List[str]     # 入口文件/API端点
    api_spec_path: str          # API文档路径（可选）

class LogConfig:
    """用户日志通道配置"""
    log_file: str               # query log文件路径
    failure_cases: List[dict]   # 人工标注的失败case（可选）
```

### 2.4 Phase 0: 输入预处理

在题目生成主流程（Phase 1-6）之前，必须执行输入预处理：

```plaintext
def preprocess_input(agent_input: AgentInput) -> InputAssessmentReport:
    """
    Phase 0: 输入预处理
    
    在进入题目生成主流程之前，验证输入质量并给出补充建议。
    """
    
    report = InputAssessmentReport()
    
    # 1. 完整性检查：必须字段是否存在
    report.completeness = check_required_fields(agent_input)
    
    # 2. 质量评估：PRD是否包含可操作的功能描述（而非仅概念性描述）
    report.quality_score = assess_input_quality(agent_input)
    
    # 3. 冲突检测：多个输入源之间是否存在矛盾
    report.conflicts = detect_input_conflicts(agent_input)
    
    # 4. 通道适配：根据输入来源选择最优的流程提取策略
    report.recommended_strategy = select_extraction_strategy(agent_input)
    
    # 5. 补充建议：缺少哪些可选输入，补充后能显著提升题目质量
    report.suggestions = generate_input_suggestions(agent_input)
    
    return report


class InputAssessmentReport:
    """输入预处理报告"""
    completeness: dict       # 各必须字段的存在状态
    quality_score: float     # 输入质量评分 (0-1)
    conflicts: List[str]     # 发现的冲突项
    recommended_strategy: str  # 推荐的流程提取策略
    suggestions: List[str]   # 补充建议
    can_proceed: bool        # 是否满足最低输入要求
```

---

## 三、输出定义

### 3.1 输出结构

```plaintext
class AgentOutput:
    """
    题目生成Agent的输出
    """
    
    # 数据集元信息
    dataset_meta: DatasetMeta
    
    # N个统一题（N=流程类型数量，动态决定）
    unified_tests: List[UnifiedTest]
    
    # N个五阶段期望行为
    reference_answers: List[ReferenceAnswer]
    
    # N个评分细则（新增：每道题配套的评分标准）
    scoring_rubrics: List[ScoringRubric]
    
    # 验证报告
    validation_report: ValidationReport
    
    # 流程提炼报告
    process_inference_report: ProcessInferenceReport
    
    # 质量度量（新增：数据集整体质量指标）
    quality_metrics: QualityMetrics


class DatasetMeta:
    """数据集元信息"""
    version: str             # 数据集版本
    domain: str              # 业务领域
    business_goal: str       # 业务目标
    created_at: str          # 生成日期
    total_items: int         # 题目总数
    difficulty_distribution: dict  # {"basic": 2, "advanced": 2, "expert": 2}
    source_channel: str      # 输入通道 "design_doc" / "gui" / "code" / "user_log"
```

### 3.2 统一题结构

```plaintext
class UnifiedTest:
    """
    统一题：完整的业务问题解决任务
    """
    
    # 基本信息
    test_id: str
    difficulty: str        # "basic" / "advanced" / "expert"
    domain: str
    
    # 题目内容
    prompt: str            # 用户向系统输入的完整问题
    
    # 题目设计要素
    user_role: str         # 用户角色
    intent_type: str       # 意图类型
    constraints: List[str]           # 约束项
    interference_items: List[str]    # 干扰项
    success_criteria: List[str]      # 成功标准
    
    # 来源标注
    source_process: str    # 题目来源的业务流程ID
    inferred: bool         # 是否为推导生成
    
    # 完整覆盖业务流程
    primary_stages: List[str]  # 所有题目都是业务闭环
```

### 3.3 五阶段期望行为结构

```plaintext
class ReferenceAnswer:
    """
    五阶段期望行为（不是"答案"，是"期望的行为"）
    """
    
    test_id: str
    
    # 定义问题阶段期望
    define_problem_expected: DefineProblemExpected
    
    # 拆解问题阶段期望
    decompose_expected: DecomposeExpected
    
    # 方案生成阶段期望
    solution_expected: SolutionExpected
    
    # 执行落地阶段期望
    execution_expected: ExecutionExpected
    
    # 元认知阶段期望
    meta_expected: MetaExpected


class DefineProblemExpected:
    """
    定义问题阶段期望行为
    """
    intent_understanding: str    # 意图理解期望
    implicit_needs: List[str]    # 隐含需求识别期望
    problem_essence: str         # 问题本质判断期望


class DecomposeExpected:
    """
    拆解问题阶段期望行为
    """
    expected_steps: List[str]    # 期望的拆解步骤
    priority_ordering: str       # 优先级排序期望


class SolutionExpected:
    """
    方案生成阶段期望行为
    """
    information_sources: List[str]  # 期望引用的信息源
    cross_doc_integration: str      # 跨文档整合期望


class ExecutionExpected:
    """
    执行落地阶段期望行为
    """
    output_format: str          # 输出格式期望
    exception_handling: str     # 异常处理期望


class MetaExpected:
    """
    元认知阶段期望行为
    """
    source_annotation: str           # 信息来源标注期望
    uncertainty_acknowledgment: str  # 不确定性说明期望
    boundary_awareness: str          # 权限边界意识期望
```

### 3.4 评分细则结构

```plaintext
class ScoringRubric:
    """
    评分细则：每道题配套的评分标准
    
    用于跑批阶段的自动评判和人工评审
    """
    test_id: str
    total_max_score: float           # 该题满分（默认10分）
    stages: List[StageRubric]        # 五阶段评分细则
    fatal_deductions: List[FatalDeduction]    # 致命扣分项
    veto_items: List[VetoItem]               # 一票否决项


class StageRubric:
    """单阶段评分细则"""
    stage_name: str          # "定义问题" / "拆解问题" / "方案生成" / "执行落地" / "元认知"
    max_score: float         # 该阶段满分 (2/2/3/2/1)
    weight: float            # 权重 (0.25/0.20/0.20/0.25/0.10)
    scoring_points: List[ScoringPoint]  # 逐项得分点


class ScoringPoint:
    """单项得分点"""
    description: str         # 例："正确识别用户意图为设备巡检查询"
    score: float            # 该项分值
    evidence_type: str      # "keyword_match" / "semantic_match" / "llm_judge"
    keywords: List[str]     # 规则匹配用的关键词（仅keyword_match类型）
    negative: bool          # 是否为扣分项（True=扣分，False=得分）


class FatalDeduction:
    """致命扣分项：触发则该题直接0分"""
    description: str         # 例："严重逻辑错误"
    detection_rule: str      # 检测规则描述


class VetoItem:
    """一票否决项：触发则整体不合格，无论总分"""
    description: str         # 例："泄露敏感数据"
    detection_rule: str      # 检测规则描述
```

### 3.5 质量度量结构

```plaintext
class QualityMetrics:
    """
    数据集质量度量
    
    在题目生成完成后自动计算，用于评估题目集的整体质量
    """
    
    # 覆盖矩阵：业务流程 x 五阶段 的覆盖情况
    coverage_matrix: dict    # {process_id: {stage: covered_by_test_ids}}
    
    # 难度分布平衡度
    difficulty_balance: dict # {"basic": N, "advanced": N, "expert": N}
    
    # 约束项/干扰项密度
    constraint_density: dict # {test_id: {"constraints": N, "interference": N}}
    
    # 预估区分度（基于题目设计特征的先验估计）
    estimated_discrimination: dict  # {test_id: estimated_D_value}
    
    # 题目独立性评分（题目之间是否有过多重叠）
    independence_score: float  # 0-1, 越高越好
```

### 3.6 标准化数据集输出格式

题目生成Agent的最终输出应为以下JSON格式，可直接送入跑批评测引擎：

```plaintext
{
  "dataset_meta": {
    "version": "1.0",
    "domain": "纪检材料智能审查",
    "business_goal": "材料审查准确率>=90%",
    "created_at": "2026-04-16",
    "total_items": 6,
    "difficulty_distribution": {"basic": 2, "advanced": 2, "expert": 2},
    "source_channel": "design_doc"
  },
  "items": [
    {
      "test_id": "JJ-001",
      "difficulty": "basic",
      "difficulty_score": 1.3,
      "domain": "规程查询",
      "prompt": "我是纪检监察室的小李，需要查一下最新的《中国共产党纪律处分条例》中关于违反中央八项规定精神的处分规定，包括具体适用条款和量纪标准。",
      "context": {
        "user_role": "纪检监察员",
        "intent_type": "单一知识查询",
        "constraints": ["依据2024年修订版纪律处分条例"],
        "interference_items": [],
        "success_criteria": [
          "正确识别用户查询意图",
          "引用最新修订版条例",
          "完整列出相关条款和量纪标准"
        ]
      },
      "reference": {
        "define_problem": {
          "intent_understanding": "应理解用户需要查询纪律处分条例中特定条款",
          "implicit_needs": ["具体条款号", "量纪标准", "适用情形"],
          "problem_essence": "法规条款精确检索"
        },
        "decompose": {
          "expected_steps": ["定位条例版本", "检索八项规定相关条款", "提取量纪标准"],
          "priority_ordering": "按条例章节结构顺序"
        },
        "solution": {
          "information_sources": ["纪律处分条例2024修订版"],
          "cross_doc_integration": "单文档内检索"
        },
        "execution": {
          "output_format": "条款列表 + 量纪标准表格",
          "exception_handling": "如条例版本有歧义应主动说明"
        },
        "metacognition": {
          "source_annotation": "应标注条例版本和具体条款号",
          "uncertainty_acknowledgment": "无需特别说明",
          "boundary_awareness": "不涉及权限边界"
        }
      },
      "rubric": {
        "total_max_score": 10,
        "stages": [
          {
            "stage_name": "定义问题",
            "max_score": 2.0,
            "weight": 0.25,
            "scoring_points": [
              {"description": "正确识别查询意图为条例条款检索", "score": 1.0, "evidence_type": "llm_judge"},
              {"description": "识别出需要最新版本条例", "score": 1.0, "evidence_type": "keyword_match", "keywords": ["2024", "修订版"]}
            ]
          },
          {
            "stage_name": "拆解问题",
            "max_score": 2.0,
            "weight": 0.20,
            "scoring_points": [
              {"description": "将查询拆解为条款定位+量纪标准两部分", "score": 1.0, "evidence_type": "llm_judge"},
              {"description": "覆盖所有请求的信息维度", "score": 1.0, "evidence_type": "llm_judge"}
            ]
          },
          {
            "stage_name": "方案生成",
            "max_score": 3.0,
            "weight": 0.20,
            "scoring_points": [
              {"description": "引用正确版本的条例", "score": 1.5, "evidence_type": "keyword_match", "keywords": ["2024"]},
              {"description": "列出具体适用条款号", "score": 1.5, "evidence_type": "llm_judge"}
            ]
          },
          {
            "stage_name": "执行落地",
            "max_score": 2.0,
            "weight": 0.25,
            "scoring_points": [
              {"description": "输出格式清晰可用", "score": 1.0, "evidence_type": "llm_judge"},
              {"description": "完整列出量纪标准", "score": 1.0, "evidence_type": "llm_judge"}
            ]
          },
          {
            "stage_name": "元认知",
            "max_score": 1.0,
            "weight": 0.10,
            "scoring_points": [
              {"description": "标注信息来源（条例版本号）", "score": 1.0, "evidence_type": "keyword_match", "keywords": ["条例", "第"]}
            ]
          }
        ],
        "fatal_deductions": [
          {"description": "引用错误版本条例（如废止版本）", "detection_rule": "llm_judge检测版本正确性"},
          {"description": "编造不存在的条款", "detection_rule": "与知识库交叉验证"}
        ],
        "veto_items": [
          {"description": "泄露涉密案件信息", "detection_rule": "敏感信息关键词扫描"}
        ]
      },
      "tags": ["single_doc_query", "regulation_lookup", "exact_retrieval"],
      "source_process": "BP-001",
      "inferred": false
    }
  ]
}
```

---

# 四、核心逻辑流程

> 目标:把"输入一个业务 PRD / 设计文档 + 业务数据" 转化为"可直接跑批的测试数据集(JSON + 兼容纪检样例的 Excel)"这件事,拆成 **5 个串行阶段**。每阶段:

> - **输入**:上一阶段产出的 MD(+ 本阶段所需的原始物料)

> - **处理**:规则代码 + LLM 协作(创造性部分交 LLM,校验与聚合交代码)

> - **产出**:一份符合统一规范的 MD 文档 + 嵌入的 JSON Artifacts

> - **交付门槛**:MD 末尾的"下一阶段校验清单"必须全部打勾才能进入下一阶段

### 4.1 Pipeline 总览

```plaintext
原始输入层                         Pipeline 5 阶段                              最终产物
┌────────────┐
│ PRD               │
│ Architecture      │ ─┐
│ 业务数据(xlsx)     │    \
│ 规程/制度文档       │     \
│ 一句话业务目标      │      ↓
└───────────┘   ┌────────────────┐
                      │ Stage 1 · 业务理解             │ → 01_understanding.md
                      │   (业务目标/用户/功能/业务支撑材料)   │
                      └─────────┬────────┘
                                       ↓
                      ┌────────────────────┐
                      │ Stage 2 · 业务流程 + 题目规划      │ → 02_plan.md
                      │   (第一层Fallback / 聚类 / 规划)   │
                      └─────────┬──────────┘
                                       ↓
                      ┌──────────────────────┐
                      │ Stage 3 · 仿真数据集的构建 + 约束/干扰设计│ → 03_context.md
                      │   (第二层Fallback / 真实性校验)        │
                      └─────────┬────────────┘
                                       ↓
                      ┌──────────────────────┐
                      │ Stage 4 · 题目 + 期望 + 评分细则       │ → 04_tests.md
                      │   (prompt/reference/rubric/难度)      
                      └─────────┬─────────────┘
                                       ↓
                      ┌────────────────────┐
                      │ Stage 5 · 验证 + benchmark       │ → 05_report.md
                      │   (5原则/覆盖矩阵/打包)            │
                      └─────────┬──────────┘
                                       ↓
                          ┌──────────────────┐
                          │ dataset.json                 │
                          │ dataset.xlsx                 │
                          │ 05_report.md                 │
                          │ traceability.json            │
                          └──────────────────┘
```

```plaintext
┌─────┬───────────────────────────────────────────────────────────────┬─────────────────────┐
│  阶段   │                            简要                             │  从抽象→具体的位置  │
├─────┼───────────────────────────────────────────────────────────────┼─────────────────────┤
│ Stage 1 │ 把原始文档变成 5 张结构化的"认知表"                           │ 非结构 → 结构化认知 │
├─────┼───────────────────────────────────────────────────────────────┼─────────────────────┤
│ Stage 2 │ 在认知上"推"出流程,再"分"出类型,再"规划"出几道题              │ 认知 → 题目骨架     │
├─────┼───────────────────────────────────────────────────────────────┼─────────────────────┤
│ Stage 3 │ 打开业务数据 xlsx,把题目骨架绑到具体条款+片段+关键字+约束干扰 │ 骨架 → 知识绑定     │
├─────┼───────────────────────────────────────────────────────────────┼─────────────────────┤
│ Stage 4 │ 用关键字扩写成口语化提问,配齐期望行为与评分细则               │ 绑定 → 完整题目     │
├─────┼───────────────────────────────────────────────────────────────┼─────────────────────┤
│ Stage 5 │ 做完验证、打包成可跑批的 JSON + 纪检样例格式 xlsx             │ 题目 → 可执行数据集 │
└─────┴───────────────────────────────────────────────────────────────┴─────────────────────┘
```

**阶段间数据契约**

| 阶段 | 上游 | 下游 | 核心字段 |
| --- | --- | --- | --- |
| Stage 1 | 源文档 | 02_plan.md | business_goal / user_groups / features / knowledge_assets / glossary |
| Stage 2 | 01_understanding.md | 03_context.md | processes / process_types / test_plan / coverage_matrix_plan |
| Stage 3 | 02_plan.md + 业务数据 | 04_tests.md | knowledge_index / test_contexts(fragments/constraints/interferences) |
| Stage 4 | 03_context.md | 05_report.md | items(prompt/reference/rubric/difficulty) |
| Stage 5 | 04_tests.md | 最终产物 | validation / dataset_meta + dataset.{json,xlsx} |

### 4.2 每阶段 MD 文档的统一格式规范

所有阶段产物遵循同一骨架,机器易解析、人工易 review。

```plaintext
---
stage: <阶段编号, 1-5>
stage_name: <阶段英文代号>
version: <语义化版本, e.g. 1.0>
upstream: <上一阶段 MD 路径 或 "源文档">
downstream: <下一阶段 MD 路径 或 "最终产物">
domain: <业务域, e.g. 纪检材料智能审查>
created_at: <ISO 8601 时间戳>
created_by: <agent-stageN / human-editor>
pass_gate: <true | false>   # 下一阶段校验清单是否全部打勾
---

# Stage N · <中文标题>

## 摘要
<5-10 句话:本阶段做了什么、产出了什么、关键数字、有没有触发 Fallback>

## <业务化小节 1>
<表格/列表,便于人工 review>

## <业务化小节 2>
...

## 结构化数据 (Artifacts)
{ ... 严格 JSON,下一阶段代码直接 json.loads 加载 ... }

## 下一阶段校验清单
- [ ] 校验项 1
- [ ] 校验项 2

## 备注与遗留问题
<Fallback 发生记录 / 推导痕迹 / 需人工确认的点>
```

**全局 ID 规范**(贯穿 5 阶段,便于追溯):

- `UG-xxx` 用户群体 · `FEAT-xxx` 核心功能 · `KB-xxx` 知识资产 · `FRAG-xxx-yyy` 资产内切片

- `BP-xxx` 业务流程 · `PT-xxx` 流程类型 · `TEST-xxx` 题目

- `C-xxx` 约束项 · `I-xxx` 干扰项

所有**推导生成**的字段必须带 `inferred: true`,便于 Stage 5 审计。

---

### 4.3 Stage 1 · 业务理解 → 01_understanding.md

#### 目标

把"一堆原始文档"解析成结构化的业务理解。**本阶段不做流程提取**,只做信息识别与归档,为后续阶段奠基。

#### 输入

| 输入 | 来源 | 必需 |
| --- | --- | --- |
| PRD 文档 | .md / .docx / .pdf | ✓ |
| 架构/设计文档 | .md / .docx | ✓ |
| 业务数据资产样本 | .xlsx / .docx 目录 | ✓ |
| 一句话业务目标 | 人工输入或 PRD 首段 | ✓ |

#### 处理逻辑

1. **文档切片**:PRD / Architecture 按章节切 chunks,建立倒排索引

1. **业务目标抽取**:LLM 从 PRD 识别"上线后要解决什么问题"的核心命题,含 success_metric

1. **用户画像识别**:枚举 `(角色, 职责, 典型诉求)` 三元组,每个典型诉求保留原文示例

1. **核心功能枚举**:从 Architecture 提取 feature 清单,补齐每个 feature 的 `input / output / depends_on(关联 KB)`

1. **业务数据资产登记**:扫描业务数据目录,对每个 xlsx / docx 生成"资产卡片"

   - 字段:文件名、sheet、行数、关键字段列表、样本 3 行、权威性标注

   - 参考:`datasets/test_agent_2/纪检项目业务数据+样例数据/业务数据/` 下的 4 个 xlsx

1. **领域术语表**:高频专业术语归档(如"八项规定"、"四种形态"、"定性量纪"),供下游 Prompt 统一用词

1. **自检**:必需字段缺失 → 写入"备注与遗留问题" + `pass_gate=false`,请求人工补充

#### 输出 MD 样例(纪检项目)

```plaintext
---
stage: 1
stage_name: business_understanding
version: 1.0
upstream: 源文档
downstream: 02_plan.md
domain: 纪检材料智能审查
created_at: 2026-04-20T10:00:00+08:00
created_by: agent-stage1
pass_gate: true
---

# Stage 1 · 业务理解

## 摘要
基于广东电网纪检项目的 PRD 与业务数据样本,识别出 2 类核心用户、4 项核心功能、
4 类业务数据资产。业务目标聚焦"党纪法规智能检索与定性量纪辅助",
未发现多源冲突。领域术语表已沉淀 12 条。

## 业务目标
| 字段 | 值 |
|------|---|
| one_liner | 为纪检监察员提供党纪法规、总书记讲话、理论文章、实务案例的 AI 语义检索与定性量纪辅助 |
| success_metric | 材料审查准确率 ≥ 90%,语义检索召回率 ≥ 85% |
| business_value | 替代 60% 人工条款查阅工作,缩短定性决策时间 |

## 用户画像
| ID | 角色 | 职责 | 典型诉求(原文示例) |
|----|------|------|---------------------|
| UG-001 | 纪检监察员 | 审查违纪案件、查询法规 | "这种情形适用哪条纪律处分条例?" |
| UG-002 | 纪检部门负责人 | 定性量纪决策、审核文书 | "类似案件历史上是怎么量纪的?" |

## 核心功能清单
| ID | 功能名 | 输入 | 输出 | 依赖资产 |
|----|--------|------|------|---------|
| FEAT-001 | 党纪法规语义检索 | 自然语言问题 | 匹配条款+出处+片段 | KB-001 |
| FEAT-002 | 总书记讲话精准定位 | 主题关键词 | 讲话摘要+上下文 | KB-002 |
| FEAT-003 | 定性量纪建议 | 案情描述 | 适用条款+量纪档次+类案 | KB-001, KB-004 |
| FEAT-004 | 实务案例检索 | 违纪情形描述 | 类似案例+处理方式 | KB-004 |

## 业务数据资产
| 资产 ID | 文件 | 行数 | 关键字段 | 权威性 |
|---------|------|------|---------|--------|
| KB-001 | 党纪法规.xlsx | 3850 | 序号, 要点词, 违纪行为 | 官方 |
| KB-002 | 总书记讲话.xlsx | ~500 | 标题, 摘要, 日期 | 官方 |
| KB-003 | 理论文章.xlsx | ~300 | 标题, 摘要 | 权威刊物 |
| KB-004 | 实务测试集.xlsx | 80  | 问题, 答案, 来源文档 | 历史案例 |

## 领域术语表(节选)
- **八项规定**:中央八项规定精神,聚焦公务接待/差旅/公款消费等
- **四种形态**:监督执纪的四种递进形态
- **定性量纪**:对违纪行为定性并决定处分档次
- **从宽情节**:主动交代/配合调查/退赔挽损等
- ...

## 结构化数据
{
  "business_goal": {
    "one_liner": "为纪检监察员提供党纪法规、总书记讲话、理论文章、实务案例的 AI 语义检索与定性量纪辅助",
    "success_metric": "材料审查准确率 ≥ 90%,语义检索召回率 ≥ 85%",
    "business_value": "替代 60% 人工条款查阅工作,缩短定性决策时间"
  },
  "user_groups": [
    {"id":"UG-001","role":"纪检监察员","responsibility":"审查违纪案件、查询法规","typical_query":"这种情形适用哪条纪律处分条例?"},
    {"id":"UG-002","role":"纪检部门负责人","responsibility":"定性量纪决策、审核文书","typical_query":"类似案件历史上是怎么量纪的?"}
  ],
  "features": [
    {"id":"FEAT-001","name":"党纪法规语义检索","input":"自然语言问题","output":"匹配条款+出处+片段","depends_on":["KB-001"]},
    {"id":"FEAT-002","name":"总书记讲话精准定位","input":"主题关键词","output":"讲话摘要+上下文","depends_on":["KB-002"]},
    {"id":"FEAT-003","name":"定性量纪建议","input":"案情描述","output":"适用条款+量纪档次+类案","depends_on":["KB-001","KB-004"]},
    {"id":"FEAT-004","name":"实务案例检索","input":"违纪情形描述","output":"类似案例+处理方式","depends_on":["KB-004"]}
  ],
  "knowledge_assets": [
    {"id":"KB-001","file":"党纪法规.xlsx","rows":3850,"key_fields":["序号","要点词","违纪行为"],"authority":"官方"},
    {"id":"KB-002","file":"总书记讲话.xlsx","rows":500,"key_fields":["标题","摘要","日期"],"authority":"官方"},
    {"id":"KB-003","file":"理论文章.xlsx","rows":300,"key_fields":["标题","摘要"],"authority":"权威刊物"},
    {"id":"KB-004","file":"实务测试集.xlsx","rows":80,"key_fields":["问题","答案","来源文档"],"authority":"历史案例"}
  ],
  "glossary": {
    "八项规定":"中央八项规定精神,聚焦公务接待/差旅/公款消费等",
    "四种形态":"监督执纪的四种递进形态",
    "定性量纪":"对违纪行为定性并决定处分档次"
  }
}


## 下一阶段校验清单
- [x] 业务目标 one_liner 字数 20-100
- [x] 至少识别 1 个用户画像,每个有 typical_query 原文示例
- [x] 至少识别 1 个核心功能,每个标注 input/output/depends_on
- [x] 每个核心功能关联 ≥ 1 个 knowledge_asset(或显式 "无资产依赖")
- [x] 领域术语表 ≥ 5 条

## 备注与遗留问题
- PRD 未明确"定性量纪建议"的合规边界,Stage 3 需引入领域专家补充 weak_points
```

#### Agent Prompt 模板

**System**:

> 你是业务分析师,负责从产品需求文档和架构设计中抽取结构化的业务理解。

> 你的输出将成为后续 Pipeline 阶段的唯一输入,必须严格、可验证、不虚构。

> 

> 原则:

> 1. 只从原文提取,不做业务推断;无明确信息则写 `"NOT_SPECIFIED"`

> 2. 保留领域术语原文(如"四种形态"),不做意译

> 3. ID 全局唯一,按 `UG-001 / FEAT-001 / KB-001` 递增

> 4. 多源冲突(PRD 与架构描述不一致)列入"备注与遗留问题",不自行裁决

**User**:

```plaintext
<business_goal_hint>{{ 一句话业务目标 }}</business_goal_hint>
<prd>{{ PRD 正文,已切片 }}</prd>
<architecture>{{ 架构设计正文 }}</architecture>
<data_assets>
{{ 每个 xlsx/docx: 文件名 + sheet + 前 3 行样本 }}
</data_assets>

请按以下 JSON Schema 输出 Artifacts,再据此用中文填写 MD 正文表格:

{
  "business_goal": {"one_liner":"string","success_metric":"string","business_value":"string"},
  "user_groups": [{"id":"UG-xxx","role":"string","responsibility":"string","typical_query":"string"}],
  "features":    [{"id":"FEAT-xxx","name":"string","input":"string","output":"string","depends_on":["KB-xxx"]}],
  "knowledge_assets": [{"id":"KB-xxx","file":"string","rows":0,"key_fields":["string"],"authority":"string"}],
  "glossary": {"term":"definition"}
}
```

---

### 4.4 Stage 2 · 业务流程提取 + 题目规划 → 02_plan.md

#### 目标

基于 Stage 1 的业务理解,做三件事:

1. **提取或推导**业务流程(**第一层 Fallback** 发生在此)

1. **聚类**流程(动态发现分类维度,而非预设类别)

1. **规划**题目总数、难度梯度、覆盖矩阵蓝图

#### 输入

- `01_understanding.md`

- 原始 PRD 中可能存在的 `business_processes` 定义段(若无则走 Fallback)

#### 处理逻辑

**Step 2.1 — 流程提取 / 推导(第一层 Fallback)**

```plaintext
if 源文档存在 business_processes 段:
    → 逐条直接转录 (id, name, actors, triggers, steps, outputs),inferred=false
else:
    → 推导公式: 流程 = 用户角色 × 核心功能 × 业务目标
      for ug in user_groups:
          for feat in match(ug.typical_query, features):
              推导(triggers, steps, outputs, actors, inferred=true)
    → 合并相似流程(步骤重合度 ≥ 0.8)
```

**Step 2.2 — 分类维度动态提取**

从全部流程中挑选**区分度 ≥ 2**(即至少出现两种取值)的维度:

- 触发类型(知识咨询 / 案件研判 / 审核复核 / 批量处理 ...)

- 输出类型(结构化条款 / 决策建议 / 检索片段 / 纠错清单 ...)

- 参与者层级(业务员 / 管理层 / 跨层协同 ...)

- 跨文档依赖度(单文档 / 2-3 文档 / 4+ 文档)

**Step 2.3 — 聚类与类型命名**

按显著维度组合聚类,类型名 = `{主触发类型}-{主输出类型}类`。

**Step 2.4 — 代表流程选择**

每类按 `importance = complexity × coverage × business_value` 选 Top 1 作为代表。

**Step 2.5 — 题目规划**

- 题目总数 `N = 流程类型数`

- 难度按聚类复杂度自动分配:

  - `complexity ≤ 0.4` → basic

  - `0.4 < complexity ≤ 0.7` → advanced

  - `complexity > 0.7` → expert

- `N < 3` → 每个类型补选次优流程,提升 1 级难度作为补充题

- `N > 10` → 按业务优先级砍掉重要度最低的类型

**Step 2.6 — 覆盖矩阵蓝图**

输出 `流程类型 × 五阶段` 的目标矩阵,每格标注"重点 / 常规"——为 Stage 4 的出题重心提供指引,为 Stage 5 的覆盖验证提供基线。

#### 输出 MD 样例

```plaintext
---
stage: 2
stage_name: process_and_plan
version: 1.0
upstream: 01_understanding.md
downstream: 03_context.md
domain: 纪检材料智能审查
created_at: 2026-04-20T11:00:00+08:00
created_by: agent-stage2
pass_gate: true
---

# Stage 2 · 业务流程提取 + 题目规划

## 摘要
共提取 6 条业务流程,其中 2 条为直接转录、4 条为推导(inferred=true)。按
"触发-输出"组合聚类为 4 个类型,规划 4 道题:1 basic + 2 advanced + 1 expert。
第一层 Fallback 已触发(源文档无流程定义段)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|----|------|------|
| business_processes 段存在 | ❌ | 全部走推导路径 |
| capability_scope.weak_points | ❌ | 将在 Stage 3 触发第二层 Fallback |

## 业务流程清单
| ID | 名称 | 触发 | 参与者 | 步骤数 | 输出 | inferred |
|----|------|------|--------|--------|------|----------|
| BP-001 | 党纪条款精确查询 | 知识咨询 | UG-001 | 3 | 条款 + 量纪档次 | true |
| BP-002 | 总书记讲话主题检索 | 知识咨询 | UG-002 | 3 | 讲话摘要 + 上下文 | true |
| BP-003 | 定性量纪决策辅助 | 案件研判 | UG-001+UG-002 | 5 | 定性 + 条款 + 档次 | false |
| BP-004 | 跨文档类案参考 | 案件研判 | UG-001 | 4 | 类案 + 处理方式 | true |
| BP-005 | 实务案例查询 | 知识咨询 | UG-001 | 3 | 实务问答 | false |
| BP-006 | 文书纠错 | 审核复核 | UG-002 | 4 | 纠错建议 + 依据 | true |

## 流程分类与代表
| 类型 ID | 类型名 | 成员 BP | 代表 BP | 复杂度 | 分配难度 |
|---------|--------|---------|---------|--------|---------|
| PT-001 | 知识咨询-单文档类 | BP-001, BP-002, BP-005 | BP-001 | 0.30 | basic |
| PT-002 | 知识咨询-跨文档类 | BP-004 | BP-004 | 0.60 | advanced |
| PT-003 | 案件研判-综合决策类 | BP-003 | BP-003 | 0.85 | expert |
| PT-004 | 审核复核-文书纠错类 | BP-006 | BP-006 | 0.55 | advanced |

## 题目规划
| 题号 | 流程类型 | 代表流程 | 难度 | 主轴 |
|------|---------|---------|------|------|
| TEST-001 | PT-001 | BP-001 | basic | 验证单文档语义检索准确性 |
| TEST-002 | PT-002 | BP-004 | advanced | 验证跨文档信息整合 |
| TEST-003 | PT-003 | BP-003 | expert | 验证定性量纪多步推理 |
| TEST-004 | PT-004 | BP-006 | advanced | 验证规范性比对与依据引用 |

## 覆盖矩阵蓝图
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|--|---------|---------|---------|---------|--------|
| TEST-001 | 重点 | 常规 | 常规 | 常规 | 常规 |
| TEST-002 | 常规 | 重点 | 重点 | 常规 | 常规 |
| TEST-003 | 重点 | 重点 | 重点 | 重点 | 重点 |
| TEST-004 | 常规 | 常规 | 常规 | 重点 | 重点 |

## 结构化数据
{
  "fallback_status": {"business_processes_present": false, "capability_scope_present": false},
  "processes": [
    {
      "id":"BP-001","name":"党纪条款精确查询",
      "actors":[{"id":"UG-001","role":"纪检监察员","level":"业务"}],
      "triggers":[{"type":"知识咨询","description":"遇到具体违纪情形需查条款"}],
      "steps":[
        {"no":1,"name":"定位条例版本"},
        {"no":2,"name":"按关键词检索条款"},
        {"no":3,"name":"提取量纪档次"}
      ],
      "outputs":[{"name":"条款号+原文+量纪档次","category":"结构化条款"}],
      "cross_process_dependency":"单流程",
      "inferred": true
    }
  ],
  "process_types": [
    {"type_id":"PT-001","name":"知识咨询-单文档类","members":["BP-001","BP-002","BP-005"],"representative":"BP-001","complexity_score":0.30,"assigned_difficulty":"basic"}
  ],
  "test_plan": [
    {"test_id":"TEST-001","process_type":"PT-001","source_process":"BP-001","difficulty":"basic","focus_stages":["定义问题"]}
  ],
  "coverage_matrix_plan": {
    "TEST-001":{"定义问题":"重点","拆解问题":"常规","方案生成":"常规","执行落地":"常规","元认知":"常规"}
  }
}

## 下一阶段校验清单
- [x] 每条 BP 至少 3 个步骤
- [x] 触发类型取值来自预设词表或 Stage 1 glossary
- [x] 聚类后的类型数 = test_plan 中的题目数
- [x] 难度分配覆盖至少 2 个等级
- [x] 覆盖矩阵蓝图中每道题至少 1 个"重点"阶段

## 备注与遗留问题
- BP-003 涉及多规程交叉应用,Stage 3 需为其准备至少 3 份来源文档切片
- 发现 BP-005 与 BP-001 步骤重合度 0.75,未触发合并阈值 0.80,保留两条
```

#### Agent Prompt 模板

**System**:

> 你是业务流程架构师。根据上游 Stage 1 的业务理解文档,提取或推导业务流程,

> 并规划覆盖这些流程的测试题目方案。

> 

> 原则:

> 1. **优先直接提取**:若源文档有流程定义段,直接转录

> 2. **否则推导**:`流程 = 用户角色 × 核心功能 × 业务目标`,inferred=true

> 3. **合并相似流程**:步骤重合度 ≥ 0.8

> 4. **聚类维度**区分度 ≥ 2(即至少 2 个不同取值)

> 5. **题目数 = 聚类类型数**,不自行增减

**User**:

```plaintext
<stage1_md>{{ 01_understanding.md 全文 }}</stage1_md>
<source_process_docs>{{ 源文档流程定义段,无则留空 }}</source_process_docs>

请严格按以下 JSON Schema 输出 Artifacts,再据此填写 MD 表格:

{
  "fallback_status": {"business_processes_present":"bool","capability_scope_present":"bool"},
  "processes": [{
    "id":"BP-xxx","name":"string",
    "actors":[{"id":"UG-xxx","role":"string","level":"业务|管理"}],
    "triggers":[{"type":"string","description":"string"}],
    "steps":[{"no":0,"name":"string"}],
    "outputs":[{"name":"string","category":"string"}],
    "cross_process_dependency":"单流程|跨流程",
    "inferred":"bool"
  }],
  "process_types":[{"type_id":"PT-xxx","name":"string","members":["BP-xxx"],"representative":"BP-xxx","complexity_score":"0-1","assigned_difficulty":"basic|advanced|expert"}],
  "test_plan":[{"test_id":"TEST-xxx","process_type":"PT-xxx","source_process":"BP-xxx","difficulty":"basic|advanced|expert","focus_stages":["五阶段名"]}],
  "coverage_matrix_plan":{"TEST-xxx":{"定义问题":"重点|常规","拆解问题":"重点|常规","方案生成":"重点|常规","执行落地":"重点|常规","元认知":"重点|常规"}}
}
```

---

### 4.5 Stage 3 · 仿真数据集的构建 + 约束/干扰设计 → 03_context.md

#### 目标

为 Stage 2 规划的每道题配齐"知识后台":

- 主参考资产、关键片段、关键字池

- **约束项**(**第二层 Fallback** 发生在此)

- **干扰项**(同层 Fallback)

- 业务真实性三检验

#### 输入

- `02_plan.md`

- Stage 1 登记的 `knowledge_assets`(业务数据 xlsx / docx)

- 可选:`capability_scope.weak_points`

#### 处理逻辑

**Step 3.1 — 仿真数据集的构建**

参考 `datasets/test_agent_2/0311构建.py` 的抽样思路:

```plaintext
for asset in knowledge_assets:
    df = load_xlsx(asset.file)
    for row_no, row in df.iterrows():
        frag = KBFragment(
            frag_id = f"FRAG-{asset.id[-3:]}-{row_no}",
            asset_id = asset.id,
            row_no = row_no,
            key_text = compose(row, asset.key_fields),  # 例如 纪检"要点词 + 违纪行为"
            full_row = row.to_dict(),
            metadata = {"date": ..., "version": ..., "source_doc": ...}
        )
        index.add(frag)
inverted_index: keyword -> [frag_ids]
```

**Step 3.2 — 题目 × 资产匹配**

| 难度 | 主资产数 | 候选 fragment 数 | 干扰用 fragment |
| --- | --- | --- | --- |
| basic | 1 | 1-3 | 0 |
| advanced | 2-3 | 5-8 | 1-2 |
| expert | 3+ | 10+ | 3+ |

匹配方式:按 `source_process.outputs.category` 反向查找 `knowledge_assets` 中匹配度最高的资产。

**Step 3.3 — 关键字候选池提取**

复用 `0311构建.py::extract_retrieval_keywords` 的做法:每个 fragment 提取一个 4-8 字的专业短语,去重后作为该题的关键字池。这些关键字是 Stage 4 组装用户 prompt 的"种子"。

**Step 3.4 — 约束项设计(第二层 Fallback)**

```plaintext
if capability_scope.weak_points 存在:
    约束项 = 从 weak_points 映射
else:
    # 从流程特性推导,5 个维度
    constraints = []
    if process.cross_process_dependency == "跨流程":
        add("需整合多个流程的信息,形成完整方案")
    if has_multiple_regulation_versions(asset):
        add("需引用最新规程版本,排除已废止版本")
    if any(a.level == "管理" for a in process.actors):
        add("需识别信息访问权限边界,标注受限信息")
    if len(process.outputs) > 1:
        add("需完整交付所有输出项,形成闭环")
    if has_fuzzy_trigger(process):
        add("需合理推断模糊需求,或主动追问澄清")

# 基础约束(始终追加)
add(f"依据 {最新规程版本}")  # 时效性
```

**Step 3.5 — 干扰项设计(同层 Fallback)**

```plaintext
干扰维度:
  1. 规程规则冲突(检测同主题条款矛盾)
  2. 规程多版本并存(按资产 date 字段检测)
  3. 流程异常情况(Stage 2 的异常步骤)
  4. 模糊触发条件
  5. 跨部门角色混淆

密度规则:
  basic     → 0 个
  advanced  → 1 个
  expert    → ≥ 2 个, 含 1 个"陷阱型"(description 必含"冲突"|"过时"|"看似合理"之一)
```

**Step 3.6 — 业务真实性三检验**

每条约束 / 干扰项三选一通过即保留:

- `regulation_support`:在 KB 中能找到对应依据(命中 fragment)

- `commonsense`:匹配领域术语表

- `llm_judge`:LLM 判定"真实场景可能出现"

未通过的项写入"备注与遗留问题",不进入 artifacts。

#### 输出 MD 样例

```plaintext
---
stage: 3
stage_name: context_and_constraints
version: 1.0
upstream: 02_plan.md
downstream: 04_tests.md
domain: 纪检材料智能审查
created_at: 2026-04-20T13:00:00+08:00
created_by: agent-stage3
pass_gate: true
---

# Stage 3 · 仿真数据集构建 + 约束/干扰设计

## 摘要
为 4 道题建立了知识索引(共索引 22 个 fragment),设计 11 条约束项、6 条干扰项
(含 2 条 expert 陷阱)。业务真实性全部通过。第二层 Fallback 已触发
(源文档无 weak_points,全部走特性推导)。

## Fallback 触发情况
| 项 | 状态 | 说明 |
|----|------|------|
| weak_points 存在 | ❌ | 全部走特性推导 |

## 知识索引摘要
| 资产 | 切片数 | 覆盖的 TEST | 关键字池大小 |
|------|--------|------------|-------------|
| KB-001 党纪法规 | 3850 | TEST-001, TEST-003 | 860 |
| KB-002 总书记讲话 | 500 | TEST-003 | 180 |
| KB-003 理论文章 | 300 | TEST-002 | 120 |
| KB-004 实务测试集 | 80 | TEST-002, TEST-004 | 65 |

## 题目上下文设计

### TEST-001 (basic · 党纪条款精确查询)
- **主资产**:KB-001
- **核心 fragment**:FRAG-001-2345(2024 修订版第九十六条,违反八项规定精神)
- **关键字候选**:"八项规定精神"、"公款旅游"、"违反中央八项规定"
- **约束项**(2):
  1. C-001 · 必须引用 2024 修订版 [来源:时效性基础约束 · 验证:regulation_support]
  2. C-002 · 必须给出具体条款号 [来源:输出项规则 · 验证:commonsense]
- **干扰项**(0)
- **真实性验证**:2/2 通过

### TEST-002 (advanced · 跨文档类案参考)
- **主资产**:KB-003, KB-004
- **核心 fragment**:FRAG-003-77 / FRAG-004-12 / FRAG-004-34
- **关键字候选**:"利益输送"、"形式主义"、"类案比对"
- **约束项**(3):
  1. C-003 · 需整合理论文章与实务案例两类资产 [跨流程推导]
  2. C-004 · 跨 2+ 文档必须标注每条结论出处 [基础约束]
  3. C-005 · 时效性:优先引用近 3 年案例 [时效性推导]
- **干扰项**(1):
  1. I-001 · KB-004 中 1 条案例的"处理结果"口径与另一条冲突,需裁决 [规程冲突维度]
- **真实性验证**:4/4 通过

### TEST-003 (expert · 定性量纪综合决策)
- **主资产**:KB-001, KB-002, KB-004
- **核心 fragment**:FRAG-001-800 / FRAG-001-1200 / FRAG-002-45 / FRAG-004-60 (+ 6 个干扰 fragment)
- **关键字候选**:"四种形态"、"从严从重"、"主动交代"、"情节较轻"
- **约束项**(4):
  1. C-006 · 定性 + 条款 + 量纪档次三位一体结论 [输出项规则]
  2. C-007 · 跨 3 个资产必须交叉验证 [跨流程推导]
  3. C-008 · 需识别"主动交代"等从宽情节 [术语表命中]
  4. C-009 · 引用 2024 修订版 [时效性基础]
- **干扰项**(3):
  1. I-002 · 案情中混入"私车公用且足额交费"的无违纪情形 [陷阱型:看似合理]
  2. I-003 · KB-001 中 2018 旧版与 2024 新版对同一情形处分差异 [陷阱型:过时]
  3. I-004 · KB-004 中 1 条口径已过时的历史案例 [陷阱型:过时]
- **真实性验证**:7/7 通过

### TEST-004 (advanced · 文书纠错)
- **主资产**:KB-001, KB-004
- **核心 fragment**:FRAG-001-3421 / FRAG-004-77
- **关键字候选**:"处分决定"、"引用依据"、"文书规范"
- **约束项**(2):
  1. C-010 · 必须指出缺失的引用依据 [输出项规则]
  2. C-011 · 依据现行条例版本 [时效性基础]
- **干扰项**(1):
  1. I-005 · 待纠错文书中"处分档次"字段已填但与情节不符,需识别 [规程冲突维度]
- **真实性验证**:3/3 通过

## 结构化数据
{
  "fallback_status": {"weak_points_present": false},
  "knowledge_index": {
    "KB-001":{"total_fragments":3850,"covered_by":["TEST-001","TEST-003"]},
    "KB-002":{"total_fragments":500, "covered_by":["TEST-003"]},
    "KB-003":{"total_fragments":300, "covered_by":["TEST-002"]},
    "KB-004":{"total_fragments":80,  "covered_by":["TEST-002","TEST-004"]}
  },
  "test_contexts": [
    {
      "test_id":"TEST-001",
      "primary_asset":"KB-001",
      "fragments":[{"frag_id":"FRAG-001-2345","snippet":"2024 修订版第九十六条..."}],
      "keyword_pool":["八项规定精神","公款旅游","违反中央八项规定"],
      "constraints":[
        {"id":"C-001","text":"必须引用 2024 修订版","source":"时效性基础","verified_by":"regulation_support"},
        {"id":"C-002","text":"必须给出具体条款号","source":"输出项规则","verified_by":"commonsense"}
      ],
      "interferences":[],
      "realism_check":{"total":2,"passed":2}
    }
  ]
}


## 下一阶段校验清单
- [x] 每道 TEST 至少 1 个约束项
- [x] basic 题无干扰项,advanced 题 1 个,expert 题 ≥ 2 个含 1 陷阱
- [x] 每个约束/干扰通过 3 选 1 真实性验证
- [x] 每道 TEST 的 keyword_pool 至少 1 项
- [x] 每道 TEST 的 fragments 至少 1 个

## 备注与遗留问题
- KB-002 仅被 TEST-003 覆盖,若后续想增加"讲话精准定位"类题目,需回 Stage 2 重规划
- 丢弃 2 条干扰提案(LLM 生成但真实性检验未通过):"纪检委员可直接处分局级干部"、"巡察与巡视可合并"
```

#### Agent Prompt 模板

**System**:

> 你是业务知识工程师。给每道题配齐"知识后台":主参考资产、关键片段、

> 关键字池、约束项、干扰项,并做业务真实性验证。

> 

> 第二层 Fallback 原则:

> - 若 `capability_scope.weak_points` 存在,优先从其映射约束/干扰

> - 否则按流程特性 5 维度推导

> 

> 干扰密度硬规则:

> - basic 0 / advanced 1 / expert ≥ 2(含 1 陷阱型:含"冲突"|"过时"|"看似合理")

> 

> 真实性三选一通过:

> - 能在 KB 找到对应依据(regulation_support)

> - 匹配领域术语表(commonsense)

> - LLM 判定真实场景可能出现(llm_judge)

**User**:

```plaintext
<stage2_md>{{ 02_plan.md 全文 }}</stage2_md>
<knowledge_assets_samples>
KB-001 党纪法规: {{ 前 20 行 + 随机 20 行 }}
KB-002 总书记讲话: ...
KB-003 理论文章: ...
KB-004 实务测试集: ...
</knowledge_assets_samples>
<capability_scope>{{ weak_points,无则留空 }}</capability_scope>
<glossary>{{ Stage 1 领域术语表 }}</glossary>

输出 JSON Schema:

{
  "fallback_status":{"weak_points_present":"bool"},
  "knowledge_index":{"KB-xxx":{"total_fragments":0,"covered_by":["TEST-xxx"]}},
  "test_contexts":[{
    "test_id":"TEST-xxx",
    "primary_asset":"KB-xxx",
    "fragments":[{"frag_id":"FRAG-xxx","snippet":"string"}],
    "keyword_pool":["string"],
    "constraints":[{"id":"C-xxx","text":"string","source":"weak_points|时效性|跨流程|...","verified_by":"regulation_support|commonsense|llm_judge"}],
    "interferences":[{"id":"I-xxx","text":"string","trap":"bool","verified_by":"..."}],
    "realism_check":{"total":0,"passed":0}
  }]
}
```

---

### 4.6 Stage 4 · 题目 + 五阶段期望 + 评分细则 → 04_tests.md

#### 目标

把 Stage 3 的"知识后台"组装成**完整可执行的题目**:

- 用户提问 `prompt`(从 keyword_pool 扩写成口语化提问,嵌入约束/干扰)

- `reference_answer` 五阶段期望行为(基于 Stage 2 的流程步骤)

- `scoring_rubric` 评分细则(含致命扣分、一票否决)

- 难度自动校准(六维量化)

#### 输入

- `03_context.md`

- Stage 2 的 `processes` 与 Stage 1 的 `glossary`(用词统一)

#### 处理逻辑

**Step 4.1 — Prompt 组装**(对齐纪检业务"关键字→问题"做法)

对每道题:

1. 从 `keyword_pool` 选 1-3 个最具辨识度的关键字

1. 拼成自然口语(像真实纪检监察员会问的,**不是考试题**)

1. 显式嵌入所有约束项(如"请依据 **2024 修订版**")

1. 隐式嵌入所有干扰项(混入案情/背景,不标红)

1. expert 题加角色设定("我是纪检监察室的小李…")

参考 `0311构建.py::generate_question_stream` 的问题生成规则(禁封闭式、长度 20-300 字、问句结尾)。

**Step 4.2 — 五阶段期望行为生成**

基于 `source_process.steps`:

| 阶段 | 映射 |
| --- | --- |
| define_problem | intent = source_process.name + 显性诉求 + 隐含诉求(outputs 列表) |
| decompose | expected_steps = source_process.steps |
| solution | information_sources = test_contexts.fragments 的 snippet 列表 |
| execution | output_format = source_process.outputs 的结构化描述 |
| metacognition | source_annotation = fragment 出处 + 版本号 + 权限边界提示 |

**Step 4.3 — 评分细则生成**

- 每阶段分值权重固定:**2 / 2 / 3 / 2 / 1**(总 10 分)

- 每阶段至少 2 个 scoring_points

- `evidence_type` 分配:

  - 精确可验证(版本号、条款号) → `keyword_match`

  - 结构化输出特征(如"包含量纪档次字段") → `semantic_match`

  - 语义理解(如"是否正确识别意图") → `llm_judge`

- **fatal_deductions**(触发该题 0 分):

  - 编造条款(与 KB 交叉验证)

  - 引用错误版本(违反时效性约束)

  - 逻辑错误(答非所问)

- **veto_items**(触发整体不合格):

  - 泄露涉密案件/举报人信息

  - 输出违反政治纪律的内容

**Step 4.4 — 难度自校准**

```plaintext
scores = {
  "意图明确度":  {"单一":1, "多意图":2, "模糊/矛盾":3},
  "信息源数量":  [≤1→1, ≤3→2, ≥4→3],
  "约束项数量":  [≤1→1, ≤3→2, ≥4→3],
  "干扰项数量":  [0→1,   1→2,   ≥2→3],
  "输出复杂度":  [≤2→1, ≤4→2, ≥5→3],
  "五阶段深度":  [关键阶段≤3→1, ≤4→2, =5→3],
}
difficulty_score = mean(6 个分数)
label: ≤1.5 basic / ≤2.3 advanced / else expert
```

**一致性检查**:若自校准 label ≠ Stage 2 的 `assigned_difficulty`,写入"备注与遗留问题",由 Stage 5 裁决(不自行覆盖)。

#### 输出 MD 样例

```plaintext
---
stage: 4
stage_name: test_items
version: 1.0
upstream: 03_context.md
downstream: 05_report.md
domain: 纪检材料智能审查
created_at: 2026-04-20T15:00:00+08:00
created_by: agent-stage4
pass_gate: true
---

# Stage 4 · 题目 + 期望 + 评分细则

## 摘要
生成 4 道题,覆盖 4 个流程类型,总分 40。难度自校准与 Stage 2 规划全部一致。
平均约束密度 2.75,expert 题陷阱数 3。单题最长 prompt 186 字。

## 题目一览
| ID | 难度 | difficulty_score | 约束 | 干扰 | 主资产 | 对应流程 |
|----|------|-----------------|------|------|--------|---------|
| TEST-001 | basic | 1.2 | 2 | 0 | KB-001 | BP-001 |
| TEST-002 | advanced | 2.0 | 3 | 1 | KB-003+KB-004 | BP-004 |
| TEST-003 | expert | 2.8 | 4 | 3 | KB-001+KB-002+KB-004 | BP-003 |
| TEST-004 | advanced | 1.9 | 2 | 1 | KB-001+KB-004 | BP-006 |

## TEST-001 · 党纪条款精确查询(basic)

### prompt
> 我是纪检监察室的小李,最近接到群众举报某干部违反中央八项规定精神搞公款旅游,
> 麻烦帮我查一下 **2024 修订版**《中国共产党纪律处分条例》对这种情形的具体条款
> 和量纪档次。

### 约束与干扰
- 约束:2024 修订版 / 给出具体条款号
- 干扰:无

### 五阶段期望
| 阶段 | 期望 |
|------|------|
| 定义问题 | 识别意图为"党纪条款精确查询",隐含需求=条款号+量纪档次 |
| 拆解问题 | ①定位条例版本 ②检索八项规定相关条款 ③提取量纪档次 |
| 方案生成 | 应引用 KB-001 FRAG-001-2345(2024 修订版第九十六条) |
| 执行落地 | 输出条款原文 + 量纪档次表格,结构清晰 |
| 元认知 | 标注版本号(2024 修订版)与条款号;无权限边界问题 |

### 评分细则
| 阶段 | 满分 | 权重 | scoring_points |
|------|-----|-----|----------------|
| 定义问题 | 2.0 | 25% | 识别意图(1.0, llm_judge) · 识别最新版本需求(1.0, keyword_match:["2024","修订版"]) |
| 拆解问题 | 2.0 | 20% | 拆为条款定位+量纪档次(1.0, llm_judge) · 覆盖请求维度(1.0, llm_judge) |
| 方案生成 | 3.0 | 20% | 引用 2024 修订版(1.5, keyword_match) · 列出条款号(1.5, semantic_match:"第\\d+条") |
| 执行落地 | 2.0 | 25% | 输出结构清晰(1.0, llm_judge) · 完整列出量纪(1.0, llm_judge) |
| 元认知 | 1.0 | 10% | 标注版本号与条款号(1.0, keyword_match) |

### 致命扣分项 / 一票否决项
- **致命扣分**:引用错误版本 → 0 分;编造不存在的条款号 → 0 分
- **一票否决**:泄露举报人身份 → 不合格

## TEST-002 · 跨文档类案参考(advanced)

### prompt
> 我在查一个涉及利益输送的国企腐败案件,情节是相关人员通过关联公司转移利益。
> 帮我从理论文章和实务案例里找几个类似案子,对比他们的定性思路和处理方式,
> 近 3 年的案例优先。注意每一条结论都要**标注出处**。

### 约束与干扰
- 约束:跨 2 类资产整合 / 每条结论标注出处 / 近 3 年优先
- 干扰:KB-004 中有 1 条案例处理结果口径与另一条冲突,需要裁决

### 五阶段期望
| 阶段 | 期望 |
|------|------|
| 定义问题 | 识别意图为"跨文档类案参考",隐含需求=对比分析+出处标注 |
| 拆解问题 | ①确定检索主题 ②理论文章检索 ③实务案例检索 ④交叉比对 |
| 方案生成 | 应引用 FRAG-003-77 + FRAG-004-12 + FRAG-004-34,识别 FRAG-004 内部冲突并裁决 |
| 执行落地 | 结构化对比表(定性/条款/处理方式/出处)+ 冲突说明 |
| 元认知 | 每条结论显式引用 FRAG 编号;对冲突案例说明裁决依据 |

### 评分细则
| 阶段 | 满分 | scoring_points |
|------|-----|----------------|
| 定义问题 | 2.0 | 识别跨文档意图(1.0, llm_judge) · 识别"出处标注"约束(1.0, keyword_match:["出处","来源"]) |
| 拆解问题 | 2.0 | 拆解包含交叉比对步骤(1.0, llm_judge) · 覆盖两类资产(1.0, llm_judge) |
| 方案生成 | 3.0 | 引用 ≥ 2 个 FRAG(1.5, semantic_match) · 识别并裁决 FRAG-004 冲突(1.5, llm_judge) |
| 执行落地 | 2.0 | 结构化对比表(1.0) · 冲突案例显式说明(1.0) |
| 元认知 | 1.0 | 每条结论引用 FRAG 编号(1.0, keyword_match:["FRAG-","来源","出处"]) |

### 致命扣分项 / 一票否决项
- **致命扣分**:未识别 KB-004 内部冲突 → 0 分;结论无任何出处标注 → 0 分
- **一票否决**:错误定性导致"无违纪"反转 → 不合格

## TEST-003 · 定性量纪综合决策(expert)
### prompt
> 案情:我这里有个干部 A,在担任项目评审专家期间,接受过评审对象宴请和价值
> 3000 元的土特产礼品,后在调查中主动交代并退还了全部礼品。另外一个情节是
> 他曾用私家车接送评审对象,但有加油票据证明费用由本人承担。请你结合
> **2024 修订版纪律处分条例**、总书记关于"四种形态"的论述,以及类似实务
> 案例,给出这个案件的**定性结论、适用条款、量纪档次**,并说明你的推理依据。

### 约束与干扰
- 约束(4):定性+条款+档次三位一体 / 跨 3 资产交叉 / 识别"主动交代"从宽 / 2024 修订版
- 干扰(3):
  1. "私车公用且足额交费"看似违纪实则不构成(陷阱型)
  2. KB-001 中 2018 旧版对同情形的处分档次与 2024 新版不同(陷阱型)
  3. KB-004 中 1 条案例的处理口径已过时(陷阱型)

### 五阶段期望
| 阶段 | 期望 |
|------|------|
| 定义问题 | 识别多意图(定性+量纪+推理依据);识别"主动交代"为从宽情节 |
| 拆解问题 | ①分离案情要素 ②定性收受礼品 ③排除私车公用 ④综合四种形态 ⑤量纪档次 |
| 方案生成 | 引用 KB-001 2024 版相关条款 / KB-002 四种形态论述 / KB-004 类案,排除旧版与过时案例 |
| 执行落地 | 定性(违反廉洁纪律)+ 条款(修订版第几条)+ 档次(警告/严重警告...)+ 推理链 |
| 元认知 | 显式声明未采纳 2018 旧版;显式说明"私车公用"不构成违纪;标注类案过时 |

### 评分细则
| 阶段 | 满分 | scoring_points |
|------|-----|----------------|
| 定义问题 | 2.0 | 识别多意图(0.7) · 识别从宽情节(0.7) · 识别"私车公用"非违纪(0.6) |
| 拆解问题 | 2.0 | 拆解含四种形态应用(1.0) · 明确排除无关情节(1.0) |
| 方案生成 | 3.0 | 引用 2024 版(1.0) · 引用四种形态(1.0) · 识别并排除旧版/过时(1.0) |
| 执行落地 | 2.0 | 定性+条款+档次齐全(1.5) · 推理链完整(0.5) |
| 元认知 | 1.0 | 显式声明未采纳旧版/过时案例(1.0, llm_judge) |

### 致命扣分项 / 一票否决项
- **致命扣分**:
  - 将"私车公用且足额交费"判定为违纪 → 0 分(陷阱识别失败)
  - 引用 2018 旧版条款作为主依据 → 0 分
  - 遗漏"主动交代"从宽情节 → 0 分
- **一票否决**:编造不存在的条款或案例 → 不合格

## TEST-004 · 文书纠错(advanced)
...(结构同上,省略)

## 结构化数据
{
  "items": [
    {
      "test_id":"TEST-001",
      "difficulty":"basic",
      "difficulty_score":1.2,
      "domain":"党纪法规检索",
      "prompt":"我是纪检监察室的小李...",
      "context": {
        "user_role":"纪检监察员",
        "intent_type":"单一知识查询",
        "constraints":["2024 修订版","给出具体条款号"],
        "interference_items":[],
        "success_criteria":["正确识别查询意图","引用 2024 修订版","列出具体条款号和量纪档次"]
      },
      "reference": {
        "define_problem":{"intent_understanding":"党纪条款精确查询","implicit_needs":["条款号","量纪档次"],"problem_essence":"法规条款精确检索"},
        "decompose":{"expected_steps":["定位条例版本","检索八项规定相关条款","提取量纪档次"],"priority_ordering":"按条例章节顺序"},
        "solution":{"information_sources":["KB-001 FRAG-001-2345 2024 修订版第九十六条"],"cross_doc_integration":"单文档内"},
        "execution":{"output_format":"条款原文+量纪档次表","exception_handling":"版本歧义应主动说明"},
        "metacognition":{"source_annotation":"标注版本号与条款号","uncertainty_acknowledgment":"无需特别说明","boundary_awareness":"不涉及权限边界"}
      },
      "rubric": {
        "total_max_score":10,
        "stages":[
          {"stage_name":"定义问题","max_score":2.0,"weight":0.25,"scoring_points":[
            {"description":"识别查询意图","score":1.0,"evidence_type":"llm_judge"},
            {"description":"识别最新版本需求","score":1.0,"evidence_type":"keyword_match","keywords":["2024","修订版"]}
          ]},
          {"stage_name":"方案生成","max_score":3.0,"weight":0.20,"scoring_points":[
            {"description":"引用 2024 修订版","score":1.5,"evidence_type":"keyword_match","keywords":["2024"]},
            {"description":"列出具体条款号","score":1.5,"evidence_type":"semantic_match","keywords":["第\\d+条"]}
          ]}
        ],
        "fatal_deductions":[
          {"description":"引用错误版本条例","detection_rule":"llm_judge 检测版本正确性"},
          {"description":"编造不存在的条款","detection_rule":"与 KB-001 交叉验证"}
        ],
        "veto_items":[
          {"description":"泄露举报人身份信息","detection_rule":"敏感信息关键词扫描"}
        ]
      },
      "source_process":"BP-001",
      "inferred":false,
      "tags":["single_doc_query","regulation_lookup","exact_retrieval"]
    }
  ]
}


## 下一阶段校验清单
- [x] 每道 TEST 的 prompt 长度 20-300 字
- [x] 每道 TEST 的 reference 覆盖全部 5 阶段
- [x] 每道 TEST 的 rubric 总分 = 10
- [x] 每道 TEST 至少 1 条 fatal_deduction + 1 条 veto_item
- [x] 难度自校准与 Stage 2 的 assigned_difficulty 一致(不一致则列入"备注")
- [x] prompt 显式嵌入所有约束项,隐式嵌入所有干扰项

## 备注与遗留问题
- TEST-003 自校准值 2.8 已触 expert 上限,下一轮迭代可考虑拆成两题
```

#### Agent Prompt 模板

**System**:

> 你是评测题目设计师。基于 Stage 3 的知识后台,组装一道完整的业务题。

> 要像真实用户口吻的自然提问,**不要像考试题**。

> 

> 核心原则:

> 1. prompt 必须**显式**体现所有约束;**隐式**体现所有干扰(混入案情,不标红)

> 2. reference.decompose.expected_steps **必须**等于 source_process.steps

> 3. rubric 总分 = 10,分配严格遵守 **2/2/3/2/1**

> 4. 每题至少 1 条 fatal_deduction + 1 条 veto_item

> 5. evidence_type:精确可验证→keyword_match;结构化特征→semantic_match;语义理解→llm_judge

**User**:

```plaintext
<stage3_md>{{ 03_context.md 全文 }}</stage3_md>
<stage2_processes>{{ 02_plan.md 中 processes[] 原文 }}</stage2_processes>
<glossary>{{ Stage 1 领域术语表 }}</glossary>

输出 JSON Schema:

{
  "items":[{
    "test_id":"TEST-xxx",
    "difficulty":"basic|advanced|expert",
    "difficulty_score":"float",
    "domain":"string",
    "prompt":"string",
    "context":{"user_role":"string","intent_type":"string","constraints":["string"],"interference_items":["string"],"success_criteria":["string"]},
    "reference":{
      "define_problem":{"intent_understanding":"string","implicit_needs":["string"],"problem_essence":"string"},
      "decompose":{"expected_steps":["string"],"priority_ordering":"string"},
      "solution":{"information_sources":["string"],"cross_doc_integration":"string"},
      "execution":{"output_format":"string","exception_handling":"string"},
      "metacognition":{"source_annotation":"string","uncertainty_acknowledgment":"string","boundary_awareness":"string"}
    },
    "rubric":{
      "total_max_score":10,
      "stages":[{"stage_name":"string","max_score":"float","weight":"float","scoring_points":[{"description":"string","score":"float","evidence_type":"keyword_match|semantic_match|llm_judge","keywords":["string"]}]}],
      "fatal_deductions":[{"description":"string","detection_rule":"string"}],
      "veto_items":[{"description":"string","detection_rule":"string"}]
    },
    "source_process":"BP-xxx",
    "inferred":"bool",
    "tags":["string"]
  }]
}
```

---

### 4.7 Stage 5 · 验证 + benchmark → 05_report.md + dataset.{json,xlsx}

#### 目标

对 Stage 4 输出做多维度验证,出具验证报告,产出**最终可跑批的数据集**。

#### 输入

- `04_tests.md`

- `02_plan.md` 的 `coverage_matrix_plan`

- `01_understanding.md` 的 `success_metric`

#### 处理逻辑

**Step 5.1 — 5 设计原则验证**

| 原则 | 判定依据 |
| --- | --- |
| 真实性(real_encounter) | 用户画像命中 AND Stage 3 真实性验证通过 |
| 闭环性(five_stage_coverage) | reference 5 阶段均非空 |
| 可量化(quantifiable_criteria) | rubric 存在 AND 所有 scoring_point 可检测 |
| 区分度(discrimination) | 难度分数 ≥ 1.5 OR 约束+干扰 ≥ 2(先验) |
| 预测力(prediction_power) | tags 或 prompt 命中 Stage 1 的 success_metric 关键词 |

任一为 false → `passed=false`,详细记录原因。

**Step 5.2 — 覆盖矩阵对齐**

```plaintext
actual_matrix[TEST][stage] = 该 TEST 的 reference.{stage} 是否有 ≥ 1 个检验点
gap = blueprint_matrix(重点格) \ actual_matrix(覆盖格)
gap 非空 → 写入"盲区清单",severity 按 blueprint 重要度分级
```

**Step 5.3 — 先验区分度估计**

```plaintext
est_D = 0.4 * difficulty_score_normalized \
      + 0.2 * constraint_density_normalized \
      + 0.3 * interference_density_normalized \
      + 0.1 * cross_asset_degree_normalized

分级:
  est_D >= 0.40  优秀
  0.30 - 0.40   合格
  0.20 - 0.30   待改进
  < 0.20        淘汰
```

**Step 5.4 — 独立性评分**

对任意两道题计算:

- 主资产重合度(Jaccard)

- keyword_pool 重合度

- source_process 步骤重合度

`pair_overlap = 0.5*asset + 0.3*keyword + 0.2*step`

`independence_score = 1 - max(pair_overlap)` · 期望 ≥ 0.5

**Step 5.5 — benchmark**

1. `dataset.json`:items[] + 全局元信息(domain / version / 难度分布 / 覆盖矩阵),可直接送跑批引擎

1. `dataset.xlsx`:**严格对齐纪检样例**(`datasets/test_agent_2/.../广东电网_文档抽取_党纪法规测试集_20250604_增加实际答案_result.xlsx`)的列结构:

| Sheet | 列 |
| --- | --- |
| 主表 | 问题 / 答案 / 实际答案(留空) / 来源文档 / 来源片段 / 标记结果(留空) / 结果(留空) |
| 评分细则 | test_id / 阶段 / 满分 / 得分点 / evidence_type / keywords |
| 约束干扰 | test_id / 类型 / 内容 / 来源维度 / 真实性验证 |
| 元信息 | version / domain / total_items / difficulty_distribution / created_at |

映射规则:

- `问题` ← `item.prompt`

- `答案` ← reference 五阶段拼接的可读文本("期望答案模板")

- `来源文档` ← test_context.primary_asset 对应的文件名

- `来源片段` ← test_context.fragments 的 snippet 按"片段N:"拼接(对齐纪检样例格式)

1. `traceability.json`:每道题的溯源链 `TEST → BP → FEAT → UG → KB → FRAG`

#### 输出 MD 样例

```plaintext
---
stage: 5
stage_name: validation_and_finalize
version: 1.0
upstream: 04_tests.md
downstream: 最终产物
domain: 纪检材料智能审查
created_at: 2026-04-20T17:00:00+08:00
created_by: agent-stage5
pass_gate: true
---

# Stage 5 · 验证报告 + benchmark

## 摘要
4 道题全部通过 5 设计原则验证。覆盖矩阵发现 1 处低严重度盲区
(TEST-001 · 拆解问题偏薄),已备注。先验区分度:2 优秀 / 1 合格 / 1 待改进。
独立性评分 0.72(达标)。数据集已打包为 dataset.json + dataset.xlsx。

## 5 设计原则验证
| TEST | 真实性 | 闭环性 | 可量化 | 区分度 | 预测力 | passed |
|------|--------|--------|--------|--------|--------|--------|
| TEST-001 | ✓ | ✓ | ✓ | ✓(1.2 偏低,但约束足) | ✓ | ✓ |
| TEST-002 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-003 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-004 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 覆盖矩阵对齐(实际 vs 蓝图)
|  | 定义问题 | 拆解问题 | 方案生成 | 执行落地 | 元认知 |
|--|---------|---------|---------|---------|--------|
| TEST-001 | 蓝图=重点✓实际=覆盖✓ | 蓝图=常规·实际=⚠️偏薄 | ✓ | ✓ | ✓ |
| TEST-002 | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-003 | ✓ | ✓ | ✓ | ✓ | ✓ |
| TEST-004 | ✓ | ✓ | ✓ | ✓ | ✓ |

**盲区清单**
- TEST-001 · 拆解问题:expected_steps 仅 3 步,建议后续补充异常分支(severity=low)

## 先验区分度估计
| TEST | est_D | 分级 | 主要贡献项 |
|------|-------|------|------------|
| TEST-001 | 0.28 | 待改进 | 难度偏低,但作为 basic 入门题保留 |
| TEST-002 | 0.42 | 优秀 | 跨资产 + 1 干扰 |
| TEST-003 | 0.55 | 优秀 | 高难度 + 3 陷阱 |
| TEST-004 | 0.35 | 合格 | 约束清晰,1 干扰 |

## 独立性评分
- 最高重合对:TEST-001 × TEST-003(主资产都含 KB-001),overlap = 0.28
- `independence_score = 0.72` ✓(≥ 0.5 达标)

## 最终产物清单
- `dataset.json` — 标准化数据集(跑批引擎直接消费)
- `dataset.xlsx` — 兼容纪检样例(问题/答案/实际答案/来源文档/来源片段/标记结果/结果)
- `05_report.md` — 本报告
- `dataset_supplementary/`
  - `rubrics.json`(评分细则独立文件,便于跑批加载)
  - `coverage_matrix.json`
  - `traceability.json`

## 结构化数据
{
  "validation": {
    "by_principle": {
      "TEST-001":{"real_encounter":true,"five_stage_coverage":true,"quantifiable_criteria":true,"discrimination":true,"prediction_power":true,"passed":true,"notes":"难度偏低但约束充分"}
    },
    "coverage_gaps": [
      {"test_id":"TEST-001","stage":"拆解问题","severity":"low","hint":"补充异常分支"}
    ],
    "discrimination_estimate": {
      "TEST-001":{"est_D":0.28,"grade":"待改进"},
      "TEST-002":{"est_D":0.42,"grade":"优秀"},
      "TEST-003":{"est_D":0.55,"grade":"优秀"},
      "TEST-004":{"est_D":0.35,"grade":"合格"}
    },
    "independence_score": 0.72,
    "most_overlapping_pair":["TEST-001","TEST-003"]
  },
  "dataset_meta": {
    "version":"1.0",
    "domain":"纪检材料智能审查",
    "business_goal":"材料审查准确率 ≥ 90%,语义检索召回率 ≥ 85%",
    "created_at":"2026-04-20",
    "total_items":4,
    "difficulty_distribution":{"basic":1,"advanced":2,"expert":1},
    "source_channel":"design_doc"
  }
}

## 最终验收清单
- [x] 所有 TEST 的 passed=true
- [x] 覆盖矩阵盲区 severity=high 数 = 0
- [x] 独立性评分 ≥ 0.5
- [x] dataset.json 通过 JSON Schema 校验
- [x] dataset.xlsx 的前 2 行人工抽检通过

## 备注与遗留问题
- TEST-001 区分度先验偏低(0.28),建议跑一轮真实评测再决定是否迭代
- 若未来扩充到 ≥ 6 道题,建议重新计算独立性评分
```

#### Agent Prompt 模板(仅用于验证部分,打包部分由代码完成)

**System**:

> 你是评测数据集质控专员,对 Stage 4 的题目集做多维度验证,出具验证报告。

> 

> 对疑问项**不擅自修改题目**,记入"备注与遗留问题"由人工决策。

**User**:

```plaintext
<stage4_md>{{ 04_tests.md 全文 }}</stage4_md>
<coverage_blueprint>{{ 02_plan.md 中的 coverage_matrix_plan }}</coverage_blueprint>
<success_metric>{{ 01_understanding.md 中的 success_metric }}</success_metric>

输出 JSON Schema:

{
  "validation":{
    "by_principle":{"TEST-xxx":{"real_encounter":"bool","five_stage_coverage":"bool","quantifiable_criteria":"bool","discrimination":"bool","prediction_power":"bool","passed":"bool","notes":"string"}},
    "coverage_gaps":[{"test_id":"TEST-xxx","stage":"string","severity":"low|mid|high","hint":"string"}],
    "discrimination_estimate":{"TEST-xxx":{"est_D":"float","grade":"优秀|合格|待改进|淘汰"}},
    "independence_score":"float",
    "most_overlapping_pair":["TEST-xxx","TEST-xxx"]
  },
  "dataset_meta":{"version":"string","domain":"string","total_items":0,"difficulty_distribution":{},"source_channel":"design_doc|gui|code|user_log"}
}
```

---

### 4.8 Pipeline 编排与工程落地

#### 编排器伪代码

```plaintext
def run_pipeline(inputs: AgentInput, work_dir: str) -> FinalArtifacts:
    """
    5 阶段串行执行,支持断点续跑
    """
    stages = [
        (1, "business_understanding",  stage1_run),
        (2, "process_and_plan",        stage2_run),
        (3, "context_and_constraints", stage3_run),
        (4, "test_items",              stage4_run),
        (5, "validation_and_finalize", stage5_run),
    ]

    for stage_no, stage_name, stage_fn in stages:
        md_path = f"{work_dir}/{stage_no:02d}_{stage_name}.md"

        # 断点续跑:已完成且校验通过则跳过
        if os.path.exists(md_path) and pass_gate(md_path):
            continue

        upstream_md = read_upstream_md(stage_no, work_dir)
        raw_inputs  = select_raw_inputs(stage_no, inputs)

        # 规则代码 + LLM Prompt 协作
        result = stage_fn(upstream_md=upstream_md, raw_inputs=raw_inputs)

        write_md(md_path, result)  # 含 frontmatter / 正文表格 / JSON artifacts / 校验清单

        # 门槛校验
        if not pass_gate(md_path):
            raise StageGateFailure(
                f"Stage {stage_no} 下一阶段校验清单未全通过,请根据 MD 末尾'备注与遗留问题'人工处理"
            )

    return finalize_artifacts(work_dir)  # 打包 dataset.{json,xlsx} + 附件


def pass_gate(md_path: str) -> bool:
    """检查 MD frontmatter 的 pass_gate 字段 + 校验清单是否全部 [x]"""
    fm, body = parse_md(md_path)
    checklist = extract_checklist(body, section="下一阶段校验清单")
    return fm.get("pass_gate") is True and all(c.checked for c in checklist)
```

## 五、Fallback机制详细设计

### 5.1 双层Fallback链

```plaintext
第一层Fallback：流程定义不存在
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
触发条件：design_docs.business_processes 为空或不存在

Fallback逻辑：
┌─────────────────────────────────────────────────────────┐
│ 从PRD推导流程                                            │
│                                                         │
│ 推导公式：流程 = 用户角色 × 核心功能 × 业务目标          │
│                                                         │
│ 推导步骤：                                              │
│ 1. 提取PRD的用户群体（谁用系统）                        │
│ 2. 提取Architecture的核心功能（系统提供什么）            │
│ 3. 提取PRD的业务目标（预期产出是什么）                  │
│ 4. 用户群体需求 × 对应功能 → 推导业务流程              │
│ 5. 为每个流程推导：触发条件、输出、步骤、参与者        │
└─────────────────────────────────────────────────────────┘

输出：List[BusinessProcess]（标注 inferred=True）
```

```plaintext
第二层Fallback：能力边界定义不存在
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
触发条件：design_docs.capability_scope 为空或不存在

Fallback逻辑：
┌─────────────────────────────────────────────────────────┐
│ 从流程特性推导约束项和干扰项                            │
│                                                         │
│ 约束项推导维度：                                        │
│ 1. 跨流程依赖 → 需要信息整合能力                      │
│ 2. 规程多版本 → 需要版本区分能力                      │
│ 3. 参与者层级 → 需要权限边界意识                      │
│ 4. 输出项数量 → 需要闭环交付能力                      │
│ 5. 触发类型 → 需要模糊需求理解能力                    │
│                                                         │
│ 干扰项推导维度：                                        │
│ 1. 规程规则冲突                                        │
│ 2. 规程多版本并存                                      │
│ 3. 流程异常情况                                        │
│ 4. 模糊触发条件                                        │
│ 5. 跨部门角色混淆                                      │
│                                                         │
│ 业务真实性验证（必须执行）                              │
└─────────────────────────────────────────────────────────┘

输出：constraints[] + interference[]（已验证业务真实性）
```

### 5.2 Fallback决策流程

```plaintext
输入层次               Fallback机制
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SystemDesignDocs       
│
├── prd                  → 必须存在（业务目标）
│   └───────────────────────────────────────── ✗ 不可缺失
│
├── architecture         → 必须存在（核心功能）
│   └───────────────────────────────────────── ✗ 不可缺失
│
├── business_processes   
│   ├── 存在             → 直接提取
│   └── 不存在           → 从PRD+Architecture推导 ⬅ 第一层Fallback
│
├── capability_scope
│   ├── weak_points存在  → 直接映射约束/干扰
│   └── 不存在           → 从流程特性推导 ⬅ 第二层Fallback
│
└── domain_knowledge     → 可选（填充细节）
```

---

## 六、设计决策记录

| 决策ID | 原始设计 | 修正后设计 | 修正原因 |
| --- | --- | --- | --- |
| D001 | 输入来源=历史数据 | 输入来源=设计文档 | 评测应验证设计意图 |
| D002 | 用户占比→题目难度 | 覆盖范围≠难度 | 两者无因果关系 |
| D003 | 固定3个题目 | 题目数量动态决定 | 通用框架不应固定 |
| D004 | 固定流程类别 | 动态提取分类 | 不同系统有不同流程 |
| D005 | 约束项固定模板 | 动态推导+Fallback | 设计文档可能无weak_points |
| D006 | 流程定义必须存在 | 双层Fallback | 设计文档可能无流程定义 |

---

## 七、Agent Prompt模板

```plaintext
# 题目生成Agent Prompt模板

你是一个"评测设计师"，负责基于智能系统设计文档生成统一题。

## 输入
你将收到：
- SystemDesignDocs（PRD、Architecture、可选的business_processes和capability_scope）
- DomainKnowledge（规程/制度样本，可选）
- BusinessGoal（业务目标）

## Fallback机制

### 第一层Fallback：流程定义不存在
如果设计文档没有business_processes：
- 从PRD业务目标+用户群体+Architecture核心功能推导流程
- 推导公式：流程 = 用户角色 × 核心功能 × 业务目标
- 推导步骤：触发条件、输出、步骤、参与者

### 第二层Fallback：能力边界定义不存在
如果设计文档没有capability_scope或weak_points：
- 从流程特性推导约束项和干扰项
- 推导维度：跨流程依赖、规程多版本、参与者层级、输出项数量、触发类型

## 核心原则

1. **覆盖范围≠题目难度**：题目数量=流程类型数量，动态决定
2. **业务闭环**：每个题目都走完五阶段
3. **难度调节**：通过约束项/干扰项调节复杂度
4. **业务真实性验证**：所有推导必须验证业务真实性

## 输出
输出N个统一题（JSON格式）+ 五阶段期望行为 + 验证报告
```

---

## 八、题目质量保障体系

### 8.1 难度量化定义

当前难度标签 "basic" / "advanced" / "expert" 需要客观的判定标准，而非主观标注。

#### 难度量化矩阵

| 维度 | Basic (赋值1) | Advanced (赋值2) | Expert (赋值3) |
| --- | --- | --- | --- |
| 意图明确度 | 单一、明确意图 | 多意图或需推断 | 模糊/矛盾/需澄清 |
| 信息源数量 | 单文档内 | 2-3个文档跨域 | 4+文档+隐含知识 |
| 约束项数量 | 0-1个 | 2-3个 | 4+个(含相互冲突) |
| 干扰项数量 | 0个 | 1个 | 2+个 |
| 输出复杂度 | 直接回答 | 结构化方案 | 多步骤可执行计划 |
| 五阶段深度 | 重点考察1-3阶段 | 全阶段覆盖可容错 | 全阶段+高标准 |

#### 难度计算公式

```plaintext
def calculate_difficulty(test: UnifiedTest) -> tuple[float, str]:
    """
    基于题目要素自动计算难度等级
    
    返回: (difficulty_score, difficulty_label)
    """
    scores = []
    
    # 1. 意图明确度
    if test.intent_type in ["单一知识查询", "明确指令"]:
        scores.append(1)
    elif test.intent_type in ["多意图查询", "隐含推断"]:
        scores.append(2)
    else:  # 模糊/矛盾/需澄清
        scores.append(3)
    
    # 2. 信息源数量
    source_count = len(test.reference_answer.solution_expected.information_sources)
    scores.append(1 if source_count <= 1 else 2 if source_count <= 3 else 3)
    
    # 3. 约束项数量
    constraint_count = len(test.constraints)
    scores.append(1 if constraint_count <= 1 else 2 if constraint_count <= 3 else 3)
    
    # 4. 干扰项数量
    interference_count = len(test.interference_items)
    scores.append(1 if interference_count == 0 else 2 if interference_count == 1 else 3)
    
    # 5. 输出复杂度（基于输出项数量和格式要求）
    output_count = len(test.primary_stages)
    scores.append(1 if output_count <= 2 else 2 if output_count <= 4 else 3)
    
    # 6. 五阶段深度
    critical_stages = count_critical_stages(test)
    scores.append(1 if critical_stages <= 3 else 2 if critical_stages <= 4 else 3)
    
    # 计算均值
    difficulty_score = sum(scores) / len(scores)
    
    # 映射到难度标签
    if difficulty_score <= 1.5:
        label = "basic"
    elif difficulty_score <= 2.3:
        label = "advanced"
    else:
        label = "expert"
    
    return difficulty_score, label
```

### 8.2 有效性保证机制

#### A. 内容有效性（Content Validity）

**覆盖矩阵验证**：生成题目集后，自动构建覆盖矩阵，确保无盲区。

```plaintext
def validate_content_validity(tests, processes):
    """
    检查题目集是否覆盖所有业务流程和五阶段
    
    输出覆盖矩阵：
    
                定义问题  拆解问题  方案生成  执行落地  元认知
    流程类型A    ✓(T-001)  ✓(T-001)  ✓(T-001)  ✓(T-001)  ✓(T-001)
    流程类型B    ✓(T-002)  ✓(T-002)  ✓(T-002)  ✓(T-002)  ✗ ← 盲区！
    流程类型C    ✓(T-003)  ✓(T-003)  ✓(T-003)  ✓(T-003)  ✓(T-003)
    """
    matrix = {}
    stages = ["定义问题", "拆解问题", "方案生成", "执行落地", "元认知"]
    
    for test in tests:
        process_type = test.source_process
        if process_type not in matrix:
            matrix[process_type] = {s: None for s in stages}
        
        for stage in stages:
            if stage_is_covered(test, stage):
                matrix[process_type][stage] = test.test_id
    
    # 检查盲区
    gaps = []
    for process, coverage in matrix.items():
        for stage, test_id in coverage.items():
            if test_id is None:
                gaps.append(f"{process} × {stage}")
    
    return matrix, gaps
```

**逆向推导检验**：对每道题反问"这道题考察了什么？"

```plaintext
def reverse_validate(test):
    """
    逆向推导：如果无法明确回答以下问题，则题目设计无效
    
    1. 这道题考察的是哪个业务流程？ → source_process 必须非空
    2. 这道题重点考察五阶段中的哪些阶段？ → 至少3个阶段有明确期望
    3. 这道题的区分点在哪里？ → 至少1个约束项或干扰项
    """
    issues = []
    
    if not test.source_process:
        issues.append("无法明确关联到具体业务流程")
    
    covered_stages = count_stages_with_expectations(test)
    if covered_stages < 3:
        issues.append(f"仅覆盖{covered_stages}个阶段，不足3个")
    
    if len(test.constraints) + len(test.interference_items) == 0:
        issues.append("无约束项和干扰项，缺乏区分度")
    
    return issues
```

#### B. 表面有效性（Face Validity）

- 3位业务专家独立评审每道题

- 评审问题："这道题是否像一个真实的业务问题？该用户在实际工作中会这样提问吗？"

- 一致性门槛：**Fleiss' Kappa >= 0.6** 方可采用该题，否则需修改

#### C. 预测有效性（Predictive Validity）

- 长期建设项：收集评测得分与上线后业务指标（人工转接率、解决率）的对应关系

- 通过 Pearson 相关系数验证"评测分高 → 业务表现好"的假设

- 初期可用专家经验判断替代，在积累3轮以上评测数据后启用统计验证

### 8.3 区分度保证机制

#### A. 事前设计（题目生成时的硬性规则）

```plaintext
def ensure_discrimination_by_design(test):
    """
    题目生成时的区分度硬性规则
    """
    rules = []
    
    # 规则1：每道题必须包含至少1个约束项或干扰项
    if len(test.constraints) + len(test.interference_items) == 0:
        rules.append("FAIL: 无约束项和干扰项，无法区分'真理解'和'简单检索'")
    
    # 规则2：不同难度等级的约束密度应有梯度
    #   basic: 0-1个约束+0个干扰
    #   advanced: 2-3个约束+1个干扰
    #   expert: 4+个约束+2+个干扰
    density = len(test.constraints) + len(test.interference_items)
    if test.difficulty == "expert" and density < 4:
        rules.append("WARN: expert级题目的约束/干扰密度不足")
    
    # 规则3：expert级题目必须包含至少1个"陷阱"
    #   陷阱 = 看似合理但实际错误的信息 / 过时的规程版本 / 角色权限边界
    if test.difficulty == "expert":
        has_trap = any(
            "过时" in i or "冲突" in i or "误导" in i 
            for i in test.interference_items
        )
        if not has_trap:
            rules.append("WARN: expert级题目缺少陷阱设计")
    
    return rules
```

#### B. 事后验证（跑批完成后的统计检验）

```plaintext
def calculate_discrimination_index(test_id, all_system_results):
    """
    项目区分度指数 D 计算
    
    用同一套题测至少3个不同水平的系统：
    1. 将系统按总分排序
    2. 取前27%为高分组(H)，后27%为低分组(L)
    3. D = H组在该题的得分率 - L组在该题的得分率
    
    判定标准：
    - D >= 0.4: 优秀题（高区分度）
    - 0.3 <= D < 0.4: 合格题
    - 0.2 <= D < 0.3: 待改进题
    - D < 0.2: 淘汰题（无区分度）
    
    注意：样本量 < 5个系统时，直接比较最高分与最低分系统的差异
    """
    
    # 按总分排序
    sorted_results = sorted(all_system_results, key=lambda r: r.total_score)
    n = len(sorted_results)
    
    if n < 5:
        # 小样本：直接比较最高分和最低分
        h_score = sorted_results[-1].get_test_score(test_id)
        l_score = sorted_results[0].get_test_score(test_id)
        max_score = sorted_results[0].get_test_max_score(test_id)
        D = (h_score - l_score) / max_score
    else:
        # 标准27%分组
        cutoff = max(1, int(n * 0.27))
        h_group = sorted_results[-cutoff:]
        l_group = sorted_results[:cutoff]
        
        h_rate = mean([r.get_test_score(test_id) for r in h_group]) / max_score
        l_rate = mean([r.get_test_score(test_id) for r in l_group]) / max_score
        D = h_rate - l_rate
    
    return D
```

#### C. 题目迭代机制

每次评测后，根据区分度和难度指标对题目进行分级管理：

| 分级 | 判定标准 | 处理 |
| --- | --- | --- |
| 优质题 | D >= 0.3 且通过有效性验证 | 进入正式题库，用于标准化比对 |
| 待改进题 | 0.2 <= D < 0.3 | Agent自动优化（增加约束项/调整干扰项），下轮重新验证 |
| 淘汰题 | D < 0.2 | 标记为淘汰，不再使用 |

### 8.4 信度保证机制

| 信度类型 | 方法 | 门槛 |
| --- | --- | --- |
| 评分者间信度 | 同一份输出由LLM Judge和人工独立打分，计算ICC | ICC >= 0.7 |
| 重测信度 | 同一系统间隔一周重测 | 得分波动 <= 10% |
| 内部一致性 | 同一难度等级多道题之间 | Cronbach's alpha >= 0.7 |
| LLM Judge稳定性 | 同一份回答评判3次取均值 | 方差 > 1分 → 标记"需人工复核" |

---

## 九、跑批评测流程

### 9.1 跑批架构

### 9.2 执行流程

```plaintext
def run_batch_evaluation(dataset_path, system_config):
    """
    跑批评测主流程
    """
    
    # 1. 加载数据集
    dataset = load_dataset(dataset_path)
    
    # 2. 环境快照（确保可复现）
    snapshot = {
        "dataset_version": dataset.meta.version,
        "system_version": system_config.version,
        "model_version": system_config.model_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # 3. 并发执行每道题
    results = []
    for item in dataset.items:
        # 按难度设置超时：basic 60s, advanced 120s, expert 300s
        timeout = {"basic": 60, "advanced": 120, "expert": 300}[item.difficulty]
        
        result = execute_single_test(
            test_item=item,
            system_config=system_config,
            timeout=timeout
        )
        
        # 逐条追加写入（断点续跑支持）
        append_result_to_jsonl(result, output_path)
        results.append(result)
    
    # 4. 三层评判
    scored_results = evaluate_results(results, dataset)
    
    # 5. 生成报告
    report = generate_evaluation_report(scored_results, dataset, snapshot)
    
    return report
```

### 9.3 三层评判管道

#### 第一层：规则匹配（自动，100%覆盖）

```plaintext
def rule_based_evaluation(system_output, rubric):
    """
    规则匹配：处理有明确对错标准的评判项
    """
    scores = {}
    
    for stage in rubric.stages:
        for point in stage.scoring_points:
            if point.evidence_type == "keyword_match":
                # 关键词/正则匹配
                matched = all(kw in system_output for kw in point.keywords)
                scores[point.description] = point.score if matched else 0
    
    # 红线检测：安全合规问题的关键词扫描
    for veto in rubric.veto_items:
        if veto_detected(system_output, veto.detection_rule):
            return {"veto_triggered": True, "reason": veto.description}
    
    return scores
```

#### 第二层：LLM-as-Judge（自动，覆盖主观评价）

```plaintext
LLM_JUDGE_PROMPT = """
你是一位AI系统评测专家。请根据以下评分标准，对被测系统的回答进行五阶段评分。

## 题目
{test_prompt}

## 期望行为
{reference_answer}

## 被测系统实际输出
{system_output}

## 评分标准
{scoring_rubric}

## 评分规则
1. 严格按五阶段逐项评分，不要笼统打分
2. 每个扣分必须给出具体原因
3. 关注过程而非仅关注结果
4. 致命扣分项：严重逻辑错误/数据造假/关键步骤缺失 → 该题0分

请输出JSON格式：
{
  "scores": {
    "定义问题": {"score": X, "max": X, "details": "..."},
    "拆解问题": {"score": X, "max": X, "details": "..."},
    "方案生成": {"score": X, "max": X, "details": "..."},
    "执行落地": {"score": X, "max": X, "details": "..."},
    "元认知": {"score": X, "max": X, "details": "..."}
  },
  "deductions": [
    {"stage": "...", "reason": "...", "points": X}
  ],
  "fatal_issues": [],
  "total": X,
  "total_max": 10
}
"""

def llm_judge_evaluation(system_output, test_item, n_samples=3):
    """
    LLM-as-Judge评判
    
    关键：多次采样取均值，方差大的标记为需人工复核
    """
    scores = []
    for _ in range(n_samples):
        result = call_llm_judge(
            prompt=LLM_JUDGE_PROMPT.format(
                test_prompt=test_item.prompt,
                reference_answer=test_item.reference,
                system_output=system_output,
                scoring_rubric=test_item.rubric
            )
        )
        scores.append(result)
    
    avg_score = mean([s["total"] for s in scores])
    variance = var([s["total"] for s in scores])
    
    return {
        "avg_score": avg_score,
        "variance": variance,
        "needs_human_review": variance > 1.0,  # 方差>1分需人工复核
        "details": scores[0]  # 使用第一次的详细评分
    }
```

#### 第三层：人工审核（抽样，质量保障）

| 抽样策略 | 覆盖范围 | 说明 |
| --- | --- | --- |
| 100%审核 | expert 级题目 | 高难度题的评判需要领域专家把关 |
| 100%审核 | LLM Judge 方差>1分的case | 评判不稳定的结果必须人工确认 |
| 20%随机抽检 | basic/advanced 级题目 | 校准自动评判的整体准确性 |

每轮评测后计算 **"人机一致率"** = LLM Judge与人工评审打分差异<=1分的比例，作为评判系统本身的质量指标。

### 9.4 统计分析方法

| 分析方法 | 用途 | 适用场景 |
| --- | --- | --- |
| 描述性统计 | 总分均值、中位数、标准差、各维度得分分布 | 每轮评测的基础数据 |
| 项目分析 | 逐题的难度指数P和区分度D | 题目质量评估和迭代 |
| ICC（组内相关系数） | 评分者间信度 | 验证LLM Judge和人工评审一致性 |
| Bootstrap置信区间 | 小样本下的得分置信区间估计 | 3题设计的置信度补偿 |
| 配对t检验/Wilcoxon | 两个系统版本间差异的统计显著性 | 版本迭代效果验证 |
| 效应量（Cohen's d） | 差异的实际意义大小 | 不只看p值，还看改进幅度 |

**注意**：本框架设计为N道题（N=流程类型数量），当N较小时（如3-6题），不应过度依赖参数检验，建议使用Bootstrap重采样估计置信区间。

---

## 十、评测报告设计

### 10.1 报告整体结构（四层）

```plaintext
AI组件系统功能评测报告
├── 第一层：管理摘要（1页）
│   ├── 评测结论：优秀/合格/不合格 + 总分(X/30)
│   ├── 核心业务指标预测：自动解决率、人工转接率
│   ├── 上线建议：立即上线 / 灰度上线 / 暂缓上线
│   └── 与上一轮评测的delta对比（如有）
│
├── 第二层：能力维度分析（2-3页）
│   ├── 五阶段雷达图：各阶段加权得分率
│   ├── 难度梯度表现：basic/advanced/expert 各级别得分率
│   ├── 能力矩阵热力图：业务流程类型 x 五阶段 得分分布
│   └── 关键短板识别：得分率最低的Top 3能力维度
│
├── 第三层：逐题详情（每题1-2页）
│   ├── 题目信息：prompt、难度、约束项、干扰项
│   ├── 五阶段逐步评分表（含扣分原因）
│   ├── 系统实际输出 vs 期望行为对比
│   ├── 关键证据：截图/日志/输出片段
│   └── 致命问题标记（如有）
│
└── 第四层：改进建议（1-2页）
    ├── 按优先级排序的短板清单
    ├── 每个短板的具体改进方向
    ├── 历史趋势对比（多轮评测时）
    └── 下次评测建议关注点
```

### 10.2 管理摘要页模板

```plaintext
┌──────────────────────────────────────────────────────────┐
│              AI组件系统功能评测报告                         │
│              [系统名称] · [评测日期] · [评测版本]            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  综合评级：优秀 (S)            总分：27 / 30              │
│                                                          │
│  ┌──────────┬──────────┬──────────┐                      │
│  │ 基础题    │ 进阶题    │ 高难度   │                      │
│  │ 9.5/10   │ 9.0/10   │ 8.5/10  │                      │
│  └──────────┴──────────┴──────────┘                      │
│                                                          │
│  核心业务指标预测                                          │
│  ────────────────────────────────                        │
│  · 预估自动解决率：≥ 90%                                   │
│  · 预估人工转接率：≤ 10%                                   │
│  · 预估用户满意度：≥ 85%                                   │
│                                                          │
│  上线建议：建议立即上线，全面推广                             │
│                                                          │
│  关键发现                                                 │
│  ────────────────────────────────                        │
│  · 强项：意图理解准确，方案生成质量高                         │
│  · 短板：跨文档信息整合时偶有遗漏                            │
│  · 安全：未触发任何红线项                                   │
│  · 对比上轮：总分+2分，方案生成阶段提升最大                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 10.3 五阶段评分详情表（每题）

| 阶段 | 满分 | 权重 | 得分 | 得分率 | 扣分说明 |
| --- | --- | --- | --- | --- | --- |
| 定义问题 | 2.0 | 25% | 2.0 | 100% | — |
| 拆解问题 | 2.0 | 20% | 1.5 | 75% | 遗漏"巡检记录填写规范"的拆解步骤 |
| 方案生成 | 3.0 | 20% | 3.0 | 100% | — |
| 执行落地 | 2.0 | 25% | 2.0 | 100% | — |
| 元认知 | 1.0 | 10% | 1.0 | 100% | — |
| 合计 | 10.0 | 100% | 9.5 | 95% |   |

致命扣分项：无  

一票否决项：无

### 10.4 可视化组件

| 图表 | 用途 | 报告位置 |
| --- | --- | --- |
| 五阶段雷达图 | 5个维度的能力轮廓，一目了然看出"强在哪弱在哪" | 管理摘要 / 能力分析 |
| 能力矩阵热力图 | 行=流程类型, 列=五阶段, 颜色=得分，精准定位薄弱环节 | 能力维度分析 |
| 瀑布图 | 从满分到最终得分的扣分路径分解 | 逐题详情 |
| 难度-得分散点图 | X轴=难度等级, Y轴=得分，展示能力衰减曲线 | 能力维度分析 |
| 漏斗图 | 五阶段逐步衰减，展示从"理解问题"到"执行落地"的能力衰减 | 能力维度分析 |
| 历史趋势折线图 | 多轮评测的总分/各维度分趋势 | 改进建议 |

### 10.5 评级与上线决策标准

| 总分 | 评级 | 预期业务表现 | 上线建议 |
| --- | --- | --- | --- |
| 25-30 | 优秀 (S) | 独立处理90%+日常事务，人工转接≤12% | 立即上线，全面推广 |
| 18-24 | 合格 (A) | 稳定处理60%-80%标准事务，人工转接≤20% | 修复核心问题后灰度上线 |
| < 18 | 不合格 (F) | 仅支持基础查询，人工转接>35% | 暂缓上线，需重新优化 |

**一票否决**：任何题目触发安全合规红线（泄露敏感数据、编造法规条文、违反数据权限等）→ 无论总分多少，整体判定为**不合格**。

### 10.6 报告输出格式

报告同时输出两种格式：

- **JSON格式**：结构化数据，用于系统间对接、历史数据存储、可视化渲染

- **Markdown格式**：人类可读，用于文档归档和分享

---

## 十一、审核要点

请审核以下关键设计决策：

1. **四通道输入来源**是否覆盖主要的评测场景？各通道的最小输入集定义是否合理？

1. **Phase 0 输入预处理**是否有遗漏的检查项？

1. **双层Fallback机制**是否完整覆盖所有可能的输入缺失场景？

1. **动态题目数量**逻辑是否合理（题目数量=流程类型数量）？

1. **难度量化矩阵**的6个维度是否足够？阈值划分（1.5/2.3）是否需要调整？

1. **有效性/区分度/信度**三维度保证机制是否可操作？

1. **三层评判管道**（规则匹配→LLM Judge→人工抽检）的分工是否合理？

1. **评测报告四层结构**是否满足不同读者（管理层/技术团队/评审专家）的需求？

1. **评分细则（Rubric）**的 `evidence_type` 设计（keyword_match / semantic_match / llm_judge）是否覆盖主要评判场景？

1. **一票否决机制**的触发条件是否明确？是否有遗漏的安全红线？

---

**审核状态**：待审核

## 会议整理

### 0417会议

1. 每个阶段的输出物定格式

1. 文档维护

1. 输入文档   业务流程 数据集 评测   输出MD报告

### 0420会议

1. 仿真数据

1. 仿真数据设计

1. stage3： 仿真数据集的构建 + 约束/干扰设计

1. stage1： 数据资产 不明确    —> 业务支撑材料

1. stage5： banchmark 

1. 小步骤的细节再完善