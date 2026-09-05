import streamlit as st
from api_config import (
    init_api_config, save_api_config, mask_api_key, normalize_api_base_url,
    test_api_connection, DEFAULT_LOCAL_EMBEDDING_MODEL,
)

st.set_page_config(page_title="通用设置", page_icon="⚙️", layout="centered")
st.title("⚙️ 通用设置")
st.caption("聊天 API 和 Embedding 配置在所有工具中共享")
st.markdown("---")

init_api_config()

# 不使用 form：切换 Embedding 方式时，相关字段可以立即显示/隐藏。
st.subheader("API 配置")
new_base_url = st.text_input("API 地址", value=st.session_state.openai_base_url,
                             placeholder="请输入服务商提供的 base URL")
new_model = st.text_input("聊天模型", value=st.session_state.openai_model,
                          placeholder="请输入聊天模型名称")
new_api_key = st.text_input(
    "API Key", type="password",
    placeholder=("已保存：" + mask_api_key(st.session_state.openai_api_key)
                 if st.session_state.openai_api_key else "请输入 API Key"),
    help="输入框不会回填已保存的真实 Key；留空表示继续使用原 Key。",
)

modes = ["不使用", "使用 Embedding API", "使用本地开源模型"]
current_mode = "使用 Embedding API" if st.session_state.embedding_api_enabled else (
    "使用本地开源模型" if st.session_state.local_embedding_enabled else "不使用"
)
embedding_mode = st.radio("是否使用智能文件问答", modes,
                          index=modes.index(current_mode), horizontal=True)

new_embedding_base_url = st.session_state.embedding_base_url
new_embedding_model = st.session_state.openai_embedding_model
new_embedding_key = ""
local_embedding_model = st.session_state.local_embedding_model or DEFAULT_LOCAL_EMBEDDING_MODEL

if embedding_mode == "使用 Embedding API":
    new_embedding_base_url = st.text_input(
        "嵌入 API 地址",
        value=st.session_state.embedding_base_url or st.session_state.openai_base_url,
        placeholder="默认继承上面的 API 地址",
    )
    new_embedding_model = st.text_input(
        "嵌入模型", value=st.session_state.openai_embedding_model,
        placeholder="请输入服务商提供的嵌入模型名称",
    )
    new_embedding_key = st.text_input(
        "嵌入 API Key", type="password",
        placeholder=("留空则继承聊天 API Key；已单独设置：" + mask_api_key(st.session_state.embedding_api_key)
                     if st.session_state.embedding_api_key else "留空则继承聊天 API Key"),
    )
elif embedding_mode == "使用本地开源模型":
    local_embedding_model = st.text_input(
        "本地模型名称", value=local_embedding_model,
        help="首次使用前请安装依赖，首次处理文件时会自动下载模型。",
    )

if st.button("保存配置", type="primary", use_container_width=True):
    if new_api_key.strip():
        st.session_state.openai_api_key = new_api_key.strip()
    st.session_state.openai_base_url = normalize_api_base_url(new_base_url)
    st.session_state.openai_model = new_model.strip()
    st.session_state.embedding_api_enabled = embedding_mode == "使用 Embedding API"
    st.session_state.local_embedding_enabled = embedding_mode == "使用本地开源模型"
    st.session_state.file_qa_enabled = embedding_mode != "不使用"
    st.session_state.embedding_base_url = (
        normalize_api_base_url(new_embedding_base_url) if embedding_mode == "使用 Embedding API" else ""
    )
    st.session_state.openai_embedding_model = new_embedding_model.strip()
    if new_embedding_key.strip():
        st.session_state.embedding_api_key = new_embedding_key.strip()
    st.session_state.local_embedding_model = local_embedding_model.strip()
    save_api_config({
        "openai_api_key": st.session_state.openai_api_key,
        "openai_base_url": st.session_state.openai_base_url,
        "openai_model": st.session_state.openai_model,
        "openai_embedding_model": st.session_state.openai_embedding_model,
        "embedding_api_key": st.session_state.embedding_api_key,
        "embedding_base_url": st.session_state.embedding_base_url,
        "file_qa_enabled": st.session_state.file_qa_enabled,
        "embedding_api_enabled": st.session_state.embedding_api_enabled,
        "local_embedding_enabled": st.session_state.local_embedding_enabled,
        "local_embedding_model": st.session_state.local_embedding_model,
    })
    st.success("配置已保存！")
    st.rerun()

if st.button("测试聊天配置", use_container_width=True):
    if not st.session_state.openai_api_key:
        st.error("请先填写 API Key 并保存配置。")
    elif not st.session_state.openai_base_url:
        st.error("请先填写 API 地址并保存配置。")
    elif not st.session_state.openai_model:
        st.error("请先填写聊天模型名称并保存配置。")
    else:
        try:
            with st.spinner("正在测试接口..."):
                response = test_api_connection()
            st.success(f"聊天配置可用，接口返回：{response[:120] or '(空响应)'}")
        except Exception as error:
            st.error("接口测试失败。请检查 API 地址、Key 和模型名称。")
            st.code(str(error), language=None)

st.markdown("---")
st.subheader("当前状态")
if st.session_state.openai_api_key:
    st.success(
        f"API Key 已设置: `{mask_api_key(st.session_state.openai_api_key)}`\n\n"
        f"API 地址: `{st.session_state.openai_base_url}`\n\n"
        f"聊天模型: `{st.session_state.openai_model}`\n\n"
        f"Embedding 使用方式: `{embedding_mode}`"
    )
else:
    st.warning("API Key 尚未设置。请填写并保存配置。")
