import streamlit as st
import json
from fpdf import FPDF
from datetime import datetime

# --- Configuración de Página ---
st.set_page_config(
    page_title="FCS Field Auditor",
    page_icon="🚌",
    layout="centered"
)

# --- Gestión del Estado y Persistencia ---
if 'step' not in st.session_state:
    st.session_state.step = 1

# Inicialización robusta de variables
# Esto asegura que las claves existan antes de crear los widgets
keys_iniciales = [
    'cliente_nombre', 'ciudad', 'tipos_vehiculos', 'total_vehiculos', 
    'puertas_articulado', 'voltaje', 'conectividad', 'tiene_diagramas',
    'tech_tarjeta', 'dueno_llaves', 'requiere_emv'
]

for key in keys_iniciales:
    if key not in st.session_state:
        if key == 'tipos_vehiculos':
            st.session_state[key] = []
        else:
            st.session_state[key] = None

# --- FUNCIÓN CLAVE PARA CORREGIR EL ERROR ---
def guardar_y_avanzar(keys_to_save):
    """
    Esta función 'toca' las variables en session_state.
    Al reasignarlas (x = x), le decimos a Streamlit: 
    "¡Hey! Estos datos son míos, no los borres aunque el widget desaparezca".
    """
    for key in keys_to_save:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]
    
    st.session_state.step += 1

def retroceder():
    st.session_state.step -= 1

# --- Lógica de Negocio: Análisis de Riesgos ---
def analizar_riesgos(data):
    riesgos = []
    
    # Regla 1: Riesgo Crítico (Vendor Lock-in / Seguridad)
    if data['tech_tarjeta'] != "Ninguna/Papel" and data['dueno_llaves'] != "Cliente":
        riesgos.append({
            "nivel": "CRITICO",
            "titulo": "BLOQUEO DE SEGURIDAD (SAM/LLAVES)",
            "mensaje": "Migración imposible sin las llaves. El cliente no tiene control. Se requiere reemplazo total de tarjetas."
        })

    # Regla 2: Riesgo Arquitectónico (Conectividad vs EMV)
    if data['conectividad'] == "Mala/Offline" and data['requiere_emv'] == "Sí":
        riesgos.append({
            "nivel": "ALTO",
            "titulo": "RIESGO DE FRAUDE EN PAGOS BANCARIOS",
            "mensaje": "Pagos EMV requieren conexión. Se necesita arquitectura de validación offline diferida (MTT)."
        })

    # Regla 3: Advertencia Eléctrica
    if data['voltaje'] == "Otro":
        riesgos.append({
            "nivel": "MEDIO",
            "titulo": "ADAPTACIÓN DE POTENCIA REQUERIDA",
            "mensaje": "Voltaje no estándar. Se requieren conversores DC-DC industriales con aislamiento."
        })
        
    # Regla 4: Advertencia Operativa (Bus Articulado)
    if data['tipos'] and "Bus Articulado" in data['tipos']:
        riesgos.append({
            "nivel": "INFO",
            "titulo": "INSTALACIÓN COMPLEJA (ARTICULADOS)",
            "mensaje": f"Articulados detectados ({data.get('puertas_articulado', 'N/A')} puertas). Considerar cableado extendido."
        })

    return riesgos

# --- Clase para Generación de PDF ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'FCS Field Auditor - Reporte Técnico', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Fecha de Auditoría: {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        try:
            texto_seguro = body.encode('latin-1', 'replace').decode('latin-1')
        except:
            texto_seguro = body
        self.multi_cell(0, 7, texto_seguro)
        self.ln()

    def add_risk_box(self, nivel, titulo, mensaje):
        self.set_font('Arial', 'B', 11)
        if nivel == "CRITICO":
            self.set_text_color(255, 0, 0)
        elif nivel == "ALTO":
            self.set_text_color(255, 140, 0)
        else:
            self.set_text_color(0, 0, 0)
        
        self.cell(0, 7, f"[{nivel}] {titulo}", 0, 1)
        self.set_text_color(50, 50, 50)
        self.set_font('Arial', '', 10)
        try:
            msg_seguro = mensaje.encode('latin-1', 'replace').decode('latin-1')
        except:
            msg_seguro = mensaje
        self.multi_cell(0, 6, msg_seguro)
        self.ln(5)
        self.set_text_color(0, 0, 0)

# --- Interfaz de Usuario ---

st.title("📋 FCS Field Auditor")
st.markdown("Herramienta de levantamiento técnico para Sistemas de Recaudo.")

progress = (st.session_state.step / 4) * 100
st.progress(int(progress))

# --- PASO 1: CLIENTE Y FLOTA ---
if st.session_state.step == 1:
    st.header("Paso 1: Cliente y Flota")
    
    st.text_input("Nombre del Cliente", key="cliente_nombre")
    st.text_input("Ciudad / Región", key="ciudad")
    
    opciones_vehiculos = ["Bus Estándar", "Bus Articulado", "Tranvía", "Metro", "Teleférico"]
    st.multiselect("Tipos de Vehículos en Flota", options=opciones_vehiculos, key="tipos_vehiculos")
    
    if st.session_state.tipos_vehiculos and "Bus Articulado" in st.session_state.tipos_vehiculos:
        st.number_input("¿Promedio de puertas por bus articulado?", min_value=1, value=3, key="puertas_articulado")
    
    st.number_input("Tamaño total de la flota", min_value=1, step=1, key="total_vehiculos")

    # Definimos qué variables de este paso queremos "salvar"
    keys_paso_1 = ['cliente_nombre', 'ciudad', 'tipos_vehiculos', 'total_vehiculos', 'puertas_articulado']
    
    st.button("Siguiente ➡", on_click=guardar_y_avanzar, args=(keys_paso_1,))


# --- PASO 2: INFRAESTRUCTURA ---
elif st.session_state.step == 2:
    st.header("Paso 2: Infraestructura y Entorno")
    
    st.markdown("### Evaluación Eléctrica")
    st.radio(
        "Voltaje operativo de la flota",
        options=["12V", "24V", "Otro"],
        help="Tranvías antiguos pueden usar 750V DC.",
        key="voltaje"
    )
    
    st.checkbox("¿El cliente posee diagramas eléctricos actualizados?", key="tiene_diagramas")
    
    st.markdown("### Comunicaciones")
    st.radio(
        "Conectividad en Ruta (Promedio)",
        options=["Buena - 4G/5G Estable", "Intermitente", "Mala/Offline"],
        key="conectividad"
    )

    keys_paso_2 = ['voltaje', 'tiene_diagramas', 'conectividad']

    col1, col2 = st.columns(2)
    with col1:
        st.button("⬅ Atrás", on_click=retroceder)
    with col2:
        st.button("Siguiente ➡", on_click=guardar_y_avanzar, args=(keys_paso_2,))


# --- PASO 3: TECNOLOGÍA Y SEGURIDAD ---
elif st.session_state.step == 3:
    st.header("Paso 3: Tecnología y Seguridad (Crítico)")
    
    st.radio(
        "Tecnología de Tarjeta Actual",
        options=["MIFARE Classic", "MIFARE DESFire", "Calypso", "Otra (FeliCa/HID)", "Ninguna/Papel"],
        key="tech_tarjeta"
    )
    
    if st.session_state.tech_tarjeta != "Ninguna/Papel" and st.session_state.tech_tarjeta is not None:
        st.warning("⚠️ Punto Crítico de Auditoría")
        st.radio(
            "¿Quién custodia las llaves de seguridad (SAM/Keys)?",
            options=["Cliente (Tiene control total)", "Proveedor Actual (Black box)", "Nadie sabe / Se perdieron"],
            key="dueno_llaves"
        )
    else:
        st.session_state.dueno_llaves = "N/A"

    st.markdown("---")
    st.radio(
        "¿Requiere integración con Validadores Bancarios (EMV)?",
        options=["Sí", "No"],
        key="requiere_emv"
    )

    keys_paso_3 = ['tech_tarjeta', 'dueno_llaves', 'requiere_emv']

    col1, col2 = st.columns(2)
    with col1:
        st.button("⬅ Atrás", on_click=retroceder)
    with col2:
        st.button("Analizar y Generar Reporte 🏁", on_click=guardar_y_avanzar, args=(keys_paso_3,))


# --- PASO 4: RESULTADOS ---
elif st.session_state.step == 4:
    st.header("Resultados de Auditoría")
    
    # Recopilar datos (Ahora sí estarán persistentes)
    data_audit = {
        "cliente": st.session_state.get('cliente_nombre', "No especificado"),
        "ciudad": st.session_state.get('ciudad', "No especificado"),
        "flota_total": st.session_state.get('total_vehiculos', 0),
        "tipos": st.session_state.get('tipos_vehiculos', []),
        "voltaje": st.session_state.get('voltaje', "No especificado"),
        "conectividad": st.session_state.get('conectividad', "No especificado"),
        "tech_tarjeta": st.session_state.get('tech_tarjeta', "No especificado"),
        "dueno_llaves": st.session_state.get('dueno_llaves', "N/A"),
        "requiere_emv": st.session_state.get('requiere_emv', "No"),
        "puertas_articulado": st.session_state.get('puertas_articulado', 'N/A')
    }

    riesgos_detectados = analizar_riesgos(data_audit)
    
    if not riesgos_detectados:
        st.success("✅ No se detectaron riesgos críticos.")
    else:
        st.write("### 🚦 Matriz de Riesgos Detectada")
        for riesgo in riesgos_detectados:
            color = "red" if riesgo['nivel'] == "CRITICO" else "orange" if riesgo['nivel'] == "ALTO" else "blue"
            st.markdown(f":{color}[**[{riesgo['nivel']}] {riesgo['titulo']}**]")
            st.write(riesgo['mensaje'])

    st.markdown("---")
    st.subheader("Descargas")

    # JSON
    json_str = json.dumps(data_audit, indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Descargar Auditoría (JSON)",
        data=json_str,
        file_name="auditoria_campo.json",
        mime="application/json"
    )

    # PDF
    try:
        pdf = PDFReport()
        pdf.add_page()
        
        lista_tipos = data_audit['tipos']
        tipos_str = ', '.join(lista_tipos) if isinstance(lista_tipos, list) and lista_tipos else "Ninguno seleccionado"

        pdf.chapter_title(f"Resumen Ejecutivo: {data_audit['cliente']}")
        resumen_texto = (
            f"Ciudad: {data_audit['ciudad']}\n"
            f"Flota Total: {data_audit['flota_total']} unidades\n"
            f"Tipos de Vehículos: {tipos_str}\n"
            f"Tecnología Actual: {data_audit['tech_tarjeta']}\n"
            f"Conectividad: {data_audit['conectividad']}"
        )
        pdf.chapter_body(resumen_texto)
        
        pdf.ln(5)
        pdf.chapter_title("Análisis de Riesgos")
        if not riesgos_detectados:
            pdf.chapter_body("No se detectaron riesgos técnicos bloqueantes.")
        else:
            for r in riesgos_detectados:
                pdf.add_risk_box(r['nivel'], r['titulo'], r['mensaje'])

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        
        st.download_button(
            label="📄 Descargar Reporte Técnico (PDF)",
            data=pdf_bytes,
            file_name="reporte_tecnico.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error generando PDF: {e}")
    
    st.button("🔄 Nueva Auditoría", on_click=lambda: st.session_state.update(step=1))
