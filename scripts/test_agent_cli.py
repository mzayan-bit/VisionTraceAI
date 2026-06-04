"""
VisionTraceAI — Agent CLI Validation.

Command-line interface to interact with the Vision Agent and validate
its real-world reasoning and routing capabilities.
"""

import os
import sys

# Ensure the root of the project is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agent.executor import VisionAgentExecutor


def main():
    print("═" * 60)
    print("🤖 VisionTraceAI — Agent Reasoning CLI")
    print("═" * 60)
    print("Type 'exit' or 'quit' to terminate.\n")
    print("Try these test queries:")
    print('  - "Who walked past gate wearing green shirt?"')
    print('  - "Who was in lobby after 8pm?"')
    print('  - "Find red extinguisher in building"\n')

    # Initialize the executor
    # Warning: The OPENAI_API_KEY must be set in the environment or `.env`
    try:
        executor = VisionAgentExecutor()
    except Exception as e:
        print(f"❌ Failed to initialize Agent Executor: {e}")
        print("Please make sure OPENAI_API_KEY is set in your environment.")
        return

    while True:
        try:
            query = input("\nQuery > ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
            
        if query.strip().lower() in ["exit", "quit"]:
            print("Exiting...")
            break
            
        if not query.strip():
            continue
            
        print("\n⏳ Processing...")
        
        try:
            # Execute pipeline
            result = executor.execute(query)
            
            # Extract formatted metrics
            intent = result.get("intent", {})
            selected_tool = intent.get("selected_tool", "None Selected")
            reasoning = intent.get("reasoning_trace", "No reasoning provided.")
            final_answer = result.get("final_answer", "")
            
            # Print output table
            print("\n" + "─" * 60)
            print(f"🎯 Selected Tool : {selected_tool}")
            print(f"🧠 Reasoning     : {reasoning}")
            print(f"✅ Final Output  :\n{final_answer}")
            print("─" * 60)
            
        except Exception as e:
            print(f"\n❌ Error executing query: {e}")


if __name__ == "__main__":
    main()
