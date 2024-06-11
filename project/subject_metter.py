from openai import OpenAI

def ai_suggested_subject(file_path):
    client = OpenAI(api_key='')
    
    assistant = client.beta.assistants.create(
      name="Topic Summarizer",
      instructions="""Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Use 3 words maximum, minimum 2 words and keep the answer as concise as possible.""",
      model="gpt-4o",
      tools=[{"type": "file_search"}],
      temperature=0,
    )

    vector_store = client.beta.vector_stores.create(name="Topic Summarizer")
    file_path = "Notebooks/" + file_path
    file_paths = [file_path]
    file_streams = [open(path, "rb") for path in file_paths]
    
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
      vector_store_id=vector_store.id, files=file_streams
    )

    assistant = client.beta.assistants.update(
      assistant_id=assistant.id,
      tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    # Upload the user provided file to OpenAI
    message_file = client.files.create(
      file=open(file_path, "rb"), purpose="assistants"
    )
    
    # Create a thread and attach the file to the message
    thread = client.beta.threads.create(
      messages=[
        {
          "role": "user",
          "content": """Determine the topic of the context. For Example, the output could be "Legal" or "Public Relation" etc.""",
          # Attach the new file to the message.
          "attachments": [
            { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
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
    # citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
        # if file_citation := getattr(annotation, "file_citation", None):
        #     cited_file = client.files.retrieve(file_citation.file_id)
        #     citations.append(f"[{index}] {cited_file.filename}")

    return message_content.value

# print(ai_suggested_subject())