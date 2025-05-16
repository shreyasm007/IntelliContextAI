from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import streamlit as st
from io import BytesIO
import tempfile
import os

class DocumentProcessor:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=100
        )

    def process_file(self, file_bytes: bytes, file_type: str, filename: str) -> str:
        """Process different file types and return extracted text"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name

        try:
            if file_type == 'pdf':
                loader = PyPDFLoader(temp_file_path)
            elif file_type == 'docx':
                loader = Docx2txtLoader(temp_file_path)
            elif file_type == 'txt':
                loader = TextLoader(temp_file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            documents = loader.load()
            text = "\n".join(doc.page_content for doc in documents)
            
            # Display document stats
            word_count = len(text.split())
            reading_time = word_count / 200  # Assuming 200 WPM
            st.info(f"""📄 Document Stats:
            - Words: {word_count:,}
            - Reading Time: {reading_time:.1f} minutes""")
            
            return text
        finally:
            os.unlink(temp_file_path)

    def create_documents(self, text: str, metadata: Dict = None) -> List:
        """Split text into documents"""
        return self.text_splitter.create_documents([text], [metadata or {}])

    def create_embeddings(self, documents: List) -> FAISS:
        """Create FAISS vectorstore from documents"""
        try:
            with st.spinner("Creating document embeddings..."):
                vectorstore = FAISS.from_documents(documents, self.embeddings)
            return vectorstore
        except Exception as e:
            raise RuntimeError(f"Failed to create embeddings: {str(e)}")