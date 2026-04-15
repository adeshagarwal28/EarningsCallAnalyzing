import streamlit as st
from dotenv import load_dotenv
from streamlit_searchbox import st_searchbox
from transcript_fetcher import fetch_transcript
import os
import requests

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HEADERS = {"User-Agent": "EarningsCallInterpreter adesh.agarwal@outlook.com"}


@st.cache_data
def load_ticker_options():
    """Fetch the full SEC ticker list and return sorted 'TICKER — Company Name' strings."""
    response = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=HEADERS
    )
    response.raise_for_status()
    data = response.json()
    options = [
        f"{entry['ticker']} — {entry['title']}"
        for entry in data.values()
    ]
    return sorted(options)


st.title("Earnings Call Interpreter")

ticker_options = load_ticker_options()


def search_tickers(query: str):
    """Return matching ticker options for the searchbox."""
    if not query:
        return []
    query_lower = query.lower()
    return [opt for opt in ticker_options if query_lower in opt.lower()][:20]


selection = st_searchbox(search_tickers, placeholder="Search by ticker or company name...")

# Extract just the ticker from the selected option e.g. "AAPL — Apple Inc." -> "AAPL"
tickerInput = selection.split(" — ")[0] if selection else ""

searchBtn = st.button("Search")

if searchBtn:
    if not tickerInput:
        st.warning("Please select a company first.")
    else:
        with st.spinner(f"Fetching transcript for {tickerInput}..."):
            result = fetch_transcript(tickerInput)

        if result is None:
            st.error(f"No earnings call transcript found for **{tickerInput}**. This company may not file transcripts with the SEC.")
        else:
            st.success(f"Transcript found for **{tickerInput}**")
            st.info("Analysis coming next...")
            # Store transcript in session state for the analysis step
            st.session_state["transcript"] = result["transcript"]
            st.session_state["ticker"] = tickerInput
