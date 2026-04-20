# 题目生成Agent设计文档_Sin

**版本**：V2.0  
**日期**：2026-04-16  
**状态**：待审核  
**更新说明**：V2.0新增四通道输入、评分细则、题目质量保障体系、跑批评测流程、评测报告设计  

现在的输入来源，只对设计文档通道进行实现，先做成一个流程。
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
|------|------|
| **从设计意图出发** | 评测应验证系统是否达成了设计意图，而非验证历史数据pattern |
| **覆盖范围≠题目难度** | 题目数量由流程类型数量动态决定，难度由约束项/干扰项调节 |
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

### 2.4 Phase 0: 输入预处理（新增）

在题目生成主流程（Phase 1-6）之前，必须执行输入预处理：

```python
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

```python
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

### 3.6 标准化数据集输出格式

题目生成Agent的最终输出应为以下JSON格式，可直接送入跑批评测引擎：

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

### 4.1 执行流程图

```
题目生成Agent执行流程
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Phase 1: 业务流程提取或提炼                              │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Fallback机制：                                       ││
│  │ if design_docs.business_processes exists:           ││
│  │     → 直接提取流程定义                               ││
│  │ else:                                               ││
│  │     → 从PRD+Architecture推导流程                     ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  Phase 2: 流程分类（动态提取）                            │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 提取流程特性作为分类维度                             ││
│  │ 根据特性组合自动聚类                                 ││
│  │ 为每个聚类命名                                       ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  Phase 3: 题目数量确定                                    │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 题目数量 = 流程类型数量                              ││
│  │ 每个流程类型选一个代表性流程                         ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  Phase 4: 约束项/干扰项设计                               │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Fallback机制：                                       ││
│  │ if capability_scope.weak_points exists:             ││
│  │     → 根据weak_points映射                            ││
│  │ else:                                               ││
│  │     → 从流程特性推导                                 ││
│  │                                                     ││
│  │ 业务真实性验证（必须执行）                           ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  Phase 5: 五阶段期望行为生成                              │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 基于业务流程步骤定义                                 ││
│  │ 每个题目都是业务闭环                                 ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  Phase 6: 验证与输出                                      │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 验证题目满足5设计原则                                ││
│  │ 输出N个统一题 + 五阶段期望行为                       ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Phase 1: 业务流程提取或提炼

#### 优先路径：设计文档有流程定义

```python
def extract_business_processes(design_docs):
    """
    优先路径：直接提取流程定义
    """
    if design_docs.business_processes and len(design_docs.business_processes) > 0:
        processes = []
        for process_def in design_docs.business_processes:
            process = BusinessProcess(
                process_id=process_def.id,
                process_name=process_def.name,
                actors=extract_actors(process_def),
                steps=extract_steps(process_def),
                triggers=extract_triggers(process_def),
                outputs=extract_outputs(process_def)
            )
            processes.append(process)
        return processes
```

#### Fallback路径：从PRD推导流程

```python
def infer_processes_from_prd(prd, architecture, domain_knowledge):
    """
    Fallback路径：从PRD推导业务流程
    
    推导公式：流程 = 用户角色 × 核心功能 × 业务目标
    """
    processes = []
    
    # 1. 提取用户群体
    user_groups = prd.target_users
    
    # 2. 提取核心功能
    core_features = architecture.core_features
    
    # 3. 提取业务目标
    business_objective = prd.business_objective
    
    # 4. 推导流程
    for user_group in user_groups:
        user_needs = user_group.get("needs", [])
        matching_features = match_user_needs_to_features(user_needs, core_features)
        
        for need, feature in matching_features:
            process = infer_single_process(
                user_role=user_group["role"],
                user_need=need,
                feature=feature,
                business_objective=business_objective
            )
            processes.append(process)
    
    # 5. 合并相似流程
    processes = merge_similar_processes(processes)
    
    return processes
```

#### 推导单个流程

```python
def infer_single_process(user_role, user_need, feature, business_objective):
    """
    推导单个业务流程
    
    推导逻辑：
    - 流程名称：用户角色 + 需求类型
    - 流程触发：该用户群体的典型需求场景
    - 流程输出：业务目标的预期产出
    - 流程步骤：核心功能的使用顺序
    """
    
    # 推导流程名称
    process_name = f"{user_role}{feature.name}流程"
    
    # 推导触发条件
    triggers = infer_triggers_from_user_need(user_role, user_need)
    
    # 推导输出
    outputs = infer_outputs_from_feature(feature, business_objective)
    
    # 推导步骤
    steps = infer_steps_from_feature(feature)
    
    # 推导参与者
    actors = [Actor(role=user_role, level=infer_actor_level(user_role))]
    
    return BusinessProcess(
        process_name=process_name,
        actors=actors,
        steps=steps,
        triggers=triggers,
        outputs=outputs,
        inferred=True  # 标注为推导生成
    )
```



### 4.3 Phase 2: 流程分类（动态提取）

#### 分类维度提取

```python
def extract_classification_dimensions(processes):
    """
    提取分类维度
    
    从所有流程的特性中提取可用于分类的维度
    """
    
    dimensions = []
    
    # 1. 提取触发类型维度
    trigger_types = set()
    for process in processes:
        for trigger in process.triggers:
            trigger_types.add(trigger.type)
    
    if len(trigger_types) > 1:
        dimensions.append(ClassificationDimension(
            name="trigger_type",
            values=list(trigger_types)
        ))
    
    # 2. 提取输出类型维度
    output_types = set()
    for process in processes:
        for output in process.outputs:
            output_types.add(output.category)
    
    if len(output_types) > 1:
        dimensions.append(ClassificationDimension(
            name="output_type",
            values=list(output_types)
        ))
    
    # 3. 提取参与者层级维度
    actor_levels = set()
    for process in processes:
        for actor in process.actors:
            actor_levels.add(actor.level)
    
    if len(actor_levels) > 1:
        dimensions.append(ClassificationDimension(
            name="actor_level",
            values=list(actor_levels)
        ))
    
    return dimensions
```

#### 流程聚类

```python
def cluster_processes_by_features(processes, dimensions):
    """
    根据特性聚类流程
    
    使用聚类算法将相似特性的流程归为一类
    """
    
    clusters = {}
    
    for process in processes:
        # 找出该流程最显著的分类特征
        primary_feature = find_primary_feature(process, dimensions)
        cluster_key = f"cluster_{primary_feature}"
        
        if cluster_key not in clusters:
            clusters[cluster_key] = []
        clusters[cluster_key].append(process)
    
    return clusters
```

#### 类型命名

```python
def generate_type_name(cluster_processes):
    """
    为聚类生成类型名称
    
    基于聚类内流程的共同特性命名
    """
    
    common_trigger = find_common_trigger_type(cluster_processes)
    common_output = find_common_output_type(cluster_processes)
    
    if common_trigger and common_output:
        return f"{common_trigger}-{common_output}类"
    elif common_trigger:
        return f"{common_trigger}类"
    elif common_output:
        return f"{common_output}类"
    else:
        return "其他类"
```

### 4.4 Phase 3: 题目数量确定

```python
def determine_test_count(process_types):
    """
    题目数量动态决定
    
    原则：每个流程类型对应一个题目
    """
    
    return len(process_types)


def select_representative_process(type_processes):
    """
    从每个类型中选择代表性流程
    
    选择依据：
    - 流程复杂度
    - 业务重要性
    - 覆盖全面性
    """
    
    # 按业务重要性排序
    scored_processes = []
    for process in type_processes:
        score = calculate_process_importance(process)
        scored_processes.append((process, score))
    
    scored_processes.sort(key=lambda x: x[1], reverse=True)
    
    return scored_processes[0][0]
```

### 4.5 Phase 4: 约束项/干扰项设计

#### 约束项设计（带Fallback）

```python
def add_constraints_dynamically(process, domain_knowledge, design_docs):
    """
    约束项动态添加（带Fallback）
    """
    
    constraints = []
    
    # === 优先路径：从weak_points映射 ===
    if design_docs.capability_scope and design_docs.capability_scope.weak_points:
        for weak_point in design_docs.capability_scope.weak_points:
            constraint = generate_constraint_from_weak_point(weak_point, process)
            if constraint:
                constraints.append(constraint)
    
    # === Fallback路径：从流程特性推导 ===
    else:
        inferred_constraints = infer_constraints_from_process(
            process, domain_knowledge
        )
        constraints.extend(inferred_constraints)
    
    # === 基础约束（始终执行）===
    # 规程时效性约束
    regulation_version = find_latest_regulation(domain_knowledge)
    if regulation_version:
        constraints.append(f"依据{regulation_version}")
    
    # 业务真实性验证
    constraints = verify_business_realism(constraints, domain_knowledge)
    
    return constraints
```

#### 约束项推导维度

```python
def infer_constraints_from_process(process, domain_knowledge):
    """
    从流程特性推导约束项
    
    推导维度：
    1. 跨流程依赖 → 需要信息整合能力
    2. 规程多版本 → 需要版本区分能力
    3. 参与者层级 → 需要权限边界意识
    4. 输出项数量 → 需要闭环交付能力
    5. 触发类型 → 需要模糊需求理解能力
    """
    
    constraints = []
    
    # 1. 跨流程依赖
    if process.cross_process_dependency == "跨流程":
        constraints.append("需整合多个流程的信息，形成完整方案")
    
    # 2. 规程多版本
    if has_multiple_regulation_versions(domain_knowledge, process):
        constraints.append("需引用最新规程版本，排除已废止版本")
    
    # 3. 参与者层级
    if "管理层" in [actor.level for actor in process.actors]:
        constraints.append("需识别信息访问权限边界，标注受限信息")
    
    # 4. 输出项数量
    if len(process.outputs) > 1:
        constraints.append("需完整交付所有输出项，形成闭环")
    
    # 5. 触发类型
    if has_fuzzy_trigger(process):
        constraints.append("需合理推断模糊需求，或主动追问澄清")
    
    return constraints
```

#### 干扰项设计（带Fallback）

```python
def add_interference_dynamically(process, domain_knowledge, design_docs):
    """
    干扰项动态添加（带Fallback）
    """
    
    interference = []
    
    # === 优先路径：从weak_points映射 ===
    if design_docs.capability_scope and design_docs.capability_scope.weak_points:
        for weak_point in design_docs.capability_scope.weak_points:
            interference_item = generate_interference_from_weak_point(weak_point, process)
            if interference_item:
                interference.append(interference_item)
    
    # === Fallback路径：从流程特性推导 ===
    else:
        inferred_interference = infer_interference_from_process(
            process, domain_knowledge
        )
        interference.extend(inferred_interference)
    
    # 业务真实性验证
    interference = verify_business_realism(interference, domain_knowledge)
    
    return interference
```

#### 干扰项推导维度

```python
def infer_interference_from_process(process, domain_knowledge):
    """
    从流程特性推导干扰项
    
    推导维度：
    1. 规程规则冲突
    2. 规程多版本并存
    3. 流程异常情况
    4. 模糊触发条件
    5. 跨部门角色混淆
    """
    
    interference = []
    
    # 1. 规程规则冲突
    if has_regulation_conflicts(domain_knowledge, process):
        interference.append("规程存在冲突条款，需正确判断适用场景")
    
    # 2. 规程多版本并存
    if has_multiple_regulation_versions(domain_knowledge, process):
        interference.append("规程有新旧版本并存，需正确引用最新版")
    
    # 3. 流程异常情况
    if has_exception_handling_steps(process):
        interference.append("流程中存在异常情况，需给出备选处理方案")
    
    # 4. 模糊触发条件
    fuzzy_triggers = find_fuzzy_triggers(process)
    if fuzzy_triggers:
        for trigger in fuzzy_triggers:
            interference.append(f"需求描述存在模糊性：'{trigger.description}'，需合理推断或追问澄清")
    
    # 5. 跨部门角色混淆
    if len(process.actors) > 1:
        interference.append("流程涉及多个角色，责任边界需明确")
    
    return interference
```

### 4.6 Phase 5: 五阶段期望行为生成

```python
def generate_reference_answer(test, process, domain_knowledge, design_docs):
    """
    五阶段期望行为生成
    
    基于业务流程步骤定义
    """
    
    reference = ReferenceAnswer(test_id=test.test_id)
    
    # 定义问题期望（基于流程触发条件）
    reference.define_problem_expected = DefineProblemExpected(
        intent_understanding=f"应理解用户意图是'{process.process_name}'",
        implicit_needs=[output.name for output in process.outputs],
        problem_essence=process.process_name
    )
    
    # 拆解问题期望（基于流程步骤）
    reference.decompose_expected = DecomposeExpected(
        expected_steps=[step.name for step in process.steps],
        priority_ordering=f"按{process.process_name}流程顺序执行"
    )
    
    # 方案生成期望（基于流程信息源）
    reference.solution_expected = SolutionExpected(
        information_sources=find_required_docs(process, domain_knowledge),
        cross_doc_integration=f"整合{len(process.required_capabilities)}个信息源"
    )
    
    # 执行落地期望（基于流程输出）
    reference.execution_expected = ExecutionExpected(
        output_format=f"结构化输出：{[o.name for o in process.outputs]}"
    )
    
    # 元认知期望（基于系统能力边界）
    reference.meta_expected = MetaExpected(
        source_annotation="应标注信息来源（规程版本、条款号）",
        boundary_awareness="应识别权限边界"
    )
    
    return reference
```

### 4.7 Phase 6: 验证与输出

#### 5设计原则验证

```python
def validate_test_quality(test, analysis):
    """
    验证5设计原则
    
    统一题验收标准（任何一个为否，题目不合格）
    """
    
    report = ValidationReport(test_id=test.test_id)
    
    # 1. 真实性：上线后每天都会遇到吗？
    report.real_encounter = validate_real_encounter(test, analysis)
    
    # 2. 闭环性：需要完整的五阶段流程吗？
    report.five_stage_coverage = validate_five_stage_coverage(test)
    
    # 3. 可量化：有明确的成功标准吗？
    report.quantifiable_criteria = validate_quantifiable(test)
    
    # 4. 区分度：能区分不同水平的系统吗？
    report.discrimination = validate_discrimination(test, analysis)
    
    # 5. 预测力：能预测业务表现吗？
    report.prediction_power = validate_prediction_power(test, analysis)
    
    report.passed = all([
        report.real_encounter,
        report.five_stage_coverage,
        report.quantifiable_criteria,
        report.discrimination,
        report.prediction_power
    ])
    
    return report
```

#### 业务真实性验证

```python
def verify_business_realism(items, domain_knowledge):
    """
    业务真实性验证
    
    验证标准：
    1. 该约束/干扰在真实业务中是否可能出现？
    2. 该约束/干扰是否符合业务常识？
    3. 该约束/干扰是否有规程/制度支撑？
    """
    
    verified_items = []
    
    for item in items:
        # 检查是否有规程支撑
        if has_real_regulation_support(item, domain_knowledge):
            verified_items.append(item)
        # 检查是否符合业务常识
        elif matches_business_commonsense(item, domain_knowledge):
            verified_items.append(item)
        # 检查是否可能出现在真实场景
        elif likely_in_real_scenario(item, domain_knowledge):
            verified_items.append(item)
    
    return verified_items
```

---

## 五、Fallback机制详细设计

### 5.1 双层Fallback链

```
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

```
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

```
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
|--------|---------|-----------|---------|
| D001 | 输入来源=历史数据 | 输入来源=设计文档 | 评测应验证设计意图 |
| D002 | 用户占比→题目难度 | 覆盖范围≠难度 | 两者无因果关系 |
| D003 | 固定3个题目 | 题目数量动态决定 | 通用框架不应固定 |
| D004 | 固定流程类别 | 动态提取分类 | 不同系统有不同流程 |
| D005 | 约束项固定模板 | 动态推导+Fallback | 设计文档可能无weak_points |
| D006 | 流程定义必须存在 | 双层Fallback | 设计文档可能无流程定义 |

---

## 七、Agent Prompt模板

```markdown
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
题目生成Agent输出                 跑批引擎                        报告生成
┌──────────────┐           ┌─────────────────┐           ┌─────────────┐
│ 标准化数据集   │──────────>│   并发调度器      │──────────>│  原始结果     │
│ (JSON)       │           │                 │           │  (JSONL)    │
└──────────────┘           │  ┌───────────┐  │           └──────┬──────┘
                           │  │ Worker 1  │  │                  │
┌──────────────┐           │  ├───────────┤  │           ┌──────v──────┐
│ 被测系统配置   │──────────>│  │ Worker 2  │  │──────────>│  三层评判引擎 │
│ (API端点/URL)│            │  ├───────────┤  │           │             │
└──────────────┘           │  │ Worker N  │  │           │ L1:规则匹配  │
                           │  └───────────┘  │           │ L2:LLM Judge│
                           │                 │           │ L3:人工抽检  │
                           │ 断点续跑/超时/限流│           └──────┬──────┘
                           └─────────────────┘                  │
                                                         ┌──────v──────┐
                                                         │  报告生成器   │
                                                         └─────────────┘
```

### 9.2 执行流程

```python
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

**注意**：本框架设计为N道题（N=流程类型数量），当N较小时（如3-6题），不应过度依赖参数检验，建议使用Bootstrap重采样估计置信区间。

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

2. **Phase 0 输入预处理**是否有遗漏的检查项？

3. **双层Fallback机制**是否完整覆盖所有可能的输入缺失场景？

4. **动态题目数量**逻辑是否合理（题目数量=流程类型数量）？

5. **难度量化矩阵**的6个维度是否足够？阈值划分（1.5/2.3）是否需要调整？

6. **有效性/区分度/信度**三维度保证机制是否可操作？

7. **三层评判管道**（规则匹配→LLM Judge→人工抽检）的分工是否合理？

8. **评测报告四层结构**是否满足不同读者（管理层/技术团队/评审专家）的需求？

9. **评分细则（Rubric）**的 `evidence_type` 设计（keyword_match / semantic_match / llm_judge）是否覆盖主要评判场景？

10. **一票否决机制**的触发条件是否明确？是否有遗漏的安全红线？

---

**审核状态**：待审核
