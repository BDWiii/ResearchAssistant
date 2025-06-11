# Research Assistant

A powerful AI-powered research assistant that helps analyze and understand academic papers. This tool can process research papers, provide detailed explanations, and generate comprehensive analyses.

## Features

- Paper Analysis: Deep analysis of academic papers with detailed explanations
- Web Search Integration: Ability to search and retrieve relevant information
- API Interface: RESTful API for easy integration
- State Management: Maintains conversation context and analysis state
- Multiple Agent System: Uses specialized agents for different aspects of research analysis

## Prerequisites

- Python 3.8+
- FastAPI
- Pydantic
- Other dependencies (to be listed in requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/research-assistant.git
cd research-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the API Server

Start the FastAPI server:
```bash
uvicorn app:app --reload
```

The server will start at `http://localhost:8000`

### API Endpoints

1. **Run Research Analysis**
   - Endpoint: `POST /run`
   - Request Body:
     ```json
     {
         "task": "Your research question or paper URL"
     }
     ```
   - Response:
     ```json
     {
         "final_output": "Analysis results",
         "reflection": "Agent's reflection on the analysis"
     }
     ```

2. **Health Check**
   - Endpoint: `GET /health`
   - Returns server status
