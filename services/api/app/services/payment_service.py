"""支付服务 · 微信支付 v3 真码 + mock 兼容.

生产：通过 httpx 手写 v3 签名流程调微信 API
开发：WECHAT_PAY_MCH_ID 以 mock_ 开头时走 mock 路径

依赖：
  - httpx：HTTP 客户端（必需）
  - cryptography：RSA 签名 + AES-GCM 解密（仅生产支付需要，mock 模式不需要）
"""
from __future__ import annotations

import json
import os
import random
import string
import time
from base64 import b64encode, b64decode
from datetime import datetime, timezone

import httpx
from loguru import logger

from app.config import settings

# cryptography 是可选依赖（仅生产支付需要），mock 模式下不需要
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning(
        "[PAY] cryptography 未安装 · 真实支付不可用 · 仅支持 mock 模式"
        "（安装: pip install cryptography）"
    )


WECHAT_V3_HOST = "https://api.mch.weixin.qq.com"


# ── 工具函数 ──────────────────────────────────────────────

def _gen_nonce() -> str:
    """生成随机 nonce 字符串（32 位字母数字）."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=32))


def _load_private_key() -> serialization.rsa.RSAPrivateKey | None:
    """从 PEM 文件加载商户私钥."""
    path = settings.WECHAT_PAY_PRIVATE_KEY_PATH
    if not path or not os.path.exists(path):
        logger.warning("微信支付私钥文件未找到: {}", path)
        return None
    with open(path, "rb") as f:
        pem_data = f.read()
    try:
        key = serialization.load_pem_private_key(pem_data, password=None, backend=default_backend())
        if not isinstance(key, serialization.rsa.RSAPrivateKey):
            return None
        return key
    except Exception as exc:
        logger.error("加载微信支付私钥失败: {}", exc)
        return None


def _sign_v3(
    method: str,
    url_path: str,
    body: str,
    *,
    private_key: serialization.rsa.RSAPrivateKey | None = None,
) -> tuple[str, dict[str, str]]:
    """构造 v3 签名，返回 (signature_base64, headers).

    签名规则：
      1. sign_message = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"
      2. 用商户私钥 SHA256-RSA2048 签名
      3. 返回 base64 编码的签名
    """
    timestamp = str(int(time.time()))
    nonce = _gen_nonce()
    sign_message = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"

    if private_key is None:
        private_key = _load_private_key()

    if private_key is None:
        # mock 或无密钥时，返回占位签名
        return (
            "MOCK_SIGNATURE",
            {
                "Authorization": (
                    f'WECHATPAY2-SHA256-RSA2048 mchid="{settings.WECHAT_PAY_MCH_ID}",'
                    f'nonce_str="{nonce}",timestamp="{timestamp}",'
                    f'serial_no="{settings.WECHAT_PAY_CERT_SERIAL_NO}",'
                    f'signature="MOCK_SIGNATURE"'
                ),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    # 真正签名
    signature_bytes = private_key.sign(
        sign_message.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    signature = b64encode(signature_bytes).decode("utf-8")

    headers = {
        "Authorization": (
            f'WECHATPAY2-SHA256-RSA2048 mchid="{settings.WECHAT_PAY_MCH_ID}",'
            f'nonce_str="{nonce}",timestamp="{timestamp}",'
            f'serial_no="{settings.WECHAT_PAY_CERT_SERIAL_NO}",'
            f'signature="{signature}"'
        ),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return signature, headers


# ── 支付 API ─────────────────────────────────────────────

async def create_jsapi_order(
    order_no: str,
    openid: str,
    amount_cny: int,
    description: str,
) -> dict:
    """创建 JSAPI 支付订单 · 返回前端 wx.requestPayment 所需参数.

    Returns:
        {
            appId: str,
            timeStamp: str,
            nonceStr: str,
            package: str,      # "prepay_id=wx..."
            signType: "RSA",
            paySign: str,
            mock: bool,         # mock 模式下为 True
        }
    """
    # ─ mock 路径 ─
    if settings.is_pay_mock:
        prepay_id = f"prepay_mock_{order_no}_{int(time.time())}"
        logger.info("[PAY][MOCK] create_jsapi mock order_no={}", order_no)
        return _mock_jsapi_params(prepay_id, order_no)

    # ─ 真实路径：调微信 v3 ─
    url_path = "/v3/pay/transactions/jsapi"
    body = {
        "appid": settings.WECHAT_APP_ID,
        "mchid": settings.WECHAT_PAY_MCH_ID,
        "description": description,
        "out_trade_no": order_no,
        "notify_url": settings.WECHAT_NOTIFY_URL,
        "amount": {
            "total": amount_cny * 100,  # 微信金额单位：分
            "currency": "CNY",
        },
        "payer": {"openid": openid},
    }
    body_str = json.dumps(body, ensure_ascii=False)

    _, req_headers = _sign_v3("POST", url_path, body_str)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                f"{WECHAT_V3_HOST}{url_path}",
                content=body_str,
                headers=req_headers,
            )
            data = resp.json()
        except Exception as exc:
            logger.error("[PAY] create_jsapi_order HTTP error: {}", exc)
            raise RuntimeError(f"微信支付请求失败: {exc}") from exc

    if resp.status_code != 200:
        logger.error(
            "[PAY] create_jsapi_order failed status={} body={}",
            resp.status_code,
            resp.text,
        )
        raise RuntimeError(f"微信支付创建失败: {data.get('message', resp.text)}")

    prepay_id = data.get("prepay_id", "")
    if not prepay_id:
        raise RuntimeError(f"微信支付未返回 prepay_id: {data}")

    return _build_jsapi_params(prepay_id)


def _mock_jsapi_params(prepay_id: str, order_no: str) -> dict:
    """构造 mock 模式的 JSAPI 调起参数."""
    timestamp = str(int(time.time()))
    nonce = _gen_nonce()
    return {
        "appId": settings.WECHAT_APP_ID or "mock_appid",
        "timeStamp": timestamp,
        "nonceStr": nonce,
        "package": f"prepay_id={prepay_id}",
        "signType": "RSA",
        "paySign": _gen_nonce(),
        "mock": True,
        "order_no": order_no,
    }


def _build_jsapi_params(prepay_id: str) -> dict:
    """用商户私钥对 prepay_id 二次签名，返回 wx.requestPayment 参数."""
    app_id = settings.WECHAT_APP_ID
    timestamp = str(int(time.time()))
    nonce = _gen_nonce()
    pkg = f"prepay_id={prepay_id}"

    # 二次签名字符串：appId, timeStamp, nonceStr, package
    sign_message = f"{app_id}\n{timestamp}\n{nonce}\n{pkg}\n"
    private_key = _load_private_key()

    if private_key is None:
        pay_sign = "MOCK_SIGNATURE"
    else:
        sig = private_key.sign(
            sign_message.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        pay_sign = b64encode(sig).decode("utf-8")

    return {
        "appId": app_id,
        "timeStamp": timestamp,
        "nonceStr": nonce,
        "package": pkg,
        "signType": "RSA",
        "paySign": pay_sign,
        "mock": False,
    }


async def create_h5_order(
    order_no: str,
    amount_cny: int,
    description: str,
    client_ip: str = "127.0.0.1",
) -> dict:
    """创建 H5 支付订单 · 返回 h5_url（微信外浏览器打开）.

    Returns:
        {
            h5_url: str,
            order_no: str,
            mock: bool,
        }
    """
    # ─ mock 路径 ─
    if settings.is_pay_mock:
        logger.info("[PAY][MOCK] create_h5 mock order_no={}", order_no)
        return {
            "h5_url": f"https://mock.example.com/h5pay/{order_no}",
            "order_no": order_no,
            "mock": True,
        }

    # ─ 真实路径 ─
    url_path = "/v3/pay/transactions/h5"
    body = {
        "appid": settings.WECHAT_APP_ID,
        "mchid": settings.WECHAT_PAY_MCH_ID,
        "description": description,
        "out_trade_no": order_no,
        "notify_url": settings.WECHAT_NOTIFY_URL,
        "amount": {
            "total": amount_cny * 100,
            "currency": "CNY",
        },
        "scene_info": {
            "payer_client_ip": client_ip,
            "h5_info": {"type": "Wap"},
        },
    }
    body_str = json.dumps(body, ensure_ascii=False)

    _, req_headers = _sign_v3("POST", url_path, body_str)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                f"{WECHAT_V3_HOST}{url_path}",
                content=body_str,
                headers=req_headers,
            )
            data = resp.json()
        except Exception as exc:
            logger.error("[PAY] create_h5_order HTTP error: {}", exc)
            raise RuntimeError(f"微信支付 H5 请求失败: {exc}") from exc

    if resp.status_code != 200:
        logger.error(
            "[PAY] create_h5_order failed status={} body={}",
            resp.status_code,
            resp.text,
        )
        raise RuntimeError(f"微信 H5 支付创建失败: {data.get('message', resp.text)}")

    return {
        "h5_url": data.get("h5_url", ""),
        "order_no": order_no,
        "mock": False,
    }


async def query_order(out_trade_no: str) -> dict:
    """查询微信支付订单状态 · GET /v3/pay/transactions/out-trade-no/{out_trade_no}.

    Returns:
        {
            trade_state: "SUCCESS" | "NOTPAY" | "REFUND" | "CLOSED" | ...,
            transaction_id: str | None,
            trade_state_desc: str,
        }
    """
    # ─ mock 路径 ─
    if settings.is_pay_mock:
        logger.info("[PAY][MOCK] query mock order_no={}", out_trade_no)
        return {
            "trade_state": "SUCCESS",
            "transaction_id": f"txn_mock_{out_trade_no}",
            "trade_state_desc": "支付成功（mock）",
        }

    url_path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}"
    # GET 请求 query 参数拼在 URL path 上，body 为空
    query_path = f"{url_path}?mchid={settings.WECHAT_PAY_MCH_ID}"
    _, req_headers = _sign_v3("GET", query_path, "")

    full_headers: dict[str, str] = {
        "Authorization": req_headers["Authorization"],
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                f"{WECHAT_V3_HOST}{query_path}",
                headers=full_headers,
            )
            data = resp.json()
        except Exception as exc:
            logger.error("[PAY] query_order HTTP error: {}", exc)
            raise RuntimeError(f"微信支付查询失败: {exc}") from exc

    if resp.status_code != 200:
        logger.error(
            "[PAY] query_order failed status={} body={}",
            resp.status_code,
            resp.text,
        )
        raise RuntimeError(f"微信支付查询失败: {data.get('message', resp.text)}")

    return {
        "trade_state": data.get("trade_state", "UNKNOWN"),
        "transaction_id": data.get("transaction_id"),
        "trade_state_desc": data.get("trade_state_desc", ""),
    }


# ── 回调验签 ─────────────────────────────────────────────

async def verify_wechat_callback(
    headers: dict,
    body: str,
) -> tuple[bool, str | None]:
    """验证微信支付回调签名。

    微信 v3 回调签名验证：
      1. 从 headers 中取 Wechatpay-Signature / Nonce / Timestamp / Serial
      2. 用微信平台证书（下载或缓存）验签
      3. 解密 body 中的 resource（AES-256-GCM）

    Args:
        headers: 请求头（含 Wechatpay-* 字段）
        body: 原始 JSON body 字符串

    Returns:
        (is_valid, order_no): 验签成功则返回订单号，失败返回 (False, None)
    """
    # ─ mock 模式直接通过 ─
    if settings.is_pay_mock:
        logger.info("[PAY][MOCK] verify_wechat_callback passed (mock mode)")
        try:
            payload = json.loads(body)
            resource = payload.get("resource", {})
            # mock 时从 body 中直接取（真实场景需 AES-GCM 解密）
            ciphertext = resource.get("ciphertext", "{}")
            if isinstance(ciphertext, str):
                inner = json.loads(ciphertext)
            else:
                inner = resource if isinstance(resource, dict) else {}
            order_no = inner.get("out_trade_no")
            if order_no:
                return True, order_no
            # fallback: 尝试从 payload 中读取
            order_no = payload.get("out_trade_no")
            return order_no is not None, order_no
        except Exception:
            return False, None

    # ─ 真实验签 ─
    wechatpay_signature = headers.get("wechatpay-signature", "")
    wechatpay_nonce = headers.get("wechatpay-nonce", "")
    wechatpay_timestamp = headers.get("wechatpay-timestamp", "")
    wechatpay_serial = headers.get("wechatpay-serial", "")

    if not all([wechatpay_signature, wechatpay_nonce, wechatpay_timestamp, wechatpay_serial]):
        logger.warning("[PAY] 微信回调缺少必要签名头")
        return False, None

    # 加载微信平台证书（此处用配置的证书序列号验签）
    # 生产环境应定期更新平台证书（从 https://api.mch.weixin.qq.com/v3/certificates 获取）
    platform_cert_pem = _load_platform_certificate(wechatpay_serial)
    if platform_cert_pem is None:
        logger.warning(
            "[PAY] 未找到序列号 {} 对应的平台证书，跳过验签（开发模式允许）",
            wechatpay_serial,
        )
        # 开发环境：跳过验签但记录日志
        if settings.NODE_ENV == "development":
            try:
                payload = json.loads(body)
                order_no = _decrypt_and_extract_order_no(payload)
                return order_no is not None, order_no
            except Exception as exc:
                logger.error("[PAY] 回调 body 解析失败: {}", exc)
                return False, None
        return False, None

    # 验签：sign_message = timestamp\nnonce\nbody\n
    sign_message = f"{wechatpay_timestamp}\n{wechatpay_nonce}\n{body}\n"

    try:
        cert = serialization.load_pem_x509_certificate(
            platform_cert_pem.encode("utf-8"),
            backend=default_backend(),
        )
        public_key = cert.public_key()
        if not isinstance(public_key, serialization.rsa.RSAPublicKey):
            logger.error("[PAY] 平台证书公钥不是 RSA")
            return False, None

        sig_bytes = b64decode(wechatpay_signature)

        public_key.verify(
            sig_bytes,
            sign_message.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        logger.info("[PAY] 微信回调验签通过")
    except Exception as exc:
        logger.error("[PAY] 微信回调验签失败: {}", exc)
        return False, None

    # 验签通过后解密 body
    try:
        payload = json.loads(body)
        order_no = _decrypt_and_extract_order_no(payload)
        return order_no is not None, order_no
    except Exception as exc:
        logger.error("[PAY] 回调 body 解析失败: {}", exc)
        return False, None


# ── 平台证书管理 ─────────────────────────────────────────

def _load_platform_certificate(serial_no: str) -> str | None:
    """从本地缓存加载微信平台证书 PEM.

    生产环境应定期从 /v3/certificates 下载并缓存到本地。
    """
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "certs")
    cert_path = os.path.join(cache_dir, f"wechat_platform_{serial_no}.pem")
    if os.path.exists(cert_path):
        with open(cert_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


async def refresh_platform_certificates() -> list[dict]:
    """从微信下载最新平台证书列表.

    Returns:
        list of {"serial_no": "...", "expire_time": "...", "pem": "..."}
    """
    if settings.is_pay_mock:
        return []

    url_path = "/v3/certificates"
    _, req_headers = _sign_v3("GET", url_path, "")

    full_headers: dict[str, str] = {
        "Authorization": req_headers["Authorization"],
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{WECHAT_V3_HOST}{url_path}",
            headers=full_headers,
        )
        data = resp.json()

    if resp.status_code != 200:
        logger.error("[PAY] 获取平台证书失败: {}", data)
        return []

    certs = []
    for cert_data in data.get("data", []):
        encrypt_cert = cert_data.get("encrypt_certificate", {})
        pem_text = _decrypt_certificate(
            encrypt_cert.get("ciphertext", ""),
            encrypt_cert.get("associated_data", ""),
            encrypt_cert.get("nonce", ""),
        )
        if pem_text:
            serial_no = cert_data.get("serial_no", "")
            expire_time = cert_data.get("expire_time", "")
            certs.append({
                "serial_no": serial_no,
                "expire_time": expire_time,
                "pem": pem_text,
            })
            # 缓存到本地
            _cache_certificate(serial_no, pem_text)

    return certs


def _cache_certificate(serial_no: str, pem: str) -> None:
    """缓存平台证书到本地文件."""
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "certs")
    os.makedirs(cache_dir, exist_ok=True)
    cert_path = os.path.join(cache_dir, f"wechat_platform_{serial_no}.pem")
    with open(cert_path, "w", encoding="utf-8") as f:
        f.write(pem)


def _decrypt_certificate(ciphertext: str, associated_data: str, nonce: str) -> str | None:
    """用 APIv3 key 解密证书密文（AES-256-GCM）."""
    if not CRYPTO_AVAILABLE:
        return None

    api_v3_key = settings.WECHAT_PAY_API_V3_KEY
    if not api_v3_key:
        return None

    try:
        key = api_v3_key.encode("utf-8")
        aesgcm = AESGCM(key)
        cipher_bytes = b64decode(ciphertext)
        nonce_bytes = nonce.encode("utf-8")
        associated_bytes = associated_data.encode("utf-8") if associated_data else b""
        plaintext = aesgcm.decrypt(nonce_bytes, cipher_bytes, associated_bytes)
        return plaintext.decode("utf-8")
    except Exception as exc:
        logger.error("[PAY] 证书密文解密失败: {}", exc)
        return None


def _decrypt_and_extract_order_no(payload: dict) -> str | None:
    """从回调 payload 中解密 resource 并提取 out_trade_no."""
    if not CRYPTO_AVAILABLE:
        return None

    resource = payload.get("resource", {})
    ciphertext = resource.get("ciphertext", "")
    nonce = resource.get("nonce", "")
    associated_data = resource.get("associated_data", "")

    if not ciphertext or not nonce:
        return None

    api_v3_key = settings.WECHAT_PAY_API_V3_KEY
    if not api_v3_key:
        # 开发模式：尝试直接解析（mock 场景）
        if settings.NODE_ENV == "development":
            try:
                plaintext = b64decode(ciphertext).decode("utf-8")
                inner = json.loads(plaintext)
                return inner.get("out_trade_no")
            except Exception:
                pass
        logger.warning("[PAY] APIv3 key 未配置，无法解密回调 body")
        return None

    try:
        key = api_v3_key.encode("utf-8")
        aesgcm = AESGCM(key)
        cipher_bytes = b64decode(ciphertext)
        nonce_bytes = nonce.encode("utf-8")
        ad_bytes = associated_data.encode("utf-8") if associated_data else b""
        plaintext = aesgcm.decrypt(nonce_bytes, cipher_bytes, ad_bytes)
        inner = json.loads(plaintext.decode("utf-8"))
        return inner.get("out_trade_no")
    except Exception as exc:
        logger.error("[PAY] 回调数据解密失败: {}", exc)
        return None


# ── 兼容旧接口（deprecated，供过渡期使用） ──────────────

async def create_wechat_pay(order: "Order") -> dict:  # noqa: F821
    """[deprecated] 旧版创建支付接口 · 内部路由到 create_jsapi_order.

    保留此函数以确保现有 api/subscription.py 调用不报错。
    新代码应直接调用 create_jsapi_order / create_h5_order。
    """
    from app.models.subscription import Order

    if not isinstance(order, Order):
        raise TypeError("order 必须是 Order 实例")

    product_name = order.sku  # fallback
    result = await create_jsapi_order(
        order_no=order.order_no,
        openid=f"user_{order.user_id}",  # 无真实 openid 时用 uid 标识
        amount_cny=order.paid_cny,
        description=f"视频 CT · {product_name}",
    )
    return result
