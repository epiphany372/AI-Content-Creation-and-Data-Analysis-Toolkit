# AI 内容创作与数据分析智能工具集

基于 Streamlit + LangChain 构建的多功能 AI 工具集，涵盖视频脚本生成、多平台内容创作、聊天对话、文档问答与 CSV 数据分析可视化，一站式满足内容创作与数据分析需求。

## 功能模块

| 模块 | 说明 |
|------|------|
| 🎬 视频脚本生成器 | 输入主题、风格、时长，AI 生成完整视频脚本（标题、分镜、BGM 推荐、关键词） |
| 📕 多平台内容助手 | 面向小红书/抖音/微博等平台生成爆款文案，提供内容类型建议和图片拍摄指导 |
| 💬 克隆 GPT | 具备长期记忆的通用聊天机器人，支持连续多轮对话 |
| ❓ 智能文件问答 | 上传 PDF/Word/TXT 文档，AI 自动生成摘要并回答相关问题 |
| 💡 CSV 数据分析工具 | 上传 CSV 文件，通过自然语言对话完成数据探索、统计分析与图表可视化 |

## 技术栈

- **前端框架**：Streamlit（多页面应用）
- **AI 框架**：LangChain（Agent、Memory、Tool Calling）
- **数据分析**：Pandas + LangChain Experimental（Pandas DataFrame Agent）
- **文档处理**：PDF/Word/TXT 解析 + 向量检索问答
- **Embedding**：支持 API Embedding 和本地 HuggingFace Embedding 双模式
- **模型接口**：兼容 OpenAI API 格式（支持各类第三方服务商）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run 首页.py
```

### 3. 配置 API

打开应用后，进入左侧导航栏的 **设置** 页面，填写：
- API Key
- API 地址（Base URL）
- 聊天模型名称
- （可选）Embedding 模型配置

配置保存后即可使用所有功能模块。

## 项目结构

```
AIweb/
├── 首页.py                      # 应用入口，工具集导航首页
├── style.css                    # 自定义样式
├── api_config.py                # API 配置管理（密钥、地址、模型）
├── prompt_template.py           # 提示词模板
├── requirements.txt             # 项目依赖
├── pages/                       # Streamlit 多页面
│   ├── 1_视频脚本生成器.py
│   ├── 2_多平台内容助手.py
│   ├── 3_克隆GPT.py
│   ├── 4_智能文件问答.py
│   ├── 5_CSV数据分析工具.py
│   └── 设置.py
├── utils_csv.py                # CSV 数据分析 Agent
├── utils_clonegpt.py           # 聊天机器人逻辑
├── utils_pdf.py                # 文档解析与问答
├── utils_video.py              # 视频脚本生成
├── utils_xiaohongshu.py        # 多平台内容生成
├── video_model.py              # 视频脚本数据模型
├── xiaohongshu_model.py        # 内容助手数据模型
└── 智能体基础/                  # Agent 基础示例
```

## 环境要求

- Python 3.10+
- 兼容 OpenAI API 格式的 LLM 服务（如 OpenAI、DeepSeek、Qwen 等）

## License

MIT
