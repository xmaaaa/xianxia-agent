# ADR-003：Phase 2b 意图路由（混合分类 + LangGraph 条件边）

## 背景

Phase 2a 的 graph 是线性的 `retrieve_context → generate_response → save_memory`。意图判断靠硬编码关键词，只区分 `skill_qa` 和 `roleplay`，且判断逻辑和 RAG 检索耦合在同一个节点。

## 决策

1. **混合分类策略**：先走关键词匹配（零成本、低延迟），匹配不到 fallback 到 LLM 分类（调 DeepSeek，temperature=0，max_tokens=20）。LLM 返回无法解析时默认 `roleplay`。
2. **四种意图**：`roleplay`（角色扮演/闲聊）、`skill_qa`（功法知识问答）、`explore`（场景探索）、`status_query`（查看角色属性）。
3. **LangGraph 条件边**：`classify_intent` 节点输出 intent 标签后，通过 `add_conditional_edges` 分发到 4 个轻量 `prepare_*` 节点，各自做差异化的上下文准备（RAG / DB 查询 / 无操作），再汇聚到共享的 `generate_response`。
4. **意图专用 hint**：explore 和 status_query 有额外 system prompt 片段（`EXPLORE_HINT`、`STATUS_QUERY_HINT`），在 `build_system_and_llm_messages` 中根据 intent 动态拼入。
5. **所有 prompt 模板仍集中在 `prompts.py`**。

## 后果

- **优点**：graph 结构直观体现分支逻辑；新增意图只需加关键词/prepare 节点/条件边映射；关键词匹配覆盖大部分场景，LLM 调用仅在模糊输入时触发。
- **代价**：LLM fallback 增加约 0.5-1 秒延迟（仅在关键词未命中时）；classify_intent 节点的 LLM 调用不走 `astream_events` token 流式（用户无感知）。

## 备选方案

- **纯 LLM 分类**：每条消息都调 LLM，延迟和成本偏高。
- **纯关键词**：零成本但不够灵活，「我想看看这里有什么」很难用关键词匹配到 explore。
- **Embedding 相似度分类**：需要维护 intent 向量库，目前 embedding 配置不完善，延后考虑。
