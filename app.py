import streamlit as st
from arxiv import Client, Result
from langchain_groq import ChatGroq
from langchain_community.utilities import (
    ArxivAPIWrapper,
    DuckDuckGoSearchAPIWrapper,
    WikipediaAPIWrapper,
)
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun 
from langchain.agents import create_agent
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_core.callbacks import CallbackManagerForToolRun
import os 
from typing import Dict, Iterator, List, Optional
from dotenv import load_dotenv
from requests.exceptions import RequestException


class ClientBasedArxivAPIWrapper(ArxivAPIWrapper):
    """Use the current arxiv Client API to fetch search results."""

    def _fetch_results(self, query: str) -> Iterator[Result]:
        if self.is_arxiv_identifier(query):
            search = self.arxiv_search(
                id_list=query.split(), max_results=self.top_k_results
            )
        else:
            search = self.arxiv_search(
                query[: self.ARXIV_MAX_QUERY_LENGTH],
                max_results=self.top_k_results,
            )
        return Client().results(search)


class ResilientDuckDuckGoSearchAPIWrapper(DuckDuckGoSearchAPIWrapper):
    """Try alternate DDGS providers when a search provider fails."""

    def _ddgs_text(
        self, query: str, max_results: Optional[int] = None
    ) -> List[Dict[str, str]]:
        from ddgs import DDGS
        from ddgs.exceptions import DDGSException

        errors = []
        for backend in ("duckduckgo", "yahoo", "google", "grokipedia", "wikipedia"):
            try:
                with DDGS() as ddgs:
                    results = ddgs.text(
                        query,
                        region=self.region,
                        safesearch=self.safesearch,
                        timelimit=self.time,
                        max_results=max_results or self.max_results,
                        backend=backend,
                    )
                if results:
                    return results
                errors.append(f"{backend}: no results")
            except DDGSException as exc:
                errors.append(f"{backend}: {exc}")

        raise DDGSException(
            "All configured DDGS search providers failed: " + "; ".join(errors)
        )


class ResilientDuckDuckGoSearchRun(DuckDuckGoSearchRun):
    """Return provider failures to the agent without aborting the chat."""

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        from ddgs.exceptions import DDGSException

        try:
            return super()._run(query, run_manager=run_manager)
        except DDGSException as exc:
            return f"Search unavailable: {exc}"


class ResilientWikipediaQueryRun(WikipediaQueryRun):
    """Keep Wikipedia API response errors from aborting the agent run."""

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            return super()._run(query, run_manager=run_manager)
        except RequestException as exc:
            return (
                "Wikipedia search is temporarily unavailable because its API "
                f"returned an invalid or failed response ({type(exc).__name__}). "
                "Try the web search tool instead."
            )


load_dotenv()
#os.environ['HF_TOKEN']=os.getenv("HF_TOKEN")



#initialization of tools 
api_wrapper_wikipedia = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=250)
wiki=ResilientWikipediaQueryRun(api_wrapper=api_wrapper_wikipedia)
api_wrapper_arxiv = ClientBasedArxivAPIWrapper(top_k_results=1, doc_content_chars_max=250)
arxiv=ArxivQueryRun(api_wrapper=api_wrapper_arxiv)
duckduckgo = ResilientDuckDuckGoSearchRun(
    name="Search",
    api_wrapper=ResilientDuckDuckGoSearchAPIWrapper(region="us-en", time=None),
)
st.title("Langchain search engine")

#sidebar 
st.sidebar.title("settings")
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "I am a helpful chatbot who can search the web and answer questions. How can i help you?"}
          
           ] 

for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])


if prompt := st.chat_input(placeholder="Ask me anything about arxiv, wikipedia or the web"):
    st.session_state.messages.append({"role": "user", "content": prompt}) #we are appending to message history
    st.chat_message("user").write(prompt)
    
    llm=ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model="openai/gpt-oss-120b", streaming=True)
    tools=[wiki, arxiv, duckduckgo]

    search_agent = create_agent(model=llm, tools=tools)

    with st.chat_message("assistant"): 
        st_cvb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=True)
        result = search_agent.invoke(
            {"messages": st.session_state.messages},
            config={"callbacks": [st_cvb]},
        )
        response = result["messages"][-1].content
        st.session_state.messages.append({"role": "assistant", "content": response})
        #print(result)
        st.write(response)