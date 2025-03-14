import os
from typing import List, Dict
import groq
import streamlit as st

class ChatManager:
    def __init__(self, api_key: str):
        self.client = groq.Client(api_key=api_key)

    def generate_response(self, messages: List[Dict], context: str = None, model: str = "mixtral-8x7b-32768") -> str:
        formatted_messages = []

        # Add system message with context if available
        if context:
            system_content = (
                "You are a helpful AI assistant. Use the following context to answer questions:\n\n"
                f"{context}\n\n"
                "If the context doesn't help answer the question, you can draw from your general knowledge. "
                "Always be clear about which information comes from the context and which is from general knowledge."
            )
            formatted_messages.append({
                "role": "system",
                "content": system_content
            })

        # Format chat history
        for message in messages:
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"]
            })

        try:
            # Generate streaming response using the provided model parameter
            chat_response = self.client.chat.completions.create(
                messages=formatted_messages,
                model=model,
                temperature=0.7,
                stream=True
            )

            # Initialize response placeholder
            response_placeholder = st.empty()
            full_response = ""

            # Stream the response
            for chunk in chat_response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")

            # Show final response (without cursor)
            response_placeholder.markdown(full_response)
            return full_response

        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            st.error(error_message)
            return error_message