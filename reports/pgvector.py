from collections import OrderedDict

from django.db import connection

from reports.models import ResearchReport
from reports.search import pgvector_enabled, serialize_embedding_for_pgvector


def search_reports_with_pgvector(user_id, query_embedding, limit=5):
    if not pgvector_enabled():
        return None

    vector_literal = serialize_embedding_for_pgvector(query_embedding)
    table_name = ResearchReport._meta.db_table
    sql = f"""
        SELECT id, 1 - (embedding_vector::vector <=> %s::vector) AS similarity
        FROM {table_name}
        WHERE user_id = %s AND embedding_vector <> ''
        ORDER BY embedding_vector::vector <=> %s::vector
        LIMIT %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [vector_literal, user_id, vector_literal, limit])
        rows = cursor.fetchall()

    if not rows:
        return []

    similarity_map = OrderedDict((report_id, float(similarity)) for report_id, similarity in rows)
    reports = ResearchReport.objects.filter(id__in=similarity_map.keys(), user_id=user_id)
    reports_by_id = {report.id: report for report in reports}
    ordered_reports = []
    for report_id, similarity in similarity_map.items():
        report = reports_by_id.get(report_id)
        if report is not None:
            report.similarity = similarity
            ordered_reports.append(report)
    return ordered_reports
