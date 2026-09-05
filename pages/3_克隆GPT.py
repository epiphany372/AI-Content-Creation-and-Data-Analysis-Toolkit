import streamlit as st
from langchain.memory import ConversationBufferMemory
from utils_clonegpt import get_chat_response

def render():
    st.title('💬 克隆GPT')
    st.caption('一个可以和你连续对话的AI助手')

    # --- 从主会话状态获取API Key ---
    openai_api_key = st.session_state.get('openai_api_key', '')

    with st.sidebar:
        if st.button("清空对话历史", use_container_width=True):
            st.session_state['clonegpt_memory'] = ConversationBufferMemory(return_messages=True)
            st.session_state['clonegpt_messages'] = [
                {'role': 'ai', 'content': '你好，我是你的AI助手，历史已清空，有什么可以帮你的吗？'}]
            st.rerun()

    # --- 初始化本页面专用的 session_state ---
    if 'clonegpt_memory' not in st.session_state:
        st.session_state['clonegpt_memory'] = ConversationBufferMemory(return_messages=True)
        st.session_state['clonegpt_messages'] = [{'role': 'ai', 'content': '你好，我是你的AI助手，有什么可以帮你的吗？'}]

    # --- 显示历史对话消息 ---
    for message in st.session_state['clonegpt_messages']:
        with st.chat_message(message['role']):
            st.write(message['content'])

    # --- 用户输入 ---
    prompt = st.chat_input("请输入你的问题...")

    if prompt:
        if not openai_api_key:
            st.info('请在左侧通用设置中输入你的 API Key')
            st.stop()

        # 添加并显示用户消息
        st.session_state['clonegpt_messages'].append({'role': 'human', 'content': prompt})
        with st.chat_message('human'):
            st.write(prompt)

        # AI生成并显示回复
        with st.chat_message("ai"):
            with st.spinner('AI正在思考中...'):
                response = get_chat_response(prompt, st.session_state['clonegpt_memory'], openai_api_key)
                st.write(response)

        # 将AI回复添加到历史记录
        st.session_state['clonegpt_messages'].append({'role': 'ai', 'content': response})


# --- 运行页面 ---
render()
