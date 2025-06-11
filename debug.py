import os
import sys
from dotenv import load_dotenv
from langsmith import traceable
from agents.compiled_agents import ResearchAssistant


# =================== Input here ===================
testing_input = "what are the top 3 SOTA models in music generation"
# ==================================================


load_dotenv()
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
os.environ["LANGCHAIN_TRACING_V2"] = "true" if LANGSMITH_TRACING else "false"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "research_assistant")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
    "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"
)

if LANGSMITH_TRACING and not os.getenv("LANGSMITH_API_KEY"):
    print(
        "❌ LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is missing!",
        file=sys.stderr,
    )
    sys.exit(1)

print(
    "🟢 LangSmith tracing ENABLED"
    if LANGSMITH_TRACING
    else "⚪️ LangSmith tracing DISABLED"
)

# 2. Initial state to run your agent
initial_state = {
    "task": testing_input,
    "search_state": {
        "task": "",
        "node_name": "",
        "next_node": "",
        "content": [],
        "retrieved_content": [],
    },
    "deep_analysis_state": {
        "task": "",
        "node_name": "",
        "next_node": "",
        "paper_name": "",
        "paper_url": "",
        "meta_data": [],
        "full_paper": "",
        "content": [],
    },
    "improver_state": {
        "content": [],
        "node_name": "",
        "reflection": "",
        "final_output": "",
        "revision_number": 1,
        "max_revisions": 2,
        "count": 0,
    },
    "node_name": "",
    "next_node": "",
    "content": [],
    "retrieved_content": [],
}

# 3. Checkpointer config
config = {
    "configurable": {
        "thread_id": "1",
        "checkpoint_ns": "default",
        "checkpoint_id": "run1",
    }
}


# 4. LangSmith-compatible tracing wrapper
@traceable(name="ResearchAssistantAgent", tags=["multi-agent"])
def run_with_tracing(agent, state, config):
    return agent.main_agent.invoke(state, config=config)


# 5. Main
if __name__ == "__main__":
    assistant = ResearchAssistant()
    result = run_with_tracing(assistant, initial_state, config)
    print("\n✅ Final result:")
    print(result)
