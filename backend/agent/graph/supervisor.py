"""
VisionTraceAI — Agent Reasoning Supervisor.

Node responsible for analyzing user queries and determining which search tools 
or workflows to trigger.
"""

from typing import Any, Dict, Literal, cast, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from backend.agent.graph.state import AgentState


class DeterministicRouterOutput(BaseModel):
    """Strict JSON output schema for the deterministic router."""
    
    intent: str = Field(
        description="The core intent extracted from the user query (e.g. 'Find person by description', 'Search timeline for specific time')."
    )
    tool_chain: List[str] = Field(
        description="An ordered list of tools to execute. Must ONLY contain 'search_timeline', 'search_visuals', or 'find_custom_object'."
    )
    filters: Dict[str, Any] = Field(
        description="Any extracted constraints, e.g. {'time': 'last 5 minutes', 'color': 'red', 'target_id': 42}. Use empty dict if none."
    )
    query_embedding: str = Field(
        description="The semantic visual concept to search for, if applicable (e.g. 'person in red jacket'). Leave empty if not applicable."
    )


def get_supervisor_prompt() -> ChatPromptTemplate:
    """Construct the supervisor system prompt."""
    system_msg = """You are a STRICT deterministic routing engine for the VisionTraceAI system.
Your job is ONLY to classify intent, build a tool chain, and return structured JSON.
You MUST NEVER generate conversational answers or hallucinate.

RULES:
1. If the query contains any TIME constraints (e.g. "last 5 minutes", "after 8pm") -> ALWAYS include "search_timeline" as the first tool in your `tool_chain`.
2. If the query contains a visual DESCRIPTION (e.g. "red shirt", "person wearing backpack") -> ALWAYS include "search_visuals" in your `tool_chain`. (If there is also time, the chain should be ["search_timeline", "search_visuals"]).
3. If the query asks for an UNKNOWN or CUSTOM object (e.g. "fire extinguisher", "blue umbrella") -> ALWAYS include "find_custom_object" in your `tool_chain`.
4. NEVER skip tool execution. NEVER respond in natural language internally.

Analyze the user's query and strictly conform to the required JSON schema output.
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
    # Initialize the LLM (requires GOOGLE_API_KEY in the environment or passed explicitly)
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    structured_llm = llm.with_structured_output(DeterministicRouterOutput)
    
    prompt = get_supervisor_prompt()
    chain = prompt | structured_llm
    
    # Run the chain to classify the intent
    result = cast(DeterministicRouterOutput, chain.invoke({"user_query": state["user_query"]}))
    
    # Return partial state update
    return {
        "parsed_intent": {
            "intent": result.intent,
            "tool_chain": result.tool_chain,
            "filters": result.filters,
            "query_embedding": result.query_embedding
        }
    }
