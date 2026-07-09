# Xianxia Agent Taro Frontend

Phase 3a mobile frontend scaffold for the Xianxia Agent project.

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

Phase 3b should replace the local placeholders in `src/services/api.ts` with calls to the FastAPI backend.
