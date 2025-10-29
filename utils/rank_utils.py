import numpy as np
from typing import List, Dict, Sequence, Tuple
from utils.vector_utils import embed_texts  # reuse same local embedding model


def _normalize(xs: Sequence[float]) -> List[float]:
    xs = list(xs)
    if not xs:
        return []
    mn, mx = min(xs), max(xs)
    if mx - mn < 1e-9:
        return [0.0 for _ in xs]
    return [(x - mn) / (mx - mn) for x in xs]


def semantic_scores(query: str, docs: List[str]) -> List[float]:
    """Cosine similarity between query and docs using the same local embed model."""
    # Embed query and docs
    qv = embed_texts([query])[0]
    D = embed_texts([d if d else "" for d in docs])
    # cosine
    qn = np.linalg.norm(qv) + 1e-9
    Dn = np.linalg.norm(D, axis=1) + 1e-9
    sims = (D @ qv) / (Dn * qn)
    return sims.tolist()


def hybrid_scores(sem_vec_metadata: List[float],
                  sem_vec_content: List[float],
                  m_sem: float = 0.5,
                  c_sem: float = 0.5) -> List[float]:
    m = _normalize(sem_vec_metadata)
    s = _normalize(sem_vec_content)
    # s = sem_vec
    return [m_sem * bi + c_sem * si for bi, si in zip(m, s)]

def topk_by(scores: List[float], items: List[Dict], k: int) -> List[Dict]:
    ranked = sorted(zip(items, scores), key=lambda x: -x[1])
    return [it for it, _ in ranked[:k]]
