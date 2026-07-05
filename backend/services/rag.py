"""
services/rag.py — Runtime PDF embeddings + JD similarity via FAISS
No external vector DB needed — all computed in-memory per request.
"""
import re
import numpy as np

# sentence-transformers is loaded lazily so startup is fast
_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # Small, fast model — good accuracy vs speed trade-off
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model



def chunk_text(text: str, chunk_size: int = 200) -> list[str]:
    """
    Split text into overlapping chunks of ~chunk_size words.
    Overlap ensures context isn't lost at boundaries.
    """
    words = text.split()
    chunks = []
    step = int(chunk_size * 0.75)  # 25% overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks



def embed_texts(texts: list[str]) -> np.ndarray:
    """Return L2-normalised embeddings (n, dim)."""
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # Normalise for cosine similarity via dot product
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / np.maximum(norms, 1e-9)



def jd_similarity_score(resume_text: str, jd_text: str) -> dict:
    """
    Compute semantic similarity between resume and job description.
    Returns overall score (0-100), top matching chunks, and gap analysis.
    """
    import faiss

    resume_chunks = chunk_text(resume_text)
    jd_chunks     = chunk_text(jd_text)

    if not resume_chunks or not jd_chunks:
        return {"score": 0, "top_matching_chunks": [], "gaps": []}

    # Embed everything
    resume_embs = embed_texts(resume_chunks)  # (n_resume, dim)
    jd_embs     = embed_texts(jd_chunks)      # (n_jd, dim)

    dim = resume_embs.shape[1]

    # Build FAISS index over resume chunks
    index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity (because normalised)
    index.add(resume_embs.astype(np.float32))

    # For each JD chunk, find best matching resume chunk
    k = min(3, len(resume_chunks))
    D, I = index.search(jd_embs.astype(np.float32), k)

    # Overall score = mean of best match per JD chunk (scaled 0-100)
    best_scores = D[:, 0]  # best match per JD chunk
    overall_score = round(float(np.mean(best_scores)) * 100)
    overall_score = max(0, min(100, overall_score))

    # Top matching resume chunks (highest similarity to any JD chunk)
    best_resume_indices = np.unique(I[:, 0])
    top_matches = [resume_chunks[i] for i in best_resume_indices[:3]]

    # Gap detection: JD chunks with low similarity = missing coverage
    gaps = []
    for jd_idx, score in enumerate(best_scores):
        if score < 0.45:  # below threshold = gap
            jd_chunk = jd_chunks[jd_idx]
            # Extract key phrases (noun phrases / skills) from the gap chunk
            keywords = _extract_keywords(jd_chunk)
            if keywords:
                gaps.extend(keywords)

    gaps = list(dict.fromkeys(gaps))[:8]  # deduplicate, top 8

    return {
        "score":               overall_score,
        "top_matching_chunks": top_matches,
        "gaps":                gaps,
    }



def _extract_keywords(text: str) -> list[str]:
    """
    Lightweight keyword extraction using regex patterns.
    Targets short capitalized phrases and known tech terms.
    """
    # Capitalised multi-word phrases (e.g. "Machine Learning", "CI/CD Pipeline")
    phrases = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text)
    # Tech terms: things with /, digits, or known patterns
    tech = re.findall(r"\b(?:CI/CD|REST|API|SQL|NoSQL|AWS|GCP|Azure|Docker|K8s|React|Node\.js)\b",
                      text, re.IGNORECASE)
    all_kw = phrases + tech
    # Filter short noise
    return [kw for kw in all_kw if len(kw) > 3][:5]
