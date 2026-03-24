"""
cloudinary_upload.py — Upload audio lên Cloudinary qua REST API
Dùng signed upload với SHA-256 (chuẩn mới của Cloudinary)

Credentials trong Streamlit Secrets hoặc .env:
    CLD_CLOUD_NAME = "your_cloud_name"
    CLD_API_KEY    = "123456789012345"
    CLD_API_SECRET = "your_api_secret"
"""

import hashlib
import io
import os
import time

import requests


def _get_creds() -> tuple[str, str, str]:
    try:
        import streamlit as st
        cloud = st.secrets.get("CLD_CLOUD_NAME", "") or os.environ.get("CLD_CLOUD_NAME", "")
        key   = st.secrets.get("CLD_API_KEY",    "") or os.environ.get("CLD_API_KEY",    "")
        sec   = st.secrets.get("CLD_API_SECRET", "") or os.environ.get("CLD_API_SECRET", "")
    except Exception:
        cloud = os.environ.get("CLD_CLOUD_NAME", "")
        key   = os.environ.get("CLD_API_KEY",    "")
        sec   = os.environ.get("CLD_API_SECRET", "")
    return cloud.strip(), key.strip(), sec.strip()


def has_cloudinary_config() -> bool:
    cloud, key, sec = _get_creds()
    return bool(cloud and key and sec)


def _sign(params: dict, secret: str) -> str:
    """
    Tạo signature đúng chuẩn Cloudinary v1.5:
    1. Lọc bỏ api_key, file, resource_type, cloud_name
    2. Sắp xếp theo alphabet
    3. Nối thành chuỗi key=value&...
    4. Thêm secret vào cuối (KHÔNG có &)
    5. SHA-1 (Cloudinary vẫn dùng SHA-1 cho REST API)
    """
    skip = {"api_key", "file", "resource_type", "cloud_name"}
    pairs = sorted(
        (k, str(v)) for k, v in params.items()
        if k not in skip and v is not None and str(v) != ""
    )
    to_sign = "&".join(f"{k}={v}" for k, v in pairs) + secret
    return hashlib.sha1(to_sign.encode("utf-8")).hexdigest()


def upload_audio_to_cloudinary(audio_bytes: bytes, filename: str) -> dict:
    """
    Upload audio bytes lên Cloudinary dạng raw resource.

    Returns:
        {"url": str, "public_id": str, "bytes": int, "format": str}

    Raises:
        RuntimeError nếu thiếu credentials hoặc Cloudinary báo lỗi
    """
    cloud, key, sec = _get_creds()

    if not all([cloud, key, sec]):
        raise RuntimeError(
            "Thiếu Cloudinary credentials!\n"
            "Thêm vào Streamlit Secrets:\n"
            "  CLD_CLOUD_NAME = ...\n"
            "  CLD_API_KEY    = ...\n"
            "  CLD_API_SECRET = ..."
        )

    timestamp = int(time.time())
    # Lưu vào folder tts_audio, không cần extension trong public_id
    base      = filename.rsplit(".", 1)[0]
    public_id = f"tts_audio/{base}"

    # Params dùng để ký — phải khớp chính xác với params gửi lên
    sign_params = {
        "public_id":        public_id,
        "timestamp":        timestamp,
        "unique_filename":  "false",
        "use_filename":     "false",
    }
    signature = _sign(sign_params, sec)

    # Endpoint raw/upload — dùng cho tất cả file không phải ảnh/video
    url = f"https://api.cloudinary.com/v1_1/{cloud}/raw/upload"

    # Form data — phải khớp với sign_params
    form_data = {
        "api_key":          key,
        "timestamp":        str(timestamp),
        "signature":        signature,
        "public_id":        public_id,
        "unique_filename":  "false",
        "use_filename":     "false",
    }

    # Detect MIME type từ extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
    mime_map = {"wav": "audio/wav", "mp3": "audio/mpeg", "ogg": "audio/ogg"}
    mime_type = mime_map.get(ext, "application/octet-stream")

    resp = requests.post(
        url,
        data=form_data,
        files={"file": (filename, io.BytesIO(audio_bytes), mime_type)},
        timeout=60,
    )

    # Parse response dù status code bao nhiêu
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Cloudinary response không hợp lệ (HTTP {resp.status_code}): {resp.text[:400]}")

    # Báo lỗi rõ ràng nếu Cloudinary trả lỗi
    if "error" in data:
        msg = data["error"].get("message", str(data["error"]))
        raise RuntimeError(f"Cloudinary từ chối upload: {msg}")

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"HTTP {resp.status_code}: {data}")

    secure_url = data.get("secure_url") or data.get("url", "")
    if not secure_url:
        raise RuntimeError(f"Upload thành công nhưng không có URL: {data}")

    return {
        "url":       secure_url,
        "public_id": data.get("public_id", ""),
        "bytes":     data.get("bytes", 0),
        "format":    data.get("format", ext),
    }
