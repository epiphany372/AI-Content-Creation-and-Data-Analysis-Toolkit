import streamlit as st
import os
from api_config import init_api_config

init_api_config()

# --- 页面配置 ---
st.set_page_config(
    page_title="AI工具集 | GPT战损版",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 加载自定义CSS ---
def load_css(file_name):
    # 获取当前脚本文件所在的目录的绝对路径
    _this_file_path = os.path.dirname(os.path.abspath(__file__))
    # 构建 style.css 文件的绝对路径
    css_file_path = os.path.join(_this_file_path, file_name)

    try:
        with open(css_file_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS文件未找到。预期路径: {css_file_path}")


load_css("style.css")

# --- 侧边栏 ---
with st.sidebar:
    st.title("导航")
    st.info("👈 请从上方选择一个工具，或进入“设置”页面配置 API Key、API 地址和模型。")

# --- 主页面内容 ---
st.title("🚀 AI内容创作与分析工具集")
st.caption("选择一个工具开始你的创作之旅吧！")
# --- 新增：检查API Key状态，并引导用户 ---
if not st.session_state.get('openai_api_key'):
    st.warning("⚠️ **你还没有设置 API Key！**")
    st.info("请先点击左侧导航栏的 **`setting`** 页面，输入你的API Key，否则所有工具都无法使用。")
st.markdown("---")

def tool_card(emoji, title, description, page_link):
    with st.container(border=True):
        st.markdown(f"### {emoji} {title}")
        st.write(description)
        st.page_link(f"pages/{page_link}", label="启动工具 →", use_container_width=True)


tools = [
    {"emoji": "🎬", "title": "视频脚本生成器",
     "description": "输入主题、风格和素材链接，AI即可生成包含标题、脚本和BGM推荐的完整视频方案。",
     "page_link": "1_视频脚本生成器.py"},
    {"emoji": "📕", "title": "多平台内容助手",
     "description": "为小红书、抖音、微博等平台创作爆款文案，并提供内容类型和图片拍摄建议。",
     "page_link": "2_多平台内容助手.py"},
    {"emoji": "💬", "title": "克隆GPT",
     "description": "一个具备长期记忆的通用聊天机器人，可以进行连续对话，体验类似ChatGPT。",
     "page_link": "3_克隆GPT.py"},
    {"emoji": "❓", "title": "智能文件问答",
     "description": "上传PDF、Word或TXT文档，AI会为你生成内容摘要，并回答你关于文档的任何问题。",
     "page_link": "4_智能文件问答.py"},
    {"emoji": "💡", "title": "CSV数据分析工具",
     "description": "上传CSV文件，通过与AI对话进行数据探索、分析和可视化，无需编写任何代码。",
     "page_link": "5_CSV数据分析工具.py"}
]

cols_per_row = 3
cols = st.columns(cols_per_row)
for i, tool in enumerate(tools):
    with cols[i % cols_per_row]:
        tool_card(tool["emoji"], tool["title"], tool["description"], tool["page_link"])
