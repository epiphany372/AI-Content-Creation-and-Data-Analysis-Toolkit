import streamlit as st
from langchain.memory import ConversationBufferMemory
from utils_pdf import qa_agent, process_document_and_summarize
from api_config import get_api_config
import os
import tempfile
import hashlib

def render():
    st.title('❓ 智能PDF/文档问答')
    st.caption("上传文档，AI为你总结并回答任何问题")

    # --- 从主会话状态获取API Key ---
    openai_api_key = st.session_state.get('openai_api_key', '')
    api_config = get_api_config()

    if not api_config["file_qa_enabled"]:
        st.info("文件问答功能当前已关闭。请前往“设置”页面勾选启用，并填写服务商提供的嵌入模型配置。")
        st.stop()
    if api_config["embedding_api_enabled"] and not api_config["embedding_model"]:
        st.error("已启用 Embedding API，但未填写嵌入模型名称，请先到“设置”页面补充配置。")
        st.stop()

    if 'memory' not in st.session_state:
        st.session_state['memory'] = ConversationBufferMemory(
            return_messages=True,
            memory_key='chat_history',
            output_key='answer'
        )

        # 存储文档内容和摘要
    if 'processed_texts' not in st.session_state:
        st.session_state['processed_texts'] = None
    if 'document_summary' not in st.session_state:
        st.session_state['document_summary'] = None
    if 'current_file_hash' not in st.session_state:  # 当前文件哈希
        st.session_state['current_file_hash'] = None
    if 'processed_file_records' not in st.session_state:
        st.session_state['processed_file_records'] = {}

    uploaded_file = st.file_uploader('请上传你的PDF/Word/TXT文件：', type=['pdf', 'docx', 'txt'])

    # 检测文件是否更换
    if uploaded_file:
        file_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
        uploaded_file.seek(0)  # 重置文件指针
        if file_hash != st.session_state['current_file_hash']:
            st.session_state['current_file_hash'] = file_hash
            record = st.session_state['processed_file_records'].get(file_hash)
            if record:
                st.session_state['processed_texts'] = record['texts']
                st.session_state['document_summary'] = record['summary']
                st.info("检测到之前处理过的文件，已直接恢复处理结果。")
            else:
                st.session_state['processed_texts'] = None
                st.session_state['document_summary'] = None
                st.session_state['memory'] = ConversationBufferMemory(
                    return_messages=True,
                    memory_key='chat_history',
                    output_key='answer'
                )
                st.info("检测到新文件，已重置内容和历史记录。")

    # 文档处理和摘要生成
    col_file_ops, col_qa_ops = st.columns([1, 1])

    with col_file_ops:
        process_button = st.button('处理文件并生成摘要', disabled=not uploaded_file)
        if uploaded_file and not openai_api_key:
                    st.info('请输入聊天 API Key 以处理文件。')

        if process_button and uploaded_file and openai_api_key:
            with st.spinner('模型正在处理文件并生成摘要中，请稍等....（使用本地开源模型首次处理文件时会自动下载模型）'):
                try:
                    # 使用临时文件来处理上传的文件
                    with tempfile.NamedTemporaryFile(delete=False,
                                                     suffix=f".{uploaded_file.type.split('/')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_file_path = tmp_file.name

                    texts, summary = process_document_and_summarize(
                        openai_api_key,
                        temp_file_path,
                        uploaded_file.type  # 传递MIME类型以判断文件格式
                    )
                    st.session_state['processed_texts'] = texts
                    st.session_state['document_summary'] = summary
                    st.session_state['processed_file_records'][file_hash] = {
                        'texts': texts,
                        'summary': summary,
                        'file_name': uploaded_file.name,
                    }
                    st.success('文件处理完成，摘要已生成！')
                except Exception as e:
                    st.error(f"处理文件时发生错误: {e}")
                finally:
                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                        os.remove(temp_file_path)  # 清理临时文件

        if st.session_state['document_summary']:
            st.write('### 文档摘要')
            st.info(st.session_state['document_summary'])

    # 问答功能
    with col_qa_ops:
        question = st.text_input('对文档内容进行提问：', disabled=not st.session_state['processed_texts'])

        submit = st.button('开始询问', disabled=not st.session_state['processed_texts'])
        if st.session_state['processed_texts'] and question and not openai_api_key:
            st.info('请输入你的 API Key 以进行提问。')

        if submit and st.session_state['processed_texts'] and question and openai_api_key:
            with st.spinner('AI正在思考中，请稍等....'):
                try:
                    response = qa_agent(
                        openai_api_key,
                        st.session_state['memory'],
                        st.session_state['processed_texts'],  # 传递已处理的文本块
                        question
                    )
                    st.write('### 答案')
                    st.write(response['answer'])
                except Exception as error:
                    st.error(f"文件问答失败：{error}")

            # 更新会话中的对话历史
            st.session_state['chat_history'] = st.session_state['memory'].buffer_as_messages

        if 'chat_history' in st.session_state and st.session_state['chat_history']:
            with st.expander('历史消息'):
                # 过滤掉非HumanMessage和AIMessage类型，或者仅显示content
                for i in range(0, len(st.session_state['chat_history']), 2):
                    if i < len(st.session_state['chat_history']):
                        human_message = st.session_state['chat_history'][i]
                        st.write(f"**你:** {human_message.content}")
                    if i + 1 < len(st.session_state['chat_history']):
                        ai_message = st.session_state['chat_history'][i + 1]
                        st.write(f"**AI:** {ai_message.content}")
                    if i + 1 < len(st.session_state['chat_history']) - 1:
                        st.divider()  # 分隔不同对话框

if __name__ == '__main__':
    render()
