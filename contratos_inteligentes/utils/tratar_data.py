from datetime import datetime
import pytz # type: ignore

def tratar_data(data):
    if isinstance(data, int):  # Se for um timestamp
        return datetime.fromtimestamp(data)
    elif isinstance(data, str):  # Se for uma string ISO
        return datetime.fromisoformat(data)
    else:
        raise ValueError("Formato de data inválido.")
