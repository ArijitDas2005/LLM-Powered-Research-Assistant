from django.db import migrations, models


def create_pgvector_extension(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return

    dimension = 384
    table_name = apps.get_model('reports', 'ResearchReport')._meta.db_table
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    schema_editor.execute(
        f'''
        CREATE INDEX IF NOT EXISTS {table_name}_embedding_vector_ivfflat
        ON {table_name}
        USING ivfflat ((embedding_vector::vector({dimension})) vector_cosine_ops)
        WITH (lists = 100);
        '''
    )


def drop_pgvector_index(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return

    table_name = apps.get_model('reports', 'ResearchReport')._meta.db_table
    schema_editor.execute(f'DROP INDEX IF EXISTS {table_name}_embedding_vector_ivfflat;')


class Migration(migrations.Migration):
    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='researchreport',
            name='embedding_vector',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.RunPython(create_pgvector_extension, drop_pgvector_index),
    ]
