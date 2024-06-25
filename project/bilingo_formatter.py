from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("prooflingo_client_api")

client = OpenAI(api_key=key)
def formatter(text):
    
    prompt = f"""You are an advanced text analysis model. You will be provided with simple text obtained from a bilingual (TXLF) file. Your task is to:

Detect Tables: Identify all tables present in the provided text. Tables are represented as simple paragraph lines.
Mark Tables: Mark the detected tables with <table></table> tags in the text.
Extract Tables: Extract the marked tables and convert them into dataframes.
Return JSON: Return the modified text with table tags and the extracted tables as dataframes in JSON format.

Output Format:
{{
    "content": "The text with <table></table> tags added around detected tables",
    "tables": [
        {
            "DataFrame representation of the table",
        }
    ]
}}
Here is the text that is extracted from txlf file and you need to analyze it and give desired results: {text}
"""
    system_prompt = "You are a billingual file expert, who can process text extracted from billingual txlf file and can return proper tables from it too.!"

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )

    json_string = response.choices[0].message.content
    
    return json_string