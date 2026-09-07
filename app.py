"""
Streamlit chat UI for the AI Business Analyst agent.
Run with: streamlit run app.py
"""

import os
import uuid

import streamlit as st

from agent import build_agent, invoke_with_retry

st.set_page_config(page_title="AI Business Analyst", page_icon="📊", layout="centered")
st.title("📊 AI Business Analyst Agent")
st.caption("Ask a question about the sample sales data in plain English.")

if not os.getenv("GROQ_API_KEY"):
    st.error(
        "No GROQ_API_KEY found. Copy `.env.example` to `.env` and add your free "
        "key from [console.groq.com](https://console.groq.com), then restart the app."
    )
    st.stop()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    with st.spinner("Starting up..."):
        st.session_state.agent = build_agent()

with st.sidebar:
    st.subheader("Try asking:")
    examples = [
        "What were total sales by region?",
        "What drove the dip in Q3 revenue?",
        "Which category has the highest return rate?",
        "Compare average order value between new and returning customers.",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending_question = ex

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart_path"):
            with open(msg["chart_path"], "r", encoding="utf-8") as f:
                st.components.v1.html(f.read(), height=450)

question = st.chat_input("Ask about the sales data...")
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=False) as status:
            def _on_retry(wait_seconds, attempt):
                status.update(
                    label=f"Hit Groq's free-tier rate limit -- waiting {wait_seconds:.0f}s "
                    f"and retrying (attempt {attempt})..."
                )

            try:
                result = invoke_with_retry(
                    st.session_state.agent,
                    {"input": question},
                    config={"configurable": {"session_id": st.session_state.session_id}},
                    on_retry=_on_retry,
                )
                output = result["output"]
                status.update(label="Done", state="complete")
            except Exception as e:
                message = str(e)
                if "rate_limit" in message.lower() or "429" in message:
                    output = (
                        "Groq's free-tier rate limit is still active after a few retries. "
                        "Wait about a minute and ask again -- this isn't a bug, just the "
                        "free tier's tight tokens-per-minute budget."
                    )
                else:
                    output = f"Something went wrong: {e}"
                status.update(label="Hit an issue", state="error")

        chart_path = None
        # If a chart tool call happened, its marker ends up referenced in
        # intermediate steps; the simplest robust approach is to scan the
        # charts/ folder for the most recently created file this turn.
        charts_dir = "charts"
        if os.path.isdir(charts_dir):
            files = [os.path.join(charts_dir, f) for f in os.listdir(charts_dir)]
            if files:
                newest = max(files, key=os.path.getctime)
                # Only attach it if it was just created (avoid re-showing old charts)
                if "shown_charts" not in st.session_state:
                    st.session_state.shown_charts = set()
                if newest not in st.session_state.shown_charts:
                    chart_path = newest
                    st.session_state.shown_charts.add(newest)

        st.markdown(output)
        if chart_path:
            with open(chart_path, "r", encoding="utf-8") as f:
                st.components.v1.html(f.read(), height=450)

    st.session_state.messages.append(
        {"role": "assistant", "content": output, "chart_path": chart_path}
    )