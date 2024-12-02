import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
from typing import List, Dict, Optional, Union


async def construct_history(
    chat_data: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """
    Constructs the chat history for the AI model.

    Args:
        chat_data (Optional[List[Dict[str, str]]]): Existing chat data with `type` and `text`.

    Returns:
        List[Dict[str, str]]: A list of chat history formatted for the AI model.
    """
    # Base chat history
    chat_history = [
        {
            "role": "user",
            "parts": """
            You are an advanced summarization and comprehension assistant. Your tasks are as follows:
            Summarize: When given a passage, create a clear, concise, and accurate summary of its key points while preserving all essential information.
            Answer Questions: If asked questions after the summary, respond only based on the summarized content and the original passage. Avoid making assumptions or adding unrelated information.
            Guidelines for Answers: Your responses should be factual, specific, and directly reference the passage or summary.
            """,
        },
    ]

    # Append additional messages from chat_data
    if chat_data:
        for message in chat_data:
            if (
                not isinstance(message, dict)
                or "type" not in message
                or "text" not in message
            ):
                raise ValueError(
                    "Each message must be a dictionary with 'type' and 'text' keys."
                )

            if message["type"] == "sent":
                chat_history.append({"role": "user", "parts": message["text"]})
            elif message["type"] == "received":
                chat_history.append({"role": "model", "parts": message["text"]})
            else:
                raise ValueError(f"Unknown message type: {message['type']}")

    return list(chat_history)


async def summarizer(
    content: str,
    chat: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, str]:
    """
    Summarizes content with an AI model, optionally incorporating chat history.

    Args:
        content (Union[Dict[str, str], str]): The content to summarize, either as a dictionary or plain text.
        chat (Optional[List[Dict[str, str]]]): Chat history to use for context.

    Returns:
        Dict[str, str]: The model's response text.
    """
    # Construct chat history
    if chat is not None:
        history = await construct_history(chat)
    else:
        history = await construct_history()

    if isinstance(history, object):
        print("object")

    # Configure and interact with the model
    genai.configure(api_key=os.getenv("ModelApiKey"))
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Start a chat session with the constructed history
    chat_session = model.start_chat(history=history)
    response = chat_session.send_message(content)

    return {"model": response.text}
