import json
import os
import time
import pandas as pd
import numpy as np
import streamlit as st

from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text
from langchain.schema import HumanMessage, SystemMessage

import helper
from helper import (
    get_avg_credit_limit_by_education,
    get_default_rate_by_education,
)

# Load environment variables from the .env file.
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
DATABASE_FILE_PATH = "./db/credit_card_default.db"

# Ensure environment variables are loaded correctly.
if not openai_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Create an engine to connect to the SQLite database.
engine = create_engine(f"sqlite:///{DATABASE_FILE_PATH}")

# Initialize OpenAI API client.
llm_name = "gpt-3.5-turbo"
client = OpenAI(api_key=openai_key)

# Create the assistant.
assistant = client.beta.assistants.create(
    name="Credit Card Default Assistant",
    description="Assistant to help with credit card default data",
    model=llm_name,
    tools=helper.tools_sql,
)

# Create a thread.
thread = client.beta.threads.create()
print(f"Thread ID: {thread.id}")

# Create a message.
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What is the default rate for university educated individuals?",
)

# List messages.
messages = client.beta.threads.messages.list(thread_id=thread.id)
print(messages)

# Run the assistant.
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
)

start_time = time.time()
status = run.status

# Main loop to check the status of the run.
while status not in ["completed", "cancelled", "expired", "failed"]:
    time.sleep(5)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    elapsed_time = time.time() - start_time
    print(f"Elapsed time: {int(elapsed_time // 60)} minutes {int(elapsed_time % 60)} seconds")
    status = run.status
    print(f"Status: {status}")

    if status == "requires_action":
        available_functions = {
            "get_avg_credit_limit_by_education": get_avg_credit_limit_by_education,
            "get_default_rate_by_education": get_default_rate_by_education,
        }

        tool_outputs = []

        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)

            print(f"Function response: {function_response}")
            print(tool_call.id)

            tool_outputs.append(
                {"tool_call_id": tool_call.id, "output": str(function_response)}
            )

        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs,
        )

messages = client.beta.threads.messages.list(thread_id=thread.id)
print(messages.model_dump_json(indent=2))