import streamlit as st
import time
from utils_video import generate_script
from video_model import VideoScript

def render():
    st.title('🎬 视频脚本生成器')
    st.caption('AI帮你搞定标题、脚本、BGM和关键词！')

    # --- 从主会话状态获取API Key ---
    openai_api_key = st.session_state.get('openai_api_key', '')

    # --- 初始化本页面专用的 session_state ---
    if 'video_script_history' not in st.session_state:
        st.session_state['video_script_history'] = []
    if 'video_generating' not in st.session_state:
        st.session_state['video_generating'] = False
    if 'video_user_inputs' not in st.session_state:
        st.session_state['video_user_inputs'] = {}

    # --- 主界面输入组件 ---
    subject = st.text_input('💡 请输入视频的主题', key='video_subject_input')
    material_url = st.text_input('🔗 请输入参考素材链接（可选）', key='video_material_url_input')
    keywords_str = st.text_input('🔑 请输入核心关键词（可选，用逗号或空格分隔）', key='video_keywords_input')
    style_options = ['轻松有趣', '专业严谨', '幽默诙谐', '温馨感人', '悬疑震撼']
    style = st.selectbox('🎭 请选择视频风格', options=style_options, key='video_style_input')
    video_length = st.number_input('🕙 请输入视频的大致时长（单位：分钟）', min_value=0.1, step=0.1,
                                   key='video_length_input')
    creativity = st.slider('🌟 请输入视频脚本的创造力', min_value=0.0, max_value=1.0, value=0.2, step=0.1,
                           key='video_creativity_input')

    # --- 按钮布局和逻辑 ---
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button('生成脚本', use_container_width=True, type="primary"):
            if not openai_api_key:
                st.error('请在左侧通用设置中输入你的 API Key')
            elif not subject:
                st.info('请输入视频的主题')
            else:
                keywords = [k.strip() for k in keywords_str.replace(',', ' ').split() if k.strip()]
                st.session_state['video_user_inputs'] = {
                    'subject': subject, 'video_length': video_length, 'creativity': creativity,
                    'style': style, 'keywords': keywords, 'material_url': material_url
                }
                st.session_state['video_generating'] = True
                user_prompt = f"主题: {subject}, 风格: {style}, 时长: {video_length}分钟..."
                st.session_state.video_script_history.append({"role": "user", "content": user_prompt})
                st.rerun()
    with col2:
        if st.button('中止生成', use_container_width=True,
                     disabled=not st.session_state.get('video_generating', False)):
            st.session_state['video_generating'] = False;
            st.warning('生成已中止。');
            time.sleep(0.5);
            st.rerun()
    with col3:
        if st.button('清空历史', use_container_width=True):
            st.session_state['video_script_history'] = [];
            st.session_state['video_generating'] = False;
            st.rerun()

    # --- 核心处理逻辑 ---
    if st.session_state.get('video_generating', False):
        inputs = st.session_state['video_user_inputs']
        with st.spinner('AI正在分析素材并构思脚本，请稍等...'):
            try:
                result: VideoScript = generate_script(
                    inputs['subject'], inputs['video_length'], inputs['creativity'],
                    openai_api_key, inputs['style'], inputs['keywords'], inputs['material_url']
                )
                if st.session_state.get('video_generating', False):
                    st.success('视频脚本及BGM推荐已生成！')
                    st.session_state.video_script_history.append({"role": "assistant", "content": result})
            except Exception as e:
                st.error(f"生成失败: {e}")
                st.session_state.video_script_history.append({"role": "assistant", "content": {"error": str(e)}})
        st.session_state['video_generating'] = False
        st.rerun()

    # --- 历史记录显示 ---
    if st.session_state.video_script_history:
        st.divider()
        st.subheader('对话历史')
        for msg in st.session_state.video_script_history:
            with st.chat_message(msg["role"]):
                content = msg["content"]
                if isinstance(content, VideoScript):
                    st.markdown(f"#### 标题：\n> {content.title}")
                    st.text_area("##### 脚本:", content.script, height=300, key=f"script_{msg['content'].title[:10]}")
                    st.markdown("---")
                    st.markdown("#### BGM 推荐:")
                    for music in content.music_recommendations:
                        st.write(f"🎵 **{music.music_name}**")
                        st.caption(f"推荐理由: {music.reason}")
                else:
                    st.markdown(str(content))


# --- 运行页面 ---
render()
