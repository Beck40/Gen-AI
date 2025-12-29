import os
import shutil   
import fitz 
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


DB_PATH = "C:\\Users\\beckk\\Documents\\Python\\GenAI_DB"

def ingest_pdf(file_path):
    """Load and process a local PDF file"""
    try:
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found!")
            return None
        
        print(f"Loading PDF: {file_path}")
        
        # Open PDF with PyMuPDF
        pdf_document = fitz.open(file_path)
        documents = []
        
        # Extract text from each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            
            # Create Document object for each page
            doc = Document(
                page_content=text,
                metadata={"source": file_path, "page": page_num + 1}
            )
            documents.append(doc)
        
        pdf_document.close()
        
        if not documents:
            print("Error: PDF appears to be empty!")
            return None
        
        print(f"Loaded {len(documents)} pages from PDF")
        return documents
    
    except Exception as e:
        print(f"Error loading PDF: {str(e)}")
        return None


def create_vector_db(documents):
    """Split documents and create vector database."""
    try:
        print("\n--- PROCESSING DOCUMENTS ---")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Increased for better context retention
            chunk_overlap=400  # Increased overlap to preserve context across boundaries
        )
        chunks = text_splitter.split_documents(documents)
        
        # Enhance metadata with page range tracking
        for chunk in chunks:
            # Store original page info
            if 'page' not in chunk.metadata:
                chunk.metadata['page'] = 1
        
        print(f"Created {len(chunks)} chunks")
        
        print("Initializing embedding model...")
        embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Remove existing database if it exists
        if os.path.exists(DB_PATH):
            print(f"Removing existing database...")
            shutil.rmtree(DB_PATH)
        
        print("Creating vector database...")
        Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=DB_PATH
        )
        
        print(f"SUCCESS! Database created with {len(chunks)} chunks in '{DB_PATH}' folder")
        
    except Exception as e:
        print(f"Error creating database: {str(e)}")

def main():
    print("=" * 50)
    print("    FINANCIAL INSIGHT ENGINE - PDF INGESTION")
    print("=" * 50)
    
    file_path = input("\nEnter the PDF file path: ").strip()
    # Remove quotes if user included them
    file_path = file_path.strip('"').strip("'")
    
    documents = ingest_pdf(file_path)
    
    if documents:
        create_vector_db(documents)
    else:
        print("\nIngestion failed. Please try again.")

if __name__ == "__main__":
    main()
