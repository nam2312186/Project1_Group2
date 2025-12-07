import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

# ==============================
# 1. CẤU HÌNH MODEL EMBEDDING LOCAL
# ==============================
# Model đa ngôn ngữ: hỗ trợ cả tiếng Việt & Anh
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

model = SentenceTransformer(EMBED_MODEL_NAME)


def chunk_text(raw: str, max_chars: int = 800):
    """
    Cắt data_dictionary thành nhiều đoạn (chunk) vừa phải.
    Ở đây demo: tách theo 2 dòng trống, rồi gộp cho đủ max_chars.
    Bạn có thể chỉnh lại cho phù hợp format file.
    """
    parts = [p.strip() for p in raw.split("\n\n") if p.strip()]

    chunks = []
    buffer = ""
    for p in parts:
        if len(buffer) + len(p) + 2 <= max_chars:
            buffer = (buffer + "\n\n" + p) if buffer else p
        else:
            if buffer:
                chunks.append(buffer)
            buffer = p
    if buffer:
        chunks.append(buffer)

    return chunks


def get_embedding(text: str):
    # Trả về list[float] để ghi vào JSON
    emb = model.encode(text, normalize_embeddings=True)
    return emb.tolist()


def main():
    # .../Application/knowledge/build_embeddings.py  -> Application
    app_dir = Path(__file__).resolve().parents[1]
    knowledge_dir = app_dir / "knowledge"
    embeddings_dir = app_dir / "embeddings"
    embeddings_dir.mkdir(exist_ok=True)

    data_path = knowledge_dir / "data_dictionary.txt"
    out_path = embeddings_dir / "kb_embeddings.json"

    if not data_path.exists():
        raise FileNotFoundError(f"Không tìm thấy {data_path}")

    raw = data_path.read_text(encoding="utf-8")
    chunks = chunk_text(raw)
    print(f"Tổng số chunk: {len(chunks)}")

    items = []
    for idx, chunk in enumerate(chunks):
        emb = get_embedding(chunk)
        items.append(
            {
                "id": idx,
                "text": chunk,
                "embedding": emb,
            }
        )
        print(f"Đã embed chunk {idx} (độ dài {len(chunk)} ký tự)")

    out_path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Đã lưu embeddings vào: {out_path}")


if __name__ == "__main__":
    main()
