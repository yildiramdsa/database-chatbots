from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
import json

# Create an engine to connect to the SQLite database.
DATABASE_FILE_PATH = "./db/credit_card_default.db"
engine = create_engine(f"sqlite:///{DATABASE_FILE_PATH}")

# Define available SQL tools for the credit card default database.
tools_sql = [
    {
        "type": "function",
        "function": {
            "name": "get_avg_credit_limit_by_education",
            "description": """Retrieves the average credit limit for a specific education level.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "education_level": {
                        "type": "string",
                        "description": """The education level (e.g., 'university', 'graduate school', 'high school').""",
                    }
                },
                "required": ["education_level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_default_rate_by_education",
            "description": """Retrieves the default rate for a specific education level.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "education_level": {
                        "type": "string",
                        "description": """The education level (e.g., 'university', 'graduate school', 'high school').""",
                    }
                },
                "required": ["education_level"],
            },
        },
    },
]

# Function to retrieve the average credit limit by education level.
def get_avg_credit_limit_by_education(education_level):
    """
    Retrieves the average credit limit for the specified education level.

    Parameters:
    education_level (str): The education level to query.

    Returns:
    dict: A dictionary containing the average credit limit.
    """
    try:
        query = f"""
        SELECT AVG(LIMIT_BAL) AS avg_credit_limit
        FROM credit_card_default
        WHERE EDUCATION_CAT = '{education_level}';
        """
        query = text(query)

        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)
        if not result.empty:
            return result.to_dict("records")[0]
        else:
            return json.dumps({"avg_credit_limit": np.nan})
    except Exception as e:
        print(e)
        return json.dumps({"avg_credit_limit": np.nan})

# Function to retrieve the default rate by education level.
def get_default_rate_by_education(education_level):
    """
    Retrieves the default rate for the specified education level.

    Parameters:
    education_level (str): The education level to query.

    Returns:
    dict: A dictionary containing the default rate.
    """
    try:
        query = f"""
        SELECT AVG("default payment next month") AS default_rate
        FROM credit_card_default
        WHERE EDUCATION_CAT = '{education_level}';
        """
        query = text(query)

        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)
        if not result.empty:
            return result.to_dict("records")[0]
        else:
            return json.dumps({"default_rate": np.nan})
    except Exception as e:
        print(e)
        return json.dumps({"default_rate": np.nan})