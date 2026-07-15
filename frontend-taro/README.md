# Xianxia Agent Taro Frontend

Phase 3a mobile frontend scaffold for the Xianxia Agent project.
Phase 3b connects the scaffold to the existing FastAPI backend with non-streaming chat.

## Stack

- Taro 4
- React 18
- TypeScript
- WeChat Mini Program first, H5 compatible

## Scripts

```bash
npm install
npm run typecheck
npm run build:h5
npm run build:weapp
npm run dev:h5
npm run dev:weapp
```

The build scripts use `--no-check` because Taro doctor's native environment check can fail in restricted local shells. TypeScript and actual Taro builds are still run separately.

## Structure

```text
src/
  pages/
    index/       character selection
    create/      character creation
    chat/        mobile chat shell
    character/   character panel
    inventory/   inventory panel
  services/
    api.ts       API facade for Phase 3b
  store/
    session.ts   temporary local session state
```

`src/services/api.ts` contains the API facade used by the pages.

## API

The frontend calls `http://127.0.0.1:8000` by default. Override it with:

```bash
TARO_APP_API_BASE_URL=https://your-api.example.com npm run build:h5
```

Current API-backed flows:

- list characters by `user_id`
- create a character
- send non-streaming chat messages
- run action buttons: explore, status, cultivate, rest
- refresh character panel and inventory after game actions
