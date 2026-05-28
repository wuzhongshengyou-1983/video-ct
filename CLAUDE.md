# Fire-Eye 项目规范 · Claude 强制执行

## 移动端调试工具规范（每次涉及相关代码时自动执行）

### Eruda 使用规范 — 每次写代码时检查

**凡涉及 eruda / 调试注入相关代码，必须做以下检查：**

1. **环境隔离检查**：`eruda.init()` 必须在环境判断内，裸调用直接指出并修正
   ```js
   // ❌ 禁止裸调用
   eruda.init()

   // ✅ 正确写法
   if (import.meta.env.DEV) { import('eruda').then(({default:e})=>e.init()) }
   ```

2. **依赖位置检查**：eruda 必须在 `devDependencies`，出现在 `dependencies` 时立即提醒

3. **生产构建检查**：每次 build 前提醒运行：
   ```bash
   grep -r "eruda.init" src/ && echo "❌ 发现裸调用，禁止构建" || echo "✅ 通过"
   ```

### Responsively App 使用规范

- 涉及响应式 CSS 时，提醒在 Responsively 中验证以下断点：
  - 375px（iPhone SE · 最小屏兜底）
  - 390px（iPhone 14 · 主流 iOS）
  - 360px（Android · 主流安卓）
  - 768px（iPad Mini · 平板）

- 每次修改布局相关代码完成后，输出一行提醒：
  > ⚠️ 记得在 Responsively (`http://localhost:[端口]`) 验证多设备布局

### 安全红线（P0）

| 红线 | 触发条件 | 动作 |
|------|---------|------|
| Eruda 生产泄露 | 发现裸 `eruda.init()` | 立即停止 + 给出修正代码 |
| 调试代码入 git | commit 包含调试注入 | 提醒加 `.gitignore` 或用环境变量 |
| BrowserSync 开放 | 未加 `--host localhost` | 提醒补参数 |

### 本项目本地服务

演示页服务：`python3 -m http.server 7788`（在 `docs/` 目录下运行）
访问地址：`http://localhost:7788/06-工程/mobile-debug-demo.html`

---

## 项目结构（火眼金睛 · 文档与代码同仓）

**工作区**：`~/Projects/fire-eye/video-ct/`（独立 git · GitHub: wuzhongshengyou-1983/video-ct）
**H5 代码**：`apps/h5/`
**项目文档**：`docs/`（01-战略~08-交接 中文分类编号单一主线 · 旧 strategy 已归档至 `docs/99-归档/strategy-旧版/`）
**凭据**：`~/vault/credentials/fire-eye/`（不入仓 · chmod 600）
**技术栈**：Vue 3 + TypeScript + Vite 5 + Vant + pnpm monorepo
**开发启动**：在仓根运行 `pnpm dev:h5`

### Eruda 已接入位置
- 文件：`apps/h5/src/main.ts`
- 方式：`import.meta.env.DEV` 条件动态 import，生产自动 tree-shake
- 构建保护：`prebuild` 脚本自动检测裸 `eruda.init()` 并阻断构建

### Responsively 使用
- 启动开发服务器后，打开 Responsively App
- 输入 `http://localhost:5173`（Vite 默认端口）
- 推荐设备组：375px · 390px · 360px · 768px
