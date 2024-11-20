from datetime import datetime
import pytz # type: ignore

def tratar_data(data_str):
    brazil_tz = pytz.timezone("America/Sao_Paulo")
    return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=brazil_tz)
