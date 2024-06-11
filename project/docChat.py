from openai import OpenAI
#from dotenv import load_dotenv
import os
import openai

#load_dotenv()
#key = os.getenv("prooflingo_client_api")
key = "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"
def docChat(file_path, user_question, key=key):
    client = OpenAI(api_key=key)
    assistant = client.beta.assistants.create(
        name="Document Chatbot",
        instructions="""You will be provided with a document to help answer specific questions.
        - If the answer is in the document, provide a concise answer in 10 words or fewer.
        - If you cannot find the answer in the document, simply respond with "I don't know."
        - Do not ask for additional documents or files.
        - Provide brief and specific answers based solely on the provided document.""",
        model="gpt-4o",
        tools=[{"type": "file_search"}],
        temperature=0,
    )

    # Create a vector store called "Document Chatbot"
    vector_store = client.beta.vector_stores.create(name="Document Chatbot")
    
    # Ready the files for upload to OpenAI
    file_streams = [open(path, "rb") for path in [file_path]]
    
    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    
    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    # Upload the user-provided file to OpenAI
    message_file = client.files.create(
        file=open(file_path, "rb"), purpose="assistants"
    )
    
    # Create a thread and attach the file to the message
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": user_question,
                "attachments": [
                    {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
                ],
            }
        ]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )

    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(f"[{index}] {cited_file.filename}")

    return message_content.value
