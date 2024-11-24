import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_openai import ChatOpenAI
from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase

# Constants for file paths.
DATABASE_FILE_PATH = "./db/credit_card_default.db"
CSV_FILE_URL = "./data/credit-card-default.csv"

# Load environment variables from the .env file.
load_dotenv()

# Retrieve the OpenAI API key from environment variables.
openai_key = os.getenv("OPENAI_API_KEY")

# Initialize the language model.
llm_name = "gpt-3.5-turbo"
model = ChatOpenAI(api_key=openai_key, model=llm_name)

# Create SQLite database and DataFrame if the database does not exist.
if not os.path.exists(DATABASE_FILE_PATH):
    engine = create_engine(f"sqlite:///{DATABASE_FILE_PATH}")
    df = pd.read_csv(CSV_FILE_URL).fillna(value=0)
    df.to_sql("credit_card_default", con=engine, if_exists="replace", index=False)

# Define the prompt for querying the chatbot.
SQL_PROMPT_PREFIX = """
You are a chatbot designed to interact with an SQL database.

## Instructions:
- Given an input question, create a syntactically correct {dialect} query to run, then look at the query results and return the answer.
- Unless the user specifies a specific number of examples they wish to obtain, **ALWAYS** limit your query to at most {top_k} results.
- Order the results by a relevant column to return the most interesting examples in the database.
- Only query for the relevant columns given the question, not all columns from a specific table.
- Double-check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
- **DO NOT MAKE ANY DML STATEMENTS (INSERT, UPDATE, DELETE, DROP, ETC.) TO THE DATABASE**.
- **DO NOT FABRICATE AN ANSWER OR USE PRIOR KNOWLEDGE. ONLY USE THE RESULTS FROM YOUR CALCULATIONS**.
- Your response should be in Markdown. However, **when running an SQL Query in "Action Input," do not include the Markdown backticks**.
Those are only for formatting the response, not for executing the command.
- **ALWAYS** include a detailed explanation of how you arrived at the answer in a section starting with "\n\nExplanation:\n".
- If the question is unrelated to the database, return "I don't know" as the answer.
- Only use the tools listed below and the information they return to construct your query and final answer.
- Use only the table names provided by the tools below; do not invent table names.
- In your final answer, include the SQL query you used in JSON or code format.

## Tools:
"""

# Instructions for formatting the agent's responses.
SQL_PROMPT_INSTRUCTIONS = """
## Use the following format:

Question: The input question you must answer.
Thought: You should always think about what to do.
Action: The action to take should be one of [{tool_names}].
Action Input: The input to the action.
Observation: The result of the action.
... (This Thought/Action/Action Input/Observation cycle can repeat N times)
Thought: I now know the final answer.
Final Answer: The final answer to the original input question.

### Example of Final Answer:
<=== Beginning of Example

Question: Which education level has the highest average credit limit? Please also provide the corresponding number.
Thought: I need to find the education level with the highest average credit limit and provide the corresponding number.
Action: query_sql_db
Action Input:
SELECT education, AVG(credit_limit) AS avg_credit_limit
FROM credit_card_default
GROUP BY education
ORDER BY avg_credit_limit DESC
LIMIT 1;

Observation:
[('university', 26000.0)]
Thought: I now know the final answer.
Final Answer: The average credit limit for university-level education is $26,000, which is the highest among all levels of education.

Explanation:
I queried the `credit_card_default` table to find the highest average credit limit by education level.
The query grouped the data by education, calculated the average credit limit for each group,
then ordered the results in descending order by average credit limit, and limited the results to one.
I used the following query:

```sql
SELECT education, AVG(credit_limit) AS avg_credit_limit
FROM credit_card_default
GROUP BY education
ORDER BY avg_credit_limit DESC
LIMIT 1;
```

===> End of Example
"""

# Initialize the SQL database.
db = SQLDatabase.from_uri(f"sqlite:///{DATABASE_FILE_PATH}")
toolkit = SQLDatabaseToolkit(db=db, llm=model)

# Create the SQL agent.
chatbot = create_sql_agent(
    prefix=SQL_PROMPT_PREFIX,
    format_instructions=SQL_PROMPT_INSTRUCTIONS,
    llm=model,
    toolkit=toolkit,
    top_k=30,
    verbose=True,
)

# Streamlit application for displaying results.
st.title("Database Chatbots: Working with SQL Data")

# User input for the question.
question = st.text_input(
    "Enter your query:",
    "What is the highest credit limit?",
)

# Run the chatbot and display the result.
if st.button("Run Query"):
    try:
        res = chatbot.invoke(question)
        final_result = res['output']
    except Exception as e:
        # Handle different types of exceptions and provide user feedback.
        if "output parsing error" in str(e):
            final_result = "An output parsing error occurred. Please try rephrasing your question."
        else:
            final_result = f"An error occurred: {e}"
    st.write("### Final Answer")
    st.markdown(final_result)

# To run the Streamlit app, use the command: streamlit run sql_database_chatbot.py

# Q:
# What is the lowest credit limit?
# What is the highest credit limit?