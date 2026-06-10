import os
import re
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted
from dotenv import load_dotenv
from tools import web_search, scrape_url

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not gemini_key:
    raise ValueError("Please set GEMINI_API_KEY in your .env file")
genai.configure(api_key=gemini_key)

GEMINI_MODEL = os.getenv("LLM_MODEL", "gemini-flash-lite-latest")


def _extract_response_text(response):
    if response is None:
        return ""
    text = getattr(response, "text", None)
    if text:
        return str(text).strip()
    candidates = getattr(response, "candidates", None)
    if candidates:
        first = candidates[0]
        return str(getattr(first, "content", getattr(first, "text", ""))).strip()
    return ""


def gemini_chat(prompt: str, model_name: str | None = None) -> str:
    model_name = model_name or GEMINI_MODEL
    model = genai.GenerativeModel(model_name=model_name)
    session = model.start_chat()
    try:
        response = session.send_message(prompt)
        return _extract_response_text(response)
    except ResourceExhausted as exc:
        return f"[Gemini quota exceeded] {exc.message if hasattr(exc, 'message') else str(exc)}"
    except GoogleAPICallError as exc:
        return f"[Gemini API error] {exc.message if hasattr(exc, 'message') else str(exc)}"
    except Exception as exc:
        return f"[Gemini error] {str(exc)}"


def _get_last_message_content(inputs):
    if not isinstance(inputs, dict):
        return ""
    messages = inputs.get("messages")
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, tuple) and len(last) >= 2:
        return last[1]
    if isinstance(last, dict):
        return last.get("content", "")
    return ""


def _find_first_url(text: str) -> str | None:
    matches = re.findall(r"https?://[^\s]+", text)
    return matches[0] if matches else None


class GeminiAgent:
    def __init__(self, invoke_fn):
        self.invoke = invoke_fn


def build_search_agent():
    def invoke(inputs):
        query = _get_last_message_content(inputs)
        if not query:
            query = "Find recent, reliable, and detailed information."
        search_results = web_search(query)
        return {"messages": [{"role": "assistant", "content": search_results}]}
    return GeminiAgent(invoke)


def build_reader_agent():
    def invoke(inputs):
        prompt_content = _get_last_message_content(inputs)
        url = _find_first_url(prompt_content)
        if not url:
            url = _find_first_url(prompt_content)
        if not url:
            return {"messages": [{"role": "assistant", "content": "No URL found to scrape."}]}
        scraped = scrape_url(url)
        return {"messages": [{"role": "assistant", "content": f"Scraped URL: {url}\n\n{scraped}"}]}
    return GeminiAgent(invoke)


class GeminiTextChain:
    def __init__(self, template: str):
        self.template = template

    def invoke(self, inputs):
        prompt = self.template.format(**inputs)
        return gemini_chat(prompt)


writer_prompt_template = (
    "You are an expert research writer. Write clear, structured, and insightful reports.\n\n"
    "Write a detailed research report on the topic below.\n\n"
    "Topic: {topic}\n\n"
    "Research Gathered:\n{research}\n\n"
    "Structure the report as:\n"
    "- Introduction\n"
    "- Key Findings (minimum 3 well-explained points)\n"
    "- Conclusion\n"
    "- Sources (list all URLs found in the research)\n\n"
    "Be detailed, factual, and professional."
)

critic_prompt_template = (
    "You are a sharp and constructive research critic. Be honest and specific.\n\n"
    "Review the research report below and evaluate it strictly.\n\n"
    "Report:\n{report}\n\n"
    "Respond in this exact format:\n\n"
    "Score: X/10\n\n"
    "Strengths:\n- ...\n- ...\n\n"
    "Areas to Improve:\n- ...\n- ...\n\n"
    "One line verdict:\n..."
)

writer_chain = GeminiTextChain(writer_prompt_template)
critic_chain = GeminiTextChain(critic_prompt_template)

