#!/usr/bin/env python3
"""
Phase Gate 状态检查

本地运行:  python3 scripts/check-phase-gate.py
CI 运行:   python3 scripts/check-phase-gate.py --json

输出当前 Phase 及距下一阶段的差距。
"""
import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.phase_gate import get_current_phase


async def main(as_json: bool) -> None:
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://video_ct:video_ct@localhost:5432/video_ct",
    )
    engine = create_async_engine(db_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        status = await get_current_phase(session)

    await engine.dispose()

    if as_json:
        print(json.dumps({
            "current_phase": status.current_phase.value,
            "metrics": status.metrics,
            "next_phase": status.next_phase.value if status.next_phase else None,
            "next_threshold": status.next_threshold,
        }, indent=2, ensure_ascii=False))
        return

    phase_labels = {0: "Phase 0 (已激活)", 1: "Phase 1", 2: "Phase 2", 3: "Phase 3"}
    print(f"✅ 当前: {phase_labels[status.current_phase.value]}")
    print(f"   指标:")
    for k, v in status.metrics.items():
        print(f"     {k}: {v}")

    if status.next_phase and status.next_threshold:
        print(f"\n📍 距 Phase {status.next_phase.value} 还需:")
        for k, v in status.next_threshold.items():
            if k.startswith("required_"):
                label = k.replace("required_", "")
                current_key = f"current_{label}" if f"current_{label}" in status.next_threshold else "current"
                current = status.next_threshold.get(current_key, status.metrics.get(label, "?"))
                print(f"     {label}: {current} / {v}")
    else:
        print("\n🎉 已达最高阶段 Phase 3")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="检查 Phase Gate 状态")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出（CI 用）")
    args = parser.parse_args()
    asyncio.run(main(args.json))
