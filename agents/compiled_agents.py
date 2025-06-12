import logging
from langchain_ollama import ChatOllama
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
    ChatMessage,
    AnyMessage,
)
from langgraph.graph import StateGraph, END
from langgraph.types import Command

# from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from tools.search_tools import arxiv_search, search_web, load_pdf
from tools.semantic_retrieval import semantic_retrieval
import utils.prompts as prompts
from agents import states

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ====================== Search/Retrieval Agent =======================
class SearchAgent:  # subGraph
    def __init__(self, llm):
        self.llm = llm  # the llm is defined once in the main graph.
        self.web_search_function = search_web
        self.semantic_retrieval_function = semantic_retrieval
        # tools = [self.web_search, self.semantic_retrieval]

        build_search = StateGraph(states.SearchState)
        build_search.add_node("router", self.search_router)
        build_search.add_node("web_search", self.web_search_node)
        build_search.add_node("semantic_retrieval", self.semantic_retrieval_node)
        build_search.add_node("generator", self.generator_node)

        build_search.set_entry_point("router")
        build_search.add_conditional_edges(
            "router",
            self.decision,
            {
                "web_search": "web_search",
                "vector_store": "semantic_retrieval",
            },
        )
        # build_search.add_edge("router", "web_search") redundant
        # build_search.add_edge("router", "retrieval")  redundant
        build_search.add_edge("web_search", "generator")
        build_search.add_edge("semantic_retrieval", "generator")
        build_search.add_edge("generator", END)

        self.search_agent = build_search.compile()

    def search_router(self, state: states.SearchState):
        messages = [
            SystemMessage(content=prompts.SEARCH_ROUTER_PROMPT),
            HumanMessage(content=state["task"]),
        ]
        response = self.llm.with_structured_output(states.SearchRouter).invoke(messages)

        return {
            "node_name": "router",
            "next_node": response.next_node,
            "task": state.get("task", ""),
        }

    def decision(self, state: states.SearchState):
        return state.get("next_node", "web_search")

    def web_search_node(self, state: states.SearchState):
        messages = [
            SystemMessage(content=prompts.SEARCH_PROMPT),
            HumanMessage(content=state.get("task", "")),
        ]
        search_queries = self.llm.with_structured_output(states.Query).invoke(messages)

        search_results = []
        for q in search_queries.query:
            response = self.web_search_function.invoke(
                q, max_results=search_queries.max_results
            )
            for item in response:
                search_results.append(
                    {
                        "type": "web_search",
                        "title": item["title"],
                        "url": item["url"],
                        "content": item["content"],
                    }
                )

        return {
            "node_name": "web_search",
            "retrieved_content": search_results,
            "task": state.get("task", ""),
        }

    def semantic_retrieval_node(self, state: states.SearchState):
        messages = [
            SystemMessage(content=prompts.SEARCH_PROMPT),
            HumanMessage(content=state.get("task", "")),
        ]
        queries = self.llm.with_structured_output(states.Query).invoke(messages)

        retrieved_content = []
        for q in queries.query:
            response = self.semantic_retrieval_function.invoke(
                q, max_results=queries.max_results
            )
            for item in response:
                retrieved_content.append(
                    {
                        "type": "semantic_retrieval",
                        "content": item["retrieved_content"],
                    }
                )

        return {
            "node_name": "semantic_retrieval",
            "retrieved_content": retrieved_content,
            "task": state.get("task", ""),
        }

    def generator_node(self, state: states.SearchState):
        formatted_retrieved_content = []
        for item in state["retrieved_content"]:
            if item["type"] == "web_search":
                formatted = f'title: {item["title"]}\nurl: {item["url"]}\ncontent: {item["content"]}'
            else:  # semantic
                formatted = f'content: {item["content"]}'
            formatted_retrieved_content.append(formatted)

        formatted_content_string = "\n\n".join(formatted_retrieved_content)

        messages = [
            SystemMessage(content=prompts.GENERATOR_PROMPT),
            HumanMessage(
                content=f'{state.get("task", "")}\n\n{formatted_content_string}'
            ),
        ]
        response = self.llm.invoke(messages)

        return {
            "node_name": "generator",
            "content": [response.content],
            "task": state.get("task", ""),
            "retrieved_content": state.get("retrieved_content", []),
        }


# ====================== Deep Analysis Agent ========================
class DeepAnalysisAgent:
    def __init__(self, llm):
        self.llm = llm
        self.search_arxiv = arxiv_search
        self.load_pdf_function = load_pdf

        build_analysis = StateGraph(states.DeepAnalysisState)
        build_analysis.add_node("paper_metadata", self.paper_metadata_node)
        build_analysis.add_node("fetch_url", self.fetch_url_node)
        build_analysis.add_node("analyze", self.analyze_node)

        build_analysis.set_entry_point("paper_metadata")

        build_analysis.add_conditional_edges(
            "paper_metadata",
            self.decision,
            {"fetch_url": "fetch_url", "analyze": "analyze"},
        )
        # build_analysis.add_edge("paper_metadata", "fetch_url")
        # build_analysis.add_edge("paper_metadata", "analyze")   #redundant
        build_analysis.add_edge("analyze", END)

        self.deep_analysis_agent = build_analysis.compile()

    def decision(self, state: states.DeepAnalysisState):
        if state.get("paper_url", ""):
            return "analyze"
        else:
            return "fetch_url"

    def paper_metadata_node(self, state: states.DeepAnalysisState) -> Command:
        messages = [
            SystemMessage(content=prompts.PAPER_FETCHING_PROMPT),
            HumanMessage(content=state.get("task", "")),
        ]
        response = self.llm.with_structured_output(states.MetaData).invoke(messages)

        next_node = "analyze" if response.paper_url else "fetch_url"
        return Command(
            goto=next_node,
            update={
                "node_name": "paper_metadata",
                "paper_name": response.paper_name or "",
                "paper_url": response.paper_url or "",
                "meta_data": [{}],
                "task": state.get("task", ""),
            },
        )

    def fetch_url_node(self, state: states.DeepAnalysisState):
        query = state.get("paper_name", "") or state.get("task", "")
        url = self.search_arxiv.invoke(query, max_results=1)
        return {
            "node_name": "fetch_url",
            "paper_url": url[0]["PDF_URL"],
            "paper_name": url[0]["Title"],
            "meta_data": [
                {"paper_id": url[0]["Paper_ID"]},
                {"publish_data": url[0]["Publish Date"]},
            ],
            "task": state.get("task", ""),
        }

    def analyze_node(self, state: states.DeepAnalysisState):
        try:
            pdf = self.load_pdf_function.invoke(state.get("paper_url", ""))
        except Exception as e:
            logger.warning(f"PDF load failed, continuing without full paper: {e}")
            pdf = ""

        messages = [
            SystemMessage(content=prompts.DEEP_ANALYSIS_PROMPT),
            HumanMessage(content=f"{state.get('task','')} {pdf}"),
        ]
        response = self.llm.invoke(messages)
        return {
            "node_name": "analyze",
            "full_paper": pdf,
            "content": [str(response.content)],
            "task": state.get("task", ""),
        }


# ==================== Generator/Reflect Agent ========================
class ImproverAgent:
    def __init__(self, llm):
        self.llm = llm

        build_improver = StateGraph(states.ImproverState)
        build_improver.add_node("reflect", self.reflect_node)
        build_improver.add_node("improver", self.improver_node)
        build_improver.add_node("final", self.final_output_node)

        build_improver.set_entry_point("reflect")
        build_improver.add_conditional_edges(
            "improver",
            self.decision,
            {"reflect": "reflect", "final": "final"},
        )

        build_improver.add_edge("reflect", "improver")
        build_improver.add_edge("final", END)

        self.improver_agent = build_improver.compile()

    def reflect_node(self, state: states.ImproverState):
        messages = [
            SystemMessage(content=prompts.REFLECTION_PROMPT),
            HumanMessage(content="\n".join(state.get("content", ""))),
        ]
        response = self.llm.invoke(messages)
        return {
            "node_name": "reflect",
            "reflection": str(response.content),
            "content": state.get("content", ""),
            "revision_number": state.get("revision_number", 1) + 1,
            "count": 1,
            "task": state.get("task", ""),
        }

    def improver_node(self, state: states.ImproverState):
        messages = [
            SystemMessage(content=prompts.IMPROVER_PROMPT),
            HumanMessage(
                content=f'{state.get("task", "")}\n\n{state.get('content',[])}\n\n here is the critique: {state.get("reflection", "")}'
            ),
        ]
        response = self.llm.invoke(messages)

        return {
            "content": [str(response.content)],
            "node_name": "improver",
            "revision_number": state.get("revision_number", 1) + 1,
            "count": 1,
        }

    def final_output_node(self, state: states.ImproverState):
        output = state["content"]

        return {
            "node_name": "final",
            "final_output": output,
            "reflection": state.get("reflection", ""),
        }

    def decision(self, state: states.ImproverState):
        return (
            "final"
            if state.get("revision_number", 1) > state.get("max_revisions", 2)
            else "improver"
        )


# ========================== Analysis Agent ==========================
class ResearchAssistant:
    def __init__(self):
        self.llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M")

        self.search_agent = SearchAgent(self.llm).search_agent
        self.deep_analysis_agent = DeepAnalysisAgent(self.llm).deep_analysis_agent
        self.improver_agent = ImproverAgent(self.llm).improver_agent

        main_builder = StateGraph(states.MainState)
        main_builder.add_node("main_router", self.main_router_node)
        main_builder.add_node("search_agent", self.search_agent_node)
        main_builder.add_node("deep_analysis_agent", self.deep_analysis_agent_node)
        main_builder.add_node("improver_agent", self.improver_agent_node)
        main_builder.add_node("chat", self.chat_node)

        main_builder.set_entry_point("main_router")
        main_builder.add_conditional_edges(
            "main_router",
            self.decision,
            {
                "search_agent": "search_agent",
                "deep_analysis_agent": "deep_analysis_agent",
                "chat": "chat",
            },
        )
        # main_builder.add_edge("main_router", "search_agent")
        # main_builder.add_edge("main_router", "deep_analysis_agent") #redundant
        main_builder.add_edge("search_agent", "improver_agent")
        main_builder.add_edge("deep_analysis_agent", "improver_agent")
        main_builder.add_edge("chat", END)
        main_builder.add_edge("improver_agent", END)

        conn = sqlite3.connect(
            "checkpoints/checkpoints.sqlite", check_same_thread=False
        )
        memory = SqliteSaver(conn)
        compile_kwargs = {"checkpointer": memory}

        self.main_agent = main_builder.compile(**compile_kwargs)

    def main_router_node(self, state: states.MainState):
        messages = [
            SystemMessage(content=prompts.MAIN_ROUTER_PROMPT),
            HumanMessage(
                content=f'{state.get("task", "")}\n\nhere is the previous content: {state.get('content',[])}'
            ),
        ]
        response = self.llm.with_structured_output(states.MainRouter).invoke(messages)
        return {
            "node_name": "main_router",
            "next_node": response.next_node,
            "task": state.get("task", ""),
        }

    def search_agent_node(self, state: states.MainState):
        # task = state.get("task", "")
        search_state = state["search_state"]
        search_state["task"] = state.get("task", "")
        output = self.search_agent.invoke(search_state)

        return {
            "search_state": output,
            "retrieved_content": output.get("retrieved_content", []),
            "content": output.get("content", []),
            "task": state.get("task", ""),
        }

    def deep_analysis_agent_node(self, state: states.MainState):
        # task = state.get("task", "")
        deep_analysis_state = state["deep_analysis_state"]
        deep_analysis_state["task"] = state.get("task", "")
        output = self.deep_analysis_agent.invoke(deep_analysis_state)

        return {
            "deep_analysis_state": output,
            "content": output.get("content", []),
            "task": state.get("task", ""),
        }

    def improver_agent_node(self, state: states.MainState):
        improver_state = state["improver_state"]
        improver_state["content"] = state["content"]
        improver_state["task"] = state.get("task", "")

        output = self.improver_agent.invoke(improver_state)
        final_output = output.get("final_output", "")

        return {
            "improver_state": output,
            "final_output": final_output,
            "reflection": output.get("reflection", ""),
            "task": state.get("task", ""),
        }

    def chat_node(self, state: states.MainState):
        messages = [
            SystemMessage(content=prompts.CHAT_PROMPT),
            HumanMessage(
                content=f'{state.get("task", "")}\n\n{state.get("content", "")}\n\n{state.get('retrieved_content')}'
            ),
        ]
        response = self.llm.invoke(messages)
        state["improver_state"]["final_output"] = str(response.content)

        return {
            "content": [str(response.content)],
            "node_name": "chat",
            "task": state.get("task", ""),
        }

    def decision(self, state: states.MainState):
        next_node = state.get("next_node", "")
        if next_node not in ["search_agent", "deep_analysis_agent", "chat"]:
            return "chat"
        return next_node


#########################################################################
