# Heimdall Frontend

Vue 3 + Vite 前端工程。后端构建完成后会托管 `frontend/dist`，开发期可以单独运行 Vite。

## 常用命令

```bash
npm run dev
npm run sync:contracts
npm run typecheck
npm run build
```

`sync:contracts` 会从后端 Pydantic schema 生成 `src/types/backtest.ts`、`factor.ts`、`market.ts`、`tools.ts` 和 `config.ts`。这些文件不要手写修改；前端本地状态类型放在对应的 `*-frontend.ts` 文件里。
