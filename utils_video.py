import requests
from bs4 import BeautifulSoup
from langchain.prompts import ChatPromptTemplate
from api_config import create_chat_model
from langchain.output_parsers import PydanticOutputParser
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from video_model import VideoScript
from typing import List, Optional

def scrape_website_text(url: str) -> Optional[str]:
    """
    访问给定的URL，抓取并返回页面上的主要文本内容。
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        # 确保请求成功
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # 移除脚本和样式元素
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        # 获取文本并进行清理
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return None

def generate_script(subject: str, video_length: float, creativity: float, api_key: str, style: str,
                    keywords: Optional[List[str]] = None, material_url: Optional[str] = None,
                    api_base_url=None, model_name=None):
    parser = PydanticOutputParser(pydantic_object=VideoScript)

    # --- 内容提取与摘要 ---
    material_summary = ""
    if material_url:
        print(f"Scraping content from: {material_url}")
        scraped_text = scrape_website_text(material_url)
        if scraped_text:
            print("Content scraped successfully. Summarizing...")
            # 创建一个临时的、用于摘要的LLM实例
            summarizer_llm = create_chat_model(api_key=api_key, base_url=api_base_url,
                                               model=model_name, temperature=0)
            # 将抓取的文本包装成LangChain的Document对象
            docs = [Document(page_content=scraped_text)]
            # 创建并运行摘要链
            chain = load_summarize_chain(summarizer_llm, chain_type="refine")
            material_summary = chain.run(docs)
            print("Summarization complete.")
        else:
            print("Failed to scrape content.")

    # --- 动态构建 Prompt ---
    keyword_instruction = ""
    if keywords:
        keyword_str = ", ".join(keywords)
        keyword_instruction = f"-   **核心关键词**: 你的创作必须紧密围绕这些关键词：**{keyword_str}**"

    # <<< 如果摘要存在，则创建参考素材的指令 >>>
    reference_material_instruction = ""
    if material_summary:
        reference_material_instruction = f"""-   **重要参考素材**: 你的脚本内容必须深度参考以下核心信息。请将这些信息自然地融入你的创作中，而不是生硬地复述。
        ---
        {material_summary}
        ---
        """

    prompt_template_text = f'''你是一位顶级的短视频策划和编剧，能够将复杂的信息转化为引人入胜的视频内容。
        **核心任务**: 根据用户要求及下方提供的参考素材，完成视频标题、脚本和BGM推荐，生成的脚本的长度尽量遵循视频时长的要求。
        要求开头抓住眼球，中间提供干货内容，结尾有惊喜，脚本格式也请按照【开头、中间，结尾】分隔。

        ---
        **!!! 最重要规则：你生成的所有内容，包括标题、脚本、BGM推荐理由，都必须使用【简体中文】。这是强制性的要求。**
        ---

        **用户要求:**
        -   **主题**: {{subject}}
        -   **视频时长**: {{duration}} 分钟
        -   **内容风格**: {style}
        {keyword_instruction}

        {reference_material_instruction}

        **输出格式要求:**
        你必须严格按照下面的JSON格式输出，不要有任何多余的文字。
        {{format_instructions}}
        '''

    prompt = ChatPromptTemplate.from_messages([('human', prompt_template_text)])
    model = create_chat_model(api_key=api_key, base_url=api_base_url, model=model_name,
                              temperature=creativity,
                              model_kwargs={"response_format": {"type": "json_object"}})
    chain = prompt | model | parser

    response = chain.invoke({
        'subject': subject,
        'duration': video_length,
        'format_instructions': parser.get_format_instructions(),
        'keywords': keywords if keywords else []
    })

    return response
