# Python SDK

视频 CT 提供 Python SDK，基于 httpx 封装了鉴权、错误处理、类型提示。

## 安装

```bash
pip install video-ct-sdk
```

或使用 poetry / pdm：

```bash
poetry add video-ct-sdk
```

## 快速上手

### 基础封装（httpx）

以下是一个完整的 Python 客户端封装示例。它展示了如何访问所有主要端点。

```python
"""video_ct_sdk.py — 视频 CT Python SDK"""

from __future__ import annotations

import time
from typing import Any, Generic, TypeVar

import httpx

T = TypeVar("T")


class ApiResponse(Generic[T]):
    """统一 API 响应包装"""

    def __init__(self, code: str, message: str, data: T | None):
        self.code = code
        self.message = message
        self.data = data


class VideoCTError(Exception):
    """视频 CT API 错误"""

    def __init__(self, code: str, message: str, status: int | None = None):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(f"[{code}] {message}")


class VideoCTClient:
    """视频 CT API 客户端"""

    def __init__(
        self,
        base_url: str = "https://api.video-ct.cn",
        api_prefix: str = "/api/v1",
        timeout: float = 30.0,
        api_key: str | None = None,
    ):
        self.base_url = f"{base_url}{api_prefix}"
        self.timeout = timeout
        self.api_key = api_key
        self._token: str | None = None
        self._client = httpx.AsyncClient(timeout=timeout)

    # ─── 鉴权管理 ──────────────────────────────────

    def set_token(self, token: str) -> None:
        """设置 JWT token"""
        self._token = token

    def clear_token(self) -> None:
        """清除 token"""
        self._token = None

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        await self._client.aclose()

    # ─── HTTP 请求基础方法 ─────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        url = f"{self.base_url}{path}"
        resp = await self._client.request(
            method, url, json=json, params=params, headers=headers
        )

        data = resp.json()
        if resp.status_code >= 400:
            raise VideoCTError(
                code=data.get("code", "UNKNOWN"),
                message=data.get("message", "Unknown error"),
                status=resp.status_code,
            )

        return data

    # ─── 鉴权 ──────────────────────────────────────

    async def send_otp(self, phone: str) -> dict[str, Any]:
        """发送手机验证码"""
        return await self._request("POST", "/auth/otp/send", json={"phone": phone})

    async def verify_otp(
        self, phone: str, code: str, referrer_code: str | None = None
    ) -> dict[str, Any]:
        """验证码登录/注册"""
        body: dict[str, Any] = {"phone": phone, "code": code}
        if referrer_code:
            body["referrer_code"] = referrer_code
        return await self._request("POST", "/auth/otp/verify", json=body)

    async def wechat_login(
        self, code: str, referrer_code: str | None = None
    ) -> dict[str, Any]:
        """微信登录"""
        body: dict[str, Any] = {"code": code}
        if referrer_code:
            body["referrer_code"] = referrer_code
        return await self._request("POST", "/auth/wechat/login", json=body)

    async def get_me(self) -> dict[str, Any]:
        """获取当前用户信息"""
        return await self._request("GET", "/auth/me")

    # ─── 诊断 ──────────────────────────────────────

    async def submit_diagnosis(
        self,
        video_url: str,
        track: str | None = None,
        diagnosis_type: str = "ct_basic",
        title: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """提交视频诊断"""
        body: dict[str, Any] = {
            "video_url": video_url,
            "diagnosis_type": diagnosis_type,
        }
        if track:
            body["track"] = track
        if title:
            body["title"] = title
        if description:
            body["description"] = description
        return await self._request("POST", "/diagnoses/submit", json=body)

    async def list_diagnoses(self, limit: int = 20) -> dict[str, Any]:
        """诊断历史"""
        return await self._request("GET", "/diagnoses", params={"limit": limit})

    async def get_diagnosis(self, diagnosis_id: int) -> dict[str, Any]:
        """诊断详情"""
        return await self._request("GET", f"/diagnoses/{diagnosis_id}")

    async def get_report(self, diagnosis_id: int) -> dict[str, Any]:
        """获取诊断报告"""
        return await self._request("GET", f"/diagnoses/{diagnosis_id}/report")

    async def submit_feedback(
        self, diagnosis_id: int, rating: int, feedback: str | None = None
    ) -> dict[str, Any]:
        """提交报告反馈"""
        body: dict[str, Any] = {"rating": rating}
        if feedback:
            body["feedback"] = feedback
        return await self._request(
            "POST", f"/diagnoses/{diagnosis_id}/report/feedback", json=body
        )

    # ─── 对标 ──────────────────────────────────────

    async def list_tracks(self) -> dict[str, Any]:
        """所有对标赛道"""
        return await self._request("GET", "/benchmarks/tracks")

    async def get_top10(self, track: str) -> dict[str, Any]:
        """赛道 Top10"""
        return await self._request("GET", f"/benchmarks/top10/{track}")

    async def compute_gap(
        self, track: str, user_metrics: dict[str, float]
    ) -> dict[str, Any]:
        """计算对标差距"""
        return await self._request(
            "POST", "/benchmarks/gap",
            params={"track": track, "user_metrics": user_metrics},
        )

    # ─── 人设 ──────────────────────────────────────

    async def scan_persona(
        self,
        sample_video_urls: list[str] | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """人设扫描"""
        body: dict[str, Any] = {}
        if sample_video_urls:
            body["sample_video_urls"] = sample_video_urls
        if description:
            body["description"] = description
        return await self._request("POST", "/personas/scan", json=body)

    async def get_my_persona(self) -> dict[str, Any]:
        """我的人设档案"""
        return await self._request("GET", "/personas/me")

    async def get_archetypes(self) -> dict[str, Any]:
        """人设原型列表"""
        return await self._request("GET", "/personas/archetypes")

    # ─── 商业定位 ──────────────────────────────────

    async def scan_positioning(
        self, description: str | None = None
    ) -> dict[str, Any]:
        """商业定位扫描"""
        body: dict[str, Any] = {}
        if description:
            body["description"] = description
        return await self._request("POST", "/positionings/scan", json=body)

    async def get_my_positioning(self) -> dict[str, Any]:
        """我的定位档案"""
        return await self._request("GET", "/positionings/me")

    # ─── 订阅 ──────────────────────────────────────

    async def list_products(self) -> dict[str, Any]:
        """产品列表"""
        return await self._request("GET", "/subscriptions/products")

    async def create_order(
        self,
        sku: str,
        coupon_code: str | None = None,
        use_deduction: bool = False,
        referrer_code: str | None = None,
    ) -> dict[str, Any]:
        """创建订单"""
        body: dict[str, Any] = {
            "sku": sku,
            "use_deduction": use_deduction,
        }
        if coupon_code:
            body["coupon_code"] = coupon_code
        if referrer_code:
            body["referrer_code"] = referrer_code
        return await self._request("POST", "/subscriptions/orders", json=body)

    async def mock_pay(self, order_no: str) -> dict[str, Any]:
        """模拟支付（仅开发）"""
        return await self._request(
            "POST", f"/subscriptions/orders/{order_no}/mock-pay"
        )

    async def get_my_subscription(self) -> dict[str, Any]:
        """我的订阅"""
        return await self._request("GET", "/subscriptions/my")

    async def get_my_orders(self) -> dict[str, Any]:
        """我的订单"""
        return await self._request("GET", "/subscriptions/orders")

    # ─── 分享官 ────────────────────────────────────

    async def get_my_referrer(self) -> dict[str, Any]:
        """我的分享官信息"""
        return await self._request("GET", "/referrers/me")

    async def get_referrer_link(self) -> dict[str, Any]:
        """获取分享链接"""
        return await self._request("GET", "/referrers/link")

    async def get_referral_records(self) -> dict[str, Any]:
        """分享记录"""
        return await self._request("GET", "/referrers/records")

    async def withdraw(self, amount_cny: int) -> dict[str, Any]:
        """提现申请"""
        return await self._request(
            "POST", "/referrers/withdraw", json={"amount_cny": amount_cny}
        )

    async def get_leaderboard(self, limit: int = 30) -> dict[str, Any]:
        """本月分享榜"""
        return await self._request(
            "GET", "/referrers/leaderboard", params={"limit": limit}
        )

    # ─── 成长档案 ──────────────────────────────────

    async def get_my_archive(self) -> dict[str, Any]:
        """我的档案"""
        return await self._request("GET", "/archives/me")

    async def get_growth_curve(self) -> dict[str, Any]:
        """成长曲线"""
        return await self._request("GET", "/archives/me/curve")


# ─── 轮询工具 ──────────────────────────────────────

async def wait_for_report(
    client: VideoCTClient,
    diagnosis_id: int,
    max_retries: int = 30,
    interval: float = 2.0,
) -> dict[str, Any]:
    """轮询等待诊断报告完成"""
    for _ in range(max_retries):
        resp = await client.get_report(diagnosis_id)
        if resp.get("data") is not None:
            return resp["data"]
        await asyncio.sleep(interval)
    raise VideoCTError("TIMEOUT", "诊断超时")
```

## 使用示例

```python
import asyncio
from video_ct_sdk import VideoCTClient, wait_for_report

async def main():
    client = VideoCTClient(base_url="https://api.video-ct.cn")

    try:
        # 1. 发送验证码
        result = await client.send_otp("13800138000")
        dev_code = result["data"]["dev_code"]
        print(f"验证码（开发模式）: {dev_code}")

        # 2. 登录
        login = await client.verify_otp("13800138000", dev_code)
        token = login["data"]["access_token"]
        client.set_token(token)
        print(f"登录成功，用户: {login['data']['nickname']}")

        # 3. 提交诊断
        diag = await client.submit_diagnosis(
            video_url="https://v.douyin.com/xxxxx/",
            track="美食",
            diagnosis_type="ct_basic",
        )
        diagnosis_id = diag["data"]["id"]
        print(f"诊断已提交: #{diagnosis_id}")

        # 4. 等待报告
        report = await wait_for_report(client, diagnosis_id)
        print(f"综合评分: {report['overall_score']}")
        print(f"评级: {report['grade']}")

        # 5. 查看对标
        top10 = await client.get_top10("美食")
        for item in top10["data"]:
            print(f"  #{item['rank']} {item['nickname']} ({item['follower_count']}粉)")

        # 6. 人设扫描
        persona = await client.scan_persona(
            description="我是一个有态度的美食测评博主"
        )
        print(f"主原型: {persona['data']['primary_archetype']}")

    finally:
        await client.close()

asyncio.run(main())
```

## Flask / FastAPI 集成

```python
# app.py — FastAPI 后端使用视频 CT SDK
from fastapi import FastAPI, Depends
from video_ct_sdk import VideoCTClient

app = FastAPI()
vct_client = VideoCTClient(
    base_url="https://api.video-ct.cn",
    api_key="vct_sk_xxxxxxxx",  # 服务端使用 API Key
)


@app.get("/api/trending-bloggers")
async def get_trending_bloggers():
    """代理：获取多个赛道的头部博主"""
    tracks = ["美食", "科技", "穿搭"]
    results = {}
    for track in tracks:
        resp = await vct_client.get_top10(track)
        results[track] = resp["data"]
    return {"tracks": results}


@app.get("/api/benchmark/{track}")
async def benchmark_track(track: str):
    """代理：获取某赛道对标数据"""
    resp = await vct_client.get_top10(track)
    return resp["data"]
```

## Django 集成

```python
# services.py
from video_ct_sdk import VideoCTClient
from django.conf import settings

vct_client = VideoCTClient(
    base_url=settings.VCT_API_BASE_URL,
    api_key=settings.VCT_API_KEY,
)


async def get_user_report(diagnosis_id: int) -> dict:
    """获取用户的诊断报告"""
    resp = await vct_client.get_report(diagnosis_id)
    return resp["data"]
```

## 类型提示

如果你使用 Pydantic 定义数据模型，可以参考后端 schema 定义对应的模型类：

```python
from pydantic import BaseModel
from datetime import datetime


class DiagnosisOut(BaseModel):
    id: int
    video_url: str
    video_platform: str | None
    status: str
    diagnosis_type: str
    progress_pct: int
    created_at: datetime
    completed_at: datetime | None


class ReportOut(BaseModel):
    id: int
    diagnosis_id: int
    overall_score: int
    grade: str
    dimensions: dict
    findings: list[dict]
    benchmark_gap: dict | None
    created_at: datetime
```

::: tip 同步用法
如果需要同步调用，可以使用 `httpx.Client` 替代 `httpx.AsyncClient`，
或使用 `asyncio.run()` 包装异步调用。
:::
