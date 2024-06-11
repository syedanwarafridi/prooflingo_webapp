import PyPDF2
import openai
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
key= os.getenv('prooflingo_client_api')

client = OpenAI(api_key=key)

def read_pdf(file_path):
    pdf_file = open(file_path, 'rb')
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    num_pages = min(5, len(list(pdf_reader.pages)))
    text = ''
    for page in range(num_pages):
        page_obj = pdf_reader.pages[page]
        text += page_obj.extract_text()
    pdf_file.close()
    text = text.replace('\n', ' ')
    return text

def smart_ref(file_path, translation):
    text = read_pdf(file_path)
    
    system_prompt = "You are a Reference Document Analyzer"

    prompt = f"""You are a Reference Document Analyzer. Your task is to analyze the reference document text to grasp and mimic its writing style and word choices. 
    Then, apply that style to the translation to align it with the preferred tone and terminology.

    Reference Text: {text}

    Translation: {translation}

    You are required to highlight instances inside the tags where formatting, terminology, or stylistic elements deviate from the style guide in the translation using different tags.
    Use the following tags exactly as specified:
    - For formatting issues: <formatting></formatting>
    - For terminology issues: <terminology></terminology>
    - For stylistic issues: <stylistic></stylistic>

    It is crucial that you use these tags correctly and return the response in the exact format specified below.

    Return the response in the following JSON format:
    {{
        "translation_with_corrections": "Here should be the translation text with corrected formatting, styles, and terminology tags."
    }}
    Ensure that your output strictly adheres to these instructions and includes the tags where applicable.

    If there is no need for above formatting, style or terminology then return: Document is already well formalized.
    """
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
            temperature=0,
        )

    json_string = response.choices[0].message.content


    return json_string
