# Generated by Django 5.1.1 on 2024-10-12 04:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contratos_inteligentes', '0003_remove_rentalcontract_termination_fee_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rentalcontract',
            name='rent_due_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
