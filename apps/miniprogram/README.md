# 微信小程序端（预留）

> 状态：未启动  
> 启动条件：PRO 订阅用户 ≥ 500，或运营决策明确推进小程序分发

## 定位

四端之②（见 `docs/01-战略/14-四端对齐与同步开发.md`）。  
与 H5 共用同一套后端 API，小程序专属能力：微信授权登录、分享卡片、订阅消息推送。

## 技术选型（待定）

- 原生小程序 + TypeScript
- 或 Uni-app（与 H5 共用代码，优先级低）

## 启动时同步的工作

- `packages/shared/src/api-client/` 适配小程序 `wx.request`
- 后端 `app/api/wechat.py` 扩展小程序鉴权流程
- `pnpm-workspace.yaml` 注册 `apps/miniprogram`
