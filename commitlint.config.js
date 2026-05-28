/** @type {import('@commitlint/types').UserConfig} */
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // 新功能 → minor bump
        'fix',      // Bug 修复 → patch bump
        'perf',     // 性能优化 → patch bump
        'refactor', // 重构（无新功能）→ patch bump
        'style',    // 格式/空白 → patch bump
        'docs',     // 文档 → 无 bump
        'test',     // 测试 → 无 bump
        'chore',    // 构建/依赖 → 无 bump
        'ci',       // CI 配置 → 无 bump
        'revert',   // 回滚 → patch bump
        'hotfix',   // 紧急修复 → patch bump
      ],
    ],
    'subject-empty': [2, 'never'],
    'subject-case': [2, 'always', 'lower-case'],
    'header-max-length': [2, 'always', 100],
    'body-max-line-length': [0],
  },
};
