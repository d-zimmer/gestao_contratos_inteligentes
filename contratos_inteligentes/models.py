from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

# Opções de status para o contrato
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

# Modelo para usuários (locador e inquilino)
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_landlord = models.BooleanField(default=False)
    wallet_address = models.CharField(max_length=42, unique=True)  # Endereço da wallet blockchain
    signature = models.CharField(max_length=132, blank=True)  # Assinatura digital

    def clean(self):
        if len(self.wallet_address) != 42:
            raise ValidationError('Endereço da wallet deve ter 42 caracteres.')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'usuarios'

# Modelo para pagamentos de aluguel e depósito
class Payment(models.Model):
    contract = models.ForeignKey(RentalContract, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=10, choices=[('rent', 'Aluguel'), ('deposit', 'Depósito')])
    payment_date = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    transaction_hash = models.CharField(max_length=66, unique=True)

    def __str__(self):
        return f"Pagamento {self.payment_type} de {self.amount} para o contrato {self.contract}"

    class Meta:
        db_table = 'pagamento_contrato'

# Modelo para encerramento de contrato
class ContractTermination(models.Model):
    contract = models.OneToOneField(RentalContract, on_delete=models.CASCADE)
    termination_date = models.DateTimeField(default=timezone.now)
    terminated_by = models.CharField(max_length=42)
    termination_transaction_hash = models.CharField(max_length=66, unique=True, blank=True)

    def __str__(self):
        return f"Encerramento do contrato {self.contract} por {self.terminated_by}"

    class Meta:
        db_table = 'encerramento_contrato'

# Modelo para eventos de contrato
class ContractEvent(models.Model):
    EVENT_TYPES = [
        ('create', 'Create Contract'),
        ('sign', 'Sign Contract'),
        ('pay_rent', 'Pay Rent'),
        ('pay_deposit', 'Pay Deposit'),
        ('execute', 'Execute Contract'),
        ('terminate', 'Terminate Contract'),
    ]
    
    contract = models.ForeignKey(RentalContract, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    user_address = models.CharField(max_length=42)  # Endereço do usuário que realizou a ação
    event_data = models.JSONField()  # Informações adicionais do evento, ex: hash da transação
    transaction_hash = models.CharField(max_length=66, blank=True, null=True)  # Hash da transação no blockchain
    from_address = models.CharField(max_length=42, blank=True, null=True)  # Endereço de quem fez a transação
    gas_used = models.BigIntegerField(blank=True, null=True)  # Opcional: quantidade de gas usado
    block_number = models.BigIntegerField(blank=True, null=True)  # Opcional: número do bloco
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.event_type} no contrato {self.contract.id}"

    class Meta:
        db_table = 'eventos_contrato'
