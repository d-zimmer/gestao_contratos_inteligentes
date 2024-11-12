from django.core.exceptions import ValidationError  # type: ignore
from django.db import models  # type: ignore
from django.utils import timezone  # type: ignore

STATUS_CHOICES = [
    ("pending", "Pendente"),
    ("active", "Ativo"),
    ("terminated", "Encerrado"),
]

class RentalContract(models.Model):
    landlord = models.CharField(max_length=42)
    tenant = models.CharField(max_length=42)
    rent_amount = models.DecimalField(max_digits=38, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=38, decimal_places=2)
    contract_address = models.CharField(max_length=42, unique=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    rent_due_date = models.DateField(
        null=True, blank=True
    )  # Data de vencimento do aluguel
    contract_duration = models.PositiveIntegerField(
        help_text="Duração do contrato em meses", null=True
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("active", "Active"),
            ("terminated", "Terminated"),
        ],
        default="pending",
    )
    landlord_signature = models.CharField(max_length=132, blank=True)
    tenant_signature = models.CharField(max_length=132, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    simulated_time = models.DateField(default=timezone.now, null=True, blank=True)

    def clean(self):
        # Validação do comprimento dos endereços
        if len(self.contract_address) != 42:
            raise ValidationError("Endereço do contrato deve ter 42 caracteres.")

        if len(self.landlord) != 42 or len(self.tenant) != 42:
            raise ValidationError(
                "O endereço do locador e do inquilino devem ter 42 caracteres."
            )

        # Verificação da data de término ser posterior à data de início
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError(
                "A data de término deve ser posterior à data de início."
            )

        # Validação do valor do aluguel e do depósito
        if self.rent_amount <= 0:
            raise ValidationError("O valor do aluguel deve ser maior que zero.")
        if self.deposit_amount < 0:
            raise ValidationError("O valor do depósito não pode ser negativo.")

        super().clean()

    def __str__(self):
        return f"Contrato {self.id}: {self.landlord} - {self.tenant}"

    def is_fully_signed(self):
        return bool(self.landlord_signature) and bool(self.tenant_signature)

    def is_contract_active(self):
        return self.start_date <= timezone.now().date() <= self.end_date

    class Meta:
        db_table = "contratos"

class Usuario(models.Model):
    login = models.CharField(max_length=100, unique=True)
    email = models.EmailField(blank=True, null=True)
    is_landlord = models.BooleanField(default=False)
    id_account = models.TextField(blank=True, null=True)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)

    class Meta:
        db_table = 'usuarios_contratos'

class Payment(models.Model):
    contract = models.ForeignKey(
        RentalContract, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(
        max_length=10, choices=[("rent", "Aluguel"), ("deposit", "Depósito")]
    )
    payment_date = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    transaction_hash = models.CharField(max_length=66, unique=True)

    def __str__(self):
        return f"Pagamento {self.payment_type} de {self.amount} para o contrato {self.contract}"

    class Meta:
        db_table = "pagamento_contrato"


# Modelo para encerramento de contrato
class ContractTermination(models.Model):
    contract = models.OneToOneField(RentalContract, on_delete=models.CASCADE)
    termination_date = models.DateTimeField(default=timezone.now)
    terminated_by = models.CharField(max_length=42)
    termination_transaction_hash = models.CharField(
        max_length=66, unique=True, blank=True
    )

    def __str__(self):
        return f"Encerramento do contrato {self.contract} por {self.terminated_by}"

    class Meta:
        db_table = "encerramento_contrato"

class ContractEvent(models.Model):
    EVENT_TYPES = [
        ("create", "Create Contract"),
        ("sign", "Sign Contract"),
        ("pay_rent", "Pay Rent"),
        ("pay_deposit", "Pay Deposit"),
        ("execute", "Execute Contract"),
        ("terminate", "Terminate Contract"),
        ("partial_payment", "Partial Payment"),
        ("failure", "Failure"),
    ]

    contract = models.ForeignKey(
        RentalContract, on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    user_address = models.CharField(max_length=42)
    event_data = models.JSONField()
    transaction_hash = models.CharField(max_length=66, blank=True, null=True)
    from_address = models.CharField(max_length=42, blank=True, null=True)
    gas_used = models.BigIntegerField(blank=True, null=True)
    block_number = models.BigIntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    detalhes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.event_type} no contrato {self.contract.id}"

    class Meta:
        db_table = "eventos_contrato"
