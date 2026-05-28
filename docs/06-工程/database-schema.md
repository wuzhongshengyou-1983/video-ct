# 数据库 Schema 说明

> 迁移脚本：`infra/migrations/init_schema.sql` + `services/api/alembic/`  
> ORM 模型：`services/api/app/models/`  
> 当前表数：20 张（init_schema）+ 扩展表（alembic 迁移）

---

## 核心业务表

### 用户体系

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `users` | 用户主表 | `id`, `phone`, `role(user/admin/consultant)`, `is_active` |
| `user_profiles` | 扩展信息 | `user_id`, `nickname`, `avatar_url`, `douyin_uid`, `kuaishou_uid` |

### 订阅与支付

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `product_catalog` | 产品目录（PRO/MAX/单次） | `id`, `name`, `price_cents`, `scan_quota`, `type` |
| `subscriptions` | 用户订阅状态 | `user_id`, `product_id`, `status`, `expire_at`, `remaining_scans` |
| `orders` | 订单 | `order_no`, `user_id`, `amount_cents`, `status(pending/paid/cancelled)`, `pay_method` |
| `coupons` | 优惠券 | `code`, `discount_type`, `discount_value`, `valid_until`, `max_uses` |
| `coupon_redemptions` | 使用记录 | `coupon_id`, `user_id`, `order_id` |
| `reward_accounts` | 奖励账户（分享官收益） | `user_id`, `balance_cents`, `total_earned_cents` |
| `reward_transactions` | 奖励流水 | `account_id`, `amount_cents`, `type(referral/withdrawal)`, `status` |

### 诊断核心

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `diagnoses` | 诊断任务 | `id`, `user_id`, `video_url`, `status(pending/running/done/failed)`, `account_id`(可空), `diagnosis_sequence`(可空) |
| `reports` | 诊断报告 | `diagnosis_id`, `overall_score`, `dimensions_json`, `suggestions_json`, `version` |
| `benchmarks` | 头部对标库 | `track`, `creator_uid`, `platform`, `metrics_json`, `crawled_at` |
| `benchmark_snapshots` | 每日差距快照 | `user_id`, `track`, `gap_json`, `snapshot_date` |
| `archives` | 成长档案 | `user_id`, `track`, `created_at` |
| `archive_snapshots` | 档案月度快照 | `archive_id`, `month`, `metrics_json`, `score` |

### 人设与定位

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `personas` | IPP 人设档案 | `user_id`, `identity`, `personality`, `positioning`, `version` |
| `positionings` | BPS 商业定位档案 | `user_id`, `bps_json`, `roadmap_json`, `version` |

### 分享官体系

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `referrer_links` | 分享归因链接 | `user_id`, `code`, `click_count`, `conversion_count` |
| `referrer_levels` | 分享官等级 | `user_id`, `level(1-4)`, `total_referrals`, `updated_at` |

### 事件与日志

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `event_logs` | 行为事件流（v2.5+） | `user_id`, `event_type`, `payload_json`, `diagnosis_id`, `suggestion_id` |
| `audit_logs` | 操作审计（Admin） | `operator_id`, `action`, `target_type`, `target_id`, `ip` |

---

## Phase 1 预建表（已在 schema 中，尚无业务写入）

| 表名 | 用途 | 启用条件 |
|------|------|---------|
| `account_entities` | 账号实体，跨视频聚合 | Phase 0 完成后 |
| `account_health_snapshots` | 账号健康分时序快照 | Phase 1 账号中心页上线 |
| `recurring_issues` | 复发问题检测记录 | Phase 2 |

---

## 常用查询示例

```sql
-- 查询用户当前有效订阅
SELECT * FROM subscriptions
WHERE user_id = $1 AND status = 'active' AND expire_at > NOW();

-- 查询账号下所有诊断历史（按时序）
SELECT * FROM diagnoses
WHERE account_id = $1
ORDER BY diagnosis_sequence ASC;

-- 查询某赛道头部博主均值（对标基准）
SELECT AVG((metrics_json->>'completion_rate')::float) as avg_completion
FROM benchmarks WHERE track = $1;
```

---

## 迁移说明

```bash
# 新建迁移
cd services/api
alembic revision --autogenerate -m "add video_metrics table"

# 执行迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1
```
