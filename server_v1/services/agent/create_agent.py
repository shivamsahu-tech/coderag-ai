import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from services.agent.tools import retrieve_context_wrapper
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage

# --- 1. Define State (The Memory) ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- 2. Build the Graph (Run this ONCE) ---
def build_agent_graph():
    # A. Setup Gemini 2.5
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0.5,
        max_tokens=1000,
        api_key=os.getenv("LLM_API_KEY")
    )

    tools = [retrieve_context_wrapper]
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: State):
        
        sys_msg = SystemMessage(content="""
        You are an expert CodeBase Assistant for user .
        
        This codebase, is broken into the dependency graph with tree sitter, and here are each nodes structure : 
            ast_type: elif_clause
            calls: lower, extend, error, _extract_document_file, endswith
            code_str: `elif include_docs and file.lower().endswith(DOC_EXTENSIONS): try: doc_nodes = _extract_document_file(file_path, relative_path) if doc_nodes: for node in doc_nodes: node_lookup[node['id']] = node file_to_nodes relative_path = [n['id'] for n in doc_nodes] all_nodes.extend(doc_nodes) stats['files_processed'] += 1 stats['nodes_extracted'] += len(doc_nodes) except Exception as e: logger.error(f"Doc error relative_path: e")
            depth: 9
            end_byte: 5346
            end_line: 131
            file: data/repos/f18d2f57-cf74-46a8-9ff0-850c3e2936ab/src/file_traversal.py
            id: data/repos/f18d2f57-cf74-46a8-9ff0-850c3e2936ab/src/file_traversal.py:119:elif_clause
            is_definition: false
            language: python
            name: elif_clause
            session_id: 4d217bd9-e710-4021-9dba-3fe5f4dbc363
            size: 666
            start_byte: 4680
            start_line: 120

        and in the embedding a string with collection of ast_type | code_str | file_name | name
        is created so, your query in the retrieve_context tool will target the embeddings, related with it, so you are free to create reform the query so it can extract better nodes
        YOUR GOAL:
        Help the user understand their codebase by retrieving relevant context and explaining it clearly.
        
        INSTRUCTIONS:
        1. Use the 'retrieve_context' tool, if the user asks about specific files, functions, or logic, you can enhance the user query if need
        2. Do not hallucinate code. If you don't know, use the tool to find out, you can try max 3 times to extract the nodes, so you can get better output for the user query
        3. If the tool returns no results, ask the user to clarify their query.
        4. Keep your answers concise and technical. Any question beside the codeRAG or codebase, you will tell user that i am not able to provide resoponse for those questions
        """)
        messages = [sys_msg] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}
    



    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges(
        "chatbot", 
        tools_condition
    )
    builder.add_edge("tools", "chatbot")

    # F. Add Memory Persistence
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

# Create the global agent instance
agent_app = build_agent_graph()