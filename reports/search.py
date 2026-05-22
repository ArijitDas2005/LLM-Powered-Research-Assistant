import hashlib
import math
from functools import lru_cache

from django.conf import settings
from django.db import connection

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - graceful fallback for environments without model support
    SentenceTransformer = None


@lru_cache(maxsize=1)
def _load_model():
    if SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    except Exception:
        return None


def _fallback_embedding(text):
    dimension = settings.EMBEDDING_DIMENSION
    vector = [0.0] * dimension
    for token in text.lower().split():
        index = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16) % dimension
        vector[index] += 1.0
    return _normalize(vector)


def _normalize(vector):
    vector = _fit_dimension(vector)
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def _fit_dimension(vector):
    dimension = settings.EMBEDDING_DIMENSION
    cleaned = [float(value) for value in vector[:dimension]]
    if len(cleaned) < dimension:
        cleaned.extend([0.0] * (dimension - len(cleaned)))
    return cleaned


def generate_embedding(text):
    model = _load_model()
    if model is None:
        return _fallback_embedding(text)

    encoded = model.encode(text)
    return _normalize([float(value) for value in encoded])


def cosine_similarity(vector_a, vector_b):
    if not vector_a or not vector_b:
        return 0.0

    length = min(len(vector_a), len(vector_b))
    return sum(float(vector_a[index]) * float(vector_b[index]) for index in range(length))


def serialize_embedding_for_pgvector(vector):
    fitted = _fit_dimension(vector)
    return '[' + ','.join(f'{value:.8f}' for value in fitted) + ']'


def pgvector_enabled():
    return settings.USE_PGVECTOR and connection.vendor == 'postgresql'
