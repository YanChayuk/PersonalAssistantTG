import chromadb
from chromadb.config import Settings
import os
class VStore:
    def __init__(self, chroma_dir='./chroma_db'):
        os.makedirs(chroma_dir, exist_ok=True)
        self.client = chromadb.Client(Settings(chroma_db_impl='duckdb+parquet', persist_directory=chroma_dir))
        try:
            self.col = self.client.get_collection('assistant_docs')
        except Exception:
            self.col = self.client.create_collection('assistant_docs')
    def add(self, doc_id, text, meta=None):
        self.col.add(ids=[doc_id], documents=[text], metadatas=[meta or {}])
        self.client.persist()
    def search(self, text, k=3):
        try:
            results = self.col.query(queries=[text], n_results=k)
            docs = []
            for r in results['documents'][0]:
                docs.append(r)
            return docs
        except Exception:
            return []
    def ping(self):
        try:
            _ = self.client.list_collections()
            return True
        except:
            return False
