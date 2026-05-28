import { danger, warn, fail } from "danger";

// ─── 1. 分支名校验（feat/fix/chore-MMDD 格式）────────────────────────────
const branchName = danger.github.pr.head.ref;
const validBranch = /^(feat|fix|chore|docs|refactor|test|ci)-\d{4}(-\S+)?$/.test(branchName);
if (!validBranch) {
  warn(
    `分支名 \`${branchName}\` 不符合规范。` +
    "应为 `feat/fix/chore/docs/refactor/test/ci-MMDD[-描述]`，例：`feat-0529-phase-gate`。"
  );
}

// ─── 2. Commit type 校验（所有 PR commit 必须符合 Conventional Commits）─────
const VALID_TYPES = ["feat", "fix", "docs", "style", "refactor", "test", "chore", "ci", "perf", "build", "revert"];
const commits = danger.github.commits;
for (const { commit, sha } of commits) {
  const msg = commit.message.split("\n")[0];
  const match = msg.match(/^(\w+)(\(.+\))?!?: .+/);
  if (!match || !VALID_TYPES.includes(match[1])) {
    warn(
      `Commit \`${sha.slice(0, 7)}\` 的提交信息不符合 Conventional Commits 规范：\`${msg}\`。` +
      `合法 type：${VALID_TYPES.join(", ")}`
    );
  }
}

// ─── 3. 历史归档区变动检测（禁止意外修改已归档文档）──────────────────────────
const ARCHIVE_PATHS = ["docs/99-归档/", "火眼docs/docs/99-归档/"];
const modifiedFiles = [
  ...danger.git.modified_files,
  ...danger.git.deleted_files,
];
const archiveViolations = modifiedFiles.filter((f) =>
  ARCHIVE_PATHS.some((p) => f.startsWith(p))
);
if (archiveViolations.length > 0) {
  fail(
    "以下文件属于历史归档区，禁止在 PR 中直接修改（归档文档只增不改）：\n" +
    archiveViolations.map((f) => `- \`${f}\``).join("\n")
  );
}

// ─── 4. PR 描述非空检查 ───────────────────────────────────────────────────
const prBody = danger.github.pr.body;
if (!prBody || prBody.trim().length < 20) {
  warn("PR 描述过短，请补充功能说明、测试计划或关联 issue。");
}
