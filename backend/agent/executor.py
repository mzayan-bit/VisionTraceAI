"""
VisionTraceAI — Agent Executor.

End-to-end wrapper for the LangGraph pipeline, orchestrating query ingestion,
state management, and result formatting.
"""

from typing import Any, Dict, List

from backend.agent.graph.state import AgentState
from backend.agent.graph.workflow import app


def format_final_answer(user_query: str, tool_outputs: List[Dict[str, Any]], history: List[Dict[str, str]] = None) -> str:
    """Format a human-readable summary from accumulated tool outputs."""
    if not tool_outputs:
        return "I couldn't find anything matching your description in the recent feeds."
        
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
        import json
        
        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.7)
        
        system_msg = """You are VisionTraceAI, a professional human analyst monitoring a live CCTV feed.
Your job is to analyze the raw search results and provide a clean, non-technical summary to the user.

CRITICAL RULES:
1. Speak like a human analyst.
2. NEVER use technical terms, model names (e.g. YOLO, SigLIP), or embeddings.
3. NEVER expose raw 'track_id's to the user.
4. NEVER expose backend errors. If no results are found or an error occurs, gracefully say "I couldn't find anything matching your description in the recent feeds."
5. You MUST include the 'crop_url' of the person/object inline as an HTML image tag (`<img src="url" alt="Detection" />`) so the user can see them, but DO NOT mention their track ID.

You MUST structure your response EXACTLY like this using HTML tags:

<div class='insight-section'><strong>What happened:</strong> <p>[Describe the event naturally, e.g. "A person in a white shirt walked from left to right." Include the `<img src="url" alt="Detection" />` here inline.]</p></div>
<div class='insight-section'><strong>Where & When:</strong> <p>[State the camera and time naturally]</p></div>
<div class='insight-section'><strong>Confidence:</strong> <p>[High/Medium/Low based on score]</p></div>

Do not output any other raw logs or text outside this structure. Be concise."""

        messages = [("system", system_msg)]
        if history:
            for msg in history[:-1]:
                role = "assistant" if msg["role"] == "assistant" else "human"
                messages.append((role, msg["content"]))
                
        messages.append(("human", "Query: {user_query}\n\nRaw Search Results:\n{tool_outputs}"))
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # Clean up tool outputs for the prompt to avoid token bloat
        clean_outputs = []
        for out in tool_outputs:
            if isinstance(out.get("result"), list):
                # only keep top 5
                top_results = out["result"][:5]
                clean_outputs.append({"tool": out.get("tool"), "result": top_results})
            else:
                clean_outputs.append(out)
                
        chain = prompt | llm
        response = chain.invoke({"user_query": user_query, "tool_outputs": json.dumps(clean_outputs, default=str)})
        return response.content
    except Exception as e:
        return f"Found matching records, but failed to generate a conversational response: {e}"


class VisionAgentExecutor:
    """End-to-end wrapper for the LangGraph agent pipeline."""
    
    def __init__(self) -> None:
        self.app = app
        
    def execute(self, query: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Execute the full LangGraph pipeline for a user query.
        
        Args:
            query: Natural language query string.
            history: Optional list of previous conversation messages.
            
        Returns:
            Dictionary containing the final answer, parsed intent, and raw results.
        """
        if history is None:
            history = []
        # Add current query to history for state
        current_history = history + [{"role": "user", "content": query}]
        
        initial_state: AgentState = {
            "user_query": query,
            "parsed_intent": {},
            "tool_outputs": [],
            "track_ids": [],
            "final_answer": "",
            "conversation_memory": current_history,
            "diagnostic_logs": [],
            "system_health": 1.0
        }
        
        # Run the LangGraph application
        result_state = self.app.invoke(initial_state)
        
        # Collect and merge tool outputs
        tool_outputs = result_state.get("tool_outputs", [])
        
        # Format the final answer
        final_answer = format_final_answer(query, tool_outputs, current_history)
                
        return {
            "query": query,
            "intent": result_state.get("parsed_intent", {}),
            "final_answer": final_answer,
            "raw_results": tool_outputs,
            "system_health": result_state.get("system_health", 1.0)
        }
