import os
import pyrebase
import uuid
from urllib.parse import unquote, urlparse
from dotenv import load_dotenv
from pypdf import PdfReader
from fastapi import UploadFile

load_dotenv(dotenv_path=".env")


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
