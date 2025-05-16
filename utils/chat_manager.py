from typing import List, Dict
import streamlit as st
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.chains import ConversationChain

class ChatManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.memory = ConversationBufferMemory()

    def generate_response(self, messages: List[Dict], context: str = None, model: str = None) -> str:
        model = model or "deepseek-r1-distill-llama-70b"
        
        try:
            # Initialize chat model
            llm = ChatGroq(
                groq_api_key=self.api_key,
                model_name=model,
                temperature=0.7,
                streaming=True
            )

            # Format messages for LangChain
            formatted_messages = []
            if context:
                formatted_messages.append(SystemMessage(content=f"Use this context to answer questions: {context}"))

            for msg in messages:
                if msg["role"] == "user":
                    formatted_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    formatted_messages.append(AIMessage(content=msg["content"]))

            # Create conversation chain
            chain = ConversationChain(
                llm=llm,
                memory=self.memory,
                verbose=True
            )

            # Generate streaming response
            response_placeholder = st.empty()
            full_response = ""

            for chunk in chain.stream({"input": messages[-1]["content"]}):
                if isinstance(chunk, dict) and "response" in chunk:
                    full_response += chunk["response"]
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            return full_response

        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            st.error(error_message)
            return error_message