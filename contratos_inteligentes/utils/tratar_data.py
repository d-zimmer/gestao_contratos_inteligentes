from datetime import datetime
import pytz # type: ignore

def tratar_data(data_str):
    try:
        # Definir o fuso horário do Brasil
        fuso_horario = pytz.timezone("America/Sao_Paulo")
        
        # Converter a string para datetime sem fuso horário
        data_sem_fuso = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        
        # Ajustar para o fuso horário do Brasil
        data_com_fuso = fuso_horario.localize(data_sem_fuso)
        
        return data_com_fuso
    except ValueError:
        raise ValueError("Formato de data inválido. Use o formato 'yyyy-mm-dd hh:mm:ss'.")
