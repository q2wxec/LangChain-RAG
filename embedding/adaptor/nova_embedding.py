from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import BaseModel
from typing import Any, Dict, List, Optional

class NovaEmbeddings(BaseModel, Embeddings):
    st_ak: Optional[str] = None
    st_sk: Optional[str] = None
    model: Optional[str] = "nova-embedding-stable"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a HuggingFace transformer model.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        import sensenova
        sensenova.access_key_id = self.st_ak
        sensenova.secret_access_key = self.st_sk

        texts = list(map(lambda x: x.replace("\n", " "), texts))
        resp = sensenova.Embedding.create(
            model=self.model,
            input=texts
        )
        embeddings = resp['embeddings']
        result = list(map(lambda x: x['embedding'], embeddings))
        return result
    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        return self.embed_documents([text])[0]