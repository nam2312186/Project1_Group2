import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Load model 1 lần (dùng chung cho query embedding)
@lru_cache(maxsize=1)
def _get_model():
    return SentenceTransformer(EMBED_MODEL_NAME)


def _get_app_dir() -> Path:
    # .../Application/knowledge/embedding_utils.py -> Application
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_kb_embeddings():
    """
    Đọc file kb_embeddings.json chỉ 1 lần.
    Mỗi item: {id, text, embedding(np.ndarray)}
    """
    app_dir = _get_app_dir()
    emb_path = app_dir / "embeddings" / "kb_embeddings.json"

    if not emb_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file embeddings: {emb_path}. "
            f"Hãy chạy build_embeddings.py trước."
        )

    with emb_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    kb = []
    for item in data:
        vec = np.array(item["embedding"], dtype=np.float32)
        kb.append(
            {
                "id": item["id"],
                "text": item["text"],
                "embedding": vec,
            }
        )
    return kb


def get_embedding(text: str) -> np.ndarray:
    """
    Sinh embedding cho câu hỏi user bằng cùng model local.
    """
    model = _get_model()
    emb = model.encode(text, normalize_embeddings=True)
    return np.array(emb, dtype=np.float32)


def search_similar_chunks(query: str, top_k: int = 3):
    """
    Tìm các đoạn tài liệu gần nhất với câu hỏi.
    Trả về list dict: {id, text, embedding}
    """
    kb = load_kb_embeddings()
    q_emb = get_embedding(query)

    # Vì đã normalize rồi, cosine similarity = dot product
    sims = []
    for item in kb:
        v = item["embedding"]
        sim = float(np.dot(q_emb, v))
        sims.append((sim, item))

    sims.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in sims[:top_k]]
