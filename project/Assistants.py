from openai import OpenAI
import json
import os
import pdfplumber
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

key= os.getenv('prooflingo_client_api')
client = OpenAI(api_key=key)

# Testing
#---------------------------------------Main Comparison assistant Function--------------------------------------------------------------------------------------
def comparison_assistant(original_text,translated_text, history, contextual_matter, language):
    prompt = f""" Given a page from texts:
        1. Reference Text Page(error-free and complete original text): {original_text}
        2. Translated Text Page in {language} to be reviewed: {translated_text}

        Reference text is complete and correct text and translated text has mistakes and missing words, sentences, paragraphs. 

        Here is the previous pages processed, you can take context from them too, do not make changes in these pages and also do not use their text in current pages (if there is nothing then this might be the first page): {history}
        
        Your task is to analyze the Translated Text for errors by comparing it to the Reference Text. Please follow these steps to identify and categorize mistakes:
            - **Step 1:** Scrutinize for Contextual Errors where the meaning is altered, ambiguous, or inappropriate compared to the Reference Text.
            - **Step 2:** Find missing words, sentences, and paragraphs in transted text after comparing with reference text.
            - **Step 3:** Examine for Consistency Errors in terminology, style, or formatting that diverge from the Reference Text.
            - **Step 4:** Search for Incorrect Translations that do not faithfully convey the meaning of the original text.
            - **Step 5:** Find Synonyms that do not fit the context or convey the intended meaning accurately, consider it as contextual mistake.

        Provide your findings in a JSON response with involving these 3 Keys:
        1. "Translation with mistakes": Highlight errors in the Translated Text using <span> tags, categorized by error type without adding suggestions here. Give complete translation (just translation not reference text) with marked errors.
        Use following tags for marking different errors: (Give complete translation + mistakes marked with appropriate tags)
        {{
            "Contextual Error": "<span class='Contextual Error'>[text]</span>",
            "Missing Translation": "<span class='Missing Translation'>[text]</span>",
            "Consistency Error": "<span class='Consistency Error'>[text]</span>",
            "Wrong Translation": "<span class='Wrong Translation'>[text]</span>"
        }}
            In the above part just mark the errors and provide overall translation with marked errors and missing parts.

        2. "Issue and Suggestions List": List each identified issue with a description and suggested correction, including the error type.
        Example format:
        [
            {{
                "Issue": "Description of the error.",
                "Action": "Suggested correction with <s>[corrected text]</s>. In case of missing sentence, paragph give complete sentence or paragraph in mentioned spans", 
                "Type of Error": "Contextual Error / Missing Translation / Wrong Translation / Consistency Error"
            }},
            ...
        ]

        3. "Correct Translation": Provide the Translated Text with all errors corrected, highlighting the corrections as done previously.
        <span class='Type of error'>[correction]</span>
        If no errors are found, return the Translated Text as is and note in the "issues_and_suggestions" section that no mistakes were detected.

        4. "Tables with Mistakes": Give all the tables with mistakes (show the mistaked tables in this section) if any present in tables, give tables in the form of array here one by one with the key as a unique name that will be present in tag in the texts.

        5. "Tables with Corrections": Give all the tables after correcting mistakes if any present in tables, give tables in the form of array here one by one with the key as a unique name that will be present in tag in the texts.

        Important Instructions:
        Please ensure accuracy and completeness in your analysis and reporting. Ensure that missing sentences and paragraphs are added in correct translation enclosed in spans and also there must be mentioning of missing word, sentence, paragraph in translation with mistakes.
        Compare and find mistakes in tables too and return them as they were give as arrays in the end and and just in the texts give the tag like <table_1>, <table_2> and so on that will be same as key in giving tables.
        Do not give complete tables in the text section and just give unique names tags in text section and give complete tables in tables section with common unique name tag <unique_name>, same as given in text section.
        """



    system_prompt = f""" Act as a language expert who knows English and {language} languages very well.
    Help the user by catching/detecting the mistakes from translation text after comparing with the original text which will be provided to you.
    Take out as many mistakes as you can in one go!"""

    messages = [{
                "role": "system",
                "content": system_prompt
                },
                {
                "role": "user",
                "content": prompt
                }]
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        response_format={ "type": "json_object" },
        #as its a translation task so no randomness
        temperature=0,
    )

    json_string = response.choices[0].message.content


    return json_string

def extract_text_with_table_tags(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_text_with_tags = []
        tables_dict = {}
        
        for page_num, page in enumerate(pdf.pages, start=1):
            # Extract tables and their bounding boxes
            tables = page.extract_tables()
            table_bboxes = [table.bbox for table in page.find_tables()]
            
            # Extract the text and words
            text = page.extract_text()
            if text:
                words = page.extract_words()
                cleaned_words = []
                current_position = 0
                table_indices = []

                for word in words:
                    for table_index, bbox in enumerate(table_bboxes, start=1):
                        if (word["x0"] >= bbox[0] and word["x1"] <= bbox[2] and
                                word["top"] >= bbox[1] and word["bottom"] <= bbox[3]):
                            if table_index not in table_indices:
                                cleaned_words.append(f"<table{page_num}_{table_index}>")
                                table_indices.append(table_index)
                            break
                    else:
                        cleaned_words.append(word["text"])

                cleaned_text = " ".join(cleaned_words)
                all_text_with_tags.append(cleaned_text)
            
            # Process the tables and store them in the dictionary
            for table_index, table in enumerate(tables, start=1):
                df = pd.DataFrame(table[1:], columns=table[0])
                tables_dict[f"table{page_num}_{table_index}"] = df
    
    return all_text_with_tags, tables_dict

#--------------------------------Function that embeds the tables in the text by converting them in lists------------------------------------------------
def embed_tables_in_text(texts, tables_dict):
    embedded_texts = []
    for text in texts:
        for table_tag, table_df in tables_dict.items():
            table_array = table_df.values.tolist() 
            table_array_with_columns = [table_df.columns.tolist()] + table_array  
            table_str = str(table_array_with_columns)
            text = text.replace(f"<{table_tag}>", table_str)
        embedded_texts.append(text)
    return embedded_texts








#----------------------------------------------------------------------------------------------------------------

#-----------AI Assistant-------------
# that can make changes in target text according to query
#bold, italic, highlight the sentences or otherdd
def assistant(target_text, user_query):
    #system prompt
    system_prompt= """You are a helpfull assistant, that will help the user to make changes in the text shared with you!"""
    #main user prompt
    main_prompt=  f"""You are assistant whose job is to assist the user according to the questions ask.
    Here is the Text {target_text}.

    User will ask different general things realted to text or it can ask to make the general changes in the text too and you have to make the only changes asked by the user and return the updated text.

    Here are the examples of the changes user can ask:
    1. Convert all dates from US to UK format:
        For this change the formats of all the dates present in the text from US to UK or vice versa according to the requirements of the user.

    2.  Underline the names:
        For this just return the complete text provided to you by giving all the names in following tags like this:
        <span class= 'chatbot_underline'>name</span> (Give all the names present like)
        User can ask to underline different thigs like cities, dates etc following the above pattern for the underlining.

    3.  Bold anything:
        If user ask to bold anything lets say user ask to bold all the names return all names in:
        <span class='chatbot_bold'>name</span>.

    
    4. Highlight anything:
        For Highligting return all the parts that user wants to highlight in follwoing tags: <span class='chatbot_highlight>name</span>.

    5. Change format to italic:
        If user has asked to change names or anything to italic just return that entity in following tags:
        <span class='chatbot_italic'>name</span>


    4. Reformat the text to be Gender-specific:
        In this case you have to change the text format only (not overall text) so that it can addressed to females or males only.

    
    This is what user is asking for: {user_query}

    Just return the updated text without any explaination, do not answer any irrelavant and bad question,
    just tell the user that it is irrelavant questin and I am a assistant to assist for manipulating the text.
    And reply back to user nicely.
"""

    messages = [{
                "role": "system",
                "content": system_prompt
                },
                {
                "role": "user",
                "content": main_prompt
                }]
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        #as its a translation task so no randomness
        temperature=0,
    )

    json_string = response.choices[0].message.content


    return json_string




#----------------------------------------------------------------------------------------------------------------
#text tunning assistant
#that will help the user for defining, rephrasing, replacing a specific word
def text_tune_assistant(word, word_language):
    prompt = f"""Given the word: {word} which is in {word_language} language.

                Your task is to deliver the following details:

                1. **Step 1:** Suggest the best alternate word in the same language that can replace '{word}'.
                2. **Step 2:** Explain the meaning or definition of the word concisely and accurately in the same language as '{word}'.
                3. **Step 3:** Rephrase the word.

                Provide the JSON response including these elements:
                {{
                "Alternative": "Provide the alternate word here.",
                "Meaning": "Provide the meaning of the word here.",
                "Rephrased": "Provide the rephrased word here."
                }}

                ### Instructions:
                - Stick strictly to the requested information.
                - Do not add extra information or make unnecessary changes.
                """
    system_prompt = f""" Act as a language expert who knows English, Spanish, French, Arabic languages very well.
    Help the user by performing rephrasing word, changing word with alternative, and explaining the meansing of the word."""

    messages = [{
                "role": "system",
                "content": system_prompt
                },
                {
                "role": "user",
                "content": prompt
                }]
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        response_format={ "type": "json_object" },
        temperature=0,
    )

    json_string = response.choices[0].message.content
    return json_string
