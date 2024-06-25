import os
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from docx import Document
os.environ["KEY"] = ""


def load_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def docChat(file_path, user_question):
    # Load the Word document
    document_text = load_docx(file_path)

    # Split the document into smaller chunks for embedding
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(document_text)

    # Create embeddings for the document chunks
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(texts, embeddings)

    # Initialize the retriever
    retriever = vector_store.as_retriever()

    # Initialize the QA chain
    llm = OpenAI()
    qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

    # Query the document with the user's question
    response = qa_chain.run(user_question)

    return response
