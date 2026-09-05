from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from api_config import create_chat_model

def get_chat_response(prompt, memory, openai_api_key, api_base_url=None, model_name=None):
    '''
    获取AI聊天响应的核心函数
    :param prompt: 用于输入的问题或提示
    :param memory: 对话内存对象，存储历史对话
    :param openai_api_key: OpenAI API密钥
    :return: 文本
    '''
    model = create_chat_model(api_key=openai_api_key, base_url=api_base_url, model=model_name)
    chain = ConversationChain(llm=model, memory=memory)
    response = chain.invoke({'input':prompt})
    return response['response']
