"""
VisionTraceAI — Agent Reasoning Supervisor.

Node responsible for analyzing user queries and determining which search tools 
or workflows to trigger.
"""

from typing import Any, Dict, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.agent.graph.state import AgentState


class IntentClassification(BaseModel):
    """Structured output schema for the reasoning supervisor."""
    
    reasoning_trace: str = Field(
        description="Step-by-step reasoning explaining why a specific tool is required based on the user's query."
    )
    selected_tool: Literal[
        "search_timeline", 
        "search_visuals", 
        "find_custom_object", 
        "hybrid_search", 
        "none"
    ] = Field(
        description="The appropriate tool to use based on the user's query."
    )


def get_supervisor_prompt() -> ChatPromptTemplate:
    """Construct the supervisor system prompt."""
    system_msg = """You are the reasoning supervisor for the VisionTraceAI video analytics system.
Your job is to analyze the user's natural language query and route it to the correct underlying search tool.

Available tools and their mapping rules:
- search_timeline: Use when the query is strictly time-based (e.g. "after 8pm", "between 5-6pm").
- search_visuals: Use when the query is about visual appearance, standard objects, or clothing (e.g. "red backpack", "person in green shirt").
- find_custom_object: Use when the query is about specific, custom, or unknown objects that require open-vocabulary detection (e.g. "fire extinguisher", "exit sign").
- hybrid_search: Use when the query is general or combines multiple constraints.

Analyze the query step-by-step, explain your reasoning, and then select the appropriate tool.
"""
    return ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", "Query: {user_query}")
    ])


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node for intent classification.
    
    Evaluates the current `user_query` and updates the state with the `parsed_intent`.
    """
    # Initialize the LLM (requires OPENAI_API_KEY in the environment or passed explicitly)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(IntentClassification)
    
    prompt = get_supervisor_prompt()
    chain = prompt | structured_llm
    
    # Run the chain to classify the intent
    result: IntentClassification = chain.invoke({"user_query": state["user_query"]})
    
    # Return partial state update
    return {
        "parsed_intent": {
            "selected_tool": result.selected_tool,
            "reasoning_trace": result.reasoning_trace
        }
    }
