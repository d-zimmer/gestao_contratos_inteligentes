from celery import shared_task
from .models import RentalContract
from .utils import check_connection
from datetime import datetime, relativedelta
import pytz

@shared_task
def renovar_contratos_automaticamente():
    brazil_tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(brazil_tz)

    contratos = RentalContract.objects.filter(status="active", end_date__lte=now)

    for contrato in contratos:
        try:
            # Lógica de renovação
            contrato.end_date += relativedelta(months=contrato.contract_duration)
            contrato.save()
            print(f"Contrato {contrato.id} renovado até {contrato.end_date}")
        except Exception as e:
            print(f"Erro ao renovar contrato {contrato.id}: {str(e)}")
