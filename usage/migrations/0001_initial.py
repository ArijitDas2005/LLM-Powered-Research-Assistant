from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('reports', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UsageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_type', models.CharField(choices=[('api_request', 'API Request'), ('llm_research', 'LLM Research')], default='api_request', max_length=20)),
                ('endpoint', models.CharField(max_length=255)),
                ('method', models.CharField(blank=True, max_length=10)),
                ('status_code', models.PositiveSmallIntegerField(default=200)),
                ('llm_input_tokens', models.PositiveIntegerField(default=0)),
                ('llm_output_tokens', models.PositiveIntegerField(default=0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('report', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage_logs', to='reports.researchreport')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usage_logs', to='users.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
