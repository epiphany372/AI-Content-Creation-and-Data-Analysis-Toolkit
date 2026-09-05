from pydantic import BaseModel, Field
from typing import List

class Xiaohongshu(BaseModel):
    """
    代表一篇社交媒体文案的Pydantic模型。
    """
    # 移除 min_length 和 max_length，让标题数量更灵活，由LLM的prompt决定
    titles: List[str] = Field(..., description="文案标题列表，数量和风格根据平台要求调整")
    content: str = Field(..., description="正文内容，包含emoji、分段、话题标签等")

class XiaohongshuPosts(BaseModel):
    """
    代表多篇社交媒体文案的Pydantic模型。
    """
    posts: List[Xiaohongshu] = Field(..., description="生成的社交媒体文案列表")

class ContentTypeSuggestions(BaseModel):
    """
    代表内容类型建议的Pydantic模型。
    """
    suggestions: List[str] = Field(..., description="根据主题生成的内容类型建议列表")

class ImageShootingRecommendations(BaseModel):
    """
    代表图片拍摄推荐的Pydantic模型。
    """
    recommendations: List[str] = Field(..., description="图片拍摄推荐列表")