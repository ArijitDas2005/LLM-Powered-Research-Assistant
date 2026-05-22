from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('reports', '0002_researchreport_embedding_vector'),
    ]

    operations = [
        migrations.AddField(
            model_name='researchreport',
            name='analyst_notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='researchreport',
            name='is_bookmarked',
            field=models.BooleanField(default=False),
        ),
    ]
