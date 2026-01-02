"""
LangGraph RAG 节点
实现完整的 RAG 工作流
"""
from typing import TypedDict, Annotated, List, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
import os


# 定义 RAG 状态
class RAGState(TypedDict):
    messages: Annotated[List, "消息历史"]
    query: str  # 用户查询
    retrieved_docs: List[str]  # 检索到的文档
    relevant_docs: List[str]  # 相关文档（过滤后）
    rewrite_query: str  # 重写后的查询
    answer: str  # 生成的答案
    citations: List[str]  # 引用来源


def _get_llm():
    """获取 LLM 实例"""
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model="doubao-seed-1-6-251015",  # 使用集成模型
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        streaming=True,
        timeout=600
    )
    return llm


# 节点 1: 检索决策节点
def retrieve_decision(state: RAGState) -> Literal["retrieve_docs", "direct_answer"]:
    """
    决定是否需要检索文档

    判断逻辑：
    - 如果查询包含特定关键词或需要外部知识，执行检索
    - 否则直接回答
    """
    query = state["query"]
    llm = _get_llm()

    # 决策提示词
    decision_prompt = SystemMessage(content="""
你是一个检索决策助手。判断用户查询是否需要从知识库检索文档。

判断标准：
1. 如果查询涉及具体的业务规则、技术细节、产品信息等，需要检索
2. 如果是简单问候、闲聊、常识性问题，不需要检索

请只返回 "retrieve" 或 "direct_answer"。
    """)

    user_query = HumanMessage(content=f"用户查询: {query}")

    response = llm.invoke([decision_prompt, user_query])

    # 解析决策
    content = response.content
    decision = str(content).strip().lower() if isinstance(content, str) else ""

    if "retrieve" in decision:
        return "retrieve_docs"
    else:
        return "direct_answer"


# 节点 2: 文档检索节点
def retrieve_docs(state: RAGState) -> RAGState:
    """
    从知识库检索文档
    """
    query = state["query"]
    # 确保 query 是字符串
    if not isinstance(query, str):
        query = str(query)

    # 导入 RAG 检索工具
    from tools.rag_retriever import rag_retrieve_with_rerank

    # 执行检索
    retrieval_result = rag_retrieve_with_rerank(
        query=query,
        initial_k=20,
        top_n=5,
        use_rerank=True
    )

    # 解析检索结果（简化处理）
    # 在实际实现中，应该解析返回的字符串提取文档
    retrieved_docs = [retrieval_result]

    return {"retrieved_docs": retrieved_docs}


# 节点 3: 文档相关性评估节点
def grade_documents(state: RAGState) -> Literal["generate_answer", "rewrite_query"]:
    """
    评估检索到的文档是否相关

    相关性标准：
    - 文档是否真正回答了用户的问题
    - 是否包含足够的信息
    """
    query = state["query"]
    retrieved_docs = state["retrieved_docs"]
    llm = _get_llm()

    # 评估提示词
    grade_prompt = SystemMessage(content="""
你是一个文档相关性评估助手。评估检索到的文档是否相关。

评估标准：
1. 文档是否真正回答了用户的问题
2. 文档内容是否准确、完整
3. 是否包含足够的信息

请返回：
- 如果文档相关：返回 "relevant"
- 如果文档不相关：返回 "not_relevant"
    """)

    # 构建评估输入
    docs_text = "\n\n".join(retrieved_docs)
    grade_input = HumanMessage(content=f"""
用户查询: {query}

检索到的文档:
{docs_text}

这些文档是否相关？请返回 "relevant" 或 "not_relevant"。
    """)

    response = llm.invoke([grade_prompt, grade_input])
    content = response.content
    evaluation = str(content).strip().lower() if isinstance(content, str) else ""

    if "relevant" in evaluation:
        # 简化：将检索到的文档作为相关文档
        return {"relevant_docs": retrieved_docs}
    else:
        return "rewrite_query"


# 节点 4: 问题重写节点
def rewrite_query(state: RAGState) -> RAGState:
    """
    重写用户查询以提高检索效果
    """
    query = state["query"]
    llm = _get_llm()

    # 重写提示词
    rewrite_prompt = SystemMessage(content="""
你是一个查询重写助手。重写用户查询以提高检索效果。

重写原则：
1. 保持查询的原始意图
2. 使查询更清晰、更具体
3. 添加相关的关键词
4. 不要改变用户的问题

请直接返回重写后的查询，不要添加解释。
    """)

    user_query = HumanMessage(content=f"原始查询: {query}")
    response = llm.invoke([rewrite_prompt, user_query])

    content = response.content
    rewrite_query = str(content).strip() if isinstance(content, str) else ""

    return {"rewrite_query": rewrite_query}


# 节点 5: 答案生成节点（带引用）
def generate_answer(state: RAGState) -> RAGState:
    """
    基于检索到的文档生成答案，并提供引用
    """
    query = state["query"]
    relevant_docs = state.get("relevant_docs", state.get("retrieved_docs", []))
    llm = _get_llm()

    # 生成提示词
    answer_prompt = SystemMessage(content="""
你是一个知识问答助手。基于提供的知识库内容回答用户问题。

回答要求：
1. 答案必须基于提供的知识库内容
2. 不要编造信息
3. 答案要准确、清晰、结构化
4. 必须在答案末尾提供引用来源
5. 如果知识库中没有相关信息，明确说明

引用格式：
---
引用来源:
[来源1]
[来源2]
---
    """)

    # 构建上下文
    docs_text = "\n\n".join(relevant_docs)

    answer_input = HumanMessage(content=f"""
用户问题: {query}

知识库内容:
{docs_text}

请基于以上内容回答问题，并提供引用。
    """)

    response = llm.invoke([answer_prompt, answer_input])
    content = response.content
    answer = str(content).strip() if isinstance(content, str) else ""

    # 提取引用（简化处理）
    # 在实际实现中，应该解析答案中的引用部分
    citations = ["[知识库]"]  # 简化处理

    return {
        "answer": answer,
        "citations": citations
    }


# 节点 6: 后续问题建议节点
def suggest_questions(state: RAGState) -> RAGState:
    """
    基于当前问题和答案，生成后续问题建议
    """
    query = state["query"]
    answer = state.get("answer", "")
    llm = _get_llm()

    # 生成提示词
    suggest_prompt = SystemMessage(content="""
你是一个问题建议助手。基于用户的问题和答案，生成3个相关的后续问题。

后续问题要求：
1. 与当前问题和答案相关
2. 有助于用户深入了解相关话题
3. 具体且有探索价值
4. 不要重复当前问题

请以 JSON 格式返回，例如：
{
  "suggested_questions": [
    "问题1",
    "问题2",
    "问题3"
  ]
}
    """)

    suggest_input = HumanMessage(content=f"""
用户问题: {query}

AI 答案: {answer[:500]}...

请生成3个后续问题建议。
    """)

    response = llm.invoke([suggest_prompt, suggest_input])

    # 解析后续问题（简化处理）
    # 在实际实现中，应该解析 JSON
    content = response.content
    suggested_questions = str(content).strip() if isinstance(content, str) else ""

    # 添加到答案中
    final_answer = f"{state.get('answer', '')}\n\n---\n💡 后续问题建议:\n{suggested_questions}"

    return {"answer": final_answer}


def build_rag_graph():
    """
    构建 RAG LangGraph

    Returns:
        LangGraph 实例
    """
    # 创建状态图
    workflow = StateGraph(RAGState)

    # 添加节点
    workflow.add_node("retrieve_decision", retrieve_decision)
    workflow.add_node("retrieve_docs", retrieve_docs)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("rewrite_query", rewrite_query)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("suggest_questions", suggest_questions)

    # 添加边
    workflow.add_edge(START, "retrieve_decision")
    workflow.add_conditional_edges(
        "retrieve_decision",
        {
            "retrieve_docs": "retrieve_docs",
            "direct_answer": "generate_answer"
        }
    )
    workflow.add_edge("retrieve_docs", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        {
            "generate_answer": "generate_answer",
            "rewrite_query": "rewrite_query"
        }
    )
    workflow.add_edge("rewrite_query", "retrieve_docs")  # 重新检索
    workflow.add_edge("generate_answer", "suggest_questions")
    workflow.add_edge("suggest_questions", END)

    # 编译图
    app = workflow.compile()

    return app


# 使用示例
if __name__ == "__main__":
    # 构建图
    rag_app = build_rag_graph()

    # 测试运行
    test_state = {
        "query": "什么是建账规则？",
        "messages": []
    }

    # 执行图
    result = rag_app.invoke(test_state)

    print("=== RAG 流程结果 ===")
    print(result)
