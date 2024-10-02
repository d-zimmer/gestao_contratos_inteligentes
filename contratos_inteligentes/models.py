from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

STATUS_CHOICES = [
    ('pending', 'Pendente'),
    ('active', 'Ativo'),
    ('terminated', 'Encerrado'),
]

# Modelo para armazenar dados de um contrato de aluguel
class RentalContract(models.Model):
    landlord = models.CharField(max_length=42)
    tenant = models.CharField(max_length=42)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    contract_address = models.CharField(max_length=42)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    landlord_signature = models.CharField(max_length=132, blank=True)
    tenant_signature = models.CharField(max_length=132, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if len(self.contract_address) != 42:
            raise ValidationError('Endereço do contrato deve ter 42 caracteres.')

    def __str__(self):
        return f"Contrato de {self.landlord} para {self.tenant}"
    
    def is_fully_signed(self):
        return bool(self.landlord_signature) and bool(self.tenant_signature)

    class Meta:
        db_table = 'contratos'

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_landlord = models.BooleanField(default=False)  # True se o usuário for locador
    wallet_address = models.CharField(max_length=100, unique=True)  # Para guardar o endereço da wallet blockchain
    signature = models.CharField(max_length=132, blank=True)  # Assinatura digital
    
    def clean(self):
        if len(self.wallet_address) != 42:
            raise ValidationError('Endereço da wallet deve ter 42 caracteres.')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'usuários'

class Payment(models.Model):
    contract = models.ForeignKey(RentalContract, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=10, choices=[('rent', 'Aluguel'), ('deposit', 'Depósito')])
    payment_date = models.DateTimeField(default=timezone.now)  # Data do pagamento
    is_verified = models.BooleanField(default=False)
    paid_at = models.DateTimeField(default=timezone.now)
    transaction_hash = models.CharField(max_length=66, unique=True)

    def __str__(self):
        return f"Pagamento {self.payment_type} de {self.amount} para o contrato {self.contract}"

    class Meta:
        db_table = 'pagamento_contrato'

class ContractTermination(models.Model):
    contract = models.OneToOneField(RentalContract, on_delete=models.CASCADE)
    termination_date = models.DateTimeField(default=timezone.now)  # Data de encerramento do contrato
    terminated_by = models.CharField(max_length=42)  # Quem encerrou o contrato (locador ou inquilino)
    termination_transaction_hash = models.CharField(max_length=66, unique=True, blank=True)  # Hash do encerramento na blockchain

    def __str__(self):
        return f"Encerramento do contrato {self.contract} por {self.terminated_by}"
    
    class Meta:
        db_table = 'encerramento_contrato'
        
class ContractEvent(models.Model):
    contract = models.ForeignKey(RentalContract, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50)  # Ex: 'created', 'signed', 'terminated', etc.
    event_data = models.JSONField()  # Informações adicionais do evento, ex: hash da transação
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eventos_contrato'