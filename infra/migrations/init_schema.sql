-- =============================================================================
-- Video CT · 初始化数据库 Schema
-- 数据库: PostgreSQL
-- 使用: psql -U video_ct -d video_ct -f infra/migrations/init_schema.sql
-- 所有表均基于 services/api/app/models/ 中的 SQLAlchemy ORM 定义
-- =============================================================================

BEGIN;

-- ===================== 1. 用户表 =====================
-- 核心用户表 · 支持手机/邮箱/微信三通道注册
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    phone           VARCHAR(20) UNIQUE,           -- 手机号（可选）
    email           VARCHAR(120) UNIQUE,          -- 邮箱（可选）
    wechat_openid   VARCHAR(64) UNIQUE,           -- 微信 OpenID（可选）
    nickname        VARCHAR(64) NOT NULL DEFAULT '新用户',
    avatar_url      VARCHAR(500),                 -- 头像 URL
    password_hash   VARCHAR(255),                 -- bcrypt hash
    role            VARCHAR(20) NOT NULL DEFAULT 'user',  -- user / consultant / admin / partner
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_realname     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_wechat_openid ON users(wechat_openid);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- ===================== 2. 用户画像表 =====================
-- 1:1 关联 users · 细分赛道/平台/粉丝/变现路径
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id             BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    track               VARCHAR(50),             -- 细分赛道（如「美妆」「3C数码」）
    platform_main       VARCHAR(20),             -- 主阵地：抖音/快手/视频号/小红书
    follower_count      BIGINT NOT NULL DEFAULT 0,
    monetization_paths  TEXT,                    -- JSON: 变现路径列表
    bio                 TEXT,                    -- 个人简介
    goals               TEXT                     -- JSON: 成长目标
);
CREATE INDEX IF NOT EXISTS idx_user_profiles_track ON user_profiles(track);
CREATE INDEX IF NOT EXISTS idx_user_profiles_platform ON user_profiles(platform_main);

-- ===================== 3. 产品目录 =====================
-- SKU 定义 · seed 初始化时写入
CREATE TABLE IF NOT EXISTS product_catalog (
    sku             VARCHAR(50) PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    tier            VARCHAR(20) NOT NULL,         -- free / single / pro / max / addon
    billing_cycle   VARCHAR(20) NOT NULL,         -- once / monthly / quarterly / yearly
    price_cny       INTEGER NOT NULL,             -- 价格（元）
    description     TEXT,
    features        TEXT,                         -- JSON: 功能列表
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_product_catalog_tier ON product_catalog(tier);

-- ===================== 4. 订阅表 =====================
-- 用户当前/历史订阅记录
CREATE TABLE IF NOT EXISTS subscriptions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sku             VARCHAR(50) NOT NULL REFERENCES product_catalog(sku),
    tier            VARCHAR(20) NOT NULL,         -- pro / max
    status          VARCHAR(20) NOT NULL DEFAULT 'active',  -- active / canceled / expired
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,
    auto_renew      BOOLEAN NOT NULL DEFAULT FALSE,
    canceled_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_expires ON subscriptions(expires_at);

-- ===================== 5. 订单表 =====================
-- 单次诊断购买 / 订阅购买 / 加购
CREATE TABLE IF NOT EXISTS orders (
    id                  BIGSERIAL PRIMARY KEY,
    order_no            VARCHAR(40) UNIQUE NOT NULL,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sku                 VARCHAR(50) NOT NULL,
    quantity            INTEGER NOT NULL DEFAULT 1,
    unit_price_cny      INTEGER NOT NULL,         -- 单价（元）
    total_cny           INTEGER NOT NULL,         -- 原价（元）
    deduction_cny       INTEGER NOT NULL DEFAULT 0,-- 余额抵扣（元）
    coupon_code         VARCHAR(40),              -- 使用的优惠券码
    paid_cny            INTEGER NOT NULL,         -- 实付（元）
    payment_method      VARCHAR(20),              -- 支付方式：wechat / alipay
    payment_status      VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending / paid / refunded / canceled
    paid_at             TIMESTAMPTZ,
    referred_by_user_id BIGINT,                   -- 推荐人 user_id
    extra               TEXT,                     -- JSON: 扩展字段
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_referred ON orders(referred_by_user_id);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);

-- ===================== 6. 诊断任务表 =====================
-- 每次提交一条视频 = 一个诊断任务
CREATE TABLE IF NOT EXISTS diagnoses (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_url       VARCHAR(1000) NOT NULL,
    video_platform  VARCHAR(20),                  -- 抖音/快手/B站/小红书/YouTube
    video_meta      JSONB,                        -- 标题/时长/封面/播放数等
    status          VARCHAR(20) NOT NULL DEFAULT 'queued',  -- queued / processing / done / failed
    diagnosis_type  VARCHAR(20) NOT NULL DEFAULT 'ct_basic', -- ct_basic / ct_full / persona / positioning
    quota_source    VARCHAR(20) NOT NULL DEFAULT 'free',     -- free / single / pro / max
    progress_pct    INTEGER NOT NULL DEFAULT 0,   -- 0-100
    error           TEXT,                         -- 失败原因
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_diagnoses_user ON diagnoses(user_id);
CREATE INDEX IF NOT EXISTS idx_diagnoses_status ON diagnoses(status);
CREATE INDEX IF NOT EXISTS idx_diagnoses_type ON diagnoses(diagnosis_type);
CREATE INDEX IF NOT EXISTS idx_diagnoses_created ON diagnoses(created_at);

-- ===================== 7. 诊断报告表 =====================
-- 一次 diagnosis 对应一份 report
CREATE TABLE IF NOT EXISTS reports (
    id                  BIGSERIAL PRIMARY KEY,
    diagnosis_id        BIGINT NOT NULL REFERENCES diagnoses(id) ON DELETE CASCADE,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    overall_score       INTEGER NOT NULL,          -- 综合评分 0-100
    grade               VARCHAR(10) NOT NULL,      -- L1-L6 等级
    dimensions          JSONB NOT NULL,            -- 6 维评分: hook/结构/信息密度/情绪/画面/节奏
    findings            JSONB,                     -- 病灶定位（含时间戳）
    suggestions         JSONB,                     -- 修复建议清单
    benchmark_gap       JSONB,                     -- 与对标账号差距
    html_path           VARCHAR(500),              -- HTML 报告路径
    pdf_path            VARCHAR(500),              -- PDF 报告路径
    model_used          VARCHAR(50),               -- 使用的 AI 模型
    cost_cents          INTEGER NOT NULL DEFAULT 0,-- API 费用（分）
    user_rating         INTEGER,                   -- 用户评分 1-5
    user_feedback       TEXT,                      -- 用户反馈
    consultant_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    consultant_notes    TEXT,                      -- 顾问批注
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reports_diagnosis ON reports(diagnosis_id);
CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_grade ON reports(grade);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);

-- ===================== 8. 终身成长档案 =====================
-- 每个客户一份 · 终身唯一
CREATE TABLE IF NOT EXISTS archives (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    archive_no      VARCHAR(40) UNIQUE NOT NULL,   -- 档案编号
    track           VARCHAR(50),                   -- 赛道
    current_level   VARCHAR(10) NOT NULL DEFAULT 'L1',  -- L1-L6 当前等级
    initial_baseline JSONB,                        -- 首次诊断基线
    total_diagnoses INTEGER NOT NULL DEFAULT 0,    -- 累计诊断次数
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_archives_user ON archives(user_id);
CREATE INDEX IF NOT EXISTS idx_archives_track ON archives(track);
CREATE INDEX IF NOT EXISTS idx_archives_level ON archives(current_level);

-- ===================== 9. 档案月度快照 =====================
-- 用于画成长曲线
CREATE TABLE IF NOT EXISTS archive_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    archive_id      BIGINT NOT NULL REFERENCES archives(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL,
    snapshot_date   DATE NOT NULL,
    metrics         JSONB NOT NULL,                -- 六大指标快照
    benchmark_gap   JSONB,                        -- 与头部差距 %
    level           VARCHAR(10) NOT NULL,          -- L1-L6
    overall_score   INTEGER,                      -- 综合评分
    notes           VARCHAR(1000),                 -- 月度备注
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_archive_snaps_archive ON archive_snapshots(archive_id);
CREATE INDEX IF NOT EXISTS idx_archive_snaps_user ON archive_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_archive_snaps_date ON archive_snapshots(snapshot_date);

-- ===================== 10. 头部对标库 =====================
-- 各赛道头部博主数据
CREATE TABLE IF NOT EXISTS benchmarks (
    id              BIGSERIAL PRIMARY KEY,
    track           VARCHAR(50) NOT NULL,          -- 赛道
    platform        VARCHAR(20) NOT NULL,          -- 平台
    account_id      VARCHAR(100) NOT NULL,         -- 平台账号 ID
    nickname        VARCHAR(100) NOT NULL,         -- 昵称
    follower_count  BIGINT NOT NULL DEFAULT 0,
    avatar_url      VARCHAR(500),
    bio             VARCHAR(500),                  -- 简介
    style_archetype VARCHAR(20),                   -- 风格原型
    monetization    JSONB,                        -- 变现方式
    rank_in_track   INTEGER NOT NULL DEFAULT 999,  -- 赛道排名
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_benchmarks_track ON benchmarks(track);
CREATE INDEX IF NOT EXISTS idx_benchmarks_platform ON benchmarks(platform);
CREATE INDEX IF NOT EXISTS idx_benchmarks_active ON benchmarks(is_active);

-- ===================== 11. 头部数据每日快照 =====================
-- 每天的指标数据快照
CREATE TABLE IF NOT EXISTS benchmark_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    benchmark_id    BIGINT NOT NULL REFERENCES benchmarks(id) ON DELETE CASCADE,
    snapshot_date   DATE NOT NULL,
    metrics         JSONB NOT NULL,                -- 六大指标均值
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_benchmark_snaps_bid ON benchmark_snapshots(benchmark_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_snaps_date ON benchmark_snapshots(snapshot_date);

-- ===================== 12. 人设 IPP 档案 =====================
-- 每次 IPP 扫描产生一条记录
CREATE TABLE IF NOT EXISTS personas (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    primary_archetype   VARCHAR(20),               -- 主原型（12 品牌原型）
    sub_archetype        VARCHAR(20),              -- 子原型
    contrast_point      VARCHAR(200),              -- 反差点
    self_tags           JSONB,                     -- 自我认知标签
    audience_tags       JSONB,                     -- 观众认知标签
    scores              JSONB NOT NULL,            -- 6 维评分
    consistency_score   INTEGER NOT NULL,          -- 一致性评分
    canvas              JSONB,                     -- 人设画布 9 模块
    diagnosis           JSONB,                     -- 病灶 + 建议
    drift_alert         BOOLEAN NOT NULL DEFAULT FALSE,  -- 是否触发人设偏移告警
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_personas_user ON personas(user_id);
CREATE INDEX IF NOT EXISTS idx_personas_archetype ON personas(primary_archetype);
CREATE INDEX IF NOT EXISTS idx_personas_created ON personas(created_at);

-- ===================== 13. 商业定位 BPS 档案 =====================
-- 商业模式定位分析
CREATE TABLE IF NOT EXISTS positionings (
    id                      BIGSERIAL PRIMARY KEY,
    user_id                 BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scores                  JSONB NOT NULL,         -- 6 维评分
    monetization_paths      JSONB NOT NULL,         -- 6 路径成熟度
    recommended_archetype   VARCHAR(30),            -- 推荐商业原型
    recommended_routes      JSONB,                  -- 推荐变现路径
    avoid_routes            JSONB,                  -- 避免的路径
    roadmap_12m             JSONB,                  -- 12 月路线图
    risk_level              INTEGER NOT NULL DEFAULT 1,  -- 风险等级 1-5
    canvas_bmc              JSONB,                  -- 商业模式九宫格
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_positionings_user ON positionings(user_id);

-- ===================== 14. 品牌分享官推荐链接 =====================
-- 邀请归因记录
CREATE TABLE IF NOT EXISTS referrer_links (
    id              BIGSERIAL PRIMARY KEY,
    inviter_id      BIGINT NOT NULL REFERENCES users(id),     -- 邀请人
    invitee_id      BIGINT REFERENCES users(id),              -- 被邀请人（注册后回填）
    link_code       VARCHAR(32) UNIQUE NOT NULL,              -- 唯一邀请码
    source          VARCHAR(50),                              -- 来源渠道
    first_paid_at   TIMESTAMPTZ,                              -- 首单付费时间
    reward_amount_cny INTEGER NOT NULL DEFAULT 0,             -- 推荐奖励（元）
    reward_status   VARCHAR(20) NOT NULL DEFAULT 'pending',   -- pending / paid / invalid
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_referrer_links_inviter ON referrer_links(inviter_id);
CREATE INDEX IF NOT EXISTS idx_referrer_links_invitee ON referrer_links(invitee_id);
CREATE INDEX IF NOT EXISTS idx_referrer_links_code ON referrer_links(link_code);

-- ===================== 15. 分享官等级 =====================
-- 每位分享官的等级状态
CREATE TABLE IF NOT EXISTS referrer_levels (
    user_id                 BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    level                   VARCHAR(10) NOT NULL DEFAULT 'bronze',  -- bronze / silver / gold / diamond
    total_valid_referrals   INTEGER NOT NULL DEFAULT 0,
    total_rewards_cny       INTEGER NOT NULL DEFAULT 0,
    activated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    level_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_referrer_levels_level ON referrer_levels(level);

-- ===================== 16. 奖励账户 =====================
-- 通用奖励账户：现金 + 抵扣 + 诊断券
CREATE TABLE IF NOT EXISTS reward_accounts (
    user_id                 BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    cash_balance_cny        INTEGER NOT NULL DEFAULT 0,            -- 可提现金额
    deduction_balance_cny   INTEGER NOT NULL DEFAULT 0,            -- 抵扣余额
    ticket_balance          INTEGER NOT NULL DEFAULT 0,            -- 诊断券数量
    total_earned_cny        INTEGER NOT NULL DEFAULT 0,            -- 累计收入
    total_withdrawn_cny     INTEGER NOT NULL DEFAULT 0,            -- 累计提现
    total_deducted_cny      INTEGER NOT NULL DEFAULT 0,            -- 累计抵扣
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ===================== 17. 奖励交易流水 =====================
-- 奖励账户的每一笔变动
CREATE TABLE IF NOT EXISTS reward_transactions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    txn_type        VARCHAR(20) NOT NULL,           -- earn / withdraw / deduct / refund / adjust
    amount_cny      INTEGER NOT NULL,               -- 变动金额
    balance_after_cny INTEGER NOT NULL,             -- 变动后余额
    related_id      VARCHAR(50),                    -- 关联业务 ID
    note            VARCHAR(500),                   -- 备注
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reward_txns_user ON reward_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_reward_txns_type ON reward_transactions(txn_type);
CREATE INDEX IF NOT EXISTS idx_reward_txns_created ON reward_transactions(created_at);

-- ===================== 18. 优惠券 =====================
-- 优惠券模板
CREATE TABLE IF NOT EXISTS coupons (
    id              BIGSERIAL PRIMARY KEY,
    code            VARCHAR(40) UNIQUE NOT NULL,
    name            VARCHAR(120) NOT NULL,
    discount_type   VARCHAR(20) NOT NULL,           -- amount / percent / free_trial
    discount_value  INTEGER NOT NULL,               -- 折扣值（元或%）
    min_spend_cny   INTEGER NOT NULL DEFAULT 0,     -- 最低消费门槛
    applicable_skus VARCHAR(500),                   -- 适用 SKU（逗号分隔）
    max_uses        INTEGER NOT NULL DEFAULT 1,     -- 总可用次数
    used_count      INTEGER NOT NULL DEFAULT 0,     -- 已使用次数
    valid_from      TIMESTAMPTZ,                    -- 生效时间
    valid_to        TIMESTAMPTZ,                    -- 失效时间
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code);
CREATE INDEX IF NOT EXISTS idx_coupons_valid ON coupons(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_coupons_active ON coupons(is_active);

-- ===================== 19. 优惠券核销记录 =====================
-- 每次优惠券使用记录
CREATE TABLE IF NOT EXISTS coupon_redemptions (
    id              BIGSERIAL PRIMARY KEY,
    coupon_id       BIGINT NOT NULL REFERENCES coupons(id),
    user_id         BIGINT NOT NULL REFERENCES users(id),
    order_id        BIGINT,                       -- 关联订单
    discount_cny    INTEGER NOT NULL,              -- 实际抵扣金额
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_coupon_redemptions_coupon ON coupon_redemptions(coupon_id);
CREATE INDEX IF NOT EXISTS idx_coupon_redemptions_user ON coupon_redemptions(user_id);

-- ===================== 20. 事件日志 =====================
-- 审计 + 行为埋点合一
CREATE TABLE IF NOT EXISTS event_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT,                                   -- 可为 NULL（匿名事件）
    event_type      VARCHAR(50) NOT NULL,                     -- 事件类型
    payload         JSONB,                                   -- 事件数据
    ip              VARCHAR(64),                             -- 来源 IP
    user_agent      VARCHAR(500),                            -- User-Agent
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_event_logs_user ON event_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_type ON event_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_event_logs_created ON event_logs(created_at);

-- =============================================================================
-- 初始化种子数据：产品目录
-- =============================================================================

INSERT INTO product_catalog (sku, name, tier, billing_cycle, price_cny, description, features) VALUES
('free',      '免费版',    'free',   'once',     0,   '每月 3 次免费诊断，基础报告',     '["CT基础诊断x3","基础报告","社区访问"]'),
('single',    '单次诊断',  'single', 'once',     19,  '单次 CT 全维诊断 + 完整报告',    '["CT全维诊断","完整报告","PDF导出"]'),
('pro-month', 'PRO 月度',  'pro',    'monthly',  99,  'PRO 全功能 · 月度订阅',            '["无限诊断","IPP人设档案","BPS商业定位","对标库","PDF导出","顾问批注"]'),
('pro-year',  'PRO 年度',  'pro',    'yearly',   990, 'PRO 全功能 · 年度订阅（省 170元）', '["无限诊断","IPP人设档案","BPS商业定位","对标库","PDF导出","顾问批注","专属顾问"]'),
('max-month', 'MAX 月度',  'max',    'monthly',  499, 'MAX 全量 + AI 陪跑 · 月度',       '["PRO全部","AI量化策略","成长曲线","投流建议","1v1陪跑","优先体验"]'),
('max-year',  'MAX 年度',  'max',    'yearly',   4990,'MAX 全量 + AI 陪跑 · 年度（省 998元）', '["PRO全部","AI量化策略","成长曲线","投流建议","1v1陪跑","优先体验","年度复盘"]')

ON CONFLICT (sku) DO NOTHING;

-- =============================================================================
-- 函数：自动更新 updated_at 字段
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为有 updated_at 字段的表创建触发器
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name = 'updated_at'
          AND table_name NOT IN (
              SELECT trigger_name
              FROM information_schema.triggers
              WHERE trigger_name = 'trg_update_updated_at'
          )
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_update_updated_at BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at()', tbl
        );
    END LOOP;
END $$;

COMMIT;
