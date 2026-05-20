# 修仙 AI Agent（Phase 2d）

基于 **LangGraph** 编排、**Chroma** 本地向量库与 **FastAPI** 的修仙题材对话 Agent：玩家创建角色后与「叙事之灵」对话。Graph 内部通过 **意图路由**（关键词优先 + LLM fallback）分发到不同处理分支（角色扮演 / 功法问答 / 场景探索 / 修炼 / 调息 / 使用物品 / 状态查询），各分支做差异化上下文准备后统一生成。Phase 2d 新增了独立游戏规则引擎：探索、修炼、调息和使用物品会产生可落账的角色状态变化，支持修为增长、境界突破、背包增减和近事记录。会话记忆在 **Redis** 中分层存储：**滚动摘要** + **近期原文轮次**。MVP 前端为 **Streamlit**，流式与非流式共用同一张 LangGraph。

**建议运行环境：Python 3.11+**（依赖栈按 3.11 测试；生产请固定解释器版本。）

## 架构（Mermaid）

```mermaid
flowchart LR
  subgraph client [Client]
    ST[Streamlit MVP]
  end
  subgraph api [FastAPI]
    CR["/api/v1/characters"]
    CH["/api/v1/chat"]
  end
  subgraph agent [LangGraph]
    CLS[classify_intent]
    PR[prepare_roleplay]
    PS[prepare_skill_qa]
    PE[prepare_explore]
    PQ[prepare_status_query]
    G[generate_response]
    AGD[apply_game_delta]
    S[save_memory]
    CLS -->|roleplay| PR
    CLS -->|skill_qa| PS
    CLS -->|explore| PE
    CLS -->|status_query| PQ
    PR --> G
    PS --> G
    PE --> G
    PQ --> G
    G --> AGD
    AGD --> S
  end
  subgraph data [Data]
    PG[(PostgreSQL)]
    RD["Redis<br/>摘要+近期轮次"]
    CHM[(Chroma 本地)]
  end
  ST --> CR
  ST --> CH
  CH --> agent
  CR --> PG
  CH --> RD
  CH --> PG
  PS --> CHM
  PQ --> PG
  AGD --> PG
  S --> RD
```

## 快速启动

### 1. 基础设施（PostgreSQL + Redis）

```bash
docker compose up -d
```

默认数据库：`postgresql://xianxia:xianxia@localhost:5432/xianxia_db`（应用在 `DATABASE_URL` 中请使用 `postgresql+psycopg://...` 以走 psycopg3 驱动）。

### 2. Python 环境与依赖

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY
```

### 3. 数据库迁移

```bash
export PYTHONPATH=.
alembic upgrade head
```

### 4. 启动 API

```bash
export PYTHONPATH=.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：<http://127.0.0.1:8000/health>

### 5. 启动 Streamlit 前端

```bash
source .venv/bin/activate
export PYTHONPATH=.
streamlit run frontend/streamlit_app.py
```

浏览器打开 Streamlit 提示的地址（默认 <http://localhost:8501>），侧栏填写 `user_id`、创建或选择角色后即可对话。流式对话调用 `POST /api/v1/chat/stream`。

### 6. 测试

```bash
export PYTHONPATH=.
pytest -q
```

## API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/characters/` | 创建角色 |
| GET | `/api/v1/characters/?user_id=...` | 按用户列出角色 |
| GET | `/api/v1/characters/{id}?user_id=...` | 获取角色（校验归属） |
| PATCH | `/api/v1/characters/{id}?user_id=...` | 更新角色 |
| DELETE | `/api/v1/characters/{id}?user_id=...` | 删除角色 |
| POST | `/api/v1/chat/` | 非流式对话（body 中 `stream` 须为 `false`） |
| POST | `/api/v1/chat/stream` | SSE 流式（body 中建议 `stream: true`） |

## 环境变量（记忆分层，可选）

| 变量 | 默认 | 说明 |
|------|------|------|
| `MEMORY_RECENT_TURNS_MAX` | `10` | Redis 中保留的完整对话轮次上限（user+assistant 为 1 轮） |
| `MEMORY_SUMMARY_MAX_CHARS` | `1200` | 滚动摘要目标最大字数 |
| `MEMORY_MAX_TOKENS` | `4000` | 近期消息 token 上限（轮次与 token 双门槛，先到先触发压缩） |

## 阶段说明（Phase 2d）

Phase 2d 在 Phase 2c 角色状态落账之上加入独立游戏行动系统：

- `characters` 表新增 `location`、`inventory`、`event_log` 字段，迁移见 `alembic/versions/20260425_0002_character_game_state.py`。
- `app/game/engine.py` 负责确定性的行动规则：探索、修炼、调息、使用物品、经验阈值和境界突破。
- `prepare_explore` 与 `prepare_game_action` 会生成 `game_delta`，`apply_game_delta` 负责把修为、境界、位置、物品、近事写入 PostgreSQL。
- 状态查询会读取最新角色档案，包含位置、背包与近事。
- Streamlit 角色面板展示位置、背包和近事，快捷行动支持探索、查看属性、修炼与调息；本地 API 客户端关闭环境代理继承，避免本机请求被代理层误伤。

核心目录与职责与仓库内 `app/`、`frontend/`、`alembic/`、`tests/` 一致；意图分类、prepare 节点与游戏状态落账在 `app/agent/nodes.py`，规则引擎在 `app/game/engine.py`，Graph 条件边和落账节点串联在 `app/agent/graph.py`，所有 prompt 模板在 `app/agent/prompts.py`。分层会话读写见 `app/memory/layered.py`。

## 许可证

见仓库根目录 `LICENSE`。
