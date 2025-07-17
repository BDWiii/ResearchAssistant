
**Research Assistant** is a multi-agent AI system designed to revolutionize the way you analyze, understand, and interact with academic research. Harnessing the power of advanced language models and seamless agent collaboration, this platform delivers deep, actionable insights from scientific literature and live web data—all through a clean, robust, and extensible API.

![Research Graph](images/Research%20Graph.png)
 ---
## 🚀 Why Research Assistant?

- **Multi-Agent Intelligence:**  
  Orchestrates a suite of specialized agents—each an expert in search, deep analysis, synthesis, and reflection—working in concert to tackle complex research tasks.
- **Seamless Cooperation & State Management:**  
  Features a persistent, thread-based state system that enables context-rich, multi-turn conversations and uninterrupted analytical workflows.
- **Live & Deep Analysis:**  
  Effortlessly switches between broad web-scale search and in-depth, document-level analysis, adapting to your research needs in real time.
- **API-First, Developer-Friendly:**  
  Built on FastAPI, with clear endpoints and modern standards for easy integration into your own tools, dashboards, or pipelines.
- **Extensible & Production-Ready:**  
  Modular design, Docker support, and robust checkpointing make it suitable for both rapid prototyping and enterprise deployment.

---

## 🧠 Core Features

- **Multi-Agent System:**  
  - **Search Agent:** Retrieves and synthesizes information from the web and vector stores.
  - **Deep Analysis Agent:** Performs comprehensive, document-level analysis of academic papers.
  - **Improver/Reflector Agent:** Iteratively refines and critiques outputs for clarity and depth.
  - **Main Orchestrator:** Routes tasks and manages agent cooperation for optimal results.

- **Persistent State & Threading:**  
  - Every research session is tracked via a unique `thread_id`, ensuring continuity and context retention across multiple interactions.

- **Rich API Endpoints:**  
  - **/run:** Launch a new research session or continue an existing one.
  - **/state/{thread_id}:** Retrieve the current state of any session.
  - **/health:** Instantly check system status.

---

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/BDWiii/ResearchAssistant
   cd research-assistant
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. *(Optional)* **Run in Docker:**
   ```bash
   docker build -t research-assistant .
   docker run -p 8000:8000 research-assistant
   ```

---

## ⚡ Usage

### Start the API Server

```bash
uvicorn app:app --reload
```
The server will be available at [http://localhost:8000](http://localhost:8000).

---

### API Endpoints

#### 1. **Run Research Analysis**

- **Endpoint:** `POST /run`
- **Description:** Start a new research session or continue an existing one by providing a `thread_id`.
- **Request Body:**
  ```json
  {
    "task": "Your research question or paper URL",
    "thread_id": null
  }
  ```
- **Response:**
  ```json
  {
    "final_output": "Analysis results",
    "reflection": "Agent's reflection on the analysis",
    "thread_id": "unique-session-id"
  }
  ```

#### 2. **Get Session State**

- **Endpoint:** `GET /state/{thread_id}`
- **Description:** Retrieve the current state and context of a research session.

#### 3. **Health Check**

- **Endpoint:** `GET /health`
- **Description:** Returns server status.

---

## 🏗️ Architecture Overview

At its core, Research Assistant leverages a **stateful, multi-agent graph** architecture, where each agent is responsible for a distinct aspect of the research workflow. The system’s orchestrator ensures seamless transitions and data flow between agents, while robust checkpointing guarantees that every session is recoverable and persistent.

---

## 🌟 Get Involved

- **Extensible:** Add new agents, tools, or data sources with minimal effort.
- **Customizable:** Tailor prompts, agent logic, and state handling to your domain.
- **Open Source:** Contributions and feedback are welcome!

---

## 📄 License

This project is licensed under the terms of the [LICENSE](LICENSE) file.

---

**Empower your research with intelligent, collaborative AI.**  
*Research Assistant: Where multi-agent synergy meets scientific discovery.*
