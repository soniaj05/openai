import fitz  
import os
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT
from urllib.parse import quote_plus
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Securely get database credentials
DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", "$onia@24")) 
DATABASE_URL = f"mysql+pymysql://root:{DB_PASSWORD}@localhost/testdb"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Define MySQL table for storing documents
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(LONGTEXT)

# Create the table
Base.metadata.create_all(engine)

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as pdf_document:
        for page in pdf_document:
            text += page.get_text() + "\n"
    return text

# Function to store extracted text into MySQL
def store_pdf_text(text):
    session = SessionLocal()
    new_doc = Document(content=text)
    session.add(new_doc)
    session.commit()
    session.close()


pdf_files = ["model.pdf"]  

for pdf in pdf_files:
    text = extract_text_from_pdf(pdf)
    store_pdf_text(text)

# Connect LangChain to MySQL
db = SQLDatabase.from_uri(DATABASE_URL)

# Configure Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBMe-rq71SGRjBFZj88hBkP3nrqwCl-HNI") 
llm = GoogleGenerativeAI(model="gemini-pro", google_api_key=GEMINI_API_KEY)

# Define a LangChain prompt template
prompt = PromptTemplate(
    input_variables=["document_text", "question"],
    template="Answer the following question based on these documents:\n\n{document_text}\n\nQuestion: {question}"
)

# Retrieve stored text from MySQL
def retrieve_document_text():
    session = SessionLocal()
    docs = session.query(Document).all() # Retrieve stored document text
    session.close()
    return "\n\n" .join (doc.content for doc in docs if doc.content) 

def ask_gemini(question):
    document_text = retrieve_document_text()
    if not document_text:
        return "No document found in the database."
    
    formatted_prompt = prompt.format(document_text=document_text, question=question)
    response = llm.invoke(formatted_prompt)
    return response


# Chatbot interaction loop
def chatbot():
    print("Chatbot is ready! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Chatbot: Goodbye!")
            break
        response = ask_gemini(user_input)
        print(f"Chatbot: {response}")

# Run chatbot
if __name__ == "__main__":
    chatbot()
