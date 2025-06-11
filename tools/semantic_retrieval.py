from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from typing import List, Dict
from pydantic import BaseModel
from langchain.tools import tool


class SemnaticInput(BaseModel):
    query: str


@tool(args_schema=SemnaticInput)
def semantic_retrieval(
    query: str,
    chroma_dir: str = "/Users/mac/Desktop/Projects/Scripts/research_assistant/vector_store/Chroma_vs",
    model: str = "llama3.1:8b-instruct-q4_K_M",
) -> List[Dict]:
    """
    do semantic retrieval from a vector store of mesh and StyleGAN topics
    """
    embeddings = OllamaEmbeddings(model=model)
    vector_store = Chroma(persist_directory=chroma_dir, embedding_function=embeddings)
    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": 10}
    )
    full_results = retriever.invoke(query)

    return [{"retrieved_content": result.page_content} for result in full_results]
