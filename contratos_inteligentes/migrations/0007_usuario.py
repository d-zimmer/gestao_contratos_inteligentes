# Generated by Django 5.1.1 on 2024-11-12 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contratos_inteligentes", "0006_alter_rentalcontract_deposit_amount_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Usuario",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("login", models.CharField(max_length=100, unique=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("is_landlord", models.BooleanField(default=False)),
                ("id_account", models.TextField(blank=True, null=True)),
                (
                    "wallet_address",
                    models.CharField(blank=True, max_length=42, null=True),
                ),
            ],
            options={
                "db_table": "usuarios",
            },
        ),
    ]
