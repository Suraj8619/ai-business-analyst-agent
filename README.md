AI Business Analyst Agent

An AI-powered Business Analyst Agent that allows users to analyze sales data using natural-language queries. The application combines LLMs, Python, SQL, and data analysis tools to generate business insights and answer analytical questions.

🚀 Features
🤖 AI-powered business analysis
📊 Sales data analysis and insights
💬 Ask business questions using natural language
🗄️ SQL-based data querying
📈 Generate charts and visualizations
🔍 Automated data analysis
🛡️ Database access and query safeguards
📁 Includes sample sales data for testing
🧩 Modular tool-based agent architecture
🛠️ Tech Stack
Python
LLMs / Generative AI
SQL / SQLite
Pandas
Data Analysis & Visualization
Streamlit
Git & GitHub
📂 Project Structure
ai-business-analyst-agent/
│
├── app.py                    # Application entry point
├── agent.py                  # AI agent and reasoning logic
├── tools.py                  # Data analysis / business tools
├── db_guard.py               # Database query validation and safeguards
├── db_setup.py               # Database initialization
├── requirements.txt          # Python dependencies
│
├── data/
│   ├── sales_data.csv        # Sample sales dataset
│   └── generate_sample_data.py
│
├── charts/                   # Generated charts
│
├── README.md
└── .gitignore
⚙️ Installation
1. Clone the repository
git clone https://github.com/Suraj8619/ai-business-analyst-agent.git
cd ai-business-analyst-agent
2. Create a virtual environment
python -m venv venv

Activate it on Windows:

venv\Scripts\activate

On macOS/Linux:

source venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables

Create a .env file in the project root and add the required API credentials.

Example:

OPENAI_API_KEY=your_api_key_here

Never commit your .env file or API keys to GitHub.

▶️ Run the Application

Run the application using:

streamlit run app.py

The application will open in your browser.

💡 Example Queries

You can ask questions such as:

What were the total sales this year?

Which product generated the highest revenue?

What are the best-performing regions?

Show me the monthly sales trend.

Which products have declining sales?

What percentage of total revenue comes from each region?

The agent processes the question, uses the appropriate analytical tools, and returns a business-focused answer.

🧠 How It Works
User Query
     ↓
AI Business Analyst Agent
     ↓
Query Understanding
     ↓
Select Appropriate Tool
     ↓
SQL / Data Analysis
     ↓
Result Processing
     ↓
Business Insight / Visualization

The project separates the agent logic, database operations, and analytical tools, making it easier to extend with additional business-analysis capabilities.

📊 Dataset

The repository includes a sample sales dataset located at:

data/sales_data.csv

A Python script is also provided to generate sample data:

python data/generate_sample_data.py
🔐 Security

The project includes database safeguards to help prevent unsafe database operations. API keys and other sensitive configuration values are stored using environment variables and excluded from version control through .gitignore.

🔮 Future Improvements
Add support for multiple datasets
Add more advanced business KPIs
Improve chart and dashboard generation
Add forecasting and predictive analytics
Support additional LLM providers
Add authentication and user-specific analysis
Deploy the application to the cloud
👨‍💻 Author

Suraj Kumar
B.Tech — IIIT Bhagalpur
