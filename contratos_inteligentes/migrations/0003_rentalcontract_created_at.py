# Generated by Django 5.1.1 on 2024-10-01 00:07

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contratos_inteligentes', '0002_alter_rentalcontract_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='rentalcontract',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
