import streamlit as st
import os
from dotenv import load_dotenv
from utils.document_processor import DocumentProcessor
from utils.chat_manager import ChatManager
import gc

# Load environment variables
load_dotenv()

# Set the page configuration
st.set_page_config(
    page_title="🤖 RAG-Powered AI Assistant (Developed by Shreyas Mohite)",
    page_icon="🤖",
    layout="wide"
)

# Now display the title in the app
st.title("🤖 RAG-Powered AI Assistant (Developed by Shreyas Mohite)")

# Load custom CSS
with open("styles/main.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = None
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "doc_processor" not in st.session_state:
    st.session_state.doc_processor = DocumentProcessor()

@st.cache_data(show_spinner=True)
def get_groq_models(api_key: str):
    from groq import Groq  # ensure groq is installed: pip install groq
    try:
        client = Groq(api_key=api_key)
        models_response = client.models.list()  # returns a ModelListResponse object
        model_ids = [model.id for model in models_response.data]
        if not model_ids:
            st.error("No models returned from Groq API. Please check your API key or account settings.")
            return ["mixtral-8x7b-32768", "llama3-8b-8192", "llama-3.1-70b-versatile", "llama-3.3-70b-versatile"]
        return model_ids
    except Exception as e:
        st.error("Failed to fetch models from Groq API: " + str(e))
        return ["mixtral-8x7b-32768", "llama3-8b-8192", "llama-3.1-70b-versatile", "llama-3.3-70b-versatile"]


# Sidebar for configuration
with st.sidebar:
    st.title("⚙️ Configuration")

    # API Key input without a hardcoded default
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        value="",
        help="🔹 Get your API key from https://groq.com. Sign in, go to API Keys, and generate a new one."
    )
    
    if not api_key.strip():
        st.warning("No API key provided. Fallback static models will be used. Please enter a valid API key for dynamic model fetching.")
        model_ids = ["mixtral-8x7b-32768", "llama3-8b-8192", "llama-3.1-70b-versatile", "llama-3.3-70b-versatile"]
    else:
        model_ids = get_groq_models(api_key)
    
    # Wrap the model dropdown in a form to prevent immediate reruns
    with st.form(key="model_form"):
        selected_model = st.selectbox(
            "Select LLM Model (Groq AI Inference)",
            options=model_ids,
            help="Choose a model from Groq's available models"
        )
        submit_model = st.form_submit_button("Set Model")
        if submit_model:
            st.session_state.selected_model = selected_model
            st.success(f"Selected model: {selected_model}")

    # If no model has been submitted yet, set a default (optional)
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = model_ids[0]


    # File upload section with cleaner UI
    st.subheader("📄 Upload Documents")
    uploaded_file = st.file_uploader(
    "Upload a document",  # Provide a meaningful label
    type=["pdf", "docx", "txt"],
    help="Upload PDF, DOCX, or TXT files to provide context for the AI",
    label_visibility="collapsed"  # Hides the label while keeping accessibility
    )


    if uploaded_file:
        with st.spinner("Processing document..."):
            try:
                # Clear previous vectorstore to free memory
                if st.session_state.vectorstore:
                    del st.session_state.vectorstore
                    gc.collect()

                # Get file type and process
                file_type = uploaded_file.name.split('.')[-1].lower()
                text = st.session_state.doc_processor.process_file(
                    uploaded_file.read(),
                    file_type,
                    uploaded_file.name
                )

                # Create documents with metadata
                documents = st.session_state.doc_processor.create_documents(
                    text,
                    metadata={'source': uploaded_file.name}
                )

                # Create embeddings
                st.session_state.vectorstore = st.session_state.doc_processor.create_embeddings(documents)
                st.success("✅ Document processed successfully!")

            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")

# Main chat interface
if not api_key:
    st.warning("Please enter your Groq API key in the sidebar to start chatting.")
else:
    # Initialize chat manager
    chat_manager = ChatManager(api_key)

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get relevant context if vectorstore exists
        context = None
        if st.session_state.vectorstore and prompt:
            try:
                with st.spinner("Searching relevant context..."):
                    results = st.session_state.vectorstore.similarity_search(prompt, k=2)
                    if results:
                        context = "\n\n".join([doc.page_content for doc in results])

                        # Display context area
                        with st.expander("📚 Relevant Context", expanded=False):
                            st.markdown(f'''
                            <div class="context-area">
                            {context}
                            </div>
                            ''', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error retrieving context: {str(e)}")

        # Generate and display assistant response using Groq
        with st.chat_message("assistant"):
            response = chat_manager.generate_response(
                st.session_state.messages,
                context=context
            )
            # Only add to session state, don't display again
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

        # Clean up memory
        gc.collect()