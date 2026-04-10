# ADR-002：Phase 2a 分层会话记忆与统一对话路径

## 背景

Phase 1 将会话全文存入 Redis，流式接口在路由层手写「检索 → 流式生成 → 存 Redis」，与非流式的 LangGraph 路径重复，且长对话会线性膨胀上下文成本。

## 决策

1. **Redis 载荷**：采用 `{"v":2,"summary":str,"messages":[...]}`；兼容旧版纯列表 JSON，首次解析时对过长列表按 `MEMORY_RECENT_TURNS_MAX` 截断尾部窗口。
2. **滑动窗口**：仅将近期完整轮次注入 LangChain 消息列表；更早内容进入 `summary`。
3. **摘要压缩**：当轮次超过上限 **或近期消息 token 数超过 `MEMORY_MAX_TOKENS`** 时，将超出部分一次性合并进既有摘要（单次 LLM 调用），温度绑定为约 0.2，字数受 `MEMORY_SUMMARY_MAX_CHARS` 约束。Token 计数优先使用 tiktoken，不可用时回退到字符启发估算。
4. **统一路径**：流式与非流式均走同一个 LangGraph 编排 (`retrieve_context → generate_response → save_memory`)。
   - 非流式：`await graph.ainvoke()`
   - 流式：`graph.astream_events(version="v2")`，过滤 `on_chat_model_stream` 事件（按 `metadata.langgraph_node == "generate_response"` 区分节点）
   - `generate_response` 节点为 async，内部调用 `llm.astream()` 以产生 token 级事件
5. **Prompt 集中管理**：所有 prompt 模板（系统提示、摘要合并）统一放在 `app/agent/prompts.py`。

## 后果

- **优点**：控制上下文长度（双重门槛：轮次 + token）；流式与非流式完全共用同一张图和同一组节点；摘要失败时有纯文本拼接回退。
- **代价**：超限时触发额外 LLM 调用（压缩）；Redis 中不再保存完整逐字历史（仅摘要 + 窗口）；流式依赖 `astream_events` 的 event metadata 格式。

## 备选方案

- **向量记忆库**：延迟到 Phase 2b/3，与 Intent 路由一并评估。
- **每轮单独摘要**：调用次数多、延迟高，故采用批量折叠。
- **按轮次压缩（无 token 门槛）**：初版实现；缺点是短轮次浪费窗口、长轮次可能超上下文。
