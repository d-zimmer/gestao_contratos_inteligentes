from ..models import ContractEvent  # type: ignore


def log_contract_event(
    contract, event_type, user_address, tx_hash=None, event_data=None
):
    if contract is None:
        raise ValueError("O contrato não pode ser None.")
    if not event_type:
        raise ValueError("O tipo de evento não pode ser vazio.")
    if not user_address:
        raise ValueError("O endereço do usuário não pode ser vazio.")

    ContractEvent.objects.create(
        contract=contract,
        event_type=event_type,
        user_address=user_address,
        event_data=event_data or {},
        transaction_hash=tx_hash,
    )
