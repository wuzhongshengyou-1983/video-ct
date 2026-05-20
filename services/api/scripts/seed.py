"""数据库初始化 seed · 产品目录 + 头部对标库样例 + 管理员账号."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import ProductCatalog, User, Benchmark  # noqa: E402
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


BENCHMARKS = [
    {"track": "职场干货", "platform": "douyin", "account_id": "demo_pro_zc_1", "nickname": "职场老炮（演示）", "follower_count": 5_120_000, "rank_in_track": 1, "style_archetype": "干货型-教学派"},
    {"track": "职场干货", "platform": "douyin", "account_id": "demo_pro_zc_2", "nickname": "HR 王姐（演示）", "follower_count": 3_400_000, "rank_in_track": 2, "style_archetype": "气场型-行业权威"},
    {"track": "职场干货", "platform": "douyin", "account_id": "demo_pro_zc_3", "nickname": "面试官说（演示）", "follower_count": 2_800_000, "rank_in_track": 3, "style_archetype": "干货型-拆解派"},

    {"track": "美食料理", "platform": "douyin", "account_id": "demo_food_1", "nickname": "厨神老张（演示）", "follower_count": 8_200_000, "rank_in_track": 1, "style_archetype": "趣味型-段子手"},
    {"track": "美食料理", "platform": "douyin", "account_id": "demo_food_2", "nickname": "深夜食堂（演示）", "follower_count": 5_600_000, "rank_in_track": 2, "style_archetype": "共情型-治愈系"},

    {"track": "穿搭时尚", "platform": "xiaohongshu", "account_id": "demo_fashion_1", "nickname": "时尚 Vivi（演示）", "follower_count": 1_200_000, "rank_in_track": 1, "style_archetype": "气场型-反差大佬"},
    {"track": "穿搭时尚", "platform": "douyin", "account_id": "demo_fashion_2", "nickname": "穿搭研究室（演示）", "follower_count": 980_000, "rank_in_track": 2, "style_archetype": "干货型-资源派"},

    {"track": "育儿亲子", "platform": "douyin", "account_id": "demo_baby_1", "nickname": "豆豆妈成长记（演示）", "follower_count": 2_300_000, "rank_in_track": 1, "style_archetype": "共情型-闺蜜型"},

    {"track": "科技数码", "platform": "bilibili", "account_id": "demo_tech_1", "nickname": "科技阿杰（演示）", "follower_count": 4_500_000, "rank_in_track": 1, "style_archetype": "干货型-拆解派"},
    {"track": "科技数码", "platform": "douyin", "account_id": "demo_tech_2", "nickname": "数码老炮（演示）", "follower_count": 3_100_000, "rank_in_track": 2, "style_archetype": "气场型-行业权威"},
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
