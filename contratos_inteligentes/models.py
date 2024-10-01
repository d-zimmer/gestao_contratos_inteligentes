from django.db import models
from django.utils import timezone

# Modelo para armazenar dados de um contrato de aluguel
class RentalContract(models.Model):
    landlord = models.CharField(max_length=42)
    tenant = models.CharField(max_length=42)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    contract_address = models.CharField(max_length=42)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contrato de {self.landlord} para {self.tenant}"

    class Meta:
        db_table = 'contratos'
        
class Payment(models.Model):
    contract = models.ForeignKey(RentalContract, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=10, choices=[('rent', 'Aluguel'), ('deposit', 'Depósito')])
    payment_date = models.DateTimeField(default=timezone.now)  # Data do pagamento
    paid_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Pagamento {self.payment_type} de {self.amount} para o contrato {self.contract}"

    class Meta:
        db_table = 'pagamento_contrato'

class ContractTermination(models.Model):
    contract = models.OneToOneField(RentalContract, on_delete=models.CASCADE)
    termination_date = models.DateTimeField(default=timezone.now)  # Data de encerramento do contrato
    terminated_by = models.CharField(max_length=42)  # Quem encerrou o contrato (locador ou inquilino)

    def __str__(self):
        return f"Encerramento do contrato {self.contract} por {self.terminated_by}"
    
    class Meta:
        db_table = 'encerramento_contrato'