import streamlit as st
import time
from utils_xiaohongshu import generate_social_media_post, generate_content_type_suggestions, generate_image_shooting_recommendations
from xiaohongshu_model import XiaohongshuPosts

def render():
    st.set_page_config(layout="wide") # 设置宽布局
    st.header('多平台爆款文案AI助手 ✨')

    # --- 从主会话状态获取API Key ---
    openai_api_key = st.session_state.get('openai_api_key', '')

    # --- 初始化 session_state ---
    if 'xiaohongshu_history' not in st.session_state:
        st.session_state['xiaohongshu_history'] = []
    if 'generating' not in st.session_state:
        st.session_state['generating'] = False
    if 'user_inputs' not in st.session_state:
        st.session_state['user_inputs'] = {}
    if 'latest_social_media_posts' not in st.session_state: # 更名为通用名称
        st.session_state['latest_social_media_posts'] = None

    # 内容类型建议相关状态
    if 'suggested_content_types' not in st.session_state:
        st.session_state['suggested_content_types'] = []
    if 'last_theme_for_suggestions' not in st.session_state:
        st.session_state['last_theme_for_suggestions'] = ""
    if 'generating_suggestions' not in st.session_state:
        st.session_state['generating_suggestions'] = False
    if 'current_theme_input' not in st.session_state:
        st.session_state['current_theme_input'] = ""

    # 图片拍摄推荐相关状态
    if 'image_recommendations_results' not in st.session_state:
        st.session_state['image_recommendations_results'] = []
    if 'generating_image_recommendations' not in st.session_state:
        st.session_state['generating_image_recommendations'] = False

    # --- 主界面输入组件 ---
    # 平台选择
    platform_options = ["小红书 (Xiaohongshu)", "抖音 (TikTok)", "微博 (Weibo)", "其他 (Other)"]
    selected_platform = st.selectbox('💻 选择目标平台', platform_options, index=0)

    theme_input_val = st.text_input(
        '💡 请输入文案主题',
        value=st.session_state['current_theme_input'],
        key='theme_input_box'
    )
    st.session_state['current_theme_input'] = theme_input_val

    # 检查主题是否改变，如果改变且非空，且API Key存在，则尝试生成新的内容类型建议
    if theme_input_val and theme_input_val != st.session_state['last_theme_for_suggestions'] and openai_api_key:
        st.session_state['generating_suggestions'] = True
        st.session_state['last_theme_for_suggestions'] = theme_input_val
        st.rerun()

    if st.session_state['generating_suggestions']:
        with st.spinner('AI正在为你生成内容类型建议...'):
            try:
                if openai_api_key:
                    st.session_state['suggested_content_types'] = generate_content_type_suggestions(
                        st.session_state['last_theme_for_suggestions'], openai_api_key
                    )
                else:
                    st.warning("请输入 API Key 以获取内容类型建议。")
                    st.session_state['suggested_content_types'] = []
            except Exception as e:
                st.error(f"生成内容类型建议失败：{e}")
                st.session_state['suggested_content_types'] = []
        st.session_state['generating_suggestions'] = False
        st.rerun()

    # 构建内容类型选项列表
    dynamic_content_type_options = []
    if st.session_state['suggested_content_types']:
        dynamic_content_type_options.extend(st.session_state['suggested_content_types'])
        dynamic_content_type_options.append("--- 常用类型 ---")

    common_content_type_options = [
        "产品测评 (Product Review)", "探店分享 (Shop/Location Exploration)",
        "美妆教程 (Makeup Tutorial)", "穿搭分享 (Outfit Share)",
        "生活日常 (Daily Life)", "旅游攻略 (Travel Guide)",
        "美食分享 (Food Share)", "学习打卡 (Study Check-in)",
        "职场经验 (Career Experience)", "情感分享 (Emotional Sharing)",
        "技能学习 (Skill Learning)", "书籍推荐 (Book Recommendation)",
        "影视推荐 (Movie/TV Recommendation)", "健康养生 (Health & Wellness)",
        "家居布置 (Home Decor)", "数码科技 (Digital Tech)",
        "节日祝福 (Holiday Greetings)", "活动宣传 (Event Promotion)",
        "抽奖福利 (Giveaway/Benefit)", "其他 (Other)"
    ]
    for opt in common_content_type_options:
        if opt not in dynamic_content_type_options and opt not in st.session_state['suggested_content_types']:
            dynamic_content_type_options.append(opt)

    if not dynamic_content_type_options:
        dynamic_content_type_options = ["请先输入主题并提供API Key"]

    content_type = st.selectbox(
        '📝 请选择内容类型',
        dynamic_content_type_options,
        index=0,
        help="根据您输入的主题，AI会为您推荐相关的内容类型"
    )

    num_posts_to_generate = st.number_input(
        '🔢 你希望生成多少篇文案？',
        min_value=1, max_value=3, value=1, step=1,
        help="你可以选择生成1到3篇不同的文案供你选择"
    )

    # --- 按钮布局和逻辑 ---
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button('开始创作', use_container_width=True, type="primary"):
            if not openai_api_key:
                st.error('请输入你的 API Key')
            elif not theme_input_val:
                st.info('请输入文案主题')
            else:
                st.session_state['user_inputs'] = {
                    'platform': selected_platform,
                    'theme': theme_input_val,
                    'content_type': content_type,
                    'num_posts_to_generate': num_posts_to_generate
                }
                st.session_state['generating'] = True
                st.session_state.xiaohongshu_history.append({"role": "user", "content": f"平台: {selected_platform}\n主题: {theme_input_val}\n内容类型: {content_type}\n生成数量: {num_posts_to_generate}篇"})
                st.rerun()

    with col2:
        if st.button('停止创作', use_container_width=True, disabled=not st.session_state['generating']):
            st.session_state['generating'] = False
            st.warning('创作已停止。')
            time.sleep(0.5)
            st.rerun()

    with col3:
        if st.button('清空历史', use_container_width=True):
            st.session_state['xiaohongshu_history'] = []
            st.session_state['generating'] = False
            st.session_state['latest_social_media_posts'] = None
            st.session_state['suggested_content_types'] = []
            st.session_state['last_theme_for_suggestions'] = ""
            st.session_state['current_theme_input'] = ""
            st.session_state['image_recommendations_results'] = []
            st.session_state['generating_image_recommendations'] = False
            st.rerun()

    with col4:
        if st.button('生成图片拍摄推荐', use_container_width=True, disabled=not (theme_input_val and content_type and openai_api_key)):
            if not openai_api_key:
                st.error('请输入你的 API Key')
            elif not theme_input_val or not content_type:
                st.info('请输入主题并选择内容类型以生成图片推荐')
            else:
                st.session_state['generating_image_recommendations'] = True
                st.rerun()

    # 图片拍摄推荐生成逻辑
    if st.session_state['generating_image_recommendations']:
        with st.spinner('AI正在为你生成图片拍摄推荐...'):
            try:
                if openai_api_key:
                    st.session_state['image_recommendations_results'] = generate_image_shooting_recommendations(
                        selected_platform, theme_input_val, content_type, openai_api_key
                    )
                    if st.session_state['image_recommendations_results']:
                        st.session_state.xiaohongshu_history.append({"role": "assistant", "content": f"**图片拍摄推荐（平台：{selected_platform}，主题：{theme_input_val}，类型：{content_type}）:**\n" + "\n".join([f"- {rec}" for rec in st.session_state['image_recommendations_results']])})
                    else:
                        st.warning("未能生成图片拍摄推荐，请尝试调整主题或内容类型。")
                else:
                    st.warning("请输入 API Key 以获取图片拍摄推荐。")
            except Exception as e:
                st.error(f"生成图片拍摄推荐失败：{e}")
                st.session_state['image_recommendations_results'] = []
        st.session_state['generating_image_recommendations'] = False # 修复了拼写错误
        st.rerun()

    # --- 核心处理逻辑：仅在 'generating' 状态为 True 时执行 ---
    if st.session_state['generating']:
        inputs = st.session_state['user_inputs']

        with st.spinner('AI正在努力创作中，请稍等... (可点击停止)'):
            try:
                result: XiaohongshuPosts = generate_social_media_post( # 调用通用函数
                    inputs['platform'],
                    inputs['theme'],
                    inputs['content_type'],
                    inputs['num_posts_to_generate'],
                    openai_api_key
                )

                if st.session_state['generating']:
                    st.success(f'{inputs["platform"]}文案已生成！')
                    st.session_state['latest_social_media_posts'] = result

                    ai_response_history = ""
                    for i, post in enumerate(result.posts):
                        ai_response_history += f"""
**=== 文案选项 {i+1} (平台: {inputs['platform']}) ===**

**标题{'s' if '小红书' in inputs['platform'] else ''}:**
"""
                        for j, title in enumerate(post.titles):
                            # 对于抖音/微博，只显示一个标题 (如果LLM返回多个，只取第一个)
                            if '抖音' in inputs['platform'] or '微博' in inputs['platform']:
                                if j == 0:
                                    ai_response_history += f"1. {title}\n"
                                break
                            else: # 小红书显示所有
                                ai_response_history += f"{j+1}. {title}\n"

                        ai_response_history += f"""
**正文内容:**
{post.content}

"""
                    st.session_state.xiaohongshu_history.append({"role": "assistant", "content": ai_response_history})
            except Exception as e:
                st.error(f"生成失败，请检查API Key或稍后再试。错误: {e}")
                st.session_state['latest_social_media_posts'] = None

        st.session_state['generating'] = False
        st.rerun()

    # --- 显示逻辑：显示最新生成的结果和完整的历史记录 ---
    # 1. 显示最新生成的小红书文案结果
    if st.session_state['latest_social_media_posts']:
        st.divider()
        st.subheader("✨ 最新生成结果")

        posts_to_display = st.session_state['latest_social_media_posts'].posts
        tab_titles = [f"文案 {i+1}" for i in range(len(posts_to_display))]
        tabs = st.tabs(tab_titles)

        current_platform_for_display = st.session_state['user_inputs'].get('platform', '小红书 (Xiaohongshu)')


        for i, post in enumerate(posts_to_display):
            with tabs[i]:
                left_column, right_column = st.columns(2)
                with left_column:
                    title_header = "##### 备选标题"
                    if "抖音" in current_platform_for_display:
                        title_header = "##### 视频Hook/标题"
                    elif "微博" in current_platform_for_display:
                        title_header = "##### 微博标题"
                    st.markdown(title_header)

                    st.info("点击即可复制")
                    for j, title in enumerate(post.titles):
                        if '抖音' in current_platform_for_display or '微博' in current_platform_for_display:
                            if j == 0:
                                if st.button(title, use_container_width=True, key=f"title_btn_tab{i}_item{j}"):
                                    st.toast(f'已复制: "{title}"')
                                    st.code(title, language=None)
                            break
                        else:
                            if st.button(title, use_container_width=True, key=f"title_btn_tab{i}_item{j}"):
                                st.toast(f'已复制: "{title}"')
                                st.code(title, language=None)

                with right_column:
                    content_header = "##### 正文内容"
                    if "抖音" in current_platform_for_display:
                        content_header = "##### 视频描述/旁白"
                    elif "微博" in current_platform_for_display:
                        content_header = "##### 微博正文"
                    st.markdown(content_header)

                    st.text_area(" ", value=post.content.strip(), height=400,
                                 help="你可以直接在这里编辑和复制内容", key=f"content_area_tab{i}")

    # 2. 显示最新生成的图片拍摄推荐
    if st.session_state['image_recommendations_results']:
        st.divider()
        st.subheader("📸 图片/视觉内容推荐")
        for i, rec in enumerate(st.session_state['image_recommendations_results']):
            st.info(f"- {rec}")
        st.caption("这些建议是根据您提供的主题和内容类型生成的。")


    # 3. 显示完整的历史记录
    if st.session_state['xiaohongshu_history']:
        st.divider()
        st.subheader('对话历史')
        for msg in reversed(st.session_state['xiaohongshu_history']):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])


if __name__ == '__main__':
    render()
