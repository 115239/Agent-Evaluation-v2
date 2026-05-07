# Future AGI 测试用例生成机制详解

## 架构概览

Future AGI 的测试用例生成采用 **Persona × Scenario × SimulatorAgent** 三维架构，通过 Temporal Workflow 编排整个生命周期。

```
┌─────────────────────────────────────────────────────────────────┐
│                    测试用例生成架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Persona (用户画像)                                             │
│      │                                                          │
│      │ 18种系统预设 × 14+可配置字段                               │
│      │                                                          │
│      ▼                                                          │
│   Scenario (测试场景)                                            │
│      │                                                          │
│      │ Dataset / Graph / Script 三种类型                         │
│      │                                                          │
│      ▼                                                          │
│   SimulatorAgent (模拟智能体)                                     │
│      │                                                          │
│      │ 根据 Persona + Scenario 自动生成                          │
│      │                                                          │
│      ▼                                                          │
│   Temporal Workflow 编排                                         │
│      │                                                          │
│      │ TestExecutionWorkflow → CallExecutionWorkflow             │
│      │                                                          │
│      ▼                                                          │
│   评测结果聚合                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 一、Persona（用户画像）

### 1.1 系统预设 Persona

Future AGI 内置 **18种系统 Persona**，覆盖典型用户交互场景：

| Persona | 描述 | 典型用途 |
|---------|------|---------|
| `CustomerSupport` | 客服代表 | FAQ问答、投诉处理 |
| `TechnicalEngineer` | 技术工程师 | API调用、问题诊断 |
| `SalesRepresentative` | 销售代表 | 产品推荐、报价 |
| `HRManager` | 人力资源经理 | 招聘、员工关系 |
| `FinancialAdvisor` | 财务顾问 | 投资建议、风险分析 |
| `LegalAdvisor` | 法务顾问 | 合同审查、合规咨询 |
| `MarketingSpecialist` | 市场营销专家 | 广告投放、品牌策略 |
| `ProductManager` | 产品经理 | 功能规划、需求分析 |
| `DataAnalyst` | 数据分析师 | 报表生成、趋势预测 |
| `SoftwareDeveloper` | 软件开发工程师 | 代码编写、Bug修复 |
| `QAEngineer` | 测试工程师 | 测试用例设计、自动化测试 |
| `SystemAdmin` | 系统管理员 | 配置管理、故障排除 |
| `HealthcareProfessional` | 医疗专业人士 | 诊断建议、病历分析 |
| `Educator` | 教育工作者 | 课程设计、学生指导 |
| `Researcher` | 研究人员 | 文献综述、实验设计 |
| `ContentCreator` | 内容创作者 | 文案撰写、素材制作 |
| `ProjectManager` | 项目经理 | 进度管理、资源协调 |
| `ExecutiveAssistant` | 行政助理 | 日程安排、文档处理 |

### 1.2 Persona 可配置字段

每个 Persona 包含 **14+ 可配置字段**，定义用户的完整画像：

```python
# futureagi/simulate/models/persona.py

class Persona(models.Model):
    # === 核心属性 ===
    name = models.CharField(max_length=255)              # 画像名称
    description = models.TextField()                     # 画像描述
    persona_type = models.CharField(max_length=50)       # 类型：SYSTEM / CUSTOM

    # === 用户背景 ===
    demographics = models.JSONField(default=dict)        # 人口统计学特征
    # {
    #   "age_range": "25-35",
    #   "gender": "male/female/other",
    #   "education": "bachelor/master/phd",
    #   "occupation": "software_engineer",
    #   "income_level": "middle",
    #   "location": "urban/suburban/rural"
    # }

    # === 技能水平 ===
    technical_proficiency = models.JSONField(default=dict)  # 技术熟练度
    # {
    #   "overall_level": "beginner/intermediate/advanced/expert",
    #   "specific_skills": {
    #     "programming": 0.7,
    #     "api_usage": 0.5,
    #     "command_line": 0.3
    #   },
    #   "familiar_frameworks": ["react", "django"],
    #   "unfamiliar_areas": ["rust", "blockchain"]
    # }

    # === 行为模式 ===
    behavioral_patterns = models.JSONField(default=dict)    # 行为特征
    # {
    #   "interaction_style": "direct/exploratory/methodical",
    #   "question_frequency": "high/medium/low",
    #   "error_tolerance": "low/medium/high",
    #   "patience_level": "low/medium/high",
    #   "follow_up_behavior": "proactive/passive"
    # }

    # === 语言特征 ===
    language_profile = models.JSONField(default=dict)      # 语言偏好
    # {
    #   "primary_language": "en/zh/es/...",
    #   "formality_level": "formal/casual/mixed",
    #   "vocabulary_complexity": "simple/technical/mixed",
    #   "sentence_structure": "concise/elaborate/mixed",
    #   "emoji_usage": "none/sparse/moderate/heavy",
    #   "typo_frequency": "none/rare/common"
    # }

    # === 目标驱动 ===
    goals_and_motivations = models.JSONField(default=dict)  # 目标与动机
    # {
    #   "primary_goal": "solve_problem/learn/explore/validate",
    #   "secondary_goals": ["optimize", "document"],
    #   "success_criteria": ["working_solution", "understanding"],
    #   "motivation_intensity": "high/medium/low",
    #   "time_pressure": "urgent/moderate/none"
    # }

    # === 知识背景 ===
    knowledge_domains = models.JSONField(default=dict)     # 知识领域
    # {
    #   "expert_areas": ["web_development", "database_design"],
    #   "familiar_areas": ["devops", "testing"],
    #   "novice_areas": ["ml", "security"],
    #   "misconceptions": ["async_is_slow", "sql_is_obsolete"]
    # }

    # === 情绪状态 ===
    emotional_state = models.JSONField(default=dict)       # 情绪特征
    # {
    #   "baseline_mood": "neutral/positive/negative/anxious",
    #   "stress_level": "low/medium/high",
    #   "frustration_triggers": ["slow_response", "unclear_answer"],
    #   "satisfaction_triggers": ["quick_solution", "clear_explanation"]
    # }

    # === 决策模式 ===
    decision_making = models.JSONField(default=dict)       # 决策偏好
    # {
    #   "style": "analytical/intuitive/hybrid",
    #   "risk_tolerance": "conservative/moderate/aggressive",
    #   "information_need": "minimal/moderate/comprehensive",
    #   "decision_speed": "quick/moderate/deliberate"
    # }

    # === 上下文环境 ===
    environmental_context = models.JSONField(default=dict)  # 使用环境
    # {
    #   "device_type": "desktop/mobile/tablet",
    #   "network_quality": "stable/unstable",
    #   "time_available": "limited/moderate/unlimited",
    #   "distraction_level": "low/medium/high",
    #   "workspace_type": "office/home/mobile"
    # }

    # === 历史交互 ===
    interaction_history = models.JSONField(default=dict)   # 历史记录
    # {
    #   "previous_sessions": 10,
    #   "common_queries": ["how to", "why"],
    #   "known_solutions": ["auth_fix", "cache_setup"],
    #   "recurrent_issues": ["timeout", "permission"]
    # }

    # === 偏好设置 ===
    preferences = models.JSONField(default=dict)           # 用户偏好
    # {
    #   "response_length": "brief/standard/detailed",
    #   "explanation_depth": "minimal/standard/deep",
    #   "code_examples": "none/inline/full",
    #   "step_by_step": true,
    #   "visual_aids": false,
    #   "external_links": true
    # }

    # === 限制约束 ===
    constraints = models.JSONField(default=dict)           # 约束条件
    # {
    #   "budget_limit": "free/standard/premium",
    #   "time_constraint": "5min/30min/1hour",
    #   "access_level": "basic/pro/enterprise",
    #   "privacy_requirement": "standard/strict"
    # }
```

### 1.3 Persona 示例：技术工程师

```python
{
    "name": "TechnicalEngineer_Debug",
    "description": "中级工程师，擅长Web开发，正在调试API问题",
    "demographics": {
        "age_range": "25-35",
        "education": "master",
        "occupation": "backend_engineer"
    },
    "technical_proficiency": {
        "overall_level": "intermediate",
        "specific_skills": {
            "programming": 0.8,
            "api_usage": 0.7,
            "debugging": 0.6
        },
        "familiar_frameworks": ["django", "fastapi"],
        "unfamiliar_areas": ["async_patterns"]
    },
    "behavioral_patterns": {
        "interaction_style": "methodical",
        "question_frequency": "medium",
        "error_tolerance": "low",
        "follow_up_behavior": "proactive"
    },
    "language_profile": {
        "primary_language": "zh",
        "formality_level": "mixed",
        "vocabulary_complexity": "technical",
        "typo_frequency": "rare"
    },
    "goals_and_motivations": {
        "primary_goal": "solve_problem",
        "success_criteria": ["root_cause", "working_fix"],
        "time_pressure": "urgent"
    },
    "knowledge_domains": {
        "expert_areas": ["web_development"],
        "familiar_areas": ["database_design"],
        "novice_areas": ["concurrency"],
        "misconceptions": ["async_is_slow"]
    },
    "emotional_state": {
        "baseline_mood": "neutral",
        "stress_level": "high",
        "frustration_triggers": ["slow_response", "ambiguous_answer"]
    },
    "decision_making": {
        "style": "analytical",
        "information_need": "comprehensive",
        "decision_speed": "deliberate"
    },
    "preferences": {
        "response_length": "detailed",
        "explanation_depth": "deep",
        "code_examples": "full",
        "step_by_step": true
    }
}
```

---

## 二、Scenario（测试场景）

### 2.1 Scenario 类型

```python
# futureagi/simulate/models/scenarios.py

class ScenarioTypes:
    GRAPH = "graph"      # 基于图谱的场景生成
    SCRIPT = "script"    # 基于脚本的场景生成
    DATASET = "dataset"  # 基于数据集的场景生成
```

| 类型 | 描述 | 适用场景 |
|------|------|---------|
| `GRAPH` | 状态图驱动，节点=用户状态，边=转换条件 | 复杂多轮对话、决策树场景 |
| `SCRIPT` | 预定义脚本，固定对话流程 | 标准化流程测试、回归测试 |
| `DATASET` | 数据集驱动，批量生成场景 | 大规模覆盖测试、统计验证 |

### 2.2 Scenario 来源类型

```python
class ScenarioSourceType:
    AGENT_DEFINITION = "agent_definition"  # 从 Agent 定义提取
    PROMPT = "prompt"                       # 从提示词模板生成
```

### 2.3 Scenario 配置示例

```python
# Dataset 类型场景
{
    "type": "dataset",
    "source_type": "agent_definition",
    "config": {
        "agent_id": "customer_support_v1",
        "num_scenarios": 100,
        "diversity_weight": 0.7,  # 场景多样性权重
        "complexity_range": [1, 5]  # 复杂度范围（对话轮数）
    }
}

# Graph 类型场景
{
    "type": "graph",
    "source_type": "prompt",
    "config": {
        "graph_definition": {
            "nodes": [
                {"id": "initial_query", "state": "user_has_question"},
                {"id": "clarification", "state": "user_needs_detail"},
                {"id": "solution_accepted", "state": "user_satisfied"},
                {"id": "escalation", "state": "user_frustrated"}
            ],
            "edges": [
                {"from": "initial_query", "to": "clarification", "condition": "ambiguous"},
                {"from": "clarification", "to": "solution_accepted", "condition": "clear_answer"},
                {"from": "clarification", "to": "escalation", "condition": "no_progress"}
            ]
        },
        "entry_node": "initial_query",
        "exit_nodes": ["solution_accepted", "escalation"]
    }
}
```

---

## 三、SimulatorAgent（模拟智能体）

### 3.1 自动生成逻辑

```python
# futureagi/simulate/services/scenario_service.py:93-108

def create_simulator_agent(persona: Persona, scenario: Scenario) -> SimulatorAgent:
    """根据 Persona + Scenario 自动生成模拟智能体"""

    agent_config = {
        "name": f"Simulator_{persona.name}_{scenario.id}",
        "persona_profile": persona.to_dict(),
        "scenario_context": scenario.to_dict(),

        # === LLM 配置 ===
        "llm_config": {
            "model": persona.preferences.get("model_preference", "gpt-4"),
            "temperature": calculate_temperature(persona),
            "max_tokens": persona.constraints.get("response_length_limit", 2000)
        },

        # === 行为策略 ===
        "behavior_strategy": {
            "response_pattern": persona.behavioral_patterns["interaction_style"],
            "error_handling": persona.behavioral_patterns["error_tolerance"],
            "follow_up_mode": persona.behavioral_patterns["follow_up_behavior"]
        },

        # === 评测目标 ===
        "evaluation_targets": scenario.config.get("evaluation_metrics", [])
    }

    return SimulatorAgent(**agent_config)


def calculate_temperature(persona: Persona) -> float:
    """根据 Persona 特征计算温度参数"""
    base_temp = 0.7

    # 根据 tech proficiency 调整
    tech_level = persona.technical_proficiency.get("overall_level", "intermediate")
    tech_modifier = {
        "beginner": 0.3,   # 低技术用户 → 更确定性回复
        "intermediate": 0.0,
        "advanced": 0.2,   # 高技术用户 → 更多样性探索
        "expert": 0.4
    }

    # 根据 emotional state 调整
    stress_level = persona.emotional_state.get("stress_level", "medium")
    stress_modifier = {
        "low": 0.0,
        "medium": -0.1,   # 中等压力 → 更稳定输出
        "high": -0.2      # 高压力 → 最确定性行为
    }

    return base_temp + tech_modifier.get(tech_level, 0) + stress_modifier.get(stress_level, 0)
```

### 3.2 SimulatorAgent 运行机制

```
┌─────────────────────────────────────────────────────────────────┐
│                    SimulatorAgent 运行流程                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 接收测试目标 Agent 的响应                                     │
│     │                                                           │
│     ▼                                                           │
│  2. Persona 特征注入                                             │
│     │                                                           │
│     │ - 人口统计学特征决定语言风格                                 │
│     │ - 技术熟练度决定问题深度                                     │
│     │ - 行为模式决定追问策略                                       │
│     │ - 情绪状态决定语气强度                                       │
│     │                                                           │
│     ▼                                                           │
│  3. 生成下一轮输入                                                │
│     │                                                           │
│     │ - 符合 Persona 的语言特征                                   │
│     │ - 符合 Scenario 的状态转换                                  │
│     │ - 符合评测目标的触发条件                                     │
│     │                                                           │
│     ▼                                                           │
│  4. 评测触发                                                      │
│     │                                                           │
│     │ - 实时评测：响应质量、相关性                                 │
│     │ - 交互评测：对话流畅度、任务完成度                           │
│     │                                                           │
│     ▼                                                           │
│  5. 状态更新                                                      │
│     │                                                           │
│     │ - 更新情绪状态（满意/失望）                                  │
│     │ - 更新对话轮数                                              │
│     │ - 判断是否终止                                              │
│     │                                                           │
│     ▼                                                           │
│  6. 输出评测数据                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、Temporal Workflow 编排

### 4.1 TestExecutionWorkflow（父工作流）

```python
# futureagi/simulate/temporal/workflows/test_execution_workflow.py

@workflow.defn
class TestExecutionWorkflow:
    """测试执行主工作流 - 编排整个测试生命周期"""

    def __init__(self):
        self.status = TestStatus.INITIALIZING
        self.results = []
        self.total_calls = 0
        self.completed_calls = 0

    @workflow.run
    async def run(self, input: TestExecutionInput) -> TestExecutionResult:
        # === Phase 1: 初始化 ===
        self.status = TestStatus.INITIALIZING
        test_config = await workflow.execute_activity(
            load_test_config,
            input.test_id,
            start_to_close_timeout=30
        )

        # === Phase 2: 场景生成 ===
        scenarios = await workflow.execute_activity(
            generate_scenarios,
            GenerateScenariosInput(
                persona_id=input.persona_id,
                scenario_config=test_config.scenario_config
            ),
            start_to_close_timeout=60
        )

        self.total_calls = len(scenarios)

        # === Phase 3: 并发执行 ===
        self.status = TestStatus.LAUNCHING
        call_handles = []

        for scenario in scenarios:
            handle = await workflow.start_child_workflow(
                CallExecutionWorkflow.run,
                CallExecutionInput(
                    scenario=scenario,
                    persona=await workflow.execute_activity(
                        load_persona,
                        input.persona_id
                    ),
                    target_agent_id=input.target_agent_id
                ),
                id=f"call-{scenario.id}"
            )
            call_handles.append(handle)

        # === Phase 4: 等待完成 ===
        self.status = TestStatus.RUNNING

        for handle in call_handles:
            result = await handle
            self.results.append(result)
            self.completed_calls += 1

            # 发送进度信号
            await workflow.signal_external_workflow(
                input.progress_signal_workflow,
                "progress_update",
                ProgressUpdate(
                    completed=self.completed_calls,
                    total=self.total_calls
                )
            )

        # === Phase 5: 结果聚合 ===
        self.status = TestStatus.FINALIZING
        aggregated = await workflow.execute_activity(
            aggregate_results,
            AggregateInput(
                results=self.results,
                metrics=test_config.evaluation_metrics
            ),
            start_to_close_timeout=120
        )

        return TestExecutionResult(
            test_id=input.test_id,
            status=TestStatus.COMPLETED,
            metrics=aggregated.metrics,
            summary=aggregated.summary
        )
```

### 4.2 CallExecutionWorkflow（子工作流）

```python
@workflow.defn
class CallExecutionWorkflow:
    """单个对话执行工作流 - 管理一轮完整对话"""

    @workflow.run
    async def run(self, input: CallExecutionInput) -> CallExecutionResult:
        simulator = SimulatorAgent(
            persona=input.persona,
            scenario=input.scenario
        )

        conversation = []
        evaluations = []

        # === 初始化对话 ===
        initial_message = await simulator.generate_initial_message()
        conversation.append({
            "role": "user",
            "content": initial_message,
            "timestamp": datetime.now()
        })

        # === 多轮对话循环 ===
        max_turns = input.scenario.config.get("max_turns", 10)
        current_turn = 0

        while current_turn < max_turns:
            # 调用目标 Agent
            agent_response = await workflow.execute_activity(
                call_target_agent,
                CallAgentInput(
                    agent_id=input.target_agent_id,
                    message=conversation[-1]["content"],
                    context=conversation
                ),
                start_to_close_timeout=60
            )

            conversation.append({
                "role": "assistant",
                "content": agent_response.content,
                "timestamp": datetime.now()
            })

            # 实时评测
            eval_result = await workflow.execute_activity(
                evaluate_response,
                EvaluateInput(
                    response=agent_response.content,
                    persona=input.persona,
                    metrics=input.scenario.evaluation_metrics
                ),
                start_to_close_timeout=30
            )
            evaluations.append(eval_result)

            # 判断是否终止
            should_continue = await simulator.should_continue(
                conversation=conversation,
                evaluation=eval_result
            )

            if not should_continue:
                break

            # SimulatorAgent 生成下一轮
            next_message = await simulator.generate_next_message(
                conversation=conversation,
                last_response=agent_response
            )
            conversation.append({
                "role": "user",
                "content": next_message,
                "timestamp": datetime.now()
            })

            current_turn += 1

        return CallExecutionResult(
            scenario_id=input.scenario.id,
            conversation=conversation,
            evaluations=evaluations,
            final_status=simulator.get_final_status()
        )
```

### 4.3 Workflow 状态机

```
┌─────────────────────────────────────────────────────────────────┐
│                  TestExecutionWorkflow 状态转换                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INITIALIZING ─────► 加载测试配置                                │
│       │                                                         │
│       ▼                                                         │
│  GENERATING ───────► 生成场景列表                                │
│       │                                                         │
│       ▼                                                         │
│  LAUNCHING ───────► 启动子工作流                                 │
│       │                                                         │
│       │  ┌─────────────────────────────────┐                   │
│       │  │ CallExecutionWorkflow (并发)    │                   │
│       │  │  ├─ call-001                    │                   │
│       │  │  ├─ call-002                    │                   │
│       │  │  ├─ call-003                    │                   │
│       │  │  └─ ...                         │                   │
│       │  └─────────────────────────────────┘                   │
│       │                                                         │
│       ▼                                                         │
│  RUNNING ─────────► 等待完成 + 进度信号                          │
│       │                                                         │
│       │  每完成一个 call → 发送 progress_update                  │
│       │                                                         │
│       ▼                                                         │
│  FINALIZING ───────► 聚合评测结果                                │
│       │                                                         │
│       ▼                                                         │
│  COMPLETED ───────► 返回最终报告                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、评测指标聚合

### 5.1 支持的评测维度

| 维度 | 指标 | 计算方式 |
|------|------|---------|
| **响应质量** | accuracy, relevance, clarity | LLM-as-Judge |
| **任务完成** | goal_completion_rate, task_success | Grounded Eval + 规则 |
| **用户体验** | satisfaction_score, frustration_rate | 情绪分析 + 交互统计 |
| **效率指标** | avg_turns, avg_latency, token_usage | 统计聚合 |
| **安全性** | pii_exposure, harmful_content | 规则扫描 + ML模型 |
| **一致性** | coherence_score, consistency_rate | LLM-as-Judge |

### 5.2 聚合公式

```python
# futureagi/simulate/services/aggregation_service.py

def aggregate_results(results: List[CallExecutionResult], metrics: List[str]) -> AggregatedMetrics:
    """聚合所有 Call 的评测结果"""

    aggregated = {}

    for metric in metrics:
        values = [
            call.evaluations.get(metric, 0)
            for call in results
        ]

        # 基础统计
        aggregated[metric] = {
            "mean": np.mean(values),
            "median": np.median(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "count": len(values),

            # 分位数
            "p25": np.percentile(values, 25),
            "p75": np.percentile(values, 75),
            "p90": np.percentile(values, 90),
            "p95": np.percentile(values, 95)
        }

        # 按 Persona 特征分组统计
        for group_by in ["technical_level", "interaction_style"]:
            grouped_values = group_by_persona_attribute(results, metric, group_by)
            aggregated[f"{metric}_by_{group_by}"] = grouped_values

    # 趋势分析
    aggregated["trends"] = calculate_trends(results)

    return AggregatedMetrics(**aggregated)
```

---

## 六、完整流程示例

### 6.1 创建测试

```python
# 1. 创建 Persona
persona = Persona.objects.create(
    name="DebugEngineer_Urgent",
    persona_type="CUSTOM",
    technical_proficiency={"overall_level": "intermediate"},
    behavioral_patterns={"interaction_style": "methodical"},
    emotional_state={"stress_level": "high"},
    goals_and_motivations={"primary_goal": "solve_problem"}
)

# 2. 创建 Scenario
scenario_config = {
    "type": "dataset",
    "source_type": "agent_definition",
    "config": {
        "agent_id": "customer_support_v1",
        "num_scenarios": 50,
        "complexity_range": [2, 8]
    }
}

# 3. 启动测试
test_input = TestExecutionInput(
    test_id="test-debug-001",
    persona_id=persona.id,
    scenario_config=scenario_config,
    target_agent_id="customer_support_v1",
    evaluation_metrics=["accuracy", "relevance", "satisfaction"]
)

# 4. 执行 Temporal Workflow
handle = await client.start_workflow(
    TestExecutionWorkflow.run,
    test_input,
    id="test-debug-001"
)

result = await handle.result()
```

### 6.2 结果输出

```json
{
    "test_id": "test-debug-001",
    "status": "COMPLETED",
    "metrics": {
        "accuracy": {
            "mean": 0.85,
            "median": 0.87,
            "std": 0.12,
            "p90": 0.95
        },
        "relevance": {
            "mean": 0.78,
            "median": 0.80
        },
        "satisfaction": {
            "mean": 0.72,
            "by_technical_level": {
                "beginner": 0.65,
                "intermediate": 0.78,
                "advanced": 0.85
            }
        },
        "avg_turns": 4.2,
        "goal_completion_rate": 0.89
    },
    "summary": {
        "total_scenarios": 50,
        "successful_scenarios": 44,
        "failed_scenarios": 6,
        "avg_duration_seconds": 12.5,
        "recommendations": [
            "减少 ambiguous 回复，提高 clarity",
            "针对 beginner 用户简化解释深度",
            "优化 frustration 触发点的响应策略"
        ]
    }
}
```

---

## 七、关键设计优势

### 7.1 真实用户模拟

- **18种预设 Persona** 覆盖典型用户画像
- **14+可配置字段** 精细控制用户行为
- **动态温度参数** 根据 Persona 特征自适应
- **情绪状态跟踪** 模拟真实用户满意度变化

### 7.2 场景多样性

- **三种场景类型** 支持不同测试需求
- **自动场景生成** 从 Agent 定义提取测试点
- **复杂度控制** 调整对话轮数范围
- **状态图驱动** 精确控制对话流程

### 7.3 Temporal 编排

- **并发执行** 50+场景同时运行
- **进度跟踪** 实时反馈完成状态
- **失败隔离** 单个场景失败不影响整体
- **信号机制** 父子工作流高效通信

### 7.4 评测闭环

- **实时评测** 每轮对话即时评估
- **多维指标** 覆盖质量/体验/效率/安全
- **分群统计** 按 Persona 特征分组分析
- **趋势分析** 识别性能退化

---

## 八、扩展方向

### 8.1 语音模拟

企业版支持 **VOICE_SIM** 功能，通过 VAPI 集成实现语音交互测试：

```python
# 企业版语音模拟
persona.voice_profile = {
    "voice_id": "engineer_male_01",
    "speech_rate": "normal",
    "accent": "neutral"
}

scenario.voice_config = {
    "phone_number": "+1xxx",
    "recording_enabled": true
}
```

### 8.2 多 Persona 协作

测试多用户协作场景：

```python
# 多 Persona 协作测试
multi_persona_test = {
    "personas": [
        {"role": "primary_user", "persona_id": "pm_001"},
        {"role": "stakeholder", "persona_id": "exec_001"},
        {"role": "technical_reviewer", "persona_id": "eng_001"}
    ],
    "interaction_pattern": "sequential",  # 或 "parallel"
    "conflict_scenarios": ["deadline_conflict", "scope_disagreement"]
}
```

### 8.3 自适应场景生成

根据历史评测结果动态调整场景：

```python
# 自适应场景生成
adaptive_config = {
    "baseline_scenarios": 30,
    "adaptive_scenarios": 20,
    "focus_areas": ["low_accuracy_scenarios", "high_frustration_scenarios"],
    "diversity_boost": true
}
```

---

## 九、总结

Future AGI 的测试用例生成机制通过 **Persona × Scenario × SimulatorAgent** 三维架构实现了：

1. **真实用户模拟**：18种预设 Persona + 14+可配置字段，精细控制用户行为
2. **场景多样性**：三种场景类型（Dataset/Graph/Script），自动生成 + 手动定义
3. **智能编排**：Temporal Workflow 父子工作流，并发执行 + 进度跟踪
4. **闭环评测**：实时评测 + 多维指标聚合 + 分群统计 + 趋势分析

这套机制让 Agent 评测从"人工测试"升级为"自动化大规模真实场景模拟"，显著提升评测效率和覆盖率。