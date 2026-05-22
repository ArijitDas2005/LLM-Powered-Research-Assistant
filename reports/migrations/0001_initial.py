from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('research', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResearchReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=255)),
                ('company_overview', models.TextField()),
                ('market_position', models.TextField()),
                ('financial_health', models.TextField()),
                ('recent_developments', models.TextField()),
                ('key_risks', models.TextField()),
                ('opportunities', models.TextField()),
                ('overall_sentiment', models.PositiveSmallIntegerField()),
                ('full_report_text', models.TextField()),
                ('embedding', models.JSONField(blank=True, default=list)),
                ('source_payload', models.JSONField(blank=True, default=dict)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='report', to='research.researchjob')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='users.user')),
            ],
            options={
                'ordering': ['-generated_at'],
            },
        ),
    ]
