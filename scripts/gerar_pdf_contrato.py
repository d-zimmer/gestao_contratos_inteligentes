from reportlab.lib.pagesizes import A4 # type: ignore
from reportlab.pdfgen import canvas # type: ignore
from reportlab.lib.units import cm # type: ignore
from datetime import datetime 
from io import BytesIO

def gerar_pdf_contrato(contract):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - 2 * cm, "CONTRATO DE LOCAÇÃO DE IMÓVEL")
    
    y = height - 4 * cm
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, y, f"Locador(a): {contract['landlord']}")
    y -= 1 * cm
    c.drawString(2 * cm, y, f"Locatário(a): {contract['tenant']}")
    y -= 1 * cm
    c.drawString(2 * cm, y, f"Valor do Aluguel: {contract['rent_amount']} ETH")
    y -= 1 * cm
    c.drawString(2 * cm, y, f"Valor do Depósito: {contract['deposit_amount']} ETH")
    y -= 1 * cm
    c.drawString(2 * cm, y, f"Endereço do Contrato: {contract['contract_address']}")
    y -= 1.5 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "CLÁUSULA 1ª - DO OBJETO")
    y -= 0.7 * cm
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, y, f"O objeto deste contrato é a locação do imóvel localizado em [Endereço do Imóvel],")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, "destinado exclusivamente para uso residencial/comercial.")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "CLÁUSULA 2ª - DO PRAZO")
    y -= 0.7 * cm
    c.setFont("Helvetica", 12)

    start_date_iso = contract['start_date'].split('+')[0]
    end_date_iso = contract['end_date'].split('+')[0]

    start_date = datetime.strptime(start_date_iso, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
    end_date = datetime.strptime(end_date_iso, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')

    c.drawString(2 * cm, y, f"O prazo de locação é de {contract.get('contract_duration', 'N/A')} meses, iniciando-se em {start_date}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"e terminando em {end_date}. Ao término do prazo, o(a) locatário(a) obriga-se a devolver")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, "o imóvel em perfeito estado de conservação.")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "CLÁUSULA 3ª - DO ALUGUEL E ENCARGOS")
    y -= 0.7 * cm
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, y, f"O aluguel mensal é de {contract['rent_amount']} ETH, a ser pago até o dia [Dia de Vencimento]")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, "de cada mês. O(a) locatário(a) será responsável pelo pagamento de todas as despesas")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, "de água, luz e outras taxas associadas ao imóvel.")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "CLÁUSULA 4ª - DO REAJUSTE")
    y -= 0.7 * cm
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, y, "O valor do aluguel será reajustado anualmente, de acordo com o Índice Geral de Preços")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, "– Mercado (IGP-M) ou outro índice que reflita a variação inflacionária.")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "CLÁUSULA 5ª - DA MULTA POR INFRAÇÃO")
    y -= 0.7 * cm
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, y, "O não pagamento do aluguel e/ou encargos no prazo estipulado resultará em multa de [X]%")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, "sobre o valor devido, além de juros de [Y]% ao mês.")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "CLÁUSULA 6ª - DAS OBRIGAÇÕES DO LOCATÁRIO")
    y -= 0.7 * cm
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, y, "O(a) locatário(a) obriga-se a usar o imóvel de forma adequada, manter em bom estado")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, "de conservação, efetuar reparos necessários e comunicar ao locador qualquer problema.")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "CLÁUSULA 7ª - DAS DISPOSIÇÕES FINAIS")
    y -= 0.7 * cm
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, y, "As partes elegem o foro da Comarca de [Cidade] para dirimir quaisquer dúvidas decorrentes")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, "deste contrato, renunciando a qualquer outro, por mais privilegiado que seja.")
    y -= 1.5 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Assinatura do Locador: ___________________________")
    y -= 1 * cm
    c.drawString(2 * cm, y, "Assinatura do Locatário: ___________________________")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()