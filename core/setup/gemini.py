import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


chat_history = [
    {
        "role": "user",
        "parts": "You are gemini an ai assistant for summarizzation of document pages, you also give insights on the document",
    },
    {
        "role": "model",
        "parts": "Okay, I'm Gemini, If you share the document or details about its content, I’ll summarize it for you and provide key insights or actionable points based on its information. Upload or describe the document whenever you're ready!",
    },
]


async def summarizer(
    content, doc_len: int = None, pages: list[int] = None
) -> dict[str:str]:

    global chat_history

    text_input = content

    if doc_len is not None and doc_len > 5 and pages is None:
        return {
            "message",
            "Document page is too much please select which page you want to summarize",
        }

    if type(content) is dict:
        # Convert dictionary to a plain string
        text_input = "\n".join([f"{key}: {value}" for key, value in content.items()])

    genai.configure(api_key=os.getenv("ModelApiKey"))
    model = genai.GenerativeModel("gemini-1.5-flash")
    chat = model.start_chat(history=chat_history)

    chat_history.append({"role": "user", "parts": text_input})

    response = chat.send_message(text_input)

    chat_history.append({"role": "model", "parts": response.text})

    return {"model": response.text}
