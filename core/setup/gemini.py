import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


def summarizer(
    content: dict[str:str], doc_len: int, pages: list[int] = None
) -> dict[str:str]:
    if doc_len > 8 and pages is None:
        return {
            "message",
            "Document page is too much please select which page you want to summarize",
        }

    # Convert dictionary to a plain string
    text_input = ",".join([f"{key}: {value}" for key, value in content.items()])
    print(text_input)

    genai.configure(api_key=os.getenv("ModelApiKey"))
    model = genai.GenerativeModel("gemini-1.5-flash")
    model.start_chat(
        history=[
            {
                "role": "user",
                "parts": "You are gemini an ai assistant for summarizzation of document pages",
            },
            {
                "role": "model",
                "parts": "Okay, I'm Gemini, your AI assistant for summarizing document pages.  Please provide me with the text you'd like me to summarize.",
            },
        ]
    )

    response = model.generate_content(text_input)

    return {"model": response.text}
