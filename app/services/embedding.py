from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_name = "all-MiniLM-L6-v2"

    def _load_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)

    def generate(self, text: str) -> list[float]:
        """Generate embedding for text"""
        self._load_model()
        if not text or not text.strip():
            return [0.0] * 384
        embedding = self.model.encode(text.strip(), normalize_embeddings=True)
        return embedding.tolist()


embedding_service = EmbeddingService()
