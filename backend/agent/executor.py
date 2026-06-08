"""
VisionTraceAI — Agent Executor.

End-to-end wrapper for the LangGraph pipeline, orchestrating query ingestion,
state management, and result formatting.
"""

from typing import Any, Dict, List

from backend.agent.graph.state import AgentState
from backend.agent.graph.workflow import app


def format_final_answer(user_query: str, tool_outputs: List[Dict[str, Any]]) -> str:
    """Format a human-readable summary from accumulated tool outputs."""
    if not tool_outputs:
        return "I couldn't find any results matching your query in the current video stream."
        
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
        import json
        
        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.7)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are VisionTraceAI, a highly intelligent AI Insight Engine. Your job is to analyze the raw search results and provide a clean, non-technical summary.\n"
                       "You MUST structure your response EXACTLY like this using HTML tags:\n\n"
                       "<div class='insight-section'><strong>What is happening:</strong> <p>[1 sentence summary of the event/findings]</p></div>\n"
                       "<div class='insight-section'><strong>Who/What is involved:</strong> <p>[Describe the top matches. You MUST include their 'crop_url' inline as `<img src=\"url\" alt=\"Track ID\" />` so the user sees the person]</p></div>\n"
                       "<div class='insight-section'><strong>Confidence level:</strong> <p>[State the average or highest confidence level cleanly, e.g. 'High (95%)']</p></div>\n\n"
                       "Do not output any other raw logs or text outside this structure. Be concise."),
            ("human", "Query: {user_query}\n\nRaw Search Results:\n{tool_outputs}")
        ])
        
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
        
    def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute the full LangGraph pipeline for a user query.
        
        Args:
            query: Natural language query string.
            
        Returns:
            Dictionary containing the final answer, parsed intent, and raw results.
        """
        initial_state: AgentState = {
            "user_query": query,
            "parsed_intent": {},
            "tool_outputs": [],
            "track_ids": [],
            "final_answer": "",
            "conversation_memory": [{"role": "user", "content": query}]
        }
        
        # Run the LangGraph application
        result_state = self.app.invoke(initial_state)
        
        # Collect and merge tool outputs
        tool_outputs = result_state.get("tool_outputs", [])
        
        # Format the final answer
        final_answer = format_final_answer(query, tool_outputs)
                
        return {
            "query": query,
            "intent": result_state.get("parsed_intent", {}),
            "final_answer": final_answer,
            "raw_results": tool_outputs
        }
