import streamlit as st
from fpdf import FPDF
from io import BytesIO

def generate_kpi_report():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Reporte KPI", ln=True, align="C")
    pdf.cell(200, 10, txt="Generado con Streamlit y FPDF", ln=True, align="C")

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Este es un ejemplo de informe.", ln=True, align="L")

    # Generar el contenido del PDF como bytes
    pdf_content = pdf.output(dest='S').encode('latin1')  # Convertir a bytes
    return BytesIO(pdf_content)  # Crear un objeto BytesIO a partir de los bytes


def reports_page():
    st.subheader("Reportes")
    st.write("Aquí puedes generar reportes en PDF.")

    if st.button("Generar reporte KPI"):
        pdf_file = generate_kpi_report()

        # Descargar el PDF en Streamlit
        st.download_button(
            label="Descargar Informe KPI",
            data=pdf_file,
            file_name="reporte_kpi.pdf",
            mime="application/pdf"
        )

    if st.button("Cerrar Sesión"):
        st.session_state['page'] = 'login'

