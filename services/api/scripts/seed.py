"""数据库初始化 seed · 产品目录 + 头部对标库样例 + 管理员账号."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import ProductCatalog, User, Benchmark, Coupon  # noqa: E402
from app.core.security import hash_password  # noqa: E402


# 战略 06 章 + 13 章产品定义
PRODUCTS = [
    # 免费层
    {"sku": "free", "name": "免费体验", "tier": "free", "billing_cycle": "monthly",
     "price_cny": 0, "description": "每月免费 3 次 CT 扫描",
     "features": ["每月 3 次 CT 扫描", "简版报告", "30+ 赛道库存对标均值"]},

    # 单次付费
    {"sku": "single_ct", "name": "单次完整 CT 诊断", "tier": "single", "billing_cycle": "once",
     "price_cny": 19, "description": "一次完整 6 维 18 点位 CT 诊断",
     "features": ["完整 CT 报告", "病灶定位", "修复建议清单", "对标头部均值"]},
    {"sku": "single_hook", "name": "单次钩子/标题/封面", "tier": "single", "billing_cycle": "once",
     "price_cny": 9, "description": "AI 生成 5 套钩子/标题/封面",
     "features": ["5 条钩子候选", "5 条标题候选", "3 套封面文案"]},
    {"sku": "single_persona", "name": "单次人设 IPP 诊断", "tier": "single", "billing_cycle": "once",
     "price_cny": 49, "description": "6 维人设诊断 + 12 原型匹配",
     "features": ["6 维 IPP 评分", "12 原型匹配", "人设画布", "演进建议"]},
    {"sku": "single_bps", "name": "单次商业定位 BPS", "tier": "single", "billing_cycle": "once",
     "price_cny": 49, "description": "6 维商业扫描 + 12 月路线图",
     "features": ["6 维 BPS 评分", "5 变现原型匹配", "TOP3 路径推荐", "12 月演进路线"]},

    # PRO 月卡
    {"sku": "pro_monthly", "name": "PRO 月卡", "tier": "pro", "billing_cycle": "monthly",
     "price_cny": 99, "description": "AI 月度体检 + 模板套用",
     "features": [
         "4 条 CT 完整诊断/月", "30 赛道头部对标均值", "月度差距进度报告",
         "6 月成长档案", "模板库（库存）", "月度直播复盘", "社群答疑",
         "人设 IPP 季度自测", "商业定位 BPS 季度扫描",
     ]},
    {"sku": "pro_yearly", "name": "PRO 年卡", "tier": "pro", "billing_cycle": "yearly",
     "price_cny": 999, "description": "PRO 月卡年付 · 17% 折扣",
     "features": ["含 PRO 全部权益", "12 个月连续订阅", "送 2 次单次商业扫描"]},

    # MAX 月卡
    {"sku": "max_monthly", "name": "MAX 月卡", "tier": "max", "billing_cycle": "monthly",
     "price_cny": 499, "description": "十大头部对标 + AI 人工双轨陪跑",
     "features": [
         "不限次 CT 诊断", "专属 TOP10 对标池", "六大指标日级更新",
         "实时数据异动预警", "评论情绪 AI 分析",
         "终身个人成长档案", "L1-L6 等级晋升", "差距进度条",
         "月度 1v1 顾问 60 分钟", "工单 24h 内首响",
         "钩子/标题/封面定制生成", "字幕优化无限次", "变现植入建议",
         "全量模板库下载", "人设 IPP 终身追踪", "BPS 月度扫描",
         "一页纸人设画布", "商业模式九宫格", "12 月演进路线图",
     ]},
    {"sku": "max_yearly", "name": "MAX 年卡", "tier": "max", "billing_cycle": "yearly",
     "price_cny": 4999, "description": "MAX 月卡年付 · 17% 折扣 + 年度白皮书 + 头部资源对接",
     "features": ["含 MAX 全部权益", "年度成长白皮书印刷", "头部商单资源优先对接"]},

    # 加购
    {"sku": "addon_script", "name": "头部同款爆款脚本定制", "tier": "addon", "billing_cycle": "once",
     "price_cny": 298, "description": "对标 10 大头部爆款框架，定制原创脚本",
     "features": ["3 个工作日交付", "Claude Opus 级模型"]},
    {"sku": "addon_ip_reset", "name": "全账号 IP 重塑全案", "tier": "addon", "billing_cycle": "once",
     "price_cny": 1280, "description": "顾问主导，7 工作日交付",
     "features": ["人设画布定稿", "视觉/语言/情绪锚点", "演进 12 月路线", "MAX 客户专享"]},
    {"sku": "addon_biz_upgrade", "name": "全套变现体系升级方案", "tier": "addon", "billing_cycle": "once",
     "price_cny": 1680, "description": "对标头部商业模型重构",
     "features": ["10 工作日交付", "BMC 九宫格", "MAX 客户专享"]},
]


# 头部对标库 · 10 个赛道 × 3 个头部 = 30 个
BENCHMARKS: list[dict] = [
    # ---- 1. 职场干货 ----
    {"track": "职场干货", "platform": "douyin", "account_id": "demo_zc_1", "nickname": "职场老炮", "follower_count": 5_120_000, "rank_in_track": 1, "style_archetype": "干货型-教学派"},
    {"track": "职场干货", "platform": "douyin", "account_id": "demo_zc_2", "nickname": "HR王姐", "follower_count": 3_400_000, "rank_in_track": 2, "style_archetype": "气场型-行业权威"},
    {"track": "职场干货", "platform": "xiaohongshu", "account_id": "demo_zc_3", "nickname": "面试官说", "follower_count": 2_800_000, "rank_in_track": 3, "style_archetype": "干货型-拆解派"},

    # ---- 2. 美食料理 ----
    {"track": "美食料理", "platform": "douyin", "account_id": "demo_food_1", "nickname": "厨神老张", "follower_count": 8_200_000, "rank_in_track": 1, "style_archetype": "趣味型-段子手"},
    {"track": "美食料理", "platform": "douyin", "account_id": "demo_food_2", "nickname": "深夜食堂", "follower_count": 5_600_000, "rank_in_track": 2, "style_archetype": "共情型-治愈系"},
    {"track": "美食料理", "platform": "bilibili", "account_id": "demo_food_3", "nickname": "料理研究家", "follower_count": 2_100_000, "rank_in_track": 3, "style_archetype": "干货型-教学派"},

    # ---- 3. 穿搭时尚 ----
    {"track": "穿搭时尚", "platform": "xiaohongshu", "account_id": "demo_fashion_1", "nickname": "时尚Vivi", "follower_count": 1_200_000, "rank_in_track": 1, "style_archetype": "气场型-反差大佬"},
    {"track": "穿搭时尚", "platform": "douyin", "account_id": "demo_fashion_2", "nickname": "穿搭研究室", "follower_count": 980_000, "rank_in_track": 2, "style_archetype": "干货型-资源派"},
    {"track": "穿搭时尚", "platform": "douyin", "account_id": "demo_fashion_3", "nickname": "潮人阿Ken", "follower_count": 760_000, "rank_in_track": 3, "style_archetype": "趣味型-挑战派"},

    # ---- 4. 育儿亲子 ----
    {"track": "育儿亲子", "platform": "douyin", "account_id": "demo_baby_1", "nickname": "豆豆妈成长记", "follower_count": 2_300_000, "rank_in_track": 1, "style_archetype": "共情型-闺蜜型"},
    {"track": "育儿亲子", "platform": "xiaohongshu", "account_id": "demo_baby_2", "nickname": "儿科医生张爸爸", "follower_count": 1_800_000, "rank_in_track": 2, "style_archetype": "气场型-行业权威"},
    {"track": "育儿亲子", "platform": "douyin", "account_id": "demo_baby_3", "nickname": "育儿百科李老师", "follower_count": 1_500_000, "rank_in_track": 3, "style_archetype": "干货型-教学派"},

    # ---- 5. 科技数码 ----
    {"track": "科技数码", "platform": "bilibili", "account_id": "demo_tech_1", "nickname": "科技阿杰", "follower_count": 4_500_000, "rank_in_track": 1, "style_archetype": "干货型-拆解派"},
    {"track": "科技数码", "platform": "douyin", "account_id": "demo_tech_2", "nickname": "数码老炮", "follower_count": 3_100_000, "rank_in_track": 2, "style_archetype": "气场型-行业权威"},
    {"track": "科技数码", "platform": "douyin", "account_id": "demo_tech_3", "nickname": "极客小白", "follower_count": 2_600_000, "rank_in_track": 3, "style_archetype": "趣味型-体验派"},

    # ---- 6. 知识教育 ----
    {"track": "知识教育", "platform": "bilibili", "account_id": "demo_edu_1", "nickname": "罗老师讲知识", "follower_count": 6_800_000, "rank_in_track": 1, "style_archetype": "干货型-教学派"},
    {"track": "知识教育", "platform": "douyin", "account_id": "demo_edu_2", "nickname": "3分钟硬核科普", "follower_count": 4_200_000, "rank_in_track": 2, "style_archetype": "干货型-拆解派"},
    {"track": "知识教育", "platform": "xiaohongshu", "account_id": "demo_edu_3", "nickname": "每天学点心理学", "follower_count": 3_500_000, "rank_in_track": 3, "style_archetype": "共情型-闺蜜型"},

    # ---- 7. 美妆护肤 ----
    {"track": "美妆护肤", "platform": "douyin", "account_id": "demo_beauty_1", "nickname": "化妆师Lisa", "follower_count": 7_200_000, "rank_in_track": 1, "style_archetype": "干货型-教学派"},
    {"track": "美妆护肤", "platform": "xiaohongshu", "account_id": "demo_beauty_2", "nickname": "成分党小K", "follower_count": 2_900_000, "rank_in_track": 2, "style_archetype": "干货型-拆解派"},
    {"track": "美妆护肤", "platform": "douyin", "account_id": "demo_beauty_3", "nickname": "素人改造日记", "follower_count": 1_600_000, "rank_in_track": 3, "style_archetype": "共情型-治愈系"},

    # ---- 8. 健身运动 ----
    {"track": "健身运动", "platform": "douyin", "account_id": "demo_fit_1", "nickname": "健身老刘", "follower_count": 9_500_000, "rank_in_track": 1, "style_archetype": "干货型-教学派"},
    {"track": "健身运动", "platform": "bilibili", "account_id": "demo_fit_2", "nickname": "帕姐陪你练", "follower_count": 6_300_000, "rank_in_track": 2, "style_archetype": "趣味型-挑战派"},
    {"track": "健身运动", "platform": "douyin", "account_id": "demo_fit_3", "nickname": "跑步教练大李", "follower_count": 3_100_000, "rank_in_track": 3, "style_archetype": "共情型-闺蜜型"},

    # ---- 9. 旅游出行 ----
    {"track": "旅游出行", "platform": "douyin", "account_id": "demo_travel_1", "nickname": "行走的阿楠", "follower_count": 4_800_000, "rank_in_track": 1, "style_archetype": "氛围型-视觉盛宴"},
    {"track": "旅游出行", "platform": "xiaohongshu", "account_id": "demo_travel_2", "nickname": "城市漫步指南", "follower_count": 3_200_000, "rank_in_track": 2, "style_archetype": "干货型-资源派"},
    {"track": "旅游出行", "platform": "douyin", "account_id": "demo_travel_3", "nickname": "民宿体验官", "follower_count": 2_100_000, "rank_in_track": 3, "style_archetype": "共情型-治愈系"},

    # ---- 10. 财经商业 ----
    {"track": "财经商业", "platform": "douyin", "account_id": "demo_biz_1", "nickname": "商业观察室", "follower_count": 3_900_000, "rank_in_track": 1, "style_archetype": "气场型-行业权威"},
    {"track": "财经商业", "platform": "bilibili", "account_id": "demo_biz_2", "nickname": "硬核商业分析", "follower_count": 2_700_000, "rank_in_track": 2, "style_archetype": "干货型-拆解派"},
    {"track": "财经商业", "platform": "douyin", "account_id": "demo_biz_3", "nickname": "30秒看懂财报", "follower_count": 1_900_000, "rank_in_track": 3, "style_archetype": "干货型-教学派"},
]

# 优惠券模板 · 5 种场景
COUPONS: list[dict] = [
    {
        "code": "NEW70OFF",
        "name": "新用户 7 折券",
        "discount_type": "percent",
        "discount_value": 30,  # 减 30%
        "min_spend_cny": 1,
        "applicable_skus": "pro_monthly,max_monthly",
        "max_uses": 1000,
        "description": "新注册用户首次订阅 PRO 或 MAX 享 7 折",
    },
    {
        "code": "PRO49FIRST",
        "name": "PRO 首月 49 元",
        "discount_type": "amount",
        "discount_value": 50,  # 原价 99 - 50 = 49
        "min_spend_cny": 99,
        "applicable_skus": "pro_monthly",
        "max_uses": 500,
        "description": "PRO 月卡首月仅需 49 元",
    },
    {
        "code": "MAX299FIRST",
        "name": "MAX 首月 299 元",
        "discount_type": "amount",
        "discount_value": 200,  # 原价 499 - 200 = 299
        "min_spend_cny": 499,
        "applicable_skus": "max_monthly",
        "max_uses": 300,
        "description": "MAX 月卡首月仅需 299 元",
    },
    {
        "code": "RENEWAL90OFF",
        "name": "续费 9 折券",
        "discount_type": "percent",
        "discount_value": 10,  # 减 10%
        "min_spend_cny": 99,
        "applicable_skus": "pro_monthly,max_monthly,pro_yearly,max_yearly",
        "max_uses": 2000,
        "description": "老用户续费任意月卡/年卡享 9 折",
    },
    {
        "code": "SHAREOFFICIAL",
        "name": "分享官专属券",
        "discount_type": "percent",
        "discount_value": 20,  # 减 20%
        "min_spend_cny": 1,
        "applicable_skus": "pro_monthly,max_monthly,single_ct,single_hook,single_persona,single_bps",
        "max_uses": 100,
        "description": "分享官专属 · 邀请好友注册后获得 · 全品类 8 折",
    },
]


async def main() -> None:
    # 确保表存在
    async with engine.begin() as conn:
        from app import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # 产品目录
        for p in PRODUCTS:
            res = await db.execute(select(ProductCatalog).where(ProductCatalog.sku == p["sku"]))
            if res.scalar_one_or_none():
                continue
            db.add(ProductCatalog(
                sku=p["sku"], name=p["name"], tier=p["tier"],
                billing_cycle=p["billing_cycle"], price_cny=p["price_cny"],
                description=p["description"],
                features=json.dumps(p["features"], ensure_ascii=False),
            ))
        print(f"✓ 产品目录: {len(PRODUCTS)} 项")

        # 对标库样例
        for b in BENCHMARKS:
            res = await db.execute(
                select(Benchmark).where(
                    Benchmark.platform == b["platform"],
                    Benchmark.account_id == b["account_id"],
                )
            )
            if res.scalar_one_or_none():
                continue
            db.add(Benchmark(**b))
        print(f"✓ 头部对标库: {len(BENCHMARKS)} 名")

        # 优惠券模板
        from datetime import datetime, timezone, timedelta

        coupon_count = 0
        for c in COUPONS:
            res = await db.execute(select(Coupon).where(Coupon.code == c["code"]))
            if res.scalar_one_or_none():
                continue
            db.add(Coupon(
                code=c["code"],
                name=c["name"],
                discount_type=c["discount_type"],
                discount_value=c["discount_value"],
                min_spend_cny=c.get("min_spend_cny", 0),
                applicable_skus=c.get("applicable_skus"),
                max_uses=c.get("max_uses", 1),
                valid_from=datetime.now(timezone.utc),
                valid_to=datetime.now(timezone.utc) + timedelta(days=365),
                is_active=True,
            ))
            coupon_count += 1
        print(f"✓ 优惠券模板: {coupon_count} 张")

        # 管理员账号
        res = await db.execute(select(User).where(User.phone == "13800138000"))
        if not res.scalar_one_or_none():
            admin = User(
                phone="13800138000", nickname="超级管理员", role="admin",
                password_hash=hash_password("admin1234"), is_active=True, is_realname=True,
            )
            db.add(admin)
            print("✓ 管理员 phone=13800138000 password=admin1234")

        # 顾问账号
        res = await db.execute(select(User).where(User.phone == "13900139000"))
        if not res.scalar_one_or_none():
            consultant = User(
                phone="13900139000", nickname="资深顾问·小张", role="consultant",
                password_hash=hash_password("consult1234"), is_active=True, is_realname=True,
            )
            db.add(consultant)
            print("✓ 顾问 phone=13900139000 password=consult1234")

        await db.commit()
        print("\nDone. 启动后端：uvicorn app.main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(main())
