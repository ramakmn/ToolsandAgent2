SearchAgent — AI Research Assistant
SearchAgent is a Streamlit-based research assistant that uses a Groq-hosted language model and LangChain tools to answer questions using web search, Wikipedia, and arXiv. Rather than relying only on the model's built-in knowledge, the agent can select a relevant source, retrieve information, and use those results to construct a response.
Features
- Multi-source research: Search the web, look up Wikipedia entries, and find scholarly papers on arXiv.
- Agent-driven tool selection: LangChain's create_agent lets the model decide when to call the available tools.
- Interactive chat: Streamlit provides a conversational interface and keeps messages in session state.
- Visible execution steps: A Streamlit callback displays agent/tool activity as it runs.
- Resilient search: If a DuckDuckGo search provider fails, the app attempts alternative backends. Search and Wikipedia failures are returned to the agent as useful messages rather than necessarily ending the conversation.
Tech stack
Component	Technology
User interface	Streamlit
Agent orchestration	LangChain (create_agent)
Language model	openai/gpt-oss-120b via Groq (langchain_groq)
Web search	DuckDuckGo / DDGS with fallback providers
Reference search	Wikipedia API
Academic search	arXiv API
Configuration	Python environment variables with python-dotenv


How it works
1. A user enters a question in the Streamlit chat interface.
2. The app creates a Groq-backed chat model and a LangChain agent with three tools: Wikipedia, arXiv, and web search.
3. The agent chooses tools as needed and receives the retrieved results.
4. The model generates an answer, which is displayed in the chat interface.
5. User and assistant messages are retained for the current Streamlit session.
User question
     |
     v
Streamlit chat interface
     |
     v
LangChain agent <--> Groq-hosted LLM
     |
     +--> Wikipedia
     +--> arXiv
     +--> Web search (DDGS with provider fallbacks)
     |
     v
Response + visible tool activity
Getting started
Prerequisites
- Python 3.10+ (a recent Python 3.11 version is a good choice)
- A Groq API key
- Internet access for the model and search tools
1. Clone the repository
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
cd <YOUR_REPOSITORY>
2. Create and activate a virtual environment
Windows (PowerShell):
py -m venv .venv
.\.venv\Scripts\Activate.ps1
macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
Note: The application also directly uses python-dotenv, requests, and ddgs. Ensure those packages are included in requirements.txt (or install them with pip install python-dotenv requests ddgs).

4. Configure environment variables
Create a .env file in the project root:
GROQ_API_KEY=your_groq_api_key_here
# Optional; not used by the current app.py flow:
# HF_TOKEN=your_hugging_face_token_here
Never commit .env or actual API tokens. Add them to .gitignore and use .env.example for shareable sample configuration. If a key was previously shared or committed, revoke/rotate it and create a new one.
5. Run the application
streamlit run app.py
Open the local address displayed in your terminal (typically http://localhost:8501).
Example prompts
- "What are the main differences between retrieval-augmented generation and fine-tuning?"
- "Find recent arXiv research about multi-agent systems."
- "Explain the basics of quantum computing using Wikipedia as a starting point."
- "Search for information about current developments in AI infrastructure."
Answers depend on tool availability, returned sources, and the model's response. Check original sources for consequential claims.
Reliability and design decisions
arXiv compatibility: ClientBasedArxivAPIWrapper uses the current arxiv.Client().results(...) flow for both search terms and arXiv identifiers.

Web-search fallback: ResilientDuckDuckGoSearchAPIWrapper tries the configured DDGS backends in sequence and returns the first nonempty result set. If all backends fail, ResilientDuckDuckGoSearchRun catches the provider exception and sends a readable error to the agent.

Wikipedia failure handling: ResilientWikipediaQueryRun catches request-related errors and returns a fallback message suggesting web search.

Conversation state: Chat history is stored in st.session_state, so it survives Streamlit reruns within the current session. It is not written to a database.
Project structure
.
├── app.py               # Streamlit UI, LangChain agent, search integrations
├── requirements.txt     # Python dependencies
├── .env.example         # Safe example environment variables (recommended)
├── .gitignore           # Excludes secrets and local environments (recommended)
└── README.md            # Project documentation
Current limitations and next steps
- Search results may be unavailable because of network conditions, provider limits, or API changes.
- The application does not currently enforce citations in the final answer or verify claims independently.
- Chat history is session-scoped and is not persisted between sessions.
- The Groq model and agent are initialized when a new prompt is submitted; caching or reusing resources could improve efficiency.
- Potential enhancements include source links in answers, automated tests for fallback behavior, configurable model selection, and more structured error reporting.
Security
Store credentials in environment variables, keep .env out of Git, and rotate any credential that has been exposed. Do not log, screenshot, or include tokens in issues or commits.
