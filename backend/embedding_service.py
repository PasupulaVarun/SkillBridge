import math
import re

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

_MODEL = None

def _model():
    global _MODEL
    if _MODEL is None and SentenceTransformer is not None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL

def normalize_text(items):
    return ", ".join(re.sub(r"\s+", " ", str(x).strip().lower()) for x in items if str(x).strip())

def _hash_embedding(text, dims=128):
    vec = [0.0] * dims
    for token in re.findall(r"[a-z0-9+#.-]+", text.lower()):
        vec[hash(token) % dims] += 1.0
    norm = math.sqrt(sum(x*x for x in vec)) or 1.0
    return [x / norm for x in vec]

def embed(items):
    text = normalize_text(items)
    model = _model()
    if model:
        return model.encode(text, normalize_embeddings=True).tolist()
    return _hash_embedding(text)

def cosine(a,b):
    if not a or not b or len(a)!=len(b): return 0.0
    return max(-1.0,min(1.0,sum(x*y for x,y in zip(a,b))))
