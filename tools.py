"""
Custom LangChain tool that lets the agent generate a chart when a visual
would explain the answer better than a number alone.

The agent decides *when* to call this -- it passes the tool a small JSON
table (column names + rows) and a suggested chart type, and this tool
turns it into a Plotly chart saved as an HTML file the UI can display.
"""

import json
import uuid
from pathlib import Path

import pandas as pd
import plotly.express as px
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

CHARTS_DIR = Path("charts")
CHARTS_DIR.mkdir(exist_ok=True)


class ChartInput(BaseModel):
    data_json: str = Field(
        description=(
            "A JSON string representing tabular data, e.g. "
            '\'[{"region": "North", "revenue": 1200}, {"region": "South", "revenue": 900}]\'. '
            "Must have at least two columns: one categorical/date column and one numeric column."
        )
    )
    chart_type: str = Field(
        default="bar",
        description="One of: 'bar', 'line', 'pie'. Use 'line' for trends over time, "
        "'bar' for comparisons across categories, 'pie' for proportions.",
    )
    title: str = Field(default="Chart", description="A short, descriptive chart title.")


def _generate_chart(data_json: str, chart_type: str = "bar", title: str = "Chart") -> str:
    try:
        rows = json.loads(data_json)
        df = pd.DataFrame(rows)
    except Exception as e:
        return f"Could not parse data_json: {e}"

    if df.empty or len(df.columns) < 2:
        return "Not enough data to build a chart -- need at least 2 columns."

    x_col, y_col = df.columns[0], df.columns[1]

    if chart_type == "line":
        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
    elif chart_type == "pie":
        fig = px.pie(df, names=x_col, values=y_col, title=title)
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=title)

    filename = f"{uuid.uuid4().hex[:8]}.html"
    filepath = CHARTS_DIR / filename
    fig.write_html(filepath, include_plotlyjs="cdn")

    return f"CHART_GENERATED:{filepath}"


# chart_tool = StructuredTool.from_function(
#     func=_generate_chart,
#     name="generate_chart",
#     description=(
#         "Generate a chart (bar, line, or pie) from a small JSON table of query results. "
#         "Use this when showing a trend, comparison, or breakdown would help explain the "
#         "answer better than text alone. Do not use this for single-number answers."
#     ),
#     args_schema=ChartInput,
# )

chart_tool = StructuredTool.from_function(
    func=_generate_chart,
    name="generate_chart",
    description=(
        "Generate ONE chart from a small JSON table of query results. "
        "Use only when a visual materially improves the answer. "
        "Do not call this tool more than once for a single user question."
    ),
    args_schema=ChartInput,
)
