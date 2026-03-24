"""
cloudinary_upload.py — Upload audio lên Cloudinary qua REST API
Credentials lưu trong Streamlit Secrets hoặc .env

Cần có trong Secrets / .env:
    CLD_CLOUD_NAME = "your_cloud_name"
    CLD_API_KEY    = "your_api_key"
    CLD_API_SECRET = "your_api_secret"

Lấy tại: https://cloudinary.com/console → Settings → API Keys
"""

import hashlib
import io
import os
import time

import requests


# ─── Credentials ──────────────────────────────────────────────────────────────

def _get_creds() -> tuple[str, str, str]:
    """Đọc credentials từ Streamlit Secrets hoặc biến môi trường."""
    try:
        import streamlit as st
        cloud = st.secrets.get("CLD_CLOUD_NAME", "")
        key   = st.secrets.get("CLD_API_KEY",    "")
        sec   = st.secrets.get("CLD_API_SECRET", "")
        # Fallback sang env nếu secrets trống
        if not cloud: cloud = os.environ.get("CLD_CLOUD_NAME", "")
        if not key:   key   = os.environ.get("CLD_API_KEY",    "")
        if not sec:   sec   = os.environ.get("CLD_API_SECRET", "")
    except Exception:
        cloud = os.environ.get("CLD_CLOUD_NAME", "")
        key   = os.environ.get("CLD_API_KEY",    "")
        sec   = os.environ.get("CLD_API_SECRET", "")
    return cloud.strip(), key.strip(), sec.strip()


def has_cloudinary_config() -> bool:
    """Kiểm tra đã cấu hình đủ credentials chưa."""
    cloud, key, sec = _get_creds()
    return bool(cloud and key and sec)


# ─── Signature ────────────────────────────────────────────────────────────────

def _make_signature(params: dict, api_secret: str) -> str:
    """
    Tạo SHA-1 signature đúng chuẩn Cloudinary:
    - Sắp xếp params theo alphabet
    - Nối key=value&key=value
    - Append api_secret (không có dấu &)
    - SHA-1 hex
    """
    # Loại bỏ các key không được ký
    excluded = {"api_key", "cloud_name", "resource_type", "file"}
    sorted_params = sorted(
        (k, v) for k, v in params.items()
        if k not in excluded and v is not None and v != ""
    )
    param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
    to_sign   = param_str + api_secret
    return hashlib.sha1(to_sign.encode("utf-8")).hexdigest()


# ─── Upload ───────────────────────────────────────────────────────────────────

def upload_audio_to_cloudinary(audio_bytes: bytes, filename: str) -> dict:
    """
    Upload audio bytes lên Cloudinary dưới dạng raw file.

    Returns:
        {
          "url":       "https://res.cloudinary.com/.../tts_audio/xxx.wav",
          "public_id": "tts_audio/xxx",
          "bytes":     12345,
          "format":    "wav",
        }

    Raises:
        RuntimeError: thiếu credentials hoặc Cloudinary trả lỗi
        requests.HTTPError: lỗi HTTP
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

    # public_id: lưu vào folder tts_audio, bỏ extension
    base_name = filename.rsplit(".", 1)[0]          # vd: tts_Dennis_1234567890
    public_id = f"tts_audio/{base_name}"

    timestamp = int(time.time())

    # Các params sẽ được ký (theo đúng thứ tự chuẩn Cloudinary)
    sign_params = {
        "public_id":  public_id,
        "timestamp":  timestamp,
        "use_filename": "false",
        "unique_filename": "false",
    }

    signature = _make_signature(sign_params, sec)

    # Upload lên endpoint /raw/upload (dành cho file không phải ảnh/video)
    upload_url = f"https://api.cloudinary.com/v1_1/{cloud}/raw/upload"

    resp = requests.post(
        upload_url,
        data={
            "api_key":         key,
            "timestamp":       timestamp,
            "signature":       signature,
            "public_id":       public_id,
            "use_filename":    "false",
            "unique_filename": "false",
        },
        files={
            "file": (filename, io.BytesIO(audio_bytes), "application/octet-stream"),
        },
        timeout=60,
    )

    # Log response để debug nếu cần
    try:
        resp_json = resp.json()
    except Exception:
        resp.raise_for_status()
        raise RuntimeError(f"Cloudinary trả về response không hợp lệ: {resp.text[:300]}")

    if "error" in resp_json:
        msg = resp_json["error"].get("message", str(resp_json["error"]))
        raise RuntimeError(f"Cloudinary lỗi: {msg}")

    resp.raise_for_status()

    return {
        "url":       resp_json.get("secure_url") or resp_json.get("url", ""),
        "public_id": resp_json.get("public_id", ""),
        "bytes":     resp_json.get("bytes", 0),
        "format":    resp_json.get("format", ""),
    }
