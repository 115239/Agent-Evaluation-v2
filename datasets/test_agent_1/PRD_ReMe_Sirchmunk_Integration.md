# PRD: ReMe + Sirchmunk 集成产品需求文档

**文档版本**: v2.0  
**创建日期**: 2026-04-16  
**最后更新**: 2026-04-16  
**产品名称**: ReMe-Sirchmunk 多租户智能记忆与检索系统  

---

## 1. 产品概述

### 1.1 产品定位

ReMe-Sirchmunk 是一个**企业级多租户 AI Agent 记忆管理与文档检索平台**，已完成深度集成：

**核心特性**:
- **ReMe**: 多租户记忆管理框架，提供上下文压缩、长期记忆持久化、会话隔离
- **Sirchmunk**: 通过 MCP 协议集成的无索引实时文档检索引擎
- **TenantAgentPool**: 租户级资源共享 + 会话级隔离的双层架构

### 1.2 已实现的集成架构

**当前状态**: ✅ **已完成集成**

```
┌─────────────────────────────────────────────────────────────────┐
│                    HTTP/MCP/CLI 服务层                           │
│  FastAPI REST + SSE / MCP stdio / CLI                           │
├─────────────────────────────────────────────────────────────────┤
│                    QueryHandler（路由层）                        │
│  InputAdapter → TenantAgentPool → OutputAdapter                 │
├─────────────────────────────────────────────────────────────────┤
│              TenantAgentPool（多租户核心）                       │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │ TenantResources      │      │ Session              │        │
│  │ (租户级共享)          │      │ (会话级隔离)          │        │
│  │ - as_llm             │      │ - session_id         │        │
│  │ - toolkit            │      │ - messages           │        │
│  │ - file_store         │      │ - previous_summary   │        │
│  │ - mcp_session ✅     │      │ - dialog_path        │        │
│  │ - sirchmunk_search ✅│      └──────────────────────┘        │
│  └──────────────────────┘                                       │
├─────────────────────────────────────────────────────────────────┤
│              记忆管理层（已集成）                                │
│  ContextChecker → MemoryCompactor → MemorySummarizer            │
│  ToolResultCompactor → SessionPersistence                       │
├─────────────────────────────────────────────────────────────────┤
│              工具层（已集成 Sirchmunk）                          │
│  FileIO / Shell / MemorySearch / sirchmunk_search (MCP) ✅      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 核心价值主张

| 维度 | ReMe | Sirchmunk | **已实现的集成价值** |
|------|------|-----------|---------------------|
| **多租户隔离** | ✅ TenantAgentPool | ❌ | ✅ 每租户独立 working_dir + MCP 连接 |
| **记忆管理** | ✅ 上下文压缩、对话持久化 | ❌ | ✅ 自动压缩 + 持久化到 memory/*.md |
| **文档检索** | ✅ memory_search | ✅ sirchmunk_search | ✅ 双工具并存，Agent 自主选择 |
| **知识沉淀** | ✅ Markdown 记忆 | ✅ KnowledgeCluster | ✅ 双层知识：个人记忆 + 文档聚类 |
| **MCP 集成** | ✅ SSE 长连接 | ✅ MCP Server | ✅ 通过 MCP 协议无缝集成 |
| **会话管理** | ✅ Session 持久化 | ❌ | ✅ 自动保存 + 恢复会话 |

### 1.4 目标用户

1. **企业 AI 平台**: 需要多租户隔离的 Agent 服务
2. **知识库应用**: 私有文档检索 + 用户记忆管理
3. **编程助手**: 代码库检索 + 编码偏好记忆（如 CoPaw）
4. **客服系统**: 产品文档检索 + 客户历史记录

---

## 2. 系统架构（已实现）

### 2.1 TenantAgentPool 双层架构

**核心设计**: 租户级资源共享 + 会话级消息隔离

```
TenantAgentPool (1300+ 行核心文件)
├── TenantResources（租户级共享，长生命周期）
│   ├── as_llm: ChatModelBase              # LLM 实例
│   ├── as_llm_formatter: FormatterBase    # 消息格式化器
│   ├── toolkit: Toolkit                   # 工具集（懒加载）
│   │   ├── FileIO (read/write/edit)
│   │   ├── Shell (execute_shell_command)
│   │   ├── memory_search                  # ReMe 记忆检索
│   │   └── sirchmunk_search ✅            # MCP 工具（SSE 长连接）
│   ├── file_store: ChromaDB               # 租户隔离的向量索引
│   ├── file_watcher: FileWatcher          # 监控 .md 文件变化
│   ├── tool_result_compactor              # 工具结果截断
│   ├── mcp_session: ClientSession ✅      # SSE 连接到 Sirchmunk
│   ├── working_path: .reme/{tenant_id}/
│   ├── memory_path: .reme/{tenant_id}/memory/
│   ├── dialog_path: .reme/{tenant_id}/dialog/
│   └── path_index: dict ✅                # 路径修正索引
│
└── Session（会话级隔离，短生命周期）
    ├── session_id: str
    ├── tenant_id: str
    ├── messages: list[Msg]                # 对话历史
    ├── previous_summary: str              # 压缩摘要
    ├── created_at / last_used: float
    └── dialog_path / session_state_path   # 持久化路径
```

**关键特性**:
- ✅ **MCP SSE 长连接**: 每个租户维护一个到 Sirchmunk 的 SSE 连接
- ✅ **路径修正**: `_fix_search_paths()` 自动修正 sirchmunk_search 的路径参数
- ✅ **自动保存**: 5 分钟定时保存所有活跃会话
- ✅ **会话恢复**: `recover_session()` 从持久化文件恢复会话
- ✅ **资源清理**: 空闲超时自动清理（会话 30 分钟，租户 1 小时）

### 2.2 数据流设计（已实现）

#### 2.2.1 查询处理流程

```
用户请求 (HTTP/MCP/CLI)
  ↓
InputAdapter.parse_request()
  → QueryRequest(tenant_id, session_id, query)
  ↓
TenantAgentPool.query()
  ↓
获取/创建 Session
  ↓
获取 TenantResources（懒加载 toolkit + MCP 连接）
  ↓
_execute_with_session()
  ├─ compact_tool_result()        # 截断超长工具输出
  ├─ _validate_messages()         # 校验 tool_use/tool_result 完整性
  ├─ _pre_reasoning_hook()        # 上下文检查 + 压缩
  │   ├─ check_context()          # Token 计数
  │   ├─ compact_memory()         # 生成摘要（同步）
  │   ├─ persist_messages()       # 持久化到 dialog/*.jsonl
  │   └─ _schedule_summary_task() # 异步写入 memory/*.md
  ├─ _build_system_prompt()       # 构建系统提示词
  │   ├─ 注入 soul.md（全局提示词）
  │   ├─ 注入 skills 信息
  │   └─ 注入 previous_summary
  ├─ ReActAgent(model, toolkit, sys_prompt)
  └─ stream_printing_messages()   # 流式推理
      ↓
  OutputAdapter.send_stream()
      ↓
  更新 Session.messages
```

#### 2.2.2 Sirchmunk MCP 集成流程（已实现）

```
_init_mcp_connection()
  ↓
遍历 config.mcp_servers.mcpServers
  ↓
sse_client(url) → SSE 长连接
  ↓
ClientSession(read, write)
  ↓
session.initialize() + session.list_tools()
  ↓
_register_mcp_tools_from_session()
  ├─ 为每个 MCP tool 创建 wrapper
  ├─ sirchmunk_search wrapper:
  │   ├─ _fix_search_paths() 修正路径 ✅
  │   ├─ session.call_tool(name, kwargs)
  │   └─ 返回 ToolResponse
  └─ toolkit.register_tool_function(wrapper, json_schema)
```

**路径修正机制** (`_fix_search_paths`):
```python
# 问题：Agent 可能传入相对路径或不存在的路径
# 解决：建立 basename → 绝对路径 的索引
path_index = _build_path_index("/data/云南项目知识文档")
# {"项目A": "/data/云南项目知识文档/子目录/项目A", ...}

# 调用 sirchmunk_search 时自动修正
paths = _fix_search_paths(["项目A", "不存在的路径"], path_index)
# → ["/data/云南项目知识文档/子目录/项目A", "不存在的路径"]
```

#### 2.2.3 记忆管理流程（已实现）

```
_pre_reasoning_hook()
  ↓
ContextChecker.check_context()
  ├─ Token 计数（HuggingFace tokenizer）
  ├─ 判断是否超过阈值（context_window * compact_ratio）
  └─ 拆分为 messages_to_compact + messages_to_keep
  ↓
messages_to_compact 非空？
  ↓ 是
SessionPersistence.persist_messages()
  → 写入 dialog/YYYY-MM-DD.jsonl（原始对话）
  ↓
MemoryCompactor.compact()
  ├─ 调用 ReActAgent（reme_compactor）
  ├─ 生成结构化摘要（Goal/Progress/Decisions...）
  └─ 返回 new_summary
  ↓
更新 Session
  ├─ session.previous_summary = new_summary
  └─ session.messages = messages_to_keep
  ↓
_schedule_summary_task()（异步后台）
  ├─ MemorySummarizer.summarize_to_files()
  ├─ 调用 ReActAgent（reme_summarizer）
  ├─ 使用 FileIO 工具（read/write/edit）
  └─ 写入 memory/YYYY-MM-DD.md
```

---

## 3. 核心功能清单（已实现 vs 待优化）

### 3.1 记忆管理 (ReMe) - ✅ 已实现

#### 3.1.1 上下文管理

| 功能 | 状态 | 实现位置 | 说明 |
|------|------|----------|------|
| **Token 计数** | ✅ | `ContextChecker` | HuggingFace tokenizer，支持 Qwen/GPT 等 |
| **自动压缩** | ✅ | `MemoryCompactor` | 超过 `context_window * compact_ratio` 触发 |
| **工具结果截断** | ✅ | `ToolResultCompactor` | 超过 1000 字符截断，保存到 `tool_result/*.txt` |
| **增量摘要** | ✅ | `compact_memory()` | 支持 `previous_summary` 参数 |
| **消息校验** | ✅ | `_validate_messages()` | 裁剪不完整的 tool_use/tool_result 对 |

**配置参数** (已实现):
```yaml
context_window_tokens: 100000   # 上下文窗口
reserve_tokens: 30000           # 响应预留
keep_recent_tokens: 10000       # 保留最近消息
compact_ratio: 0.7              # 压缩触发比例（70%）
tool_result_threshold: 1000     # 工具结果截断阈值（字符）
retention_days: 7               # 工具结果保留天数
```

#### 3.1.2 长期记忆

| 功能 | 状态 | 实现位置 | 说明 |
|------|------|----------|------|
| **记忆持久化** | ✅ | `MemorySummarizer` | ReActAgent + FileIO 工具，写入 `memory/*.md` |
| **记忆检索** | ✅ | `memory_search` 工具 | 向量 + BM25 混合检索（权重 0.7:0.3） |
| **文件监控** | ✅ | `FileWatcher` | 监控 `.md` 文件变化，自动更新索引 |
| **跨会话记忆** | ✅ | `_build_system_prompt()` | 自动注入 `previous_summary` |
| **soul.md 注入** | ✅ | `_build_system_prompt()` | 全局系统提示词 |

**文件结构** (已实现):
```
.reme/{tenant_id}/
├── soul.md                    # 全局系统提示词（可选）
├── MEMORY.md                  # 长期记忆（手动维护）
├── memory/
│   └── 2026-04-16.md          # 每日摘要（自动生成）
├── dialog/
│   └── 2026-04-16.jsonl       # 原始对话（自动保存）
├── tool_result/
│   └── <uuid>.txt             # 工具输出缓存（自动清理）
├── session_state/
│   └── {session_id}.json      # 会话状态（自动保存）
└── file_store/                # ChromaDB 向量索引
```

#### 3.1.3 会话管理

| 功能 | 状态 | 实现位置 | 说明 |
|------|------|----------|------|
| **会话持久化** | ✅ | `SessionPersistence` | 自动保存到 `dialog/*.jsonl` |
| **会话恢复** | ✅ | `recover_session()` | 从 `session_state/*.json` 恢复 |
| **自动保存** | ✅ | `_auto_save_loop()` | 5 分钟定时保存所有活跃会话 |
| **多租户隔离** | ✅ | `TenantAgentPool` | 每租户独立 working_dir |
| **空闲清理** | ✅ | `cleanup_idle_sessions()` | 30 分钟空闲自动清理 |

### 3.2 文档检索 (Sirchmunk) - ✅ 已通过 MCP 集成

#### 3.2.1 MCP 集成

| 功能 | 状态 | 实现位置 | 说明 |
|------|------|----------|------|
| **SSE 长连接** | ✅ | `_init_mcp_connection()` | 每租户维护一个 SSE 连接 |
| **工具注册** | ✅ | `_register_mcp_tools_from_session()` | 动态注册 MCP 工具到 toolkit |
| **路径修正** | ✅ | `_fix_search_paths()` | 自动修正相对路径/不存在路径 |
| **多服务器支持** | ✅ | 遍历 `mcp_servers.mcpServers` | 支持连接多个 MCP 服务器 |

**sirchmunk_search 工具参数** (已实现):
```python
async def sirchmunk_search(
    query: str,                      # 搜索查询
    paths: list[str] | str,          # 搜索路径（自动修正）
    mode: str = "FAST",              # FAST/DEEP/FILENAME_ONLY
    max_depth: int = 5,
    top_k_files: int = 3,
    max_loops: int = 10,
    max_token_budget: int = 128000,
    enable_dir_scan: bool = True,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    return_context: bool = False,
) -> ToolResponse
```

#### 3.2.2 Sirchmunk 特性（由 Sirchmunk 服务端实现）

| 特性 | 说明 | ReMe 侧状态 |
|------|------|------------|
| **FAST 模式** | 2 次 LLM 调用，2-5s | ✅ 通过 MCP 调用 |
| **DEEP 模式** | 10-30 次 LLM 调用，10-30s | ✅ 通过 MCP 调用 |
| **知识聚类** | KnowledgeCluster 自动生成 | ✅ Sirchmunk 侧管理 |
| **蒙特卡洛采样** | 证据提取算法 | ✅ Sirchmunk 侧实现 |

### 3.3 多租户架构 - ✅ 已实现

#### 3.3.1 租户管理

| 功能 | 状态 | 实现位置 | 说明 |
|------|------|----------|------|
| **自动创建租户** | ✅ | `_load_tenant_config()` | 以 default 租户为模板自动创建 |
| **租户隔离** | ✅ | `TenantResources` | 独立 working_dir + file_store + MCP 连接 |
| **资源共享** | ✅ | `TenantResources` | 同租户会话共享 LLM + toolkit |
| **空闲清理** | ✅ | `cleanup_idle_tenants()` | 1 小时无会话自动清理资源 |

#### 3.3.2 Skill 系统

| 功能 | 状态 | 实现位置 | 说明 |
|------|------|----------|------|
| **Skill 发现** | ✅ | `_discover_skills()` | 扫描 `{working_dir}/skills/` |
| **SKILL.md 解析** | ✅ | `_load_skill_metadata()` | 解析 YAML frontmatter |
| **工具动态加载** | ✅ | `_load_skill_tools()` | 导入 `tools.py` 并注册 |
| **系统提示词注入** | ✅ | `_build_skill_prompt()` | 自动注入 skill 说明到 system prompt |

**Skill 目录结构**:
```
.reme/{tenant_id}/skills/
└── my_skill/
    ├── SKILL.md          # 元数据（name, description）
    └── tools.py          # 工具函数（可选）
```

---

## 4. 技术规格（已实现）

### 4.1 性能指标

| 指标 | 当前实现 | 测量方法 |
|------|----------|----------|
| **上下文压缩率** | > 95% | (原始 tokens - 压缩后) / 原始 tokens |
| **会话恢复时间** | < 100ms | 从 session_state/*.json 加载 |
| **MCP 工具调用延迟** | 取决于 Sirchmunk | SSE 长连接，无额外握手开销 |
| **自动保存间隔** | 5 分钟 | 可配置 `auto_save_interval` |
| **空闲会话清理** | 30 分钟 | 可配置 `session_idle_timeout` |
| **空闲租户清理** | 1 小时 | 可配置 `tenant_idle_timeout` |

### 4.2 可扩展性

| 维度 | 当前规格 | 配置参数 |
|------|----------|----------|
| **最大会话数** | 1000 | `max_sessions` |
| **最大租户数** | 100 | `max_tenants` |
| **上下文窗口** | 100K tokens | `context_window_tokens` |
| **文档数量** | 取决于 Sirchmunk | 无限制（无索引架构） |
| **并发查询** | 取决于 LLM API | 异步处理 |

### 4.3 兼容性

#### 4.3.1 LLM 提供商（已测试）

- ✅ OpenAI (GPT-4, GPT-5.2)
- ✅ SiliconFlow (Qwen3.5-397B-A17B)
- ✅ MiniMax (MiniMax-M2.7)
- ✅ 所有 OpenAI 兼容 API

**配置示例**:
```yaml
shared:
  as_llms:
    default:
      backend: openai
      model_name: Qwen/Qwen3.5-397B-A17B
# .env 文件
LLM_API_KEY=<YOUR_API_KEY>
LLM_BASE_URL=https://api.siliconflow.cn/v1
```

#### 4.3.2 部署方式（已实现）

| 方式 | 状态 | 入口命令 | 说明 |
|------|------|----------|------|
| **HTTP API** | ✅ | `reme2 backend=http` | FastAPI + SSE 流式 |
| **MCP Server** | ✅ | `reme2 backend=mcp` | stdio/SSE 传输 |
| **CLI** | ✅ | `remecli` | 命令行交互 |
| **Python SDK** | ✅ | `from reme import ReMeLight` | 直接集成 |

#### 4.3.3 存储后端（已实现）

| 组件 | 支持的后端 | 默认 |
|------|-----------|------|
| **FileStore** | chroma, local, sqlite | chroma |
| **VectorStore** | chroma, local, es, pgvector, qdrant | chroma |
| **FileWatcher** | full, delta | full |

---

## 5. API 设计（已实现）

### 5.1 HTTP API

#### 5.1.1 聊天接口

```http
POST /chat
Content-Type: application/json

{
    "tenant_id": "alice",
    "session_id": "optional-session-id",
    "query": "如何实现 Transformer Attention？",
    "stream": true
}

Response (SSE):
data: {"chunk_type": "think", "chunk": "思考中..."}
data: {"chunk_type": "tool", "chunk": {"name": "sirchmunk_search", "input": {...}}}
data: {"chunk_type": "answer", "chunk": "Transformer..."}
data: {"chunk_type": "done", "done": true, "metadata": {"session_id": "..."}}
```

#### 5.1.2 会话管理

```http
# 创建会话
POST /session/create
{"tenant_id": "alice"}

# 获取会话历史
GET /session/{session_id}/history?limit=50

# 关闭会话
POST /session/{session_id}/close
```

### 5.2 MCP 工具定义（已实现）

**已注册的 MCP 工具**:
```json
{
  "tools": [
    {
      "name": "sirchmunk_search",
      "description": "Search documents using Sirchmunk",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "paths": {
            "oneOf": [
              {"type": "string"},
              {"type": "array", "items": {"type": "string"}}
            ]
          },
          "mode": {"enum": ["FAST", "DEEP", "FILENAME_ONLY"]},
          "max_depth": {"type": "integer"},
          "top_k_files": {"type": "integer"}
        },
        "required": ["query"]
      }
    }
  ]
}
```

### 5.3 配置文件格式（已实现）

**service.yaml 示例**:
```yaml
backend: http
working_dir: .reme

shared:
  as_llms:
    default:
      backend: openai
      model_name: Qwen/Qwen3.5-397B-A17B
  
  embedding_models:
    default:
      backend: openai
      model_name: BAAI/bge-m3
      dimensions: 1024
  
  as_token_counters:
    default:
      backend: hf
      pretrained_model_name_or_path: Qwen/Qwen2.5-7B-Instruct

tenants:
  default:
    working_dir: .reme/default
    language: zh
    context_window_tokens: 100000
    reserve_tokens: 30000
    keep_recent_tokens: 10000
    compact_ratio: 0.7
    tool_result_threshold: 1000
    retention_days: 7
    auto_save_interval: 300
    session_timeout: 1800
    
    mcp_servers:
      mcpServers:
        sirchmunk:
          url: http://localhost:8080/sse
    
    file_watchers:
      default:
        watch_paths:
          - .reme/default/memory
          - .reme/default/MEMORY.md

default_tenant: default
```

---

## 6. 用户场景（基于已实现功能）

### 6.1 场景 1: 企业多租户知识库

**背景**: 企业内部多个部门使用同一套 AI 服务，需要数据隔离

**实现方式**:
1. 配置多个租户（如 `tenants: {sales, engineering, hr}`）
2. 每个租户独立的 working_dir 和 MCP 连接
3. HTTP API 请求时指定 `tenant_id`

**流程**:
```
销售部门用户 → POST /chat {"tenant_id": "sales", "query": "..."}
  → TenantAgentPool 获取/创建 sales 租户资源
  → 使用 sales 的 file_store 检索记忆
  → 使用 sales 的 MCP 连接调用 sirchmunk_search
  → 结果保存到 .reme/sales/memory/
```

### 6.2 场景 2: 编程助手（CoPaw 集成）

**背景**: 开发者需要在大型代码库中快速查找代码 + 记住编码偏好

**实现方式**:
1. CoPaw 继承 `ReMeLight`
2. 配置 Sirchmunk MCP 服务器指向代码库
3. 使用 `soul.md` 定义编程助手人格

**流程**:
```
用户: "我喜欢使用 TypeScript strict mode"
  → ReMe 记录到 MEMORY.md

用户: "如何实现 React Hooks？"
  → Agent 调用 sirchmunk_search(paths=["/path/to/codebase"])
  → 返回相关代码片段
  → MemorySummarizer 异步写入 memory/YYYY-MM-DD.md

用户: "根据我的偏好重构这段代码"
  → Agent 调用 memory_search("TypeScript 偏好")
  → 融合记忆 + 代码检索结果
  → 生成重构建议
```

### 6.3 场景 3: 客服系统

**背景**: 客服需要快速查找产品文档 + 记录客户问题历史

**实现方式**:
1. 每个客户一个 session_id
2. Sirchmunk 索引产品文档
3. ReMe 记录客户问题历史

**流程**:
```
客户: "如何重置密码？"
  → sirchmunk_search(query="重置密码", paths=["/产品文档"])
  → 返回重置密码步骤
  → MemorySummarizer 记录客户问题

客户: "上次你说的方法不行"
  → memory_search("重置密码")
  → 检索历史对话
  → 提供替代方案
```

### 6.4 场景 4: 会话恢复

**背景**: 用户断线重连，需要恢复之前的对话

**实现方式**:
1. 自动保存机制（5 分钟一次）
2. 会话状态持久化到 `session_state/*.json`

**流程**:
```
用户断线
  → _auto_save_loop() 定时保存会话状态
  → 写入 session_state/{session_id}.json

用户重连
  → POST /chat {"session_id": "xxx", ...}
  → TenantAgentPool.recover_session(session_id)
  → 从 session_state/*.json 加载 messages + previous_summary
  → 继续对话
```

---

## 7. 测试要点

### 7.1 功能测试

#### 7.1.1 多租户隔离测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| **租户数据隔离** | 创建两个租户，分别写入记忆 | 租户 A 无法检索到租户 B 的记忆 |
| **自动创建租户** | 请求不存在的 tenant_id | 自动以 default 为模板创建 |
| **工作目录隔离** | 检查文件系统 | `.reme/tenant_a/` 和 `.reme/tenant_b/` 独立 |
| **MCP 连接隔离** | 两个租户同时调用 sirchmunk_search | 各自使用独立的 SSE 连接 |

#### 7.1.2 会话管理测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| **会话创建** | POST /chat 不带 session_id | 自动生成新 session_id |
| **会话恢复** | 断线重连，使用相同 session_id | 恢复历史对话 |
| **自动保存** | 等待 5 分钟 | session_state/*.json 自动更新 |
| **空闲清理** | 会话空闲 30 分钟 | 自动关闭并持久化 |
| **消息校验** | 发送不完整的 tool_use | 自动裁剪并补充说明消息 |

#### 7.1.3 记忆管理测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| **上下文压缩** | 发送超过 70K tokens 的对话 | 自动触发压缩，生成摘要 |
| **工具结果截断** | 工具返回超过 1000 字符 | 截断并保存到 tool_result/*.txt |
| **记忆持久化** | 触发压缩后检查文件 | memory/YYYY-MM-DD.md 自动生成 |
| **记忆检索** | 调用 memory_search 工具 | 返回相关记忆片段 |
| **文件监控** | 手动修改 memory/*.md | file_store 自动更新索引 |

#### 7.1.4 MCP 集成测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| **SSE 连接** | 启动服务 | 成功连接到 Sirchmunk MCP 服务器 |
| **工具注册** | 检查 toolkit | sirchmunk_search 工具已注册 |
| **路径修正** | 传入相对路径 "项目A" | 自动修正为绝对路径 |
| **工具调用** | Agent 调用 sirchmunk_search | 返回文档检索结果 |
| **连接重连** | 重启 Sirchmunk 服务 | 自动重连 |

#### 7.1.5 Skill 系统测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| **Skill 发现** | 在 skills/ 目录放置 SKILL.md | 自动加载 skill |
| **工具注册** | Skill 包含 tools.py | 工具函数自动注册到 toolkit |
| **提示词注入** | 检查 system prompt | 包含 skill 说明 |

### 7.2 性能测试

| 测试项 | 测试方法 | 性能指标 |
|--------|----------|----------|
| **上下文压缩率** | 100K tokens 对话压缩 | > 95% 压缩率 |
| **会话恢复时间** | 恢复包含 100 条消息的会话 | < 100ms |
| **并发会话** | 10 个租户同时查询 | 无阻塞，正常响应 |
| **内存占用** | 100 个活跃会话 | < 2GB |

### 7.3 稳定性测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| **长时间运行** | 服务运行 24 小时 | 无内存泄漏，正常运行 |
| **异常恢复** | 模拟 LLM API 失败 | 返回错误信息，不崩溃 |
| **MCP 断线** | 关闭 Sirchmunk 服务 | 降级到仅使用 memory_search |
| **磁盘满** | 模拟磁盘空间不足 | 返回错误，自动清理过期文件 |

### 7.4 边界条件测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| **空查询** | query="" | 返回错误提示 |
| **超长查询** | query 长度 > 10K 字符 | 正常处理或返回错误 |
| **不存在的租户** | tenant_id="nonexistent" | 自动创建租户 |
| **不存在的会话** | session_id="invalid" | 返回错误或创建新会话 |
| **路径不存在** | sirchmunk_search paths=["不存在"] | 尝试修正，失败则传递原路径 |

---

## 8. 附录

### 8.1 术语表

| 术语 | 定义 |
|------|------|
| **TenantAgentPool** | 多租户 Agent 池，管理租户资源和会话 |
| **TenantResources** | 租户级共享资源（LLM、toolkit、MCP 连接等） |
| **Session** | 会话级隔离的对话历史 |
| **MCP** | Model Context Protocol，模型上下文协议 |
| **SSE** | Server-Sent Events，服务器推送事件 |
| **ReMeLight** | ReMe 的文件记忆系统 |
| **KnowledgeCluster** | Sirchmunk 的知识聚类单元 |
| **soul.md** | 全局系统提示词文件 |
| **Skill** | 可动态加载的工具集 |
| **ReActAgent** | AgentScope 的 Think-Act-Observe 推理循环 |

### 8.2 关键文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `reme/core/tenant_agent_pool.py` | 1833 | 核心多租户管理 |
| `reme/core/context_checker.py` | ~200 | 上下文检查 |
| `reme/core/memory_compactor.py` | ~300 | 记忆压缩 |
| `reme/core/memory_summarizer.py` | ~400 | 记忆持久化 |
| `reme/core/session_persistence.py` | ~200 | 会话持久化 |
| `reme/core/tool_result_compactor.py` | ~150 | 工具结果截断 |
| `reme/core/service/http_service.py` | ~300 | HTTP 服务 |
| `reme/core/service/mcp_service.py` | ~200 | MCP 服务 |

### 8.3 配置示例

**最小化配置** (`.env` + `service.yaml`):
```bash
# .env
LLM_API_KEY=<YOUR_API_KEY>
LLM_BASE_URL=https://api.siliconflow.cn/v1
```

```yaml
# service.yaml
backend: http
working_dir: .reme

shared:
  as_llms:
    default:
      backend: openai
      model_name: Qwen/Qwen3.5-397B-A17B

tenants:
  default:
    working_dir: .reme/default
    mcp_servers:
      mcpServers:
        sirchmunk:
          url: http://localhost:8080/sse

default_tenant: default
```

### 8.4 环境变量清单

| 变量 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `LLM_API_KEY` | ✅ | LLM API 密钥 | `sk-xxx` |
| `LLM_BASE_URL` | ✅ | LLM API 地址 | `https://api.siliconflow.cn/v1` |
| `EMBEDDING_API_KEY` | ❌ | Embedding API 密钥 | `sk-xxx` |
| `EMBEDDING_BASE_URL` | ❌ | Embedding API 地址 | 同上 |
| `SIRCHMUNK_DEFAULT_SEARCH_BASE` | ❌ | 路径索引基础目录 | `/data/云南项目知识文档` |

### 8.5 参考资料

- [ReMe GitHub](https://github.com/agentscope-ai/ReMe)
- [Sirchmunk GitHub](https://github.com/modelscope/sirchmunk)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [AgentScope 文档](https://agentscope.io)
- [内部文档](kiro_docs/reme/)

---

**文档维护者**: AI Team  
**最后更新**: 2026-04-16  
**版本**: v2.0（测试版）  
**目标读者**: 测试团队
