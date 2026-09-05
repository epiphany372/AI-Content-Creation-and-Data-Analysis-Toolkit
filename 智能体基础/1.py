from langchain import hub  # 用于获取预定义的提示模板
from langchain.agents import create_structured_chat_agent, AgentExecutor  # 创建和执行结构化聊天代理
from langchain.memory import ConversationBufferMemory  # 对话内存，存储历史消息
from langchain.schema import HumanMessage  # 表示人类用户发送的消息
from langchain.tools import BaseTool  # 自定义工具的基类
from langchain_openai import ChatOpenAI  # OpenAI聊天模型接口

# 初始化OpenAI模型，temperature=0表示输出更确定性，减少随机性
model = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)

# 直接使用模型测试一个问题
# invoke方法接受一个消息列表，这里只有一个人类消息
model.invoke([HumanMessage(content="'君不见黄河之水天上来奔流到海不复回'，这句话的字数是多少？")])

# 创建自定义工具：文本字数计算工具
# 继承BaseTool类并实现必要的属性和方法
class TextLengthTool(BaseTool):
    name = "文本字数计算工具"  # 工具名称，供Agent识别
    description = "当你被要求计算文本的字数时，使用此工具"  # 工具描述，指导Agent何时使用

    def _run(self, text):  # 工具执行的核心逻辑
        return len(text)  # 返回文本长度

# 创建工具列表，将自定义工具添加进去
tools = [TextLengthTool()]

# 从LangChain Hub获取预定义的结构化聊天代理提示模板
# hwchase17/structured-chat-agent是一个适合结构化工具使用的提示模板
prompt = hub.pull("hwchase17/structured-chat-agent")
print(prompt)  # 打印提示模板，了解其结构和内容


agent = create_structured_chat_agent(
    llm=model,  # 使用之前初始化的OpenAI模型
    tools=tools,  # 使用自定义的文本字数计算工具
    prompt=prompt  # 使用从Hub获取的提示模板
)

# 初始化对话内存
# memory_key指定存储对话历史的键名
# return_messages=True表示返回消息对象列表而非字符串
memory = ConversationBufferMemory(
    memory_key='chat_history',
    return_messages=True
)

# 创建代理执行器
# 将代理、工具和内存组合在一起，设置为verbose模式以便查看执行过程
# handle_parsing_errors=True表示自动处理解析错误
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,    # 必需参数：传入已创建的代理对象（Agent）
    tools=tools,      # 必需参数：传入代理可使用的工具列表
    memory=memory,
    verbose=True,  # 可选参数：是否打印详细日志（调试用）
    handle_parsing_errors=True # 可选参数：是否自动处理工具调用格式错误
)

# 代理与执行器的关系：大脑与神经系统的类比
# 结构化聊天代理：相当于 "大脑"，负责：
# 理解问题（自然语言处理）
# 制定解决方案（决定是否使用工具、使用哪个工具）
# 整合信息（将工具结果转化为自然语言回答）
# 代理执行器：相当于 "神经系统"，负责：
# 传递指令（将代理的工具调用请求发送给工具）
# 管理状态（存储对话历史，保持上下文连贯）
# 处理异常（修复格式错误、重试失败的工具调用）

# 使用代理执行器回答问题
# 代理会判断是否需要使用工具，并生成相应的回答
print(agent_executor.invoke({"input": "'君不见黄河之水天上来奔流到海不复回'，这句话的字数是多少？"}))

# 测试一个不需要工具的问题
# 代理会直接使用语言模型回答
print(agent_executor.invoke({"input": "请你充当我的物理老师，告诉我什么是量子力学"}))




#!pip install langchain_experimental


# 安装langchain_experimental包（注释掉，实际教学时可能需要执行）
#!pip install langchain_experimental

# 导入创建Python代理和Python REPL工具所需的模块
from langchain_experimental.agents.agent_toolkits import create_python_agent
from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI

# 创建Python REPL工具
# 该工具允许执行Python代码并返回结果
tools = [PythonREPLTool()]

# 创建Python代理执行器
# 该代理可以生成并执行Python代码来解决问题
agent_executor = create_python_agent(
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),  # 指定OpenAI模型
    tool=PythonREPLTool(),  # 使用Python REPL工具
    verbose=True,  # 显示详细执行过程
    agent_executor_kwargs={"handle_parsing_errors": True}  # 处理解析错误
)

# 打印代理执行器信息
print(agent_executor)

# 使用Python代理计算7的2.3次方
# 代理会生成Python代码并执行计算
print(agent_executor.invoke({"input": "7的2.3次方是多少？"}))

# 使用Python代理计算第12个斐波那契数
# 代理会生成递归或迭代代码来计算斐波那契数列
print(agent_executor.invoke({"input": "第12个斐波那契数列的数字是多少？"}))




# 导入创建CSV代理所需的模块
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_openai import ChatOpenAI

# 创建CSV代理执行器
# 该代理可以读取和分析CSV文件
agent_executor = create_csv_agent(
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),  # 指定OpenAI模型
    path="house_price.csv",  # 指定CSV文件路径
    verbose=True,  # 显示详细执行过程
    agent_executor_kwargs={"handle_parsing_errors": True}  # 处理解析错误
)

# 打印代理执行器信息
print(agent_executor)

# 使用CSV代理查询数据集行数
print(agent_executor.invoke({"input": "数据集有多少行？用中文回复"}))

# 使用CSV代理查询数据集包含的变量
print(agent_executor.invoke({"input": "数据集包含哪些变量？用中文回复"}))

# 使用CSV代理计算房价平均值
print(agent_executor.invoke({"input": "数据集里，所有房子的价格平均值是多少？用中文回复"}))

# 使用CSV代理分析装修状态种类及其含义
print(agent_executor.invoke({
    "input": "数据集里，所有房子的装修状态包含哪些种类？你认为它们具体表示什么意思？用中文回复"}))






# 导入创建组合代理所需的所有模块
from langchain import hub
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool, Tool  # 注意新增的Tool类，用于包装已有执行器
from langchain_experimental.agents.agent_toolkits import create_csv_agent, create_python_agent
from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI

# 初始化基础模型
model = ChatOpenAI(model='gpt-3.5-turbo')

# 重新定义文本字数计算工具（与第一部分相同）
class TextLengthTool(BaseTool):
    name = "文本字数计算工具"
    description = "当你需要计算文本包含的字数时，使用此工具"

    def _run(self, text):
        return len(text)

# 创建Python代理执行器（与第二部分类似）
python_agent_executor = create_python_agent(
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
    tool=PythonREPLTool(),
    verbose=True,
    agent_executor_kwargs={"handle_parsing_errors": True}
)

# 创建CSV代理执行器（与第三部分类似）
csv_agent_executor = create_csv_agent(
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0,),
    path="house_price.csv",
    verbose=True,
    agent_executor_kwargs={"handle_parsing_errors": True}
)

# 创建组合工具列表
# 将Python代理、CSV代理和文本字数计算工具整合在一起
tools=[
    Tool(
        name="Python代码工具",
        description="""当你需要借助Python解释器时，使用这个工具。
        用自然语言把要求给这个工具，它会生成Python代码并返回代码执行的结果。""",
        func=python_agent_executor.invoke  # 这里直接调用Python代理执行器的invoke方法，
                                          # 意味着当Agent决定使用这个工具时，
                                          # 它会将问题传递给Python代理执行器去处理，
                                          # 代理执行器会根据问题生成Python代码并执行，然后返回结果
    ),
    Tool(
        name="CSV分析工具",
        description="""当你需要回答有关house_price.csv文件的问题时，使用这个工具。
        它接受完整的问题作为输入，在使用Pandas库计算后，返回答案。""",
        func=csv_agent_executor.invoke  # 同理，这里调用CSV代理执行器的invoke方法，
                                        # 当Agent判断问题与house_price.csv文件相关时，
                                        # 会将问题交给CSV代理执行器，它会读取文件并进行相应计算后返回答案
    ),
    TextLengthTool()  # 添加自定义文本字数计算工具的实例，
                      # 这个工具是直接继承自BaseTool的类的实例，
                      # 它的name和description属性在类定义中已经设置好，
                      # 当Agent遇到需要计算文本字数的问题时，会使用这个工具
]

# 初始化对话内存（与第一部分相同）
memory = ConversationBufferMemory(
    memory_key='chat_history',
    return_messages=True
)

# 从Hub获取结构化聊天代理提示模板（与第一部分相同）
prompt = hub.pull("hwchase17/structured-chat-agent")
print(prompt)  # 打印提示模板，这里的提示模板是从LangChain Hub上拉取的，
               # 它是一个预定义的文本模板，用于指导Agent如何思考和使用工具来回答问题，
               # 打印出来可以查看其具体内容和格式

# 创建结构化聊天代理（与第一部分类似，但使用组合工具）
agent = create_structured_chat_agent(
    llm=model,
    tools=tools,
    prompt=prompt
)

# 创建组合代理执行器
# 能够智能选择使用Python工具、CSV工具或文本计算工具
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# 测试不同类型的问题
# 代理会自动选择合适的工具来回答
print(agent_executor.invoke({"input": "第8个斐波那契数列的数字是多少？"}))  # 代理会根据问题的性质判断需要使用Python代码工具，
                                                                              # 然后调用Python代理执行器来生成并执行计算斐波那契数列的代码，最后返回结果
print(agent_executor.invoke({"input": "house_price数据集里，所有房子的价格平均值是多少？用中文回答"}))  # 代理会识别出这个问题与CSV文件相关，
                                                                                                              # 从而调用CSV代理执行器来读取house_price.csv文件并计算价格平均值，最后返回结果
print(agent_executor.invoke({"input": "'君不见黄河之水天上来奔流到海不复回'，这句话的字数是多少？"}))  # 代理会判断这个问题是关于文本字数计算的，
                                                                                                             # 然后直接使用文本字数计算工具来返回文本的字数


