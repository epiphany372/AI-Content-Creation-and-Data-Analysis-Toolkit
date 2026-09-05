from typing import List
from prompt_template import (
    user_template_text,
    system_template_content_type_suggestion, user_template_content_type_suggestion,
    system_template_image_recommendation, user_template_image_recommendation,
    platform_system_templates
)
from api_config import create_chat_model
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from xiaohongshu_model import XiaohongshuPosts, ContentTypeSuggestions, ImageShootingRecommendations

def get_llm_model(api_key: str, temperature: float = 0.7, api_base_url=None, model_name=None):
    """封装LLM模型初始化"""
    return create_chat_model(api_key=api_key, base_url=api_base_url,
                             model=model_name, temperature=temperature)

def generate_social_media_post(platform: str, theme: str, content_type: str, num_posts: int, openai_api_key: str, api_base_url=None, model_name=None) -> XiaohongshuPosts:
    '''
    生成多平台社交媒体内容的核心函数
    :param platform: 目标平台 (如 "小红书", "抖音", "微博")
    :param theme: 文案的主题
    :param content_type: 文案的内容类型细分
    :param num_posts: 要生成的文案数量
    :param openai_api_key: OpenAI API Key
    :return: XiaohongshuPosts Pydantic 模型对象 (通用结构)
    '''
    if not openai_api_key:
        raise ValueError("OpenAI API Key is not provided.")

    selected_system_template = platform_system_templates.get(
        platform,
        platform_system_templates["小红书 (Xiaohongshu)"] # 默认回退到小红书模板
    )

    prompt_instance = ChatPromptTemplate.from_messages([
        ('system', selected_system_template),
        ('user', user_template_text)
    ])
    model = get_llm_model(openai_api_key, temperature=0.7, api_base_url=api_base_url, model_name=model_name)

    output_parser = PydanticOutputParser(pydantic_object=XiaohongshuPosts)

    chain = prompt_instance | model | output_parser # 使用 prompt_instance

    try:
        # 打印生成的完整提示词，帮助调试
        formatted_system_prompt = selected_system_template.format(num_posts=num_posts)
        formatted_user_prompt = user_template_text.format(theme=theme, content_type=content_type)
        parser_instructions = output_parser.get_format_instructions()

        print(f"\n--- Generating Social Media Post (Platform: {platform}) ---")
        print("System Prompt Sent to LLM:\n", formatted_system_prompt)
        print("User Prompt Sent to LLM:\n", formatted_user_prompt)
        print("Pydantic Parser Instructions:\n", parser_instructions)
        print("--- End Prompt Details ---")

        result = chain.invoke({
            'parser_instructions': parser_instructions,
            'platform': platform, # 传递平台信息给prompt (system template可能会用到)
            'theme': theme,
            'content_type': content_type,
            'num_posts': num_posts
        })
        return result
    except Exception as e:
        # 捕获并打印原始的LLM响应，这是解决解析错误的关键
        print(f"\n!!! ERROR during generation for Platform: '{platform}', Theme: '{theme}', Type: '{content_type}' !!!")
        print(f"Error details: {e}")
        print(f"Please check the LLM's raw output in your OpenAI dashboard or logs if available.")
        raise # 重新抛出异常，让main.py捕获并显示给用户


def generate_content_type_suggestions(theme: str, openai_api_key: str, api_base_url=None, model_name=None) -> List[str]:
    '''
    根据主题生成内容类型建议
    '''
    if not openai_api_key:
        raise ValueError("OpenAI API Key is not provided.")
    if not theme:
        return []

    prompt_instance = ChatPromptTemplate.from_messages([
        ('system', system_template_content_type_suggestion),
        ('user', user_template_content_type_suggestion)
    ])
    model = get_llm_model(openai_api_key, temperature=0.5, api_base_url=api_base_url, model_name=model_name)

    output_parser = PydanticOutputParser(pydantic_object=ContentTypeSuggestions)

    chain = prompt_instance | model | output_parser
    try:
        result = chain.invoke({
            'parser_instructions': output_parser.get_format_instructions(),
            'theme': theme
        })
        return result.suggestions
    except Exception as e:
        print(f"Error generating content type suggestions for theme '{theme}': {e}")
        return []

def generate_image_shooting_recommendations(platform: str, theme: str, content_type: str, openai_api_key: str, api_base_url=None, model_name=None) -> List[str]:
    '''
    根据平台、主题和内容类型生成图片拍摄建议
    '''
    if not openai_api_key:
        raise ValueError("OpenAI API Key is not provided.")
    if not theme or not content_type:
        return []

    prompt_instance = ChatPromptTemplate.from_messages([
        ('system', system_template_image_recommendation),
        ('user', user_template_image_recommendation)
    ])
    model = get_llm_model(openai_api_key, temperature=0.6, api_base_url=api_base_url, model_name=model_name)

    output_parser = PydanticOutputParser(pydantic_object=ImageShootingRecommendations)

    chain = prompt_instance | model | output_parser
    try:
        result = chain.invoke({
            'parser_instructions': output_parser.get_format_instructions(),
            'platform': platform,
            'theme': theme,
            'content_type': content_type
        })
        return result.recommendations
    except Exception as e:
        print(f"Error generating image shooting recommendations for platform '{platform}', theme '{theme}', type '{content_type}': {e}")
        return []
