from typing import List, Dict, Literal, Annotated, Optional, TypedDict
from pydantic import BaseModel, Field
import operator


# ======================= Validation =======================


class MainRouter(BaseModel):
    next_node: Literal["search_agent", "deep_analysis_agent", "chat"] = Field(
        None, description="the next route to take based on the task."
    )


class SearchRouter(BaseModel):
    next_node: Literal["web_search", "vector_store"]


class Query(BaseModel):
    query: List[str]
    max_results: int = 3


class MetaData(BaseModel):
    paper_url: Optional[str]
    paper_name: Optional[str]


# ======================== States ==========================


class SearchState(TypedDict):
    task: str
    node_name: str
    next_node: str
    content: List[str]
    retrieved_content: List[Dict]


class DeepAnalysisState(TypedDict):
    task: str
    node_name: str
    next_node: str
    paper_name: str
    paper_url: str
    meta_data: List[Dict]
    full_paper: str
    content: List[str]


class ImproverState(TypedDict):
    content: List[str]
    task: str
    node_name: str
    reflection: str
    final_output: str
    revision_number: int
    max_revisions: int
    count: Annotated[int, operator.add]


class MainState(TypedDict):
    task: str
    search_state: SearchState
    deep_analysis_state: DeepAnalysisState
    improver_state: ImproverState
    node_name: str
    next_node: str
    content: List[str]
    retrieved_content: List[Dict]


def _initialize_state(task: str) -> MainState:
    return {
        "task": task,
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
