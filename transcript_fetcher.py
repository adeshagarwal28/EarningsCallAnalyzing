import requests
from typing import Optional

HEADERS = {"User-Agent": "EarningsCallInterpreter adesh.agarwal@outlook.com"}


def get_cik(ticker: str) -> Optional[str]:
    """Convert a ticker symbol to a zero-padded 10-digit SEC CIK number."""
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    data = response.json()
    ticker_upper = ticker.upper()

    for entry in data.values():
        if entry["ticker"] == ticker_upper:
            return str(entry["cik_str"]).zfill(10)

    return None


def get_latest_8k_filings(cik: str) -> list:
    """Return a list of recent 8-K filing accession numbers for a given CIK."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    data = response.json()
    filings = data.get("filings", {}).get("recent", {})

    forms = filings.get("form", [])
    accession_numbers = filings.get("accessionNumber", [])

    # Return accession numbers for 8-K filings only
    return [
        accession_numbers[i]
        for i, form in enumerate(forms)
        if form == "8-K"
    ]


def get_filing_exhibits(cik: str, accession_number: str) -> list:
    """Return a list of exhibit files from a specific 8-K filing index."""
    accession_clean = accession_number.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/{accession_number}-index.json"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("documents", [])


def is_transcript_exhibit(document: dict) -> bool:
    """Heuristic to detect if an exhibit is likely an earnings call transcript."""
    description = document.get("description", "").lower()
    filename = document.get("documentUrl", "").lower()

    transcript_keywords = ["transcript", "earnings call", "conference call"]
    return any(kw in description or kw in filename for kw in transcript_keywords)


def fetch_exhibit_text(document_url: str) -> str:
    """Download and return the plain text of an exhibit."""
    base_url = "https://www.sec.gov"
    full_url = base_url + document_url if document_url.startswith("/") else document_url

    response = requests.get(full_url, headers=HEADERS)
    response.raise_for_status()
    return response.text


def fetch_transcript(ticker: str) -> Optional[dict]:
    """
    Main function. Given a ticker, returns a dict with:
      - ticker
      - company (name from SEC)
      - transcript (full text)
    Returns None if no transcript could be found.
    """
    # Step 1: ticker -> CIK
    cik = get_cik(ticker)
    if not cik:
        return None

    # Step 2: get recent 8-K accession numbers
    accession_numbers = get_latest_8k_filings(cik)

    # Step 3: search through recent 8-Ks for a transcript exhibit
    for accession_number in accession_numbers[:20]:  # check up to 20 recent 8-Ks
        exhibits = get_filing_exhibits(cik, accession_number)
        for doc in exhibits:
            if is_transcript_exhibit(doc):
                transcript_text = fetch_exhibit_text(doc.get("documentUrl", ""))
                return {
                    "ticker": ticker.upper(),
                    "transcript": transcript_text,
                }

    return None
