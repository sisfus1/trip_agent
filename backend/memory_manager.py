import os
import chromadb
from chromadb.config import Settings

class MemoryManager:
    """
    负责管理 Trip Agent 的向量记忆，支持用户偏好的存储与查询。
    专为 HuggingFace Spaces Persistent Storage 优化。
    """
    
    def __init__(self):
        # 适配 HuggingFace Spaces 持久化存储
        # 默认优先读取 CHROMA_PERSIST_DIRECTORY，若无则使用 ./chroma_db 本地路径
        persist_dir = os.environ.get("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        
        # 初始化持久化客户端
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建用户偏好记忆集合
        self.collection = self.client.get_or_create_collection(
            name="user_preferences",
            metadata={"hnsw:space": "cosine"} # 使用余弦相似度
        )
        print(f"[MemoryManager] ChromaDB initialized at {persist_dir} with collection 'user_preferences'")

    def add_memory(self, doc_id: str, text: str, metadata: dict | None = None):
        """存储单条记忆记录"""
        self.collection.upsert(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )

    def search_memory(self, query: str, n_results: int = 3):
        """检索相关的记忆记录"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

# 全局单例
memory_manager = MemoryManager()
