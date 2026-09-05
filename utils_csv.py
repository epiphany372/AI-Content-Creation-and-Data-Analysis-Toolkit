import json  # 用于JSON数据处理
from api_config import create_chat_model
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent  # 导入Pandas数据框代理创建工具

# 定义提示模板，指导AI如何响应不同类型的用户请求
PROMPT_TEMPLATE = """
你是一个使用Python Pandas进行数据分析的AI智能体。你只能使用一个名为 `python_repl_ast` 的工具来执行代码。

你的工作必须严格遵循以下格式：

Question: 用户提出的原始问题。
Thought: 你必须仔细思考如何通过一步或多步的Pandas代码来解决这个问题。请在这里写下你的思考过程。
Action: 必须是 `python_repl_ast`。
Action Input: 必须是一段可以执行的、单行的Python代码。
Observation: 这是你执行代码后得到的结果。
...（这个Thought/Action/Action Input/Observation的循环可以重复多次）...

Thought: 在你看到最终的分析结果后，你必须在这里思考如何将这个结果转换成我指定的JSON格式。
Action: 必须是 `python_repl_ast`。
Action Input: 必须是一段可以执行的、单行的Python代码，这段代码的**唯一输出**就是最终的、格式化的JSON字符串。

==================== 最终输出要求 ====================
当你确定可以结束时，你的最后一个消息内容（Final Answer）必须是一个**纯 JSON 对象**，不能有任何多余字符。
结构只能是以下之一（按用户需求选择）：
- 文字回答: `{"answer": "你的答案"}`
- 表格: `{"table": {"columns": ["..."], "data": [[...]]}}`
- 条形图: `{"bar": {"columns": ["..."], "data": [...]}}`
- 折线图: `{"line": {"columns": [X轴, Y轴], "data": [[x1, y1], [x2, y2], ...]}}`
- 散点图: `{"scatter": {"columns": [X轴, Y轴], "data": [[x1, y1], [x2, y2], ...]}}`

**重要注意事项:**
- 你的**最后一次** `Action Input` 必须是生成最终JSON的代码。
- 最终的JSON必须是单行输出，不要包含任何额外字符或换行。
- 对于图表，请确保data字段的格式符合上述规则。例如，折线图和散点图的data是一个坐标对的列表 `[[x, y], [x, y], ...]`。
- 禁止在 Final Answer 里再写 Question / Thought / Action / Observation 等过程标记
- 禁止输出 Markdown 代码块（不要 ```json 或 ```）
- 禁止输出多余的解释文字、过渡句、总结句
- 禁止复制 Observation 里的内容粘贴到 Final Answer
- 只输出一个 JSON 对象，然后停止。

现在，请开始处理用户的请求。
Question: {input}
"""


def dataframe_agent(openai_api_key, df, query):
    """
    CSV数据分析智能体核心函数

    参数:
    - openai_api_key: OpenAI API密钥
    - df: 上传的CSV数据转换为的Pandas DataFrame
    - query: 用户的分析查询

    返回:
    - 包含分析结果的字典（文字回答、表格或图表数据）
    """
    # 初始化OpenAI聊天模型
    # openai_api_key: 传入API密钥
    # temperature=0: 输出更确定性，减少随机性
    model = create_chat_model(api_key=openai_api_key, temperature=0)

    # 创建Pandas数据框代理
    # llm=model: 使用初始化的OpenAI模型
    # df=df: 传入要分析的DataFrame
    # handle_parsing_errors=True: 自动处理解析错误
    # verbose=True: 打印详细执行日志
    agent = create_pandas_dataframe_agent(
        llm=model,
        df=df,
        agent_type="tool-calling",
        agent_executor_kwargs={"handle_parsing_errors": True},
        verbose=True,
        allow_dangerous_code=True  # 显式启用危险代码执行
    )

    # 组合提示模板和用户查询
    prompt = PROMPT_TEMPLATE + query

    # 调用代理处理用户查询
    response = agent.invoke({"input": prompt})

#从这里开始改变
    try:
        response_dict = json.loads(response["output"])
    except json.JSONDecodeError as e:
        print(f"Warning: Agent returned non-JSON output. Error: {e}")
        print(f"Raw agent output: {response.get('output', 'N/A')}")
        response_dict = {"answer": "抱歉，智能体未能返回有效格式的答案。"}

    return response_dict  # 返回分析结果字典

# 推荐问题库
# 键为文件类型（小写），值为该类型文件对应的推荐问题列表
RECOMMENDED_QUESTIONS = {
    'csv': [
        "统计每列的平均值",
        "找出每列的最大值和最小值",
        "计算每列的标准差",
        "统计每列的非空值数量",
        "查看前5行数据",
        "描述一下数据集的整体情况",
        "找出某一列的唯一值及其计数",
        "绘制某一列的折线图",
        "计算两列之间的相关性",
        "找出包含缺失值的列",
        "将某一列转换为日期格式",
        "找出销售额最高的10个产品"
    ]
}

def get_recommended_questions(file_type: str) -> list[str]:
    """
    根据文件类型获取推荐问题列表。

    Args:
        file_type (str): 文件的类型（例如 'csv', 'excel'）。

    Returns:
        list[str]: 推荐问题列表，如果未找到该类型则返回空列表。
    """
    # 将文件类型转换为小写，以便匹配字典中的键
    return RECOMMENDED_QUESTIONS.get(file_type.lower(), [])
