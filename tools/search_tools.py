#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from typing import Optional, Dict, List, Literal
from langchain.tools import tool
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
import arxiv
from pydantic import BaseModel, Field
import json
import requests

# from pypdf import PdfReader
import uuid
import fitz
import logging


# ====================== Web Search Tool =======================
class SearchInput(BaseModel):
    query: str = Field(..., description="The search query.")
    max_results: Optional[int] = Field(3, description="Number of results to return.")
    include_raw_content: Optional[bool] = Field(
        False, description="Flag to return more content"
    )  # only works for paid plans.


@tool(args_schema=SearchInput)
def search_web(
    query: str, max_results: int = 3, include_raw_content: bool = False
) -> List[Dict]:
    """
    Search the web for real time information and return the top results.
    """
    try:
        load_dotenv()
        search = TavilySearchAPIWrapper(tavily_api_key=os.getenv("TAVILY_API_KEY"))
        results = search.results(
            query=query,
            max_results=max_results,
            include_raw_content=include_raw_content,
        )
        return results
    except Exception as e:
        return [{"ERROR": str(e)}]


# ===================== ArXiv Search Tool ======================
class ArxivSearchInput(BaseModel):
    query: str = Field(..., description="The research paper to search for in arxiv.")
    max_results: Optional[int] = Field(1, description="Number of PDF papers to return.")
    sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"] = Field(
        "relevance", description="The sorting criteria."
    )


@tool(args_schema=ArxivSearchInput)
def arxiv_search(
    query: str, max_results: int = 1, sort_by: str = "relevance"
) -> List[Dict]:
    """
    Search the arxiv for real time information and return the top paper metadata.
    """
    try:
        client = arxiv.Client()
        search_arxiv = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion(sort_by),
        )
        results = []
        for result in client.results(search_arxiv):
            results.append(
                {
                    "PDF_URL": result.pdf_url + ".pdf",
                    "Paper_ID": result.entry_id.split("/")[-1],
                    "Title": result.title,
                    "Publish Date": result.published.isoformat(),
                }
            )
        return results
    except Exception as e:
        return [{"ERROR": str(e)}]


# ================= load pdf for analysis ================
logger = logging.getLogger(__name__)


class LoadPDFInput(BaseModel):
    url: str = Field(..., description="The URL of the PDF to load.")


def _normalize_arxiv_pdf_url(url: str) -> str:
    # arxiv.org/abs/XXXX  →  arxiv.org/pdf/XXXX.pdf
    if "arxiv.org/abs/" in url:
        paper_id = url.rsplit("/", 1)[-1]
        return f"https://arxiv.org/pdf/{paper_id}.pdf"
    return url


@tool(args_schema=LoadPDFInput, return_direct=True)
def load_pdf(url: str) -> str:
    """
    Downloads a PDF from `url`, extracts all text using PyMuPDF (fitz),
    and returns the concatenated text. Cleans up temp file on exit.
    """
    # Generate a unique temp filename
    temp_filename = f"/tmp/{uuid.uuid4().hex}.pdf"
    url = _normalize_arxiv_pdf_url(url)
    try:
        # Download PDF
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(temp_filename, "wb") as f:
            f.write(resp.content)

        # Extract text with PyMuPDF
        doc = fitz.open(temp_filename)
        all_text = []
        for page in doc:
            text = page.get_text().strip()
            if text:
                all_text.append(text)
        doc.close()

        return "\n\n".join(all_text)

    except Exception as e:
        logger.error(f"Failed to load or parse PDF at {url}: {e}")
        return ""  # or raise, depending on how you want upstream to handle failures

    finally:
        # Cleanup temp file
        try:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        except OSError as cleanup_err:
            logger.warning(f"Could not delete temp file {temp_filename}: {cleanup_err}")
