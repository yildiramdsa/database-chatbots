import json
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_openai import ChatOpenAI
from openai import OpenAI

import helper
from helper import (
    get_avg_credit_limit_by_education,
    get_default_rate_by_education,
)

# Load environment variables from the .env file.
load_dotenv()

# Retrieve the OpenAI API key from environment variables.
openai_key = os.getenv('OPENAI_API_KEY')

# Initialize the language model.
llm_name = 'gpt-3.5-turbo'
model = ChatOpenAI(api_key=openai_key, model=llm_name)

# Initialize the OpenAI client.
client = OpenAI(api_key=openai_key)

# Constants for file paths.
DATABASE_FILE_PATH = './db/credit_card_default.db'
CSV_FILE_URL = './data/credit-card-default.csv'

# Create SQLite database and load data from CSV if the database does not exist.
engine = create_engine(f'sqlite:///{DATABASE_FILE_PATH}')
os.makedirs(os.path.dirname(DATABASE_FILE_PATH), exist_ok=True)

df = pd.read_csv(CSV_FILE_URL).fillna(value=0)
df.to_sql('credit_card_default', con=engine, if_exists='replace', index=False)

def run_conversation(query: str) -> str:
    """Run a conversation with the model based on the user's query."""
    messages = [{'role': 'user', 'content': query}]

    response = client.chat.completions.create(
        model=llm_name,
        messages=messages,
        tools=helper.tools_sql,
        tool_choice='auto',
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            'get_avg_credit_limit_by_education': get_avg_credit_limit_by_education,
            'get_default_rate_by_education': get_default_rate_by_education,
        }
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            # Call the appropriate function based on the tool call
            function_response = function_to_call(
                education_level=function_args.get('education_level')
            )

            messages.append({
                'tool_call_id': tool_call.id,
                'role': 'tool',
                'name': function_name,
                'content': str(function_response),
            })

            # Get a new response from the model where it can see the function response
            second_response = client.chat.completions.create(
                model=llm_name,
                messages=messages,
            )

        return second_response

# Example calls to the functions
if __name__ == '__main__':
    res = (
        run_conversation(
            query='What is the default rate for university educated individuals?'
        ).choices[0].message.content
    )

    print(res)