from langchain.chains import ConversationalRetrievalChain, load_summarize_chain
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from api_config import create_chat_model, create_embedding_model, create_local_embedding_model, get_api_config
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader
from langchain.prompts import PromptTemplate
import re


def _summary_limit(texts) -> int:
    """根据文档规模给出摘要上限：短文约 100 字，长文最多 500 字。"""
    total_chars = sum(len(getattr(doc, "page_content", "")) for doc in texts)
    if total_chars <= 600:
        return 100
    if total_chars <= 2000:
        return 250
    return 500


def _clean_summary(summary: str, limit: int) -> str:
    """清理模型附加说明，并对模型超长输出做最终长度保护。"""
    summary = re.sub(r"^\s*(摘要|总结|summary)\s*[:：]\s*", "", summary or "", flags=re.IGNORECASE)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) <= limit:
        return summary
    clipped = summary[:limit]
    punctuation = max(clipped.rfind(mark) for mark in "。！？；.!?;" )
    return clipped[:punctuation + 1] if punctuation >= int(limit * 0.7) else clipped.rstrip() + "。"

def process_document_and_summarize(openai_api_key, file_path, file_type, api_base_url=None, model_name=None):
    """
    根据文件类型加载、分割文档，并生成摘要。
    :param openai_api_key: OpenAI API密钥
    :param file_path: 临时文件的路径
    :param file_type: 文件的MIME类型（如 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'）
    :return: (list of Document objects, str summary)
    """
    if file_type == 'application/pdf':
        loader = PyPDFLoader(file_path)
    elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        loader = Docx2txtLoader(file_path)
    elif file_type == 'text/plain':
        loader = TextLoader(file_path, encoding='utf-8') # 确保使用UTF-8编码
    else:
        raise ValueError("不支持的文件类型。请上传PDF, Word (.docx) 或 TXT 文件。")

    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=50,
        separators=['\n\n', '\n', '。', '!', '?', '，', '、', '']
    )

    texts = text_splitter.split_documents(docs)
    summary_limit = _summary_limit(texts)

    # 初始化LLM模型用于摘要
    llm_for_summary = create_chat_model(api_key=openai_api_key, base_url=api_base_url,
                                        model=model_name, temperature=0.7)

    # 定义摘要的提示模板
    question_prompt_template = PromptTemplate(
        template=("请只输出文档摘要，不要输出标题、前言、分析过程、建议、免责声明或其他说明。"
                  f"摘要应简洁准确，控制在 {summary_limit} 字以内；信息很少的文档控制在 100 字以内。"
                  "只保留事实、主题、关键结论和必要数据。\n\n{text}"),
        input_variables=["text"]
    )

    refine_prompt_template = PromptTemplate(
        template=("请根据新文本块完善摘要。最终只能输出摘要正文，不要输出标题、过程、评价、建议或任何额外说明。"
                  f"摘要总长度不得超过 {summary_limit} 字，优先保留关键信息。"
                  "\n现有摘要：\n{existing_answer}\n\n新文本块：\n{text}"),
        input_variables=["existing_answer", "text"]
    )

    # 摘要链，使用'refine'类型以处理长文档
    # 'refine' 模式会逐个处理文档块，并用每个块的信息迭代地细化（refine）摘要。
    # 这对于处理非常大的文档特别有用，因为它不会受到LLM上下文窗口大小的限制。
    summary_chain = load_summarize_chain(
        llm_for_summary,
        chain_type="refine",
        return_intermediate_steps=False,
        question_prompt=question_prompt_template, # ！！！改为PromptTemplate实例！！！
        refine_prompt=refine_prompt_template    # ！！！改为PromptTemplate实例！！！
    )

    # 生成摘要
    summary_response = summary_chain.invoke({'input_documents': texts})
    summary_text = _clean_summary(summary_response["output_text"], summary_limit)

    return texts, summary_text

def qa_agent(openai_api_key, memory, processed_texts, question, api_base_url=None,
             model_name=None, embedding_model_name=None):
    '''
    PDF/文档智能问答代理核心函数
    :param openai_api_key: OpenAI API密钥
    :param memory: 对话内存，存储历史对话
    :param processed_texts: 已经分割好的文档文本块列表 (list of Document objects)
    :param question: 用户提出的问题
    :return: AI基于文档内容生成的回答
    '''

    model = create_chat_model(api_key=openai_api_key, base_url=api_base_url, model=model_name)

    config = get_api_config()
    if config["local_embedding_enabled"]:
        embedding_model = create_local_embedding_model(config["local_embedding_model"])
    elif config["embedding_api_enabled"]:
        embedding_model = create_embedding_model(
            api_key=config["embedding_api_key"],
            base_url=config["embedding_base_url"],
            model=embedding_model_name or config["embedding_model"]
        )
    else:
        raise ValueError("未启用 Embedding。请在设置页选择 Embedding API 或本地开源模型。")

    # 使用FAISS向量存储库，将分割后的文本块和嵌入模型结合
    # 这里直接使用传入的 processed_texts
    db = FAISS.from_documents(processed_texts, embedding_model)

    # 将向量存储转换为检索器，用于后续查询
    retriever = db.as_retriever()

    qa = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        memory=memory,
        return_source_documents=True # 可选：如果需要显示来源文档，可以设置为True
    )

    # 调用方式保持不变，但现在qa_agent内部使用的是processed_texts
    response = qa.invoke({'question': question})
    return response
