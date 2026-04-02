# 修仙 AI Agent（Phase 1）

基于 **LangGraph** 编排、**Chroma** 本地向量库与 **FastAPI** 的修仙题材对话 Agent：玩家创建角色后与「叙事之灵」对话；问及功法时通过 RAG 检索内置典籍（`skills.md`）再生成回答。角色档案落在 **PostgreSQL**，同一会话的对话历史缓存在 **Redis**。MVP 前端为 **Streamlit**，独立进程调用 HTTP API。

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
    R[retrieve_context]
    G[generate_response]
    S[save_memory]
    R --> G --> S
  end
  subgraph data [Data]
    PG[(PostgreSQL)]
    RD[(Redis)]
    CHM[(Chroma 本地)]
  end
  ST --> CR
  ST --> CH
  CH --> agent
  CR --> PG
  CH --> RD
  CH --> PG
  R --> CHM
  G --> PG
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
pytest tests/test_agent.py -v
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

## 项目结构（Phase 1）

核心目录与职责与仓库内 `app/`、`frontend/`、`alembic/`、`tests/` 一致；功法示例文本位于 `app/rag/knowledge/skills.md`。

## 许可证

见仓库根目录 `LICENSE`。
