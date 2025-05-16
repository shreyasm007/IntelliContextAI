import streamlit as st
import os
from dotenv import load_dotenv
from utils.document_processor import DocumentProcessor
from utils.chat_manager import ChatManager

# Load environment variables
load_dotenv()

# Set the page configuration
st.set_page_config(
    page_title="🤖 RAG-Powered AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Load custom CSS
with open("styles/main.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "doc_processor" not in st.session_state:
    st.session_state.doc_processor = DocumentProcessor()

# Sidebar for configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="🔹 Get your API key from https://groq.com"
    )

    st.subheader("📄 Upload Documents")
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["pdf", "docx", "txt"],
        help="Upload PDF, DOCX, or TXT files"
    )

    if uploaded_file:
        try:
            # Process document
            text = st.session_state.doc_processor.process_file(
                uploaded_file.read(),
                uploaded_file.name.split('.')[-1].lower(),
                uploaded_file.name
            )

            # Create documents and embeddings
            documents = st.session_state.doc_processor.create_documents(
                text,
                metadata={'source': uploaded_file.name}
            )
            st.session_state.vectorstore = st.session_state.doc_processor.create_embeddings(documents)
            st.success("✅ Document processed successfully!")

        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")

# Main chat interface
if not api_key:
    st.warning("Please enter your Groq API key in the sidebar to start chatting.")
else:
    chat_manager = ChatManager(api_key)

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get relevant context if available
        context = None
        if st.session_state.vectorstore and prompt:
            try:
                results = st.session_state.vectorstore.similarity_search(prompt, k=2)
                context = "\n\n".join(doc.page_content for doc in results)
                with st.expander("📚 Relevant Context", expanded=False):
                    st.markdown(f'<div class="context-area">{context}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error retrieving context: {str(e)}")

        # Generate response
        with st.chat_message("assistant"):
            response = chat_manager.generate_response(
                st.session_state.messages,
                context=context
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })