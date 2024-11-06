import os.path

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain.document_loaders.base import BaseLoader
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import spacy
import re

#loads spaCy in english
nlp = spacy.load("en_core_web_sm")

#directory for storing embeddings
PERSIST_DIRECTORY = "./chroma_db"

#custom loader that inherits from LangChain's BaseLoader
class WebPageDocumentLoader(BaseLoader):
    #initialize loader with url parameter that represents the webpage to load
    def __init__(self, url: str):
        self.url = url

    #method that loads the document
    def load(self):
        #starts playwright in synchronous mode
        with sync_playwright() as p:
            #launches chromium browser instance
            browser = p.chromium.launch()
            #opens new browser tab
            page = browser.new_page()
            #navigates to url specified in loader
            page.goto(self.url)
            #extracts html content
            html_content = page.content()
            #closes browser
            browser.close()

        #use beautifulsoup to parse and clean html
        soup = BeautifulSoup(html_content, "html.parser")

        #loops through defined html tags
        for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
            #removes the elements along with their children
            element.decompose()

        #returns all human-readable text and concatenates with a space
        text = soup.get_text(separator=" ")
        #replaces consecutive whitespace with a single space and strips leading and trailing whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        #split text into sentences using spaCy
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]

        #chunks sentences into groups of 10
        chunks = [" ".join(sentences[i:i + 10]) for i in range(0, len(sentences), 10)]

        #converts chunks into langchain documents with source metadata
        chunked_documents = [
            Document(page_content=chunk.strip(), metadata={"source": self.url})
            for i, chunk in enumerate(chunks) if chunk.strip()
        ]

        return chunked_documents


#initialize the embedding model
embedding_model = HuggingFaceEmbeddings(
    model_name="arkohut/jina-embeddings-v3",
    model_kwargs={"trust_remote_code": True, "device": "cuda"}
)

def get_vector_store():
    if os.path.exists(PERSIST_DIRECTORY):
        vector_store = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding_model)
    else:
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        vector_store = Chroma(
            collection_name="webpage_chunks",
            embedding_function=embedding_model,
            persist_directory=PERSIST_DIRECTORY
        )

    return vector_store


def add_embeddings_to_vector_store(loader, vector_store):
    chunked_documents = loader.load()
    texts = [doc.page_content for doc in chunked_documents]
    metadatas = [doc.metadata for doc in chunked_documents]

    vector_store.add_texts(texts=texts, metadatas=metadatas)


loader = WebPageDocumentLoader("https://arxiv.org/abs/2406.01627")

vector_store = get_vector_store()

add_embeddings_to_vector_store(loader, vector_store)

