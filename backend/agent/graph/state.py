"""
VisionTraceAI — Agent State Schema.

Defines the LangGraph state schema for the agent orchestrator.
"""

import operator
from typing import Annotated, Any, Dict, List
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    State schema for the VisionTraceAI LangGraph orchestrator.
    
    Attributes:
        user_query: The original natural language query from the user.
        parsed_intent: A structured dictionary of the user's inferred intent.
        tool_outputs: Accumulated outputs from executed tools.
        track_ids: Accumulated track IDs identified during the agent's run.
        final_answer: The final response to return to the user.
        conversation_memory: History of messages/interactions in the conversation.
    """
    user_query: str
    parsed_intent: Dict[str, Any]
    
    # Annotated with operator.add so that elements are appended rather than overwritten
    tool_outputs: Annotated[List[Dict[str, Any]], operator.add]
    track_ids: Annotated[List[int], operator.add]
    
    final_answer: str
    
    # Message history to maintain conversation context
    conversation_memory: Annotated[List[Dict[str, Any]], operator.add]
