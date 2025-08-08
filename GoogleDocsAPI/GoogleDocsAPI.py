import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleDocsService:
    def __init__(self, document_id, credentials_path="./credentials.json", token_path="./token.json"):
        self.SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
        self.document_id = document_id
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service = None

    def authorize(self):
        """Handles authorization and credential setup."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open(self.token_path, "w") as token:
                token.write(self.creds.to_json())

    def build_service(self):
        """Builds the Docs API service. Needs authorization first"""
        try:
            self.service = build("docs", "v1", credentials=self.creds)
        except HttpError as err:
            print(f"Error building service: {err}")

    def get_document(self, document_id=None):
        """Retrieves document content."""
        if document_id is not None:
            self.document_id = document_id
        try:
            document = self.service.documents().get(documentId=self.document_id, includeTabsContent=True).execute()
            return document
        except HttpError as err:
            print(f"Error retrieving document: {document_id}")
            return None

    @staticmethod
    def document_content(document):
        """Returns list of all document contents"""

        if not document:
            print("No document found.")
            return []
        return document.get('body', {}).get('content', [])

    @staticmethod
    def get_tab(document=None, get_filter=None, by_name=True):
        if not document or not get_filter:
            return None
        for tab in document['tabs']:
            if by_name and tab['tabProperties'].get('title') == get_filter:
                return tab
            if not by_name and tab['tabProperties'].get('id') == get_filter:
                return tab

    @staticmethod
    def tab_text(tab):
        if not tab:
            return ''
        text_chunks = []
        for element in tab['documentTab']['body']['content']:
            if 'paragraph' in element:
                for run in element['paragraph'].get('elements', []):
                    text = run.get('textRun', {}).get('content')
                    if text:
                        text_chunks.append(text.strip())
        full_text = "".join(text_chunks)
        return full_text

    @staticmethod
    def document_text(document):
        """ Returns all text the document contains."""
        if not document:
            print("No document found.")
            return ''

        print(f"Document title: {document.get('title')}")
        content = document.get('body', {}).get('content', [])
        buffer = ""
        for element in content:
            if "paragraph" in element:
                for run in element["paragraph"].get("elements", []):
                    text = run.get("textRun", {}).get("content")
                    if text:
                        buffer += text
        return buffer

    def run(self, document_id=None):
        """Convenient method to run everything."""
        self.authorize()
        self.build_service()
        doc = self.get_document(document_id)
        print(self.document_text(doc))


