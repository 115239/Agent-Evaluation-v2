# 题目生成Agent设计文档_Sin

**版本**：V2.1  
**日期**：2026-04-18  
**状态**：待审核  
**更新说明**：V2.1重构为8阶段MD工件流水线，新增阶段文档契约、阶段回退机制、过程工件输出定义  

当前优先实现设计文档通道，先将 PRD/设计文档 -> 阶段工件 MD -> 最终评测数据集 的全流程跑通。
---

## 一、概述

### 1.1 设计目标

题目生成Agent负责基于智能系统设计文档，自动生成评测统一题。

**核心职责**：

- 从设计文档抽取业务模型与端到端业务流程
- 将流程抽象为可评测的场景族，并为每类场景生成代表性样本
- 为每个阶段输出标准化 MD 工件，供下游 Agent 继续处理
- 生成统一题、五阶段期望行为、评分细则和质检结果
- 发布可直接送入跑批评测引擎的数据集

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **从设计意图出发** | 评测应验证系统是否达成了设计意图，而非验证历史数据pattern |
| **覆盖范围≠题目难度** | 题目数量由场景族数量动态决定，场景族来自流程地图抽象；难度由约束项/干扰项调节 |
| **双层Fallback机制** | 流程定义不存在→从PRD推导；能力边界不存在→从流程特性推导 |
| **业务闭环** | 每个题目都走完完整的业务流程 |
| **业务真实性验证** | 所有推导必须验证是否符合真实业务场景 |

---

## 二、输入定义

### 2.1 四通道输入来源

题目生成Agent支持四种输入通道，适应不同评测场景：

| 通道 | 输入物 | 适用场景 | 说明 |
|------|--------|---------|------|
| **设计文档通道** | PRD + Architecture + 流程定义 | 上线前评测（标准路径） | 最完整的信息来源，优先使用 |
| **GUI挖掘通道** | 系统URL + 用户凭证 + 页面截图 | 已有系统但缺少文档 | 通过Playwright自动遍历挖掘业务流程 |
| **代码挖掘通道** | 源码仓库 + API接口文档 | 后端AI组件评测 | 通过AST解析和API扫描提取功能点 |
| **用户日志通道** | 生产环境query log + 高频/失败case | 上线后持续评测 | 从真实用户行为中挖掘评测场景 |

### 2.2 各通道最小输入集

#### 设计文档通道（标准路径）

```
必须：PRD（含业务目标、用户群体、核心功能）
必须：Architecture（含核心功能定义列表）
可选：业务流程定义（无 → 从PRD推导，见Fallback机制）
可选：能力边界定义（无 → 从流程特性推导，见Fallback机制）
可选：领域知识库（规程/制度文档，用于填充题目细节）
```

#### GUI挖掘通道

```
必须：系统访问URL + 登录凭证
必须：业务目标描述（1-3句话，明确"系统上线后要解决什么问题"）
可选：核心页面/功能列表（无则Agent自动遍历发现）
```

#### 代码挖掘通道

```
必须：源码目录路径或Git仓库地址
必须：入口文件/主要API端点标识
可选：API文档（Swagger/OpenAPI spec）
```

#### 用户日志通道

```
必须：query log文件（含用户输入、系统输出、时间戳）
必须：业务目标描述
可选：人工标注的失败case（用于定向生成高区分度题目）
```

### 2.3 输入数据结构

```python
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

### 2.4 Stage 0: 输入预处理（新增）

在题目生成主流程（Stage 1-7）之前，必须执行输入预处理：

```python
def preprocess_input(agent_input: AgentInput) -> InputAssessmentReport:
    """
    Stage 0: 输入预处理
    
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

```python
class AgentOutput:
    """
    题目生成Agent的输出
    """
    
    # 阶段化过程工件（00-07共8份MD）
    stage_artifacts: List[StageArtifactMeta]
    
    # 最终数据集包
    final_dataset_package: FinalDatasetPackage
    
    # 验证报告
    validation_report: ValidationReport
    
    # 流程提炼报告
    process_inference_report: ProcessInferenceReport
    
    # 质量度量（新增：数据集整体质量指标）
    quality_metrics: QualityMetrics


class StageArtifactMeta:
    """阶段工件元信息"""
    stage_id: str
    stage_name: str
    doc_type: str
    doc_path: str
    version: str
    status: str         # "draft" / "approved" / "blocked"
    upstream_docs: List[str]
    confidence: float   # 0-1


class FinalDatasetPackage:
    """最终交付包：Markdown工件 + JSON数据集"""
    final_markdown_path: str
    dataset_json_path: str
    dataset_meta: DatasetMeta
    unified_tests: List[UnifiedTest]
    reference_answers: List[ReferenceAnswer]
    scoring_rubrics: List[ScoringRubric]
    traceability_links: Dict[str, Dict[str, str]]


class ProcessMapDoc:
    """02_process_map.md 的结构化对象"""
    processes: List[BusinessProcess]
    evidence_index: Dict[str, List[str]]
    unresolved_questions: List[str]


class ScenarioInventoryDoc:
    """03_scenario_inventory.md 的结构化对象"""
    scenario_types: List[dict]
    omitted_processes: List[str]


class SampleBlueprintDoc:
    """04_sample_blueprint.md 的结构化对象"""
    sample_blueprints: List[dict]
    realism_rules: List[str]


class ReferenceSpecDoc:
    """05_reference_spec.md 的结构化对象"""
    references: List[ReferenceAnswer]
    rubrics: List[ScoringRubric]


class DatasetQCDoc:
    """06_dataset_qc.md 的结构化对象"""
    coverage_matrix: dict
    duplication_risks: List[str]
    release_decision: str


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

```python
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

```python
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

### 3.4 评分细则结构（新增）

```python
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

### 3.5 质量度量结构（新增）

```python
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

### 3.6 标准化阶段工件 Markdown 格式

题目生成Agent在最终 JSON 之外，还必须输出 8 份串行阶段工件。每个工件既给人看，也给下一个 Agent 阶段消费，因此格式固定。

#### 文件命名约定

| Stage | 文件名 | 作用 |
|------|--------|------|
| `00` | `00_input_assessment.md` | 输入完整性、质量和冲突审计 |
| `01` | `01_business_model.md` | 业务目标、角色、对象、能力边界建模 |
| `02` | `02_process_map.md` | 端到端业务流程地图 |
| `03` | `03_scenario_inventory.md` | 测试场景族与代表流程选择 |
| `04` | `04_sample_blueprint.md` | 样本蓝图、题面、约束和干扰 |
| `05` | `05_reference_spec.md` | 五阶段期望行为和评分标准 |
| `06` | `06_dataset_qc.md` | 覆盖性、独立性、真实性和发布门禁 |
| `07` | `07_final_dataset.md` | 最终数据集说明和导出结果 |

#### 通用 Frontmatter 契约

```markdown
---
doc_type: process_map
stage_id: "02"
stage_name: "流程地图生成"
version: "v2.1"
source_channel: "design_doc"
upstream_docs:
  - "01_business_model.md"
raw_inputs:
  - "prd.md"
  - "architecture.md"
status: "approved"
confidence: 0.84
open_issues:
  - "采购审批环节是否存在线下补录待确认"
next_stage: "03_scenario_inventory.md"
---

## 输入摘要

## 核心结论

## 结构化产物

## 风险与歧义

## 质量检查

## 下一阶段使用说明
```

#### 阶段文档的结构化载荷要求

| 文件 | `## 结构化产物` 必含字段 |
|------|------------------------|
| `00_input_assessment.md` | `required_inputs_status`、`quality_score`、`conflicts`、`missing_evidence`、`go_no_go` |
| `01_business_model.md` | `business_goal`、`target_users`、`core_capabilities`、`business_objects`、`success_metrics`、`system_boundaries` |
| `02_process_map.md` | `processes[]`，其中每个流程含 `process_id`、`name`、`actors`、`trigger`、`inputs`、`steps`、`outputs`、`exceptions`、`source_evidence`、`inferred` |
| `03_scenario_inventory.md` | `scenario_types[]`，其中每类场景含 `scenario_type_id`、`covered_processes`、`scenario_pattern`、`risk_focus`、`difficulty_hint`、`selected_representative_process` |
| `04_sample_blueprint.md` | `sample_blueprints[]`，其中每个样本含 `sample_id`、`prompt_draft`、`persona`、`business_context`、`input_materials`、`constraints`、`interference_items`、`success_criteria`、`source_process` |
| `05_reference_spec.md` | `references[]`，其中每项含 `sample_id`、`five_stage_expectations`、`rubric`、`fatal_deductions`、`veto_items`、`evidence_requirements` |
| `06_dataset_qc.md` | `coverage_matrix`、`difficulty_distribution`、`duplication_risks`、`business_realism_issues`、`revision_actions`、`release_decision` |
| `07_final_dataset.md` | `dataset_meta`、`items_summary`、`export_paths`、`batch_eval_mapping`、`traceability_links` |

### 3.7 标准化数据集输出格式

Stage 7 从 `07_final_dataset.md` 导出的 JSON 应为以下格式，可直接送入跑批评测引擎：

```json
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

## 四、核心逻辑流程

### 4.1 总体执行流

题目生成Agent不再直接从原始 PRD 跳到最终题目集，而是按 8 个串行阶段推进。每个阶段只产出一份标准化 MD，下一阶段优先只读上一阶段 MD 的固定结构，再按需回看原始资料。

```
原始输入
PRD / Architecture / DomainKnowledge
        │
        ▼
Stage 0 输入审计
        ▼
00_input_assessment.md
        │
        ▼
Stage 1 业务建模
        ▼
01_business_model.md
        │
        ▼
Stage 2 流程地图生成
        ▼
02_process_map.md
        │
        ▼
Stage 3 测试场景抽象
        ▼
03_scenario_inventory.md
        │
        ▼
Stage 4 样本蓝图设计
        ▼
04_sample_blueprint.md
        │
        ▼
Stage 5 五阶段参考标准生成
        ▼
05_reference_spec.md
        │
        ▼
Stage 6 数据集质检与编排
        ▼
06_dataset_qc.md
        │
        ▼
Stage 7 数据集发布
        ▼
07_final_dataset.md + dataset.json
```

### 4.2 主编排器逻辑

```python
def run_dataset_generation_pipeline(agent_input: AgentInput) -> AgentOutput:
    """
    8阶段串行流水线
    """

    artifacts = []

    stage0 = run_stage_0_input_assessment(agent_input)
    artifacts.append(stage0.meta)
    ensure_stage_gate_passed(stage0, stop_on_block=True)

    stage1 = run_stage_1_business_modeling(stage0.doc_path, agent_input)
    artifacts.append(stage1.meta)
    ensure_stage_gate_passed(stage1)

    stage2 = run_stage_2_process_mapping(stage1.doc_path, agent_input)
    artifacts.append(stage2.meta)
    ensure_stage_gate_passed(stage2)

    stage3 = run_stage_3_scenario_inventory(stage2.doc_path)
    artifacts.append(stage3.meta)
    ensure_stage_gate_passed(stage3)

    stage4 = run_stage_4_sample_blueprint(stage3.doc_path, agent_input)
    artifacts.append(stage4.meta)
    ensure_stage_gate_passed(stage4)

    stage5 = run_stage_5_reference_spec(stage4.doc_path, agent_input)
    artifacts.append(stage5.meta)
    ensure_stage_gate_passed(stage5)

    stage6 = run_stage_6_dataset_qc(stage4.doc_path, stage5.doc_path)
    artifacts.append(stage6.meta)
    ensure_stage_gate_passed(stage6)

    stage7 = run_stage_7_publish(stage6.doc_path, stage5.doc_path)
    artifacts.append(stage7.meta)

    return AgentOutput(
        stage_artifacts=artifacts,
        final_dataset_package=stage7.package,
        validation_report=stage6.validation_report,
        process_inference_report=stage2.process_inference_report,
        quality_metrics=stage6.quality_metrics,
    )
```

### 4.3 阶段串联总表

| Stage | 上游输入 | 核心任务 | 输出工件 | 放行门槛 |
|------|---------|---------|---------|---------|
| `0` 输入审计 | 原始设计文档 | 判断输入是否足以启动 | `00_input_assessment.md` | `go_no_go = go` |
| `1` 业务建模 | `00` + 原始文档 | 抽取目标、角色、对象、边界 | `01_business_model.md` | 业务目标、用户角色、核心能力完整 |
| `2` 流程地图生成 | `01` + 原始文档 | 提取或推导端到端流程 | `02_process_map.md` | 至少1个可执行闭环流程 |
| `3` 测试场景抽象 | `02` | 形成场景族并选代表流程 | `03_scenario_inventory.md` | 每类场景可映射到流程 |
| `4` 样本蓝图设计 | `03` + 领域知识 | 设计题干、约束、干扰和成功标准 | `04_sample_blueprint.md` | 每个样本具备完整题面蓝图 |
| `5` 五阶段参考标准 | `04` | 生成期望行为和评分标准 | `05_reference_spec.md` | 五阶段均可判分 |
| `6` 数据集质检 | `04` + `05` | 覆盖性、独立性、真实性、难度平衡 | `06_dataset_qc.md` | `release_decision = approved` |
| `7` 数据集发布 | `06` + `05` | 导出最终 Markdown 和 JSON | `07_final_dataset.md` | 可供跑批引擎直接消费 |

### 4.4 Stage 0: 输入审计

**目标**：在进入建模之前，明确输入是否足够、是否冲突、是否需要人工补充。

**输入**：
- 原始 PRD
- Architecture 文档
- 可选的流程定义、能力边界、领域知识库

**核心动作**：
- 检查必须字段是否存在
- 评估 PRD 是否可操作，而非只有概念描述
- 检查 PRD、Architecture、补充材料之间是否互相矛盾
- 判断设计文档通道的推荐提取策略
- 生成缺失信息列表和补充优先级

**`00_input_assessment.md` 的结构化产物格式**：
- `required_inputs_status`
- `quality_score`
- `conflicts`
- `missing_evidence`
- `suggestions`
- `go_no_go`

**推进门槛**：
- `prd` 和 `architecture` 均存在
- `quality_score >= 0.6`
- 关键冲突项全部被记录
- `go_no_go = go`

### 4.5 Stage 1: 业务建模

**目标**：把原始设计文档压缩为业务语义底座，让后续流程推导不再直接依赖杂乱原文。

**输入**：
- `00_input_assessment.md`
- 原始 PRD / Architecture / 可选知识库

**核心动作**：
- 统一业务目标和验收指标
- 抽取目标用户、关键角色、协同关系
- 建模核心能力、业务对象、输入资料、输出产物
- 划定系统边界、权限边界、不可替代的人工环节
- 标注证据来源，避免后续“模型脑补”

**`01_business_model.md` 的结构化产物格式**：
- `business_goal`
- `target_users`
- `core_capabilities`
- `business_objects`
- `success_metrics`
- `system_boundaries`
- `human_in_the_loop_points`

**推进门槛**：
- 业务目标、核心能力、目标用户三者形成闭环
- 每个核心能力都有原始文档证据
- 系统边界和人工边界被显式写出

### 4.6 Stage 2: 流程地图生成

**目标**：抽取或推导可用于评测的端到端业务流程，而不是只罗列功能点。

**输入**：
- `01_business_model.md`
- 原始流程定义（若存在）
- 原始 PRD / Architecture

**核心动作**：
- 优先直接提取设计文档中已有的业务流程定义
- 若无流程定义，则基于 `用户角色 × 核心能力 × 业务目标` 推导流程
- 将流程统一成 `触发 -> 输入 -> 步骤 -> 输出 -> 异常` 的标准形态
- 为每个流程记录证据来源、推导痕迹和置信度
- 合并高度相似流程，避免后续题目冗余

**`02_process_map.md` 的结构化产物格式**：
- `processes[]`
- 每个 `process` 固定包含：
  - `process_id`
  - `name`
  - `goal`
  - `actors`
  - `preconditions`
  - `trigger`
  - `inputs`
  - `steps`
  - `outputs`
  - `exceptions`
  - `dependencies`
  - `source_evidence`
  - `inferred`
  - `confidence`

**推进门槛**：
- 至少存在 1 个完整流程
- 每个流程都必须同时包含触发、步骤、输出
- 推导流程必须标注 `inferred = true`
- 平均流程置信度达到设定阈值，否则按第五章回退

### 4.7 Stage 3: 测试场景抽象

**目标**：把“流程列表”提升为“测试场景族”，形成后续样本设计的覆盖骨架。

**输入**：
- `02_process_map.md`

**核心动作**：
- 从流程中抽取触发模式、输出模式、风险模式、协作模式
- 将相近流程聚为同一测试场景族，而不是简单做标签分类
- 为每个场景族选取一个代表流程
- 为代表流程给出选择依据：业务重要性、覆盖面、风险度、复杂度
- 记录未被覆盖的边缘流程，供 Stage 6 做覆盖审计

**`03_scenario_inventory.md` 的结构化产物格式**：
- `scenario_types[]`
- 每个 `scenario_type` 固定包含：
  - `scenario_type_id`
  - `scenario_pattern`
  - `covered_processes`
  - `risk_focus`
  - `difficulty_hint`
  - `selected_representative_process`
  - `selection_rationale`

**推进门槛**：
- 每类场景都可映射回一个或多个流程
- 每个代表流程都给出可解释的选择依据
- 场景总数 = 首轮计划题目数

### 4.8 Stage 4: 样本蓝图设计

**目标**：把场景族转换为可生成题目的样本蓝图，定义题面、约束、干扰和成功标准。

**输入**：
- `03_scenario_inventory.md`
- 领域知识库
- 可选的能力边界定义

**核心动作**：
- 基于代表流程生成用户身份、业务上下文、输入材料和题干草案
- 若 `capability_scope.weak_points` 存在，则映射为约束项和干扰项
- 若不存在，则从流程复杂度、异常处理、跨流程依赖推导约束项和干扰项
- 执行业务真实性验证，剔除“只为难模型、不像真实业务”的设计
- 给出成功标准和预期交付物

**`04_sample_blueprint.md` 的结构化产物格式**：
- `sample_blueprints[]`
- 每个 `sample_blueprint` 固定包含：
  - `sample_id`
  - `prompt_draft`
  - `persona`
  - `business_context`
  - `input_materials`
  - `constraints`
  - `interference_items`
  - `success_criteria`
  - `source_process`
  - `realism_evidence`

**推进门槛**：
- 每个样本都有完整题干草案
- 每个样本至少绑定 1 个来源流程
- 每个样本具备成功标准
- 约束和干扰已通过真实性校验

### 4.9 Stage 5: 五阶段参考标准生成

**目标**：把样本蓝图转换为可直接评测的参考标准，而不是仅生成“参考答案”。

**输入**：
- `04_sample_blueprint.md`

**核心动作**：
- 为每个样本生成五阶段期望行为
- 生成逐阶段评分点和证据类型
- 补齐致命扣分项和一票否决项
- 标明哪些标准来自规则匹配，哪些需要 LLM Judge
- 校验每一道题是否具备“可评分、可追责、可复核”的属性

**`05_reference_spec.md` 的结构化产物格式**：
- `references[]`
- 每个 `reference` 固定包含：
  - `sample_id`
  - `five_stage_expectations`
  - `rubric`
  - `fatal_deductions`
  - `veto_items`
  - `evidence_requirements`

**推进门槛**：
- 五阶段都有明确期望行为
- 每个评分点都有证据类型
- 致命扣分和 veto 条件可操作、可解释

### 4.10 Stage 6: 数据集质检与编排

**目标**：在发布前对整套数据集做覆盖、独立性、真实性和难度的总体验证。

**输入**：
- `04_sample_blueprint.md`
- `05_reference_spec.md`

**核心动作**：
- 构建流程 x 五阶段覆盖矩阵
- 检查题目间重叠度，避免“换皮同题”
- 校验难度分布是否失衡
- 检查每题是否真实、闭环、可量化、有区分度
- 根据质检结果决定通过、回退重做或阻断发布

**`06_dataset_qc.md` 的结构化产物格式**：
- `coverage_matrix`
- `difficulty_distribution`
- `duplication_risks`
- `business_realism_issues`
- `revision_actions`
- `release_decision`

**推进门槛**：
- 无关键覆盖盲区
- 无高风险重复题
- `release_decision = approved`

### 4.11 Stage 7: 数据集发布

**目标**：基于质检通过的样本和参考标准，输出最终可交付包。

**输入**：
- `06_dataset_qc.md`
- `05_reference_spec.md`

**核心动作**：
- 生成最终 `dataset_meta`
- 组装 `items[]`
- 导出 `07_final_dataset.md`
- 导出跑批引擎可用的标准 JSON
- 写入 `traceability_links`，使每个样本都能追溯到流程、场景和质检结论

**`07_final_dataset.md` 的结构化产物格式**：
- `dataset_meta`
- `items_summary`
- `export_paths`
- `batch_eval_mapping`
- `traceability_links`

**推进门槛**：
- JSON 可直接被跑批引擎加载
- 每题都有可回溯链路
- 最终 Markdown 与 JSON 内容一致

### 4.12 业务真实性验证（贯穿 Stage 4-6）

```python
def verify_business_realism(items, domain_knowledge):
    """
    验证标准：
    1. 该约束/干扰/题面是否可能出现在真实业务中
    2. 是否符合业务常识和角色职责
    3. 是否有规程、制度或历史案例支撑
    """

    verified_items = []

    for item in items:
        if has_real_regulation_support(item, domain_knowledge):
            verified_items.append(item)
        elif matches_business_commonsense(item, domain_knowledge):
            verified_items.append(item)
        elif likely_in_real_scenario(item, domain_knowledge):
            verified_items.append(item)

    return verified_items
```

---

## 五、Fallback与回退机制详细设计

### 5.1 双层Fallback链

| 触发位置 | 缺失项 | 处理策略 | 回填到的工件 |
|---------|-------|---------|-------------|
| Stage 2 | `business_processes` 不存在 | 从 `01_business_model.md` 推导流程 | `02_process_map.md` |
| Stage 4 / 5 | `capability_scope` 或 `weak_points` 不存在 | 从流程与场景风险推导约束、干扰和评分重点 | `04_sample_blueprint.md` / `05_reference_spec.md` |

#### 第一层Fallback：流程定义不存在

```python
def infer_processes_from_business_model(business_model_doc, design_docs):
    """
    推导公式：流程 = 用户角色 × 核心能力 × 业务目标
    """

    processes = []

    for user in business_model_doc.target_users:
        for capability in business_model_doc.core_capabilities:
            if capability_supports_user_goal(user, capability, business_model_doc.business_goal):
                processes.append(
                    build_inferred_process(
                        user_role=user["role"],
                        capability=capability,
                        business_goal=business_model_doc.business_goal,
                        source_evidence=collect_evidence(user, capability, design_docs),
                    )
                )

    return merge_similar_processes(processes)
```

**推导要求**：
- 每个推导流程都要写入 `source_evidence`
- 每个推导流程都要标记 `inferred = true`
- 每个推导流程都要补出 `trigger / steps / outputs / exceptions`

#### 第二层Fallback：能力边界不存在

```python
def infer_test_stressors(process, scenario_type, domain_knowledge):
    """
    从流程复杂度和风险点推导约束项、干扰项和评分重点
    """

    constraints = []
    interference_items = []
    scoring_focus = []

    if process.cross_process_dependency == "跨流程":
        constraints.append("需整合多个流程的信息，形成完整方案")
        scoring_focus.append("跨流程信息整合")

    if has_multiple_regulation_versions(domain_knowledge, process):
        constraints.append("需引用最新规程版本，排除已废止版本")
        interference_items.append("规程有新旧版本并存，需正确引用最新版")
        scoring_focus.append("版本识别")

    if len(process.actors) > 1:
        interference_items.append("流程涉及多个角色，责任边界需明确")
        scoring_focus.append("角色边界和权限意识")

    if has_exception_handling_steps(process):
        interference_items.append("流程中存在异常情况，需给出备选处理方案")
        scoring_focus.append("异常处理")

    if has_fuzzy_trigger(process):
        constraints.append("需合理推断模糊需求，或主动追问澄清")
        scoring_focus.append("需求澄清")

    return constraints, interference_items, scoring_focus
```

**推导要求**：
- 先推导，再做真实性验证
- 约束项、干扰项、评分重点必须可追溯到流程风险
- 不允许为了提高难度而加入不真实的“陷阱”

### 5.2 阶段回退决策流程

双层 Fallback 解决“输入缺失”，阶段回退解决“输出不达标”。后者是 8 阶段流水线真正可执行的关键。

| 当前阶段 | 典型失败原因 | 回退到 | 处理动作 |
|---------|-------------|-------|---------|
| Stage 0 | 必须输入缺失、关键冲突未解决 | 停止 | 输出补充建议，不进入下游阶段 |
| Stage 1 | 业务目标、角色、能力未闭环 | Stage 0 | 补输入或重新解释输入冲突 |
| Stage 2 | 流程置信度不足、流程不闭环 | Stage 1 | 重新抽取业务对象、角色和能力证据 |
| Stage 3 | 场景族无法覆盖核心流程 | Stage 2 | 重做流程合并或代表流程选择 |
| Stage 4 | 题面不真实、蓝图过泛、成功标准缺失 | Stage 3 | 重构场景定义，收紧代表流程 |
| Stage 5 | 五阶段不可判分、rubric 不可操作 | Stage 4 | 重写题面和成功标准 |
| Stage 6 | 覆盖盲区、题目重复、难度失衡 | Stage 3 / 4 / 5 | 按问题类型回退重做 |
| Stage 7 | Markdown 与 JSON 不一致、字段不兼容 | Stage 6 | 回到质检阶段重新发布 |

```python
def resolve_stage_failure(stage_id, issue_type):
    rollback_map = {
        "missing_required_input": "stop",
        "business_model_not_closed": "stage_0",
        "low_process_confidence": "stage_1",
        "scenario_not_covering_processes": "stage_2",
        "sample_not_realistic": "stage_3",
        "rubric_not_scorable": "stage_4",
        "dataset_qc_failed": "stage_3_or_4_or_5",
        "publish_inconsistent": "stage_6",
    }
    return rollback_map[issue_type]
```

### 5.3 工件状态机

每份阶段工件必须在 frontmatter 中声明状态，供编排器和人工审核共同使用。

| 状态 | 含义 | 下一步动作 |
|------|------|-----------|
| `draft` | 阶段已产出，但尚未通过门禁 | 允许修改，不允许下游消费 |
| `approved` | 阶段通过，可进入下一阶段 | 写入 `next_stage` |
| `blocked` | 阶段失败，需要补输入或回退 | 写入 `open_issues` 和 `rollback_to` |

只有 `approved` 状态的工件，才允许作为下游阶段的正式输入。

---

## 六、设计决策记录

| 决策ID | 原始设计 | 修正后设计 | 修正原因 |
|--------|---------|-----------|---------|
| D001 | 输入来源=历史数据 | 输入来源=设计文档 | 评测应验证设计意图 |
| D002 | 用户占比→题目难度 | 覆盖范围≠难度 | 两者无因果关系 |
| D003 | 端到端一次性生成最终题库 | 改为8阶段串行工件流水线 | 需要可追溯、可回退、可审计 |
| D004 | 中间产物为自由文本 | 统一为 YAML Frontmatter + 固定章节 | 方便下游Agent稳定消费 |
| D005 | 固定流程类别 | 从流程地图抽象场景族 | 流程列表不是可直接评测的对象 |
| D006 | 约束项固定模板 | 动态推导 + Fallback | 设计文档可能无 weak_points |
| D007 | 流程定义必须存在 | 双层Fallback | 设计文档可能无流程定义 |
| D008 | 最终只保留JSON | 过程工件 + JSON双输出 | 兼顾跑批执行和过程复盘 |

---

## 七、Agent Prompt模板

```markdown
# 题目生成Agent Prompt模板（编排器）

你是一个"评测数据集编排Agent"，负责将业务PRD/设计文档逐阶段转换为评测数据集。

## 工作方式

1. 严格按 Stage 0-7 串行执行，不允许跳阶段。
2. 每个阶段只输出一份 Markdown 工件，文件名固定：
   `00_input_assessment.md` -> `07_final_dataset.md`
3. 每个阶段的 Markdown 必须包含：
   - YAML frontmatter
   - `## 输入摘要`
   - `## 核心结论`
   - `## 结构化产物`
   - `## 风险与歧义`
   - `## 质量检查`
   - `## 下一阶段使用说明`
4. 只有当当前工件 `status = approved` 时，才允许进入下一阶段。
5. 如遇输入缺失，优先使用双层 Fallback；如遇阶段门禁失败，执行阶段回退。
6. 所有结论必须尽量引用原始文档证据，不允许无依据补全。

## 输入

你将收到：
- `SystemDesignDocs`（PRD、Architecture、可选的 `business_processes` 和 `capability_scope`）
- `DomainKnowledge`（规程/制度/案例样本，可选）
- `BusinessGoal`（业务目标）
- `current_stage`
- `upstream_docs`

## 双层Fallback

### 第一层Fallback：流程定义不存在
如果设计文档没有 `business_processes`：
- 基于 `01_business_model.md` 推导流程
- 推导公式：`流程 = 用户角色 × 核心能力 × 业务目标`
- 每个推导流程必须补出：触发条件、输入、步骤、输出、异常分支、证据来源

### 第二层Fallback：能力边界不存在
如果设计文档没有 `capability_scope` 或 `weak_points`：
- 从流程复杂度和场景风险推导约束项、干扰项和评分重点
- 推导维度：跨流程依赖、规程多版本、参与者层级、异常处理、模糊触发条件
- 所有推导结果必须通过业务真实性验证

## 各阶段最低输出要求

- Stage 0：必须得出 `go_no_go`
- Stage 1：必须完成业务目标、用户角色、核心能力闭环
- Stage 2：必须输出标准化 `processes[]`
- Stage 3：必须输出 `scenario_types[]` 和代表流程
- Stage 4：必须输出可落题的 `sample_blueprints[]`
- Stage 5：必须输出五阶段期望行为和 `rubric`
- Stage 6：必须输出 `release_decision`
- Stage 7：必须输出 `07_final_dataset.md` 和最终 JSON 导出路径

## 最终目标

输出一套可追溯的阶段工件，以及一份可直接送入跑批评测引擎的数据集 JSON。
```

---

## 八、题目质量保障体系（新增）

### 8.1 难度量化定义

当前难度标签 "basic" / "advanced" / "expert" 需要客观的判定标准，而非主观标注。

#### 难度量化矩阵

| 维度 | Basic (赋值1) | Advanced (赋值2) | Expert (赋值3) |
|------|--------------|-----------------|----------------|
| **意图明确度** | 单一、明确意图 | 多意图或需推断 | 模糊/矛盾/需澄清 |
| **信息源数量** | 单文档内 | 2-3个文档跨域 | 4+文档+隐含知识 |
| **约束项数量** | 0-1个 | 2-3个 | 4+个(含相互冲突) |
| **干扰项数量** | 0个 | 1个 | 2+个 |
| **输出复杂度** | 直接回答 | 结构化方案 | 多步骤可执行计划 |
| **五阶段深度** | 重点考察1-3阶段 | 全阶段覆盖可容错 | 全阶段+高标准 |

#### 难度计算公式

```python
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

```python
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

```python
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

```python
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

```python
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
|------|---------|------|
| **优质题** | D >= 0.3 且通过有效性验证 | 进入正式题库，用于标准化比对 |
| **待改进题** | 0.2 <= D < 0.3 | Agent自动优化（增加约束项/调整干扰项），下轮重新验证 |
| **淘汰题** | D < 0.2 | 标记为淘汰，不再使用 |

### 8.4 信度保证机制

| 信度类型 | 方法 | 门槛 |
|---------|------|------|
| **评分者间信度** | 同一份输出由LLM Judge和人工独立打分，计算ICC | ICC >= 0.7 |
| **重测信度** | 同一系统间隔一周重测 | 得分波动 <= 10% |
| **内部一致性** | 同一难度等级多道题之间 | Cronbach's alpha >= 0.7 |
| **LLM Judge稳定性** | 同一份回答评判3次取均值 | 方差 > 1分 → 标记"需人工复核" |

---

## 九、跑批评测流程（新增）

### 9.1 跑批引擎架构

```
题目生成Agent输出                              跑批引擎                        报告生成
┌─────────────────────────┐           ┌─────────────────┐           ┌─────────────┐
│ 07_final_dataset.md     │           │   并发调度器      │──────────>│  原始结果     │
│ + dataset.json          │──────────>│                 │           │  (JSONL)    │
└─────────────┬───────────┘           │  ┌───────────┐  │           └──────┬──────┘
              │                       │  │ Worker 1  │  │                  │
              │ 追溯链路              │  ├───────────┤  │           ┌──────v──────┐
              ▼                       │  │ Worker 2  │  │──────────>│  三层评判引擎 │
┌─────────────────────────┐           │  ├───────────┤  │           │             │
│ 00-06阶段工件MD         │           │  │ Worker N  │  │           │ L1:规则匹配  │
│ (审计/流程/蓝图/QC)     │           │  └───────────┘  │           │ L2:LLM Judge│
└─────────────────────────┘           │                 │           │ L3:人工抽检  │
                                      │ 断点续跑/超时/限流│           └──────┬──────┘
┌──────────────┐                      └─────────────────┘                  │
│ 被测系统配置   │────────────────────────────────────────────────────────────┘
│ (API端点/URL)│
└──────────────┘
```

跑批引擎只强依赖 `dataset.json`，但评测复盘、题目追责和样本迭代必须可回溯到 `00-06` 阶段工件。

### 9.2 执行流程

```python
def run_batch_evaluation(final_dataset_package, system_config):
    """
    跑批评测主流程
    """
    
    # 1. 加载最终数据集
    dataset = load_dataset(final_dataset_package.dataset_json_path)
    traceability = final_dataset_package.traceability_links
    
    # 2. 环境快照（确保可复现）
    snapshot = {
        "dataset_version": dataset.meta.version,
        "artifact_version": final_dataset_package.dataset_meta.version,
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

        # 逐题保留追溯信息，便于评分异常时快速定位到蓝图/QC阶段
        result["traceability"] = traceability.get(item.test_id, {})
        
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

```python
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

```python
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
|---------|---------|------|
| 100%审核 | expert 级题目 | 高难度题的评判需要领域专家把关 |
| 100%审核 | LLM Judge 方差>1分的case | 评判不稳定的结果必须人工确认 |
| 20%随机抽检 | basic/advanced 级题目 | 校准自动评判的整体准确性 |

每轮评测后计算 **"人机一致率"** = LLM Judge与人工评审打分差异<=1分的比例，作为评判系统本身的质量指标。

### 9.4 统计分析方法

| 分析方法 | 用途 | 适用场景 |
|---------|------|---------|
| 描述性统计 | 总分均值、中位数、标准差、各维度得分分布 | 每轮评测的基础数据 |
| 项目分析 | 逐题的难度指数P和区分度D | 题目质量评估和迭代 |
| ICC（组内相关系数） | 评分者间信度 | 验证LLM Judge和人工评审一致性 |
| Bootstrap置信区间 | 小样本下的得分置信区间估计 | 3题设计的置信度补偿 |
| 配对t检验/Wilcoxon | 两个系统版本间差异的统计显著性 | 版本迭代效果验证 |
| 效应量（Cohen's d） | 差异的实际意义大小 | 不只看p值，还看改进幅度 |

**注意**：本框架设计为N道题（N=场景族数量），当N较小时（如3-6题），不应过度依赖参数检验，建议使用Bootstrap重采样估计置信区间。

---

## 十、评测报告设计（新增）

### 10.1 报告整体结构（四层）

```
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

```
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
|------|------|------|------|-------|---------|
| 定义问题 | 2.0 | 25% | 2.0 | 100% | — |
| 拆解问题 | 2.0 | 20% | 1.5 | 75% | 遗漏"巡检记录填写规范"的拆解步骤 |
| 方案生成 | 3.0 | 20% | 3.0 | 100% | — |
| 执行落地 | 2.0 | 25% | 2.0 | 100% | — |
| 元认知 | 1.0 | 10% | 1.0 | 100% | — |
| **合计** | **10.0** | **100%** | **9.5** | **95%** | |

致命扣分项：无  
一票否决项：无

### 10.4 可视化组件

| 图表 | 用途 | 报告位置 |
|------|------|---------|
| **五阶段雷达图** | 5个维度的能力轮廓，一目了然看出"强在哪弱在哪" | 管理摘要 / 能力分析 |
| **能力矩阵热力图** | 行=流程类型, 列=五阶段, 颜色=得分，精准定位薄弱环节 | 能力维度分析 |
| **瀑布图** | 从满分到最终得分的扣分路径分解 | 逐题详情 |
| **难度-得分散点图** | X轴=难度等级, Y轴=得分，展示能力衰减曲线 | 能力维度分析 |
| **漏斗图** | 五阶段逐步衰减，展示从"理解问题"到"执行落地"的能力衰减 | 能力维度分析 |
| **历史趋势折线图** | 多轮评测的总分/各维度分趋势 | 改进建议 |

### 10.5 评级与上线决策标准

| 总分 | 评级 | 预期业务表现 | 上线建议 |
|------|------|------------|---------|
| 25-30 | **优秀 (S)** | 独立处理90%+日常事务，人工转接≤12% | 立即上线，全面推广 |
| 18-24 | **合格 (A)** | 稳定处理60%-80%标准事务，人工转接≤20% | 修复核心问题后灰度上线 |
| < 18 | **不合格 (F)** | 仅支持基础查询，人工转接>35% | 暂缓上线，需重新优化 |

**一票否决**：任何题目触发安全合规红线（泄露敏感数据、编造法规条文、违反数据权限等）→ 无论总分多少，整体判定为**不合格**。

### 10.6 报告输出格式

报告同时输出两种格式：

- **JSON格式**：结构化数据，用于系统间对接、历史数据存储、可视化渲染
- **Markdown格式**：人类可读，用于文档归档和分享

---

## 十一、审核要点

请审核以下关键设计决策：

1. **四通道输入来源**是否覆盖主要的评测场景？各通道的最小输入集定义是否合理？

2. **8阶段串行流水线**的阶段边界是否清晰？是否足以支持“上一阶段 MD -> 下一阶段 MD”的稳定串联？

3. **阶段工件契约**（YAML frontmatter + 固定章节 + 结构化载荷）是否足够让下游 Agent 稳定消费？

4. **双层Fallback + 阶段回退机制**是否完整覆盖输入缺失和阶段质检失败两类场景？

5. **流程地图 -> 场景族 -> 样本蓝图 -> 参考标准** 这一链条是否足够清晰？是否还有遗漏的中间抽象层？

6. **动态题目数量**逻辑是否合理（首轮题目数量=场景族数量）？代表流程选择规则是否充分？

7. **难度量化矩阵**的6个维度是否足够？阈值划分（1.5/2.3）是否需要调整？

8. **有效性/区分度/信度**三维度保证机制是否可操作？

9. **三层评判管道**（规则匹配→LLM Judge→人工抽检）的分工，以及与 `07_final_dataset.md` / `dataset.json` 的衔接是否合理？

10. **评分细则（Rubric）**的 `evidence_type` 设计（keyword_match / semantic_match / llm_judge）是否覆盖主要评判场景？一票否决机制是否还有遗漏的安全红线？

---

**审核状态**：待审核
