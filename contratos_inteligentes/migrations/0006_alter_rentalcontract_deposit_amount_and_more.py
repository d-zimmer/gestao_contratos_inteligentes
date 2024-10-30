# Generated by Django 5.1.1 on 2024-10-27 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contratos_inteligentes", "0005_alter_rentalcontract_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rentalcontract",
            name="deposit_amount",
            field=models.DecimalField(decimal_places=2, max_digits=38),
        ),
        migrations.AlterField(
            model_name="rentalcontract",
            name="rent_amount",
            field=models.DecimalField(decimal_places=2, max_digits=38),
        ),
    ]
