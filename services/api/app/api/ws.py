"""WebSocket 实时推送端点 · 诊断进度 / 告警 / 对标更新 · 心跳 + Redis PubSub."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from app.config import settings
from app.core.security import decode_token

router = APIRouter()

# Redis PubSub 可选
try:
    import redis.asyncio as aioredis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    aioredis = None  # type: ignore


class ConnectionManager:
    """WebSocket 连接管理器 · 内存实现 + 可选 Redis PubSub."""

    # 心跳配置
    PING_INTERVAL_SEC = 30
    PING_TIMEOUT_SEC = 60

    def __init__(self) -> None:
        # user_id -> set of (ws, last_pong) tuples
        self._connections: dict[str, set[tuple[WebSocket, float]]] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

        # Redis PubSub（可选）
        self._redis: aioredis.Redis | None = None
        self._pubsub_task: asyncio.Task | None = None
        self._init_redis()

    def _init_redis(self) -> None:
        """初始化 Redis PubSub 连接."""
        if not HAS_REDIS or not settings.REDIS_URL:
            logger.info("[WS] Redis 未配置，跳过 PubSub")
            return
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            logger.info("[WS] Redis PubSub 已连接")
        except Exception as exc:
            logger.warning(f"[WS] Redis 连接失败，跳过 PubSub: {exc}")
            self._redis = None

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        """接受连接并注册."""
        await ws.accept()
        now = asyncio.get_event_loop().time()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add((ws, now))
        logger.info(
            f"[WS] user={user_id} connected (total users: {len(self._connections)})"
        )

        # 订阅 Redis PubSub（用户专属频道）
        if self._redis:
            await self._subscribe_user(user_id)

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        """移除连接."""
        async with self._lock:
            conns = self._connections.get(user_id, set())
            # 移除匹配的 ws
            conns = {(w, ts) for w, ts in conns if w is not ws}
            if conns:
                self._connections[user_id] = conns
            else:
                self._connections.pop(user_id, None)

        logger.info(f"[WS] user={user_id} disconnected")

        # 如果没有剩余连接，取消 Redis 订阅
        remaining = 0
        async with self._lock:
            conns = self._connections.get(user_id, set())
            remaining = len(conns)

        if remaining == 0 and self._redis:
            await self._unsubscribe_user(user_id)

    async def send_to_user(self, user_id: str | int, event: dict[str, Any]) -> None:
        """向指定用户的所有连接推送事件."""
        uid = str(user_id)
        async with self._lock:
            conns = list(self._connections.get(uid, set()))
        if not conns:
            return
        payload = json.dumps(event, ensure_ascii=False)
        dead_ws: list[WebSocket] = []
        now = asyncio.get_event_loop().time()

        for ws, _ in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_ws.append(ws)

        # 清理死连接
        if dead_ws:
            async with self._lock:
                live = self._connections.get(uid, set())
                live = {(w, ts) for w, ts in live if w not in dead_ws}
                if live:
                    self._connections[uid] = live
                else:
                    self._connections.pop(uid, None)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """向所有连接的用户广播事件."""
        async with self._lock:
            user_ids = list(self._connections.keys())
        for uid in user_ids:
            await self.send_to_user(uid, event)

    async def _heartbeat_loop(self, ws: WebSocket, user_id: str) -> None:
        """服务端心跳 · 定时发送 ping，检查客户端响应."""
        try:
            while True:
                await asyncio.sleep(self.PING_INTERVAL_SEC)

                # 发送 ping
                try:
                    await ws.send_json({"type": "ping", "ts": asyncio.get_event_loop().time()})
                except Exception:
                    logger.warning(f"[WS] ping 发送失败 user={user_id}")
                    break

                # 检查上次 pong 时间
                async with self._lock:
                    conns = self._connections.get(user_id, set())
                    last_pong = 0.0
                    for w, ts in conns:
                        if w is ws:
                            last_pong = ts
                            break

                now = asyncio.get_event_loop().time()
                if now - last_pong > self.PING_TIMEOUT_SEC:
                    logger.warning(
                        f"[WS] 心跳超时 user={user_id} "
                        f"last_pong={last_pong:.0f} now={now:.0f}"
                    )
                    break

        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error(f"[WS] 心跳异常 user={user_id}: {exc}")
        finally:
            # 心跳退出 → 关闭连接
            try:
                await ws.close(code=4002, reason="Heartbeat timeout")
            except Exception:
                pass

    async def _listen_client_messages(self, ws: WebSocket, user_id: str) -> None:
        """监听客户端消息（pong / subscribe 等）."""
        try:
            while True:
                raw = await ws.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type", "")
                now = asyncio.get_event_loop().time()

                if msg_type == "pong":
                    # 更新 last_pong 时间
                    async with self._lock:
                        conns = self._connections.get(user_id, set())
                        new_conns = set()
                        for w, ts in conns:
                            if w is ws:
                                new_conns.add((w, now))
                            else:
                                new_conns.add((w, ts))
                        self._connections[user_id] = new_conns

                elif msg_type == "subscribe":
                    # 订阅特定事件类型（预留）
                    pass

        except WebSocketDisconnect:
            logger.info(f"[WS] user={user_id} client disconnected")
        except Exception as exc:
            logger.error(f"[WS] user={user_id} message error: {exc}")

    # ---- Redis PubSub ----

    async def _subscribe_user(self, user_id: str) -> None:
        """订阅用户专属 Redis 频道."""
        if not self._redis:
            return
        try:
            pubsub = self._redis.pubsub()
            channel = f"events:user:{user_id}"
            await pubsub.subscribe(channel)
            # 后台任务：分发 Redis 消息到 WebSocket
            asyncio.create_task(self._pubsub_forward(user_id, pubsub))
            logger.info(f"[WS] Redis PubSub subscribed: {channel}")
        except Exception as exc:
            logger.warning(f"[WS] Redis subscribe failed: {exc}")

    async def _unsubscribe_user(self, user_id: str) -> None:
        """取消 Redis 频道订阅."""
        # 各 pubsub 由对应的 task 管理生命周期
        logger.info(f"[WS] Redis PubSub unsubscribed: events:user:{user_id}")

    async def _pubsub_forward(self, user_id: str, pubsub) -> None:
        """从 Redis PubSub 获取消息并转发到 WebSocket."""
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    event = json.loads(message["data"])
                    await self.send_to_user(user_id, event)
                except json.JSONDecodeError:
                    logger.warning(f"[WS] Redis PubSub 非 JSON 消息: {message['data'][:100]}")
                except Exception as exc:
                    logger.warning(f"[WS] Redis PubSub 转发失败: {exc}")
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning(f"[WS] Redis PubSub 监听异常: {exc}")
        finally:
            try:
                await pubsub.unsubscribe()
            except Exception:
                pass

    # ---- 发布事件到 Redis（供外部调用） ----

    async def publish_event(self, event_type: str, user_id: str | int, data: dict[str, Any]) -> None:
        """发布事件到 Redis，供所有服务节点消费."""
        if not self._redis:
            # 无 Redis：直接通过 WebSocket 内存推送
            await self.send_to_user(user_id, {"event": event_type, "data": data})
            return

        payload = json.dumps({"event": event_type, "data": data}, ensure_ascii=False)
        try:
            await self._redis.publish(f"events:user:{user_id}", payload)
        except Exception as exc:
            logger.warning(f"[WS] Redis publish failed: {exc}")
            # 降级：直接 WebSocket 推送
            await self.send_to_user(user_id, {"event": event_type, "data": data})

    @property
    def active_connections(self) -> int:
        """当前活跃连接总数."""
        total = 0
        for conns in self._connections.values():
            total += len(conns)
        return total


# 全局单例
manager = ConnectionManager()


async def _authenticate_ws(ws: WebSocket) -> str | None:
    """从 query param 或第一条消息中验证 JWT token，返回 user_id."""
    # 方式 1：query param ?token=xxx
    token = ws.query_params.get("token")
    if not token:
        # 方式 2：第一条消息为 JSON {"token": "xxx"}
        try:
            first_msg = await asyncio.wait_for(ws.receive_text(), timeout=10.0)
            data = json.loads(first_msg)
            token = data.get("token", "")
        except (asyncio.TimeoutError, json.JSONDecodeError):
            return None

    if not token:
        return None

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    return payload["sub"]


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(ws: WebSocket, user_id: str) -> None:
    """WebSocket 主端点 · 心跳 + Redis PubSub + 自动重连.

    认证方式：
    - Query param: /ws/123?token=jwt-token-here
    - First message: {"token": "jwt-token-here"}

    推送事件格式：
    {
      "event": "diagnosis.progress|diagnosis.completed|alert.triggered|benchmark.updated",
      "data": { ... }
    }
    """
    # 认证
    authed_user = await _authenticate_ws(ws)
    if authed_user is None or authed_user != user_id:
        # token 无效或 user_id 不匹配
        await ws.accept()
        await ws.send_json({
            "event": "auth_error",
            "data": {"message": "invalid token"},
        })
        await ws.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(user_id, ws)

    # 启动心跳任务
    heartbeat_task = asyncio.create_task(manager._heartbeat_loop(ws, user_id))

    try:
        # 发送连接确认
        await ws.send_json({
            "event": "connected",
            "data": {
                "user_id": user_id,
                "message": "WebSocket connected",
                "active_connections": manager.active_connections,
            },
        })

        # 监听客户端消息（pong / subscribe 等）
        await manager._listen_client_messages(ws, user_id)

    except WebSocketDisconnect:
        logger.info(f"[WS] user={user_id} client disconnected")
    except Exception as exc:
        logger.error(f"[WS] user={user_id} error: {exc}")
    finally:
        # 清理
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        await manager.disconnect(user_id, ws)
