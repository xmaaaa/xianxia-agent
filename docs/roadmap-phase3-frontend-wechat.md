# Phase 3 路线：前端产品化与微信小程序

## 背景

Phase 2 已完成核心 RPG Agent 闭环：角色档案、对话、分层记忆、RAG 功法问答、意图路由、探索/修炼/调息/使用物品，以及修为、境界、背包、近事的状态落账。下一阶段不再继续扩展 Phase 2，而是进入产品前端与移动端体验。

Phase 3 的目标是把当前的「后端 Agent + Streamlit 调试前端」推进为可以面向玩家使用的移动端产品，并优先兼容微信小程序。

## 技术方向

推荐新建 `frontend-taro/`，使用 **Taro + React + TypeScript** 作为正式前端：

- 优先支持微信小程序，兼顾后续 H5。
- 保留 `frontend/streamlit_app.py` 作为本地调试工具。
- FastAPI 继续作为统一后端 API。
- 小程序第一版优先使用非流式对话接口，保证稳定；H5 或后续版本再补流式体验。

建议目录：

```text
xianxia-agent/
  app/
  tests/
  frontend/
    streamlit_app.py
  frontend-taro/
    src/
      app.config.ts
      app.tsx
      pages/
        index/
        chat/
        character/
        inventory/
      services/
        api.ts
      store/
        session.ts
      components/
```

## Phase 3a：Taro 前端脚手架

目标：建立正式移动端前端工程，先跑通页面壳子。

范围：

- 新建 `frontend-taro/`。
- 使用 Taro + React + TypeScript。
- 建立基础页面：
  - 首页/角色选择。
  - 创建角色页。
  - 对话页。
  - 角色面板页。
  - 背包页。
- 建立基础布局、路由、状态存储。
- 先验证 H5 构建，再验证微信小程序构建。

建议提交：

```text
feat(phase-3a): scaffold taro frontend
```

## Phase 3b：API 接入与移动端对话

目标：让 Taro 前端连上现有 FastAPI 后端。

范围：

- 封装 `services/api.ts`。
- 接入角色 API：
  - 创建角色。
  - 查询角色列表。
  - 获取角色状态。
- 接入聊天 API：
  - 第一版使用 `POST /api/v1/chat/` 非流式接口。
  - 保留后续 WebSocket 或 H5 SSE 的扩展位置。
- 对话页展示：
  - 玩家消息。
  - Agent 回复。
  - 当前意图标签。
  - 行动结果摘要。
- 行动按钮接入：
  - 探索。
  - 查看属性。
  - 修炼。
  - 调息。

建议提交：

```text
feat(phase-3b): connect taro frontend to api
```

## Phase 3c：微信登录与用户绑定

目标：替换手填 `user_id`，引入真实用户身份。

范围：

- 小程序端调用微信登录，获取登录 code。
- 后端新增微信登录接口，换取 `openid`。
- 新增用户模型或用户绑定逻辑。
- 角色与微信用户绑定。
- 保留本地开发模式下的 demo user。
- 更新鉴权与错误处理。

建议提交：

```text
feat(phase-3c): add wechat login user binding
```

## Phase 3d：部署与小程序上线准备

目标：让小程序可以访问线上服务。

范围：

- 部署 FastAPI 后端。
- 配置 HTTPS 域名。
- 配置 PostgreSQL、Redis、Chroma 持久化。
- 小程序后台配置 request 合法域名。
- 拆分 `.env.development` 与 `.env.production`。
- GitHub Actions 增加前端 lint/build 检查。
- 补充部署说明。

建议提交：

```text
feat(phase-3d): prepare production deployment
```

## Phase 3e：RPG 移动端交互层

目标：让前端不只是聊天框，而是可玩的修仙界面。

范围：

- 角色面板：境界、修为进度、位置、近事。
- 背包页面：物品列表、点击使用。
- 行动区：探索、修炼、调息、状态查询。
- 探索结果卡片。
- 境界突破提示。
- 近事时间线。
- 为后续任务、地图、战斗系统预留 UI 区域。

建议提交：

```text
feat(phase-3e): add mobile rpg interaction layer
```

## 后续方向

Phase 3 完成后，再进入更完整的长期玩法：

- 任务系统与章节剧情。
- 世界地图与地点解锁。
- NPC 与宗门关系。
- 随机遭遇与战斗。
- 长期角色履历与重要事件记忆。

## 当前下一步

下一步优先执行：

```text
Phase 3a: Taro 前端脚手架
```

不建议继续扩展 Streamlit。Streamlit 保留为调试入口，正式用户入口从 `frontend-taro/` 开始。
