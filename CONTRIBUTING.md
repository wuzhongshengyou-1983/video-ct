# 贡献指南

## 分支策略

- `main`：稳定可发布
- `develop`：日常开发汇总
- `feature/xxx`：新功能
- `fix/xxx`：缺陷修复
- `chore/xxx`：杂项

## 提交规范（Conventional Commits）

```
<type>(<scope>): <subject>

[body]

[footer]
```

`type`: feat / fix / docs / style / refactor / perf / test / chore / ci

`scope`: h5 / admin / consultant / api / agents / db / docs / ci

示例：
```
feat(h5): 新增分享官页面 + 一键复制链接
fix(api): 修复诊断任务重复入队
chore(deps): 升级 vue 到 3.5.0
```

## 代码规范

- TS/Vue：ESLint + Prettier
- Python：Ruff + Black + mypy
- 提交前自动跑：`make lint`

## PR 流程

1. fork → 创建 feature 分支
2. 提交代码 + 通过 CI
3. 至少 1 个 reviewer 通过
4. squash & merge 到 develop
5. 每周一发布合并到 main + tag

## 安全披露

发现漏洞请发邮件至 security@video-ct.com，不要直接开 issue。
