from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict, Optional
from main import RunResearchAssistant
from agents import states


app = FastAPI()
runner = RunResearchAssistant()


class TaskRequest(BaseModel):
    task: str
    thread_id: Optional[str] = None


class AgentResponse(BaseModel):
    final_output: Any
    reflection: str
    thread_id: str


@app.post("/run", response_model=AgentResponse)
async def run_agent(request: TaskRequest):
    # data = await request.json() will be deprecated
    input_text = request.task
    thread_id = request.thread_id

    if thread_id:
        runner.thread_id = thread_id
        runner.config = {"configurable": {"thread_id": thread_id}}
        result = runner.existing_thread(input_text)
    else:
        result = runner.new_thread(input_text)

    return {
        "final_output": result["improver_state"]["final_output"],
        "reflection": result["improver_state"]["reflection"],
        "thread_id": runner.thread_id,
    }


@app.get("/state/{thread_id}")
async def get_state(thread_id: str):
    try:
        snapshot = runner.get_current_state(thread_id)
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "✅ ✅ ✅"}


# Optionally: metadata endpoint for debugging
# @app.get("/metadata")
# def metadata():
#     return {
#         "model": "llama3.1:8b-instruct-q4_K_M",
#         "pipeline": [
#             "main_router",
#             "search_agent or deep_analysis_agent",
#             "improver_agent",
#         ],
#     }
