import os
from collections.abc import Iterator
from typing import Any

import streamlit as st
from google import genai

MODEL_NAME = "gemini-2.5-flash"


def stream_gemini_response(
    client: genai.Client, contents: list[dict[str, Any]]
) -> Iterator[str]:
    """Yield response text as Gemini generates it."""
    response_stream = client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=contents,
    )
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text


def main() -> None:
    st.set_page_config(page_title="Diaa AI", page_icon="✦")
    st.title("Diaa AI")
    st.caption("A conversational assistant powered by Diaa Wesam.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("Conversation")
        if st.button("New chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        st.caption(f"Model: {MODEL_NAME}")
        st.caption("Chat history is kept for this browser session.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Message")
    if not prompt:
        return

    with st.chat_message("user"):
        st.markdown(prompt)

    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.error(
            "Gemini is not configured yet. Add GEMINI_API_KEY in the project's "
            "Replit Secrets, then restart the app."
        )
        return

    contents = [
        {
            "role": "model" if message["role"] == "assistant" else "user",
            "parts": [{"text": message["content"]}],
        }
        for message in st.session_state.messages
    ]
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    with st.chat_message("assistant"):
        try:
            client = genai.Client(api_key=api_key)
            answer = st.write_stream(stream_gemini_response(client, contents))
        except Exception:
            st.error(
                "Gemini couldn't complete that request. Check that the API key "
                "is valid and that your Google AI usage quota is available."
            )
            return

    st.session_state.messages.extend(
        [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ]
    )


if __name__ == "__main__":
    main()
