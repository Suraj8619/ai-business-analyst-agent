# AI Business Analyst Agent

An LLM-powered agent that answers natural-language business questions by querying real data, running the right analysis, and explaining the results in plain English.

## What We're Building

A tool where a user types a question like *"What drove the dip in Q3 revenue?"* and the agent:
1. Looks at the database schema
2. Writes and runs the correct SQL query
3. Generates a chart if that helps explain the answer
4. Responds in plain English, not raw numbers

## Why We're Building This

- Most people can't get answers from company data without waiting on an analyst or engineer.
- Dashboards only answer questions they were built for — this agent answers *any* question, on demand.
- It's a real, in-demand use case (LLM + data agents) that goes well beyond a basic chatbot, making it a strong portfolio project.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| LLM inference | **Groq API** (free tier) | No cost, no credit card, and very fast responses — good for an agent that needs multiple LLM calls per question |
| Model | `llama-3.3-70b-versatile` | Strong reasoning/SQL-writing quality, available free on Groq |
| Orchestration | **LangChain** | Handles the agent loop, tool calling, and SQL toolkit out of the box |
| LangChain ↔ Groq bridge | `langchain-groq` | Official integration package |
| Database | **SQLite** | Zero-setup, file-based — perfect for a demo/portfolio project |
| Data handling | **Pandas** | Cleaning data and shaping query results |
| Visualization | **Plotly** | Auto-generated charts when a number alone isn't enough |
| UI | **Streamlit** | Fastest way to get a clean chat interface running |
| Config/secrets | **python-dotenv** | Keeps your API key out of your code |

> Free-tier note: Groq's free tier is rate-limited (requests/minute and tokens/minute), not usage-limited by dollars. That's more than enough for building and demoing this project — just don't hammer it in a tight loop while testing.

---

## Prerequisites

- Python 3.10+
- A free [Groq](https://console.groq.com) account (no credit card required)
- Basic familiarity with Python and SQL

---

## Step-by-Step Build Plan

### Step 1 — Get Your Free Groq API Key
1. Go to `console.groq.com` and sign up (email or Google login).
2. Navigate to **API Keys** → **Create API Key**.
3. Copy the key somewhere safe — you won't be able to see it again.

### Step 2 — Set Up the Project

```bash
mkdir ai-business-analyst-agent && cd ai-business-analyst-agent
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install langchain langchain-groq langchain-community langchain-experimental \
            pandas plotly streamlit python-dotenv
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

### Step 3 — Set Up a Sample Database
Use any small business-style dataset (sales, orders, customers). Easiest path: load a CSV into SQLite with Pandas.

```python
import pandas as pd
import sqlite3

df = pd.read_csv("sales_data.csv")
conn = sqlite3.connect("business.db")
df.to_sql("sales", conn, if_exists="replace", index=False)
conn.close()
```

If you don't have a dataset yet, a public one like the Olist Brazilian E-Commerce dataset or the classic Northwind database works well.

### Step 4 — Connect LangChain to Groq

```python
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,   # deterministic output matters for SQL generation
)
```

### Step 5 — Build the Core SQL Agent
LangChain has a built-in toolkit that lets the LLM inspect the schema and write queries itself.

```python
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit

db = SQLDatabase.from_uri("sqlite:///business.db")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    agent_type="tool-calling",
    verbose=True,
)

response = agent.invoke({"input": "What drove the dip in Q3 revenue?"})
print(response["output"])
```

At this point you already have a working text-to-SQL agent. Everything after this step makes it more useful and safer.

### Step 6 — Add Automatic Chart Generation
Wrap chart creation as a custom LangChain `Tool` so the agent can decide *when* a chart actually helps.

```python
from langchain.tools import Tool
import plotly.express as px

def make_chart(query_result_json: str) -> str:
    df = pd.read_json(query_result_json)
    fig = px.bar(df, x=df.columns[0], y=df.columns[1])
    fig.write_html("chart.html")
    return "Chart generated: chart.html"

chart_tool = Tool(
    name="generate_chart",
    func=make_chart,
    description="Use this when a bar/line chart would help explain query results."
)
```

Add `chart_tool` to the agent's tool list alongside the SQL toolkit tools.

### Step 7 — Add a Plain-English Explanation Layer
After the SQL result comes back, run one more LLM call that turns raw numbers into an analyst-style explanation (trend, comparison, likely cause) instead of just printing the table.

### Step 8 — Add Conversation Memory
So follow-ups like *"break that down by region"* work without repeating context.

```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

history = InMemoryChatMessageHistory()

agent_with_memory = RunnableWithMessageHistory(
    agent,
    lambda session_id: history,
    input_messages_key="input",
    history_messages_key="chat_history",
)
```

### Step 9 — Build the Streamlit UI

```python
import streamlit as st

st.title("AI Business Analyst Agent")
question = st.chat_input("Ask a question about your data...")

if question:
    result = agent_with_memory.invoke(
        {"input": question},
        config={"configurable": {"session_id": "user-1"}},
    )
    st.write(result["output"])
```

Run it with:
```bash
streamlit run app.py
```

### Step 10 — Add Guardrails
This is what separates a demo from something you'd actually trust:
- Connect with a **read-only** database user/connection wherever possible.
- Add a query validator that rejects anything containing `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`.
- Wrap query execution in try/except and return a friendly error instead of crashing.
- Cap the number of rows returned to the LLM to avoid blowing up the context window.

### Step 11 — Test With Real Questions
- "What were total sales last month?"
- "Which product category had the highest return rate?"
- "Compare average order value between new and returning customers."
- "Why did revenue drop in Q3?" (tests reasoning + chart generation together)

### Step 12 — (Optional) Deploy
Both are free:
- **Streamlit Community Cloud** — deploy directly from a GitHub repo.
- **Hugging Face Spaces** — also supports Streamlit apps for free.

Remember to set `GROQ_API_KEY` as a secret in whichever platform you use — never commit `.env` to GitHub.

---

## Project Structure

```
ai-business-analyst-agent/
├── app.py                       # Streamlit chat UI
├── agent.py                     # Builds the LangChain agent (LLM + tools + memory)
├── tools.py                     # Custom chart-generation tool
├── db_guard.py                  # Read-only query validation + row-limit safety net
├── db_setup.py                  # Loads the CSV into a local SQLite database
├── data/
│   ├── generate_sample_data.py  # Generates the synthetic sales dataset
│   └── sales_data.csv           # Generated sample data (2,000 rows)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Getting Started (this repo)

```bash
git clone <your-repo-url>  # or unzip this project
cd ai-business-analyst-agent

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then paste your free Groq key into .env

python db_setup.py              # builds business.db from data/sales_data.csv
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`) and start asking questions.

### What's already tested
Every file in this repo has been run and verified: package installs cleanly from `requirements.txt` in a fresh virtual environment, the sample data generates correctly, `business.db` builds and returns the expected row/column counts, the guardrails correctly block `DROP`/`DELETE`/`UPDATE`/sneaky-CTE queries while allowing safe `SELECT`s, the chart tool renders real Plotly HTML, and the full agent constructs and runs its reasoning loop right up to the LLM call. The only step that requires your own environment is the live call to Groq's API, since that needs your personal free API key.

### If something doesn't work
- **`GROQ_API_KEY not found`** — make sure you copied `.env.example` to `.env` (not just edited the example) and restarted the app.
- **Rate limit errors** — you're on Groq's free tier; wait a minute and try again, or ask fewer follow-up questions per session.
- **Agent gives a wrong/empty answer** — check the terminal running Streamlit; `verbose=True` in `agent.py` prints the agent's SQL and reasoning so you can see exactly where it went wrong.

## Project Status
✅ MVP built and tested — ready to run with your own Groq key.

## Roadmap (Post-MVP)
- Multi-step reasoning for compound questions
- Support for connecting to a live/production database
- Proactive anomaly detection ("flag anything unusual this week")
- Exportable PDF/slide reports of findings
