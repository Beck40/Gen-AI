import os
import sys
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate

# --- CONFIGURATION ---
API_KEY = input("Enter your GROQ API key: ")
DB_PATH = "C:\\Users\\beckk\\Documents\\Python\\GenAI_DB"

def start_rag_agent():
    # 1. Safety Check: Does the DB exist?
    if not os.path.exists(DB_PATH):
        print(f"\n Error: Database folder '{DB_PATH}' not found.")
        print(" Run 'python ingest.py' first to load your data.\n")
        return

    print("--- LOADING INTELLIGENCE ---")
    
    # CRITICAL: Must use the EXACT same model as ingest.py
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Load the Vector Database
    vector_db = Chroma(persist_directory=DB_PATH, embedding_function=embedding_model)
    
    # Initialize Llama 3 (The Brain)
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, api_key=API_KEY)

    # The "Senior Analyst" Persona
    # This prompt forces the AI to be professional and admit when it doesn't know.
    custom_prompt = PromptTemplate(
        template="""You are a Senior Financial Analyst with expertise in analyzing financial documents.
        Analyze the provided context carefully and answer the question in detail.
        If you find relevant information, explain it thoroughly with specific figures and details.
        If the answer is not in the context, say "I cannot find that information in the documents."
        
        CONTEXT:
        {context}
        
        QUESTION: {question}
        
        DETAILED ANSWER:""",
        input_variables=["context", "question"]
    )

    # Create the Retrieval Chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 7}), # Increased to retrieve more relevant chunks
        return_source_documents=True, # <--- Required for Citations
        chain_type_kwargs={"prompt": custom_prompt}
    )

    print("\n" + "="*50)
    print(" FINANCIAL INSIGHT ENGINE (Ready)")
    print("="*50)
    print("Type 'exit' to quit.\n")
    
    # The Chat Loop
    while True:
        query = input("Query: ")
        if query.lower() in ["exit", "quit"]: 
            break
        
        print("\n Searching documents...")
        try:
            # Ask the AI
            res = qa_chain.invoke({"query": query})
            
            # Print the Answer
            print(f"\nAgent: {res['result']}\n")
            
            # Print the Citations (The "Senior" Feature)
            print("--- Sources ---")
            seen_sources = set()
            for doc in res['source_documents']:
                # Extract metadata carefully
                source = doc.metadata.get('source', 'Unknown')
                page = doc.metadata.get('page', None)
                
                # Format citation nicely
                if "http" in source:
                    citation = f" {source}"
                else:
                    filename = os.path.basename(source)
                    citation = f" {filename}"
                    if page is not None:
                        citation += f" (Page {page + 1})" # +1 because code counts from 0
                
                # Avoid duplicate prints
                if citation not in seen_sources:
                    print(citation)
                    seen_sources.add(citation)
            print("-" * 20 + "\n")
            
        except Exception as e:
            print(f" Error: {e}")

if __name__ == "__main__":
    start_rag_agent()