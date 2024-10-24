from fpdf import FPDF
import base64

def gerar_pdf_contrato(contrato):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Contrato de Aluguel", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Locador: {contrato['landlord']}", ln=True)
    pdf.cell(200, 10, txt=f"Inquilino: {contrato['tenant']}", ln=True)
    pdf.cell(200, 10, txt=f"Valor do Aluguel: {contrato['rent_amount']} ETH", ln=True)
    pdf.cell(200, 10, txt=f"Valor do Depósito: {contrato['deposit_amount']} ETH", ln=True)
    pdf.cell(200, 10, txt=f"Data de Início: {contrato['start_date']}", ln=True)
    pdf.cell(200, 10, txt=f"Data de Término: {contrato['end_date']}", ln=True)
    
    return pdf.output(dest='S').encode('latin1')
