from django.db import models

# Modelo para armazenar dados de um contrato de aluguel
class RentalContract(models.Model):
    landlord = models.CharField(max_length=42)  # Endereço do locador
    tenant = models.CharField(max_length=42)    # Endereço do locatário
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    contract_address = models.CharField(max_length=42, blank=True)  # Endereço do contrato na blockchain

    def __str__(self):
        return f"Contrato de {self.landlord} para {self.tenant}"

    class Meta:
        db_table = 'contratos'