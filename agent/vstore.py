import chromadb
import os

class VStore:
    def __init__(self, chroma_dir='./chroma_db'):
        os.makedirs(chroma_dir, exist_ok=True)
        # New ChromaDB API - no Settings needed
        # Disable telemetry to avoid errors
        os.environ['ANONYMIZED_TELEMETRY'] = 'False'
        self.client = chromadb.PersistentClient(path=chroma_dir)
        try:
            self.col = self.client.get_collection('assistant_docs')
        except Exception:
            self.col = self.client.create_collection('assistant_docs')
    
    def add(self, doc_id, text, meta=None):
        self.col.add(ids=[doc_id], documents=[text], metadatas=[meta or {}])
        # No need to call persist() - PersistentClient handles it automatically
    
    def search(self, text, k=3):
        try:
            results = self.col.query(query_texts=[text], n_results=k)
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
