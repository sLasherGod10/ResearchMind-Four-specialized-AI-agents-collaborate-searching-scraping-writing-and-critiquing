# ResearchMind

A Streamlit-based research assistant that uses Gemini API-backed agents to search, scrape, write, and critique research output.

## What it does

- Accepts a research topic via Streamlit UI
- Uses a search agent to gather recent web results
- Uses a reader agent to scrape and summarize a selected URL
- Uses Gemini to draft a polished research report
- Uses Gemini to critique the generated report

## Requirements

- Python 3.13
- `pip` package manager

## Install dependencies

```bash
python3.13.exe -m pip install -r requirements.txt
```

## Environment

Create a `.env` file in the project root with your Gemini key:

```text
GEMINI_API_KEY=your_gemini_api_key_here
```

> Do not commit `.env` to GitHub.

## Run the app

```bash
python3.13.exe -m streamlit run app.py
```

Then open the URL shown in the terminal, typically:

- `http://localhost:8501`

## Configuration

- `app.py` is the Streamlit frontend
- `agents.py` contains Gemini agent wrappers and prompt templates
- `tools.py` contains the search and scraping helpers

## Notes

- The app uses Gemini model `gemini-flash-lite-latest` by default
- If you hit quota or rate-limit errors, check your Gemini account billing and plan
- The repository ignores `.env` and Python cache files
