"""统一管理兼容接口配置。"""
import os
import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings

# 不预设供应商、地址或模型，由用户按服务商文档填写。
DEFAULT_API_BASE_URL = ""
DEFAULT_CHAT_MODEL = ""
DEFAULT_EMBEDDING_MODEL = ""
DEFAULT_LOCAL_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
CONFIG_FILE = Path(__file__).with_name(".api_config.json")


def normalize_api_base_url(url: str) -> str:
    """接受 base URL 或完整聊天接口 URL，统一成客户端需要的 base URL。"""
    normalized = (url or DEFAULT_API_BASE_URL).strip().rstrip("/")
    suffix = "/chat/completions"
    if normalized.lower().endswith(suffix):
        normalized = normalized[:-len(suffix)].rstrip("/")
    return normalized


def _load_saved_config() -> dict[str, str]:
    try:
        if CONFIG_FILE.exists():
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        # 配置文件损坏时回退到环境变量/默认值，避免应用无法启动。
        pass
    return {}


def save_api_config(config: dict[str, str]) -> None:
    """将配置保存到本地文件；该文件应被版本控制忽略。"""
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)


def mask_api_key(api_key: str) -> str:
    """只用于界面展示：前 4 位 + **** + 后 4 位。"""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}****{api_key[-4:]}"


def test_api_connection() -> str:
    """用最小原始 HTTP 请求测试聊天接口，避免兼容层拦截 SDK 附加参数。"""
    config = get_api_config()
    if not config["api_key"]:
        raise ValueError("API Key 未填写")
    if not config["base_url"]:
        raise ValueError("API 地址未填写")
    if not config["model"]:
        raise ValueError("聊天模型未填写")

    data = json.dumps({
        "model": config["model"],
        "messages": [{"role": "user", "content": "Say PONG"}],
        "temperature": 0,
        "max_tokens": 16,
        "stream": False,
    }, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        config["base_url"] + "/chat/completions", data=data, method="POST",
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Length": str(len(data)),
            "User-Agent": "curl/8.10.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60, context=ssl.create_default_context()) as response:
            body = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        try:
            result = json.loads(body)
            detail = (result.get("error") or {}).get("message") or result.get("message") or body
        except (json.JSONDecodeError, AttributeError):
            detail = body
        raise RuntimeError(f"HTTP {error.code}: {detail}") from None
    except urllib.error.URLError as error:
        raise RuntimeError(f"网络错误: {error.reason}") from None

    try:
        result = json.loads(body)
        content = ((result.get("choices") or [])[0].get("message") or {}).get("content", "")
    except (json.JSONDecodeError, IndexError, AttributeError, TypeError):
        raise RuntimeError(f"接口返回格式异常: {body[:400]}") from None
    return content.strip()


def init_api_config() -> None:
    """从本地 JSON 初始化会话配置，环境变量只作为后备默认值。"""
    saved = _load_saved_config()
    defaults = {
        "openai_api_key": saved.get("openai_api_key", os.getenv("OPENAI_API_KEY", "")),
        "openai_base_url": saved.get("openai_base_url", os.getenv("OPENAI_BASE_URL", DEFAULT_API_BASE_URL)),
        "openai_model": saved.get("openai_model", os.getenv("OPENAI_MODEL", DEFAULT_CHAT_MODEL)),
        "openai_embedding_model": saved.get("openai_embedding_model", os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)),
        "embedding_base_url": saved.get("embedding_base_url", ""),
        "embedding_api_key": saved.get("embedding_api_key", ""),
        "file_qa_enabled": saved.get("file_qa_enabled", False),
        "embedding_api_enabled": saved.get("embedding_api_enabled", False),
        "local_embedding_enabled": saved.get("local_embedding_enabled", False),
        "local_embedding_model": saved.get("local_embedding_model", DEFAULT_LOCAL_EMBEDDING_MODEL),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_api_config() -> dict[str, str]:
    init_api_config()
    return {
        "api_key": st.session_state.get("openai_api_key", "").strip(),
        "base_url": normalize_api_base_url(st.session_state.get("openai_base_url", DEFAULT_API_BASE_URL)),
        "model": st.session_state.get("openai_model", DEFAULT_CHAT_MODEL).strip(),
        "embedding_model": st.session_state.get("openai_embedding_model", DEFAULT_EMBEDDING_MODEL).strip(),
        "embedding_api_key": st.session_state.get("embedding_api_key", "").strip() or st.session_state.get("openai_api_key", "").strip(),
        "embedding_base_url": normalize_api_base_url(st.session_state.get("embedding_base_url", "")) or normalize_api_base_url(st.session_state.get("openai_base_url", DEFAULT_API_BASE_URL)),
        "file_qa_enabled": bool(st.session_state.get("embedding_api_enabled", False)
                                 or st.session_state.get("local_embedding_enabled", False)),
        "embedding_api_enabled": st.session_state.get("embedding_api_enabled", False),
        "local_embedding_enabled": st.session_state.get("local_embedding_enabled", False),
        "local_embedding_model": st.session_state.get("local_embedding_model", DEFAULT_LOCAL_EMBEDDING_MODEL).strip(),
    }


def create_chat_model(*, api_key: Optional[str] = None, base_url: Optional[str] = None,
                      model: Optional[str] = None, **kwargs: Any) -> ChatOpenAI:
    config = get_api_config()
    # 部分兼容接口会拦截 SDK 默认的 Python User-Agent；与可用的原始 HTTP 请求保持一致。
    kwargs.setdefault("default_headers", {
        "User-Agent": "curl/8.10.1",
        "Accept": "application/json",
    })
    return ChatOpenAI(
        model=model or config["model"],
        base_url=base_url or config["base_url"] or None,
        openai_api_key=api_key or config["api_key"],
        **kwargs,
    )


def create_embedding_model(*, api_key: Optional[str] = None, base_url: Optional[str] = None,
                           model: Optional[str] = None, **kwargs: Any) -> OpenAIEmbeddings:
    config = get_api_config()
    return OpenAIEmbeddings(
        model=model or config["embedding_model"],
        base_url=base_url or config["base_url"] or None,
        openai_api_key=api_key or config["api_key"],
        **kwargs,
    )


def create_local_embedding_model(model_name: Optional[str] = None):
    """创建本地 Hugging Face Embedding；模型会自动下载并缓存。"""
    config = get_api_config()
    model_name = model_name or config["local_embedding_model"] or DEFAULT_LOCAL_EMBEDDING_MODEL
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError as error:
            raise RuntimeError(
                "本地 Embedding 依赖未安装，请执行：pip install -U sentence-transformers langchain-huggingface"
            ) from error
    try:
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    except ImportError as error:
        raise RuntimeError(
            "本地模型依赖未安装。请使用运行 Streamlit 的 Python 环境执行："
            "python -m pip install -U sentence-transformers langchain-huggingface"
        ) from error
