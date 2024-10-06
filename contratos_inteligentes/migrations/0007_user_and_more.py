# Generated by Django 5.1.1 on 2024-10-02 01:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contratos_inteligentes', '0006_alter_rentalcontract_contract_address_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_landlord', models.BooleanField(default=False)),
                ('wallet_address', models.CharField(max_length=100, unique=True)),
                ('signature', models.CharField(blank=True, max_length=132)),
            ],
            options={
                'db_table': 'usuários',
            },
        ),
        migrations.AddField(
            model_name='contracttermination',
            name='termination_transaction_hash',
            field=models.CharField(blank=True, max_length=66, unique=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payment',
            name='transaction_hash',
            field=models.CharField(default=0, max_length=66, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rentalcontract',
            name='landlord_signature',
            field=models.CharField(blank=True, max_length=132),
        ),
        migrations.AddField(
            model_name='rentalcontract',
            name='status',
            field=models.CharField(choices=[('pending', 'Pendente'), ('active', 'Ativo'), ('terminated', 'Encerrado')], default='pending', max_length=10),
        ),
        migrations.AddField(
            model_name='rentalcontract',
            name='tenant_signature',
            field=models.CharField(blank=True, max_length=132),
        ),
        migrations.CreateModel(
            name='ContractEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=50)),
                ('event_data', models.JSONField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='contratos_inteligentes.rentalcontract')),
            ],
            options={
                'db_table': 'eventos_contrato',
            },
        ),
    ]