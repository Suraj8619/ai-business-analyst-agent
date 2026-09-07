"""
Builds the AI Business Analyst agent: a Groq-backed LLM wired up with
a guarded SQL toolkit, a chart-generation tool, and conversation memory.
"""

import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_groq import ChatGroq

from db_guard import GuardedSQLDatabase
from tools import chart_tool

# Load .env from the same folder as this file specifically -- not just
# "wherever load_dotenv() feels like looking." load_dotenv() with no
# arguments depends on the current working directory, which isn't always
# the project folder (e.g. `streamlit run app.py` from a different shell
# location, or launching via an IDE run button). Pointing at an explicit
# path removes that whole category of "it's not finding my .env" bug.
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

DB_PATH = "business.db"

SYSTEM_PREFIX = """You are an AI Business Analyst. Answer using the sales database, \
explaining results in plain English with the "so what" -- not just raw numbers.

Rules:
- Check the schema before writing a query if you haven't yet.
- Use aggregates (SUM/AVG/GROUP BY), never dump raw rows.
- Call generate_chart for comparisons, trends, or breakdowns -- skip it for single numbers.
- If a query is rejected, rewrite it as a plain SELECT instead of retrying the same thing.
- Be concise: answer first, then one or two supporting details.
"""


def get_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found. Copy .env.example to .env and add your free "
            "key from console.groq.com."
        )
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key,
        # gpt-oss is a reasoning model -- its hidden "thinking" tokens count
        # against the free tier's 8K-tokens/minute cap just like output does.
        # "low" keeps it fast and cheap; bump to "medium"/"high" only if
        # you're not fighting the rate limit and want deeper reasoning.
        reasoning_effort="low",
        # Hard ceiling on response length so one verbose answer can't eat
        # the rest of the minute's token budget.
        max_tokens=800,
    )


def build_agent():
    """Returns an agent_executor wrapped with conversation memory."""
    llm = get_llm()
    db = GuardedSQLDatabase.from_uri(
        f"sqlite:///{DB_PATH}",
        # Skip example rows in the schema tool's output -- column names
        # (order_date, region, revenue, ...) are descriptive enough on
        # their own, and this is one more per-call token cost we don't
        # need to pay on a tight free-tier budget.
        sample_rows_in_table_info=0,
    )
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        extra_tools=[chart_tool],
        prefix=SYSTEM_PREFIX,
        verbose=True,
        # Each iteration resends the whole conversation so far, so fewer
        # iterations isn't just "faster" -- it's a direct multiplier on
        # tokens-per-minute. 5 is enough for schema check -> query ->
        # (optional chart) -> answer.
        max_iterations=20,
    )

    # In-memory chat history keyed by session_id, so a Streamlit session
    # (or a script) can carry context across follow-up questions.
    _histories: dict[str, InMemoryChatMessageHistory] = {}

    def get_history(session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in _histories:
            _histories[session_id] = InMemoryChatMessageHistory()
        return _histories[session_id]

    agent_with_memory = RunnableWithMessageHistory(
        agent_executor,
        get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return agent_with_memory


# Matches Groq's own error text, e.g. "...Please try again in 4.02s."
_RATE_LIMIT_WAIT_RE = re.compile(r"try again in ([\d.]+)\s*s", re.IGNORECASE)


def invoke_with_retry(agent, inputs, config, max_attempts=3, on_retry=None):
    """
    Calls agent.invoke() and automatically retries on a 429 rate-limit
    error, waiting however long Groq says to wait (parsed straight out
    of the error message) plus a small buffer.

    on_retry, if given, is called as on_retry(wait_seconds, attempt) right
    before each sleep -- useful for showing the user what's happening
    instead of a silent pause.

    Any other kind of error is re-raised immediately; only rate limits
    are worth waiting out automatically.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return agent.invoke(inputs, config=config)
        except Exception as e:
            last_error = e
            message = str(e)
            is_rate_limit = "rate_limit" in message.lower() or "429" in message
            if not is_rate_limit or attempt == max_attempts:
                raise

            match = _RATE_LIMIT_WAIT_RE.search(message)
            wait_seconds = float(match.group(1)) + 1.0 if match else 5.0 * attempt

            if on_retry:
                on_retry(wait_seconds, attempt)
            time.sleep(wait_seconds)

    raise last_error  # pragma: no cover -- unreachable, satisfies type-checkers


if __name__ == "__main__":
    # Quick manual test from the command line:
    #   python agent.py "What were total sales last month?"
    import sys

    agent = build_agent()
    question = " ".join(sys.argv[1:]) or "What were total sales by region?"

    def _print_retry(wait_seconds, attempt):
        print(f"\n[rate limited -- waiting {wait_seconds:.1f}s, attempt {attempt}]\n")

    result = invoke_with_retry(
        agent,
        {"input": question},
        config={"configurable": {"session_id": "cli-test"}},
        on_retry=_print_retry,
    )
    print("\n--- ANSWER ---")
    print(result["output"])