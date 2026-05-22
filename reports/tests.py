import pytest

from reports.search import cosine_similarity, generate_embedding, serialize_embedding_for_pgvector


def test_cosine_similarity_handles_empty_vectors():
    assert cosine_similarity([], [1.0, 0.0]) == 0.0
    assert cosine_similarity([1.0, 0.0], []) == 0.0


def test_generate_embedding_respects_configured_dimension(settings, monkeypatch):
    settings.EMBEDDING_DIMENSION = 8
    monkeypatch.setattr('reports.search._load_model', lambda: None)

    embedding = generate_embedding('high growth ai company')

    assert len(embedding) == 8


def test_pgvector_serialization_uses_pgvector_literal_format(settings):
    settings.EMBEDDING_DIMENSION = 4

    serialized = serialize_embedding_for_pgvector([1, 2])

    assert serialized.startswith('[')
    assert serialized.endswith(']')
    assert serialized.count(',') == 3
