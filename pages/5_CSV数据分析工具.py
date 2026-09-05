import pandas as pd
import streamlit as st
import os
from utils_csv import dataframe_agent, get_recommended_questions

def create_chart(input_data, chart_type):
    """
        创建数据可视化图表
        （此函数保持你的原始代码，不做任何改动）
        """
    # 将输入数据转换为Pandas DataFrame
    df_data = pd.DataFrame(input_data["data"], columns=input_data["columns"])
    df_data.set_index(input_data["columns"][0], inplace=True)  # 设置索引列

    # 根据图表类型创建相应的可视化
    if chart_type == "bar":
        st.bar_chart(df_data)  # 创建条形图
    elif chart_type == "line":
        st.line_chart(df_data)  # 创建折线图
    elif chart_type == "scatter":
        st.scatter_chart(df_data)  # 创建散点图

def render_response(response_dict):
    """
        根据AI返回的字典内容，渲染文本、表格或图表。
        （此函数保持你的原始代码，不做任何改动）
        """
    if "answer" in response_dict:
        st.markdown(response_dict["answer"])
    if "table" in response_dict:
        st.table(pd.DataFrame(response_dict["table"]["data"], columns=response_dict["table"]["columns"]))
    if "bar" in response_dict:
        create_chart(response_dict["bar"], "bar")
    if "line" in response_dict:
        create_chart(response_dict["line"], "line")
    if "scatter" in response_dict:
        create_chart(response_dict["scatter"], "scatter")
    # 增加一个对错误信息的显示（如果你希望在历史记录中看到错误）
    if "error" in response_dict:
        st.error(f"处理失败: {response_dict['error']}")

# --- 主渲染函数 ---
def render():
    st.title("💡 CSV数据分析智能工具")
    st.caption("上传CSV，与AI对话，轻松完成数据分析与可视化")

    # --- 从主会方状态获取API Key ---
    openai_api_key = st.session_state.get('openai_api_key', '')

    # --- 初始化 Session State 变量 ---
    # 用于管理对话历史记录
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    # 用于管理AI是否正在生成回答的状态，配合暂停功能
    if 'generating' not in st.session_state:
        st.session_state.generating = False
    # 用于推荐问题列表，清空时重置
    if 'current_recommended_questions' not in st.session_state:
        st.session_state.current_recommended_questions = []
    # 用于保存用户选择的推荐问题，以便st.radio保持选中状态
    if 'user_selected_query' not in st.session_state:
        st.session_state.user_selected_query = ""
    # 用于保存用户在text_area中手动输入的或推荐问题填充的文本
    if 'current_text_area_value' not in st.session_state:  # 注意：这里沿用上次的命名以保持一致性
        st.session_state.current_text_area_value = ""

    # 创建文件上传组件
    data = st.file_uploader("上传你的数据文件（CSV格式）：", type="csv")
    if data:
        # 判断是否是新文件上传或文件内容有变化，避免重复加载相同文件
        # 使用data.name作为key来避免重复加载相同文件
        if 'df' not in st.session_state or st.session_state.get('file_name') != data.name:
            st.session_state["df"] = pd.read_csv(data)
            st.session_state["file_name"] = data.name
            st.success(f"文件 '{data.name}' 已成功上传！")

            # --- 在新文件上传时，清空相关状态和历史记录 ---
            st.session_state.messages = []  # 清空历史记录
            st.session_state.generating = False  # 停止任何可能的生成状态

            # 识别文件类型并获取推荐问题
            file_extension = os.path.splitext(data.name)[1].lower().lstrip('.')
            st.session_state["current_recommended_questions"] = get_recommended_questions(file_extension)
            # 当文件上传时，清除上次可能选择的推荐问题和用户输入的文本
            st.session_state["user_selected_query"] = ""  # 清空上次选择的推荐问题
            st.session_state["current_text_area_value"] = ""  # 清空用户输入框的当前值

    # 只有在上传了 DataFrame 后才显示后续内容
    if 'df' in st.session_state:
        with st.expander("原始数据预览"):
            st.dataframe(st.session_state["df"])

        # 预设问题库功能区域
        if st.session_state["current_recommended_questions"]:
            st.markdown("---")  # 分隔线
            st.subheader("💡 推荐问题")

            try:
                current_selected_index = st.session_state["current_recommended_questions"].index(
                    st.session_state["user_selected_query"])
            except ValueError:
                current_selected_index = None

            selected_recommended_q = st.radio(
                "请选择一个推荐问题作为你的初始查询，或在下方输入框中直接输入你的问题：",
                options=st.session_state["current_recommended_questions"],
                index=current_selected_index,
                key="recommended_question_radio_unique_key"
            )

            if selected_recommended_q and selected_recommended_q != st.session_state["current_text_area_value"]:
                st.session_state["user_selected_query"] = selected_recommended_q
                st.session_state["current_text_area_value"] = selected_recommended_q  # 将选择的问题填充到用户输入框

        # 创建查询输入区域
        query = st.text_area(
            "请输入你关于以上表格的问题，或数据提取请求，或可视化要求：",
            value=st.session_state.current_text_area_value,  # 使用session_state中的值
            key="main_query_text_area_unique_key"
        )
        # 每次text_area内容变化时，更新session_state中的用户输入文本
        st.session_state.current_text_area_value = query

        # --- 控制按钮区域（生成、停止、清空） ---
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("生成回答", type="primary", use_container_width=True, disabled=st.session_state.generating):
                if not openai_api_key:
                    st.error("请输入你的 API Key")
                elif not query.strip():
                    st.info("请输入你的问题或选择一个推荐问题。")
                else:
                    st.session_state.generating = True
                    st.session_state.messages.append({'role': 'user', 'content': query})
                    st.rerun()

        with col2:
            if st.button("停止生成", use_container_width=True, disabled=not st.session_state.generating):
                st.session_state.generating = False
                st.warning("已停止生成。")
                st.rerun()

        with col3:
            if st.button("清空历史", use_container_width=True):
                st.session_state.messages = []
                st.session_state.generating = False
                # 同时清空推荐问题选择和输入框内容
                st.session_state.selected_recommended_q_text = ""
                st.session_state.current_text_area_value = ""
                st.rerun()

    # --- 核心 AI 调用逻辑 ---
    if st.session_state.get('generating', False):
        user_query = st.session_state.messages[-1]['content']

        with st.spinner("AI正在思考中，请稍等... (可点击停止)"):
            try:
                response_dict = dataframe_agent(
                    openai_api_key,
                    st.session_state.df,
                    user_query
                )

                if st.session_state.generating:
                    st.session_state.messages.append({'role': 'assistant', 'content': response_dict})

            except Exception as e:
                st.error(f"分析失败：{e}")
                st.session_state.messages.append(
                    {'role': 'assistant', 'content': {"error": str(e), "original_query": user_query}})

        st.session_state.generating = False
        # 生成结束后立即重新渲染，恢复“生成回答”按钮，用户可以连续提问。
        st.rerun()

    # --- 历史记录显示逻辑 ---
    if st.session_state.messages:
        st.divider()
        st.subheader("对话历史")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "user":
                    st.markdown(msg["content"])
                elif msg["role"] == "assistant":
                    response_content = msg["content"]
                    if isinstance(response_content, dict):
                        render_response(response_content)
                    else:
                        st.markdown(str(response_content))

render()
