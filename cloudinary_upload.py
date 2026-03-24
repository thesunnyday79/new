"""
cloudinary_upload.py — Upload audio lên Cloudinary qua REST API
Credentials lưu trong Streamlit Secrets hoặc .env

Cần có trong Secrets / .env:
    CLD_CLOUD_NAME = "your_cloud_name"
    CLD_API_KEY    = "your_api_key"
    CLD_API_SECRET = "your_api_secret"

Lấy credentials tại: https://cloudinary.com/console
"""

import hashlib
import io
import os
import time

import requests


# ─── Lấy credentials ──────────────────────────────────────────────────────────

def _get_creds() -> tuple[str, str, str]:
    try:
        import streamlit as st
        cloud = st.secrets.get("CLD_CLOUD_NAME", os.environ.get("CLD_CLOUD_NAME", ""))
        key   = st.secrets.get("CLD_API_KEY",    os.environ.get("CLD_API_KEY", ""))
        sec   = st.secrets.get("CLD_API_SECRET", os.environ.get("CLD_API_SECRET", ""))
    except Exception:
        cloud = os.environ.get("CLD_CLOUD_NAME", "")
        key   = os.environ.get("CLD_API_KEY", "")
        sec   = os.environ.get("CLD_API_SECRET", "")
    return cloud, key, sec


def has_cloudinary_config() -> bool:
    cloud, key, sec = _get_creds()
    return bool(cloud and key and sec)


# ─── Upload ───────────────────────────────────────────────────────────────────

def upload_audio_to_cloudinary(audio_bytes: bytes, filename: str) -> dict:
    """
    Upload audio bytes lên Cloudinary.

    Returns dict:
        {
          "url":        "https://res.cloudinary.com/.../filename.wav",
          "public_id":  "tts_audio/filename",
          "bytes":      12345,
          "duration":   3.5,   # giây (nếu có)
        }

    Raises:
        RuntimeError: thiếu credentials hoặc upload thất bại
        requests.HTTPError: lỗi mạng
    """
    cloud, key, sec = _get_creds()

    if not all([cloud, key, sec]):
        raise RuntimeError(
            "Thiếu Cloudinary credentials. "
            "Thêm CLD_CLOUD_NAME, CLD_API_KEY, CLD_API_SECRET vào Streamlit Secrets hoặc .env"
        )

    # Tạo public_id từ tên file (bỏ extension)
    public_id = f"tts_audio/{filename.rsplit('.', 1)[0]}"

    # Tạo signature
    timestamp = int(time.time())
    sig_params = f"public_id={public_id}&timestamp={timestamp}{sec}"
    signature  = hashlib.sha1(sig_params.encode("utf-8")).hexdigest()

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud}/raw/upload"

    resp = requests.post(
        upload_url,
        data={
            "api_key":   key,
            "timestamp": timestamp,
            "signature": signature,
            "public_id": public_id,
            "resource_type": "raw",
        },
        files={
            "file": (filename, io.BytesIO(audio_bytes), "application/octet-stream"),
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Cloudinary error: {data['error'].get('message', data)}")

    return {
        "url":       data.get("secure_url", data.get("url", "")),
        "public_id": data.get("public_id", ""),
        "bytes":     data.get("bytes", 0),
        "duration":  data.get("duration"),
    }
