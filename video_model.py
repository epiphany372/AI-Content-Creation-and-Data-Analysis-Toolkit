from pydantic import BaseModel, Field
from typing import List, Optional

class MusicRec(BaseModel):
    """用于单首音乐推荐的 Pydantic 模型"""
    music_name: str = Field(description="推荐的歌曲名称")
    reason: str = Field(description="推荐这首歌曲作为背景音乐的简要理由")

class VideoScript(BaseModel):
    """用于视频脚本生成的 Pydantic 模型，包含标题、脚本和音乐推荐"""
    title: str = Field(description="根据主题和风格生成的视频标题")
    script: str = Field(description="根据标题、时长和风格生成的视频脚本，需严格按照【开头、中间、结尾】的格式")
    music_recommendations: List[MusicRec] = Field(
        description="推荐3首适合这个视频风格和内容的背景音乐(BGM)",
        min_length=3,
        max_length=3
    )
    # <<< 添加一个字段来描述关键词，虽然AI不会直接输出它，但这有助于构建Prompt >>>
    # 使用 Optional 表示这个字段在输入时是可选的
    keywords: Optional[List[str]] = Field(description="生成内容时需要重点围绕的核心关键词")