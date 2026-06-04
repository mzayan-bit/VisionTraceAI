"""
VisionTraceAI — Agent Executor.

End-to-end wrapper for the LangGraph pipeline, orchestrating query ingestion,
state management, and result formatting.
"""

from typing import Any, Dict, List

from backend.agent.graph.state import AgentState
from backend.agent.graph.workflow import app


def format_final_answer(tool_outputs: List[Dict[str, Any]]) -> str:
    """Format a human-readable summary from accumulated tool outputs."""
    if not tool_outputs:
        return "No results found for your query."
        
    lines = []
    for output in tool_outputs:
        tool_name = output.get("tool", "unknown")
        result = output.get("result", [])
        
        if tool_name == "search_timeline":
            lines.append(f"• Found {len(result)} active tracks during the specified time period.")
            
        elif tool_name == "search_visuals":
            lines.append(f"• Identified {len(result)} visual matches in the database.")
            # Summarize top 3 matches
            for r in result[:3]:
                score = r.get("confidence_score", 0.0)
                cam = r.get("camera_id", "unknown")
                lines.append(f"  - Track {r.get('track_id')} (Camera: {cam}, Confidence: {score:.2f})")
                
        elif tool_name == "find_custom_object":
            lines.append(f"• Detected {len(result)} instances of the custom object.")
            for r in result[:3]:
                conf = r.get("confidence", 0.0)
                lines.append(f"  - {r.get('label')} at frame {r.get('frame_index')} (Confidence: {conf:.2f})")
                
    if not lines:
        return "Executed pipeline but received no matching records."
        
    return "\n".join(lines)


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
        final_answer = format_final_answer(tool_outputs)
                
        return {
            "query": query,
            "intent": result_state.get("parsed_intent", {}),
            "final_answer": final_answer,
            "raw_results": tool_outputs
        }
