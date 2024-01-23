# Generated by Django 5.0.1 on 2024-01-15 15:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WeStatsAPI', '0003_remove_measurementorder_measurement_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeasurementOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('measurement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='WeStatsAPI.measurement')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='WeStatsAPI.measurementorder')),
            ],
        ),
    ]