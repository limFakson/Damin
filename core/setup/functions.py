import os
import pyrebase
import uuid
import ast
from urllib.parse import unquote, urlparse
from pypdf import PdfReader
from fastapi import UploadFile
from dotenv import load_dotenv
from gtts import gTTS
from pydub import AudioSegment

load_dotenv()


class FirebaseStorage:
    def __init__(self, file=None, document=None):
        self.file = file
        self.document = document

        # Firebase config for storage
        self.storage_config = {
            "apiKey": os.getenv("ApiKey"),
            "authDomain": os.getenv("AuthDomain"),
            "projectId": os.getenv("ProjectId"),
            "storageBucket": os.getenv("StorageBucket"),
            "messagingSenderId": os.getenv("SenderId"),
            "appId": os.getenv("AppId"),
            "measurementId": os.getenv("MeasureId"),
            "databaseURL": os.getenv("DatabaseUrl"),
        }

        # Initialise pyrebase to activate storage
        firebase = pyrebase.initialize_app(self.storage_config)
        self.storage = firebase.storage()
        self.auth = firebase.auth()

    # function to store document files
    def store_document(self):
        complete_filename = self.file.filename
        filename, ext = os.path.splitext(complete_filename)
        if ext in [".png", ".jpeg", ".jpg", ".svg"]:
            storage_name = f"image/{uuid.uuid4()}{ext}"
        elif ext in [".docs", ".dox", ".pdf", ".txt"]:
            storage_name = f"document/{uuid.uuid1()}{ext}"
        else:
            storage_name = f"media/{uuid.uuid4()}{ext}"

        file_content = self.file.file.read()

        # Store file in Firebase storage
        self.storage.child(storage_name).put(file_content)

        # Storage url from firebase storage
        storage_url = self.storage.child(storage_name).get_url(None)

        return storage_url, filename, ext

    # function to store document files
    def store_audio(self, file, ext):
        storage_name = f"audio/{uuid.uuid4()}{ext}"

        # Store file in Firebase storage
        self.storage.child(storage_name).put(file)

        # Storage url from firebase storage
        storage_url = self.storage.child(storage_name).get_url(None)

        return storage_url

    def delete(self, file_url):
        # Authenticate user and get the token
        user = self.auth.sign_in_with_email_and_password(
            os.getenv("Email"), os.getenv("password")
        )
        user_token = user["idToken"]

        # Extract the path after '/o/'
        parsed_url = urlparse(file_url)
        path = parsed_url.path.split("/o/")[-1]

        # Decode URL-encoded characters
        relative_path = unquote(path)
        print("Path to delete:", relative_path)

        # Delete image using decoded path
        self.storage.delete(relative_path, user_token)
        return True


def extract_content(docs: UploadFile, ext):
    if ext == ".pdf":
        reader = PdfReader(docs.file)
        number_of_pages = len(reader.pages)
        text_extracted = []

        for i in range(number_of_pages):
            page = reader.pages[i]
            text = page.extract_text()
            text_extracted.append(text)
    else:
        return

    return str(text_extracted), number_of_pages


async def make_audio(content, pref_len):
    """
    Generate audio for selected pages and merge them into a single MP3 file.

    Args:
        content (str): Content in string format representing a dictionary of pages.
        pref_len (list[int]): List of page numbers to be converted to audio.

    Returns:
        str: The path to the merged MP3 file.
    """
    # Convert content string to a dictionary
    vdata_list = ast.literal_eval(content)
    extracted_list = [vdata_list[i] for i in pref_len]

    # Generate and save audio for each selected page
    audio_segments = []
    temp_files = []  # Keep track of temporary audio files
    for idx, page_text in enumerate(extracted_list):
        tts = gTTS(page_text)
        page_audio_path = f"page_{idx + 1}.mp3"
        tts.save(page_audio_path)

        # Load the audio into pydub for merging
        audio_segment = AudioSegment.from_file(page_audio_path)
        audio_segments.append(audio_segment)

        # Add file to the temp list for deletion later
        temp_files.append(page_audio_path)

    # Merge all audio files into one
    merged_audio = sum(audio_segments)

    # Save the merged audio file
    merged_audio_path = "merged_speech.mp3"
    merged_audio.export(merged_audio_path, format="mp3")

    # Delete temporary audio files
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    # Store merged audio to firebase
    firebase_storage_path = f"audio_files/{merged_audio_path}"
    firebase = FirebaseStorage()
    audio_url = firebase.store_audio(merged_audio_path, "mp3")

    return audio_url
