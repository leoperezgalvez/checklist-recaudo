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

# --- Gestión del Estado (Session State) ---
if 'step' not in st.session_state:
    st.session_state.step = 1

# Definir valores por defecto con tipos correctos
# Corrección: tipos_vehiculos debe ser una lista vacía [], no None
if 'tipos_vehiculos' not in st.session_state:
    st.session_state.tipos_vehiculos = []

default_keys = [
    'cliente_nombre', 'ciudad', 'total_vehiculos', 
    'puertas_articulado', 'voltaje', 'conectividad', 'tiene_diagramas',
    'tech_tarjeta', 'dueno_llaves', 'requiere_emv'
]

for key in default_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# --- Lógica de Negocio: Análisis de Riesgos ---
def analizar_riesgos(data):
    riesgos = []
    
    # Regla 1: Riesgo Crítico (Vendor Lock-in / Seguridad)
    if data['tech_tarjeta'] != "Ninguna/Papel" and data['dueno_llaves'] != "Cliente":
        riesgos.append({
            "nivel": "CRITICO",
            "titulo": "BLOQUEO DE SEGURIDAD (SAM/LLAVES)",
            "mensaje": "Migración imposible sin las llaves de seguridad. El cliente no es dueño de la seguridad actual. Se requiere reemplazo total de tarjetas (re-emisión) o negociación dura con proveedor actual."
        })

    # Regla 2: Riesgo Arquitectónico (Conectividad vs EMV)
    if data['conectividad'] == "Mala/Offline" and data['requiere_emv'] == "Sí":
        riesgos.append({
            "nivel": "ALTO",
            "titulo": "RIESGO DE FRAUDE EN PAGOS BANCARIOS",
            "mensaje": "Los pagos bancarios (EMV) requieren conexión para autorización en línea o listas negras actualizadas. Se necesita arquitectura de validación offline diferida (MTT) y gestión de riesgo financiero."
        })

    # Regla 3: Advertencia Eléctrica
    if data['voltaje'] == "Otro":
        riesgos.append({
            "nivel": "MEDIO",
            "titulo": "ADAPTACIÓN DE POTENCIA REQUERIDA",
            "mensaje": "Voltaje no estándar detectado. Se requieren conversores de potencia DC-DC industriales con aislamiento galvánico para proteger los validadores."
        })
        
    # Regla 4: Advertencia Operativa (Bus Articulado)
    if data['tipos'] and "Bus Articulado" in data['tipos']:
        riesgos.append({
            "nivel": "INFO",
            "titulo": "INSTALACIÓN COMPLEJA (ARTICULADOS)",
            "mensaje": f"Se detectaron buses articulados con {data.get('puertas_articulado', 3)} puertas. Considerar cableado extendido y validadores esclavos o múltiples validadores maestros."
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
        # Latin-1 encoding para acentos básicos
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
            self.set_text_color(255, 140, 0) # Naranja oscuro
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
        self.set_text_color(0, 0, 0) # Reset color

# --- Funciones de Navegación ---
def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

# --- Interfaz de Usuario ---

st.title("📋 FCS Field Auditor")
st.markdown("Herramienta de levantamiento técnico para Sistemas de Recaudo.")

# Barra de progreso
progress = (st.session_state.step / 4) * 100
st.progress(int(progress))

# --- PASO 1: CLIENTE Y FLOTA ---
if st.session_state.step == 1:
    st.header("Paso 1: Cliente y Flota")
    
    st.text_input("Nombre del Cliente", key="cliente_nombre")
    st.text_input("Ciudad / Región", key="ciudad")
    
    opciones_vehiculos = ["Bus Estándar", "Bus Articulado", "Tranvía", "Metro", "Teleférico"]
    st.multiselect("Tipos de Vehículos en Flota", options=opciones_vehiculos, key="tipos_vehiculos")
    
    # Lógica Condicional Articulado
    if st.session_state.tipos_vehiculos and "Bus Articulado" in st.session_state.tipos_vehiculos:
        st.number_input("¿Promedio de puertas por bus articulado?", min_value=1, max_value=10, value=3, key="puertas_articulado")
    
    st.number_input("Tamaño total de la flota (cantidad de vehículos)", min_value=1, step=1, key="total_vehiculos")

    st.button("Siguiente ➡", on_click=next_step)


# --- PASO 2: INFRAESTRUCTURA ---
elif st.session_state.step == 2:
    st.header("Paso 2: Infraestructura y Entorno")
    
    st.markdown("### Evaluación Eléctrica")
    st.radio(
        "Voltaje operativo de la flota",
        options=["12V", "24V", "Otro"],
        help="Tranvías antiguos pueden usar 750V DC. Buses eléctricos suelen tener convertidores.",
        key="voltaje"
    )
    
    st.checkbox("¿El cliente posee diagramas eléctricos actualizados de los buses?", key="tiene_diagramas")
    
    st.markdown("### Comunicaciones")
    st.radio(
        "Conectividad en Ruta (Promedio)",
        options=["Buena - 4G/5G Estable", "Intermitente", "Mala/Offline"],
        key="conectividad"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.button("⬅ Atrás", on_click=prev_step)
    with col2:
        st.button("Siguiente ➡", on_click=next_step)


# --- PASO 3: TECNOLOGÍA Y SEGURIDAD ---
elif st.session_state.step == 3:
    st.header("Paso 3: Tecnología y Seguridad (Crítico)")
    
    st.info("Esta sección determina la viabilidad de la migración tecnológica.")
    
    st.radio(
        "Tecnología de Tarjeta Actual",
        options=["MIFARE Classic", "MIFARE DESFire", "Calypso", "Otra (FeliCa/HID)", "Ninguna/Papel"],
        key="tech_tarjeta"
    )
    
    # Lógica Condicional Llaves
    if st.session_state.tech_tarjeta != "Ninguna/Papel" and st.session_state.tech_tarjeta is not None:
        st.warning("⚠️ Punto Crítico de Auditoría")
        st.radio(
            "¿Quién custodia las llaves de seguridad (SAM/Keys/Master Key)?",
            options=["Cliente (Tiene control total)", "Proveedor Actual (Black box)", "Nadie sabe / Se perdieron"],
            key="dueno_llaves"
        )
    else:
        # Asegurar que la variable tenga un valor neutro si no se muestra
        st.session_state.dueno_llaves = "N/A"

    st.markdown("---")
    st.radio(
        "¿El proyecto requiere integración con Validadores Bancarios (EMV - Visa/Mastercard)?",
        options=["Sí", "No"],
        key="requiere_emv"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.button("⬅ Atrás", on_click=prev_step)
    with col2:
        st.button("Analizar y Generar Reporte 🏁", on_click=next_step)


# --- PASO 4: RESULTADOS ---
elif st.session_state.step == 4:
    st.header("Resultados de Auditoría")
    
    # Recopilar datos
    data_audit = {
        "cliente": st.session_state.cliente_nombre or "No especificado",
        "ciudad": st.session_state.ciudad or "No especificado",
        "flota_total": st.session_state.total_vehiculos or 0,
        "tipos": st.session_state.tipos_vehiculos or [],
        "voltaje": st.session_state.voltaje or "No especificado",
        "conectividad": st.session_state.conectividad or "No especificado",
        "tech_tarjeta": st.session_state.tech_tarjeta or "No especificado",
        "dueno_llaves": st.session_state.dueno_llaves or "N/A",
        "requiere_emv": st.session_state.requiere_emv or "No",
        "puertas_articulado": st.session_state.get('puertas_articulado', 'N/A')
    }

    # Ejecutar Análisis
    riesgos_detectados = analizar_riesgos(data_audit)
    
    # --- Mostrar Semáforos en Pantalla ---
    if not riesgos_detectados:
        st.success("✅ No se detectaron riesgos críticos o bloqueantes. El escenario técnico es favorable.")
    else:
        st.write("### 🚦 Matriz de Riesgos Detectada")
        for riesgo in riesgos_detectados:
            if riesgo['nivel'] == "CRITICO":
                st.error(f"**{riesgo['titulo']}**: {riesgo['mensaje']}")
            elif riesgo['nivel'] == "ALTO":
                st.warning(f"**{riesgo['titulo']}**: {riesgo['mensaje']}")
            elif riesgo['nivel'] == "MEDIO":
                st.warning(f"**{riesgo['titulo']}**: {riesgo['mensaje']}")
            else:
                st.info(f"**{riesgo['titulo']}**: {riesgo['mensaje']}")

    st.markdown("---")
    st.subheader("Descargas")

    # 1. Generar JSON
    json_str = json.dumps(data_audit, indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Descargar Auditoría (JSON)",
        data=json_str,
        file_name=f"auditoria_campo.json",
        mime="application/json"
    )

    # 2. Generar PDF
    def create_pdf():
        pdf = PDFReport()
        pdf.add_page()
        
        # Preparar string de tipos de vehículos (Corrección de error NoneType)
        lista_tipos = data_audit['tipos']
        if isinstance(lista_tipos, list):
            tipos_str = ', '.join(lista_tipos)
        else:
            tipos_str = str(lista_tipos)

        if not tipos_str:
            tipos_str = "Ninguno seleccionado"

        # Resumen General
        pdf.chapter_title(f"Resumen Ejecutivo: {data_audit['cliente']}")
        resumen_texto = (
            f"Ciudad: {data_audit['ciudad']}\n"
            f"Flota Total: {data_audit['flota_total']} unidades\n"
            f"Tipos de Vehículos: {tipos_str}\n"
            f"Tecnología Actual: {data_audit['tech_tarjeta']}\n"
            f"Conectividad: {data_audit['conectividad']}"
        )
        pdf.chapter_body(resumen_texto)
        
        # Riesgos
        pdf.ln(5)
        pdf.chapter_title("Análisis de Riesgos y Recomendaciones")
        
        if not riesgos_detectados:
            pdf.chapter_body("No se detectaron riesgos técnicos bloqueantes para la implementación.")
        else:
            for r in riesgos_detectados:
                pdf.add_risk_box(r['nivel'], r['titulo'], r['mensaje'])
                
        return pdf.output(dest='S').encode('latin-1', 'replace')

    # Botón PDF
    # Generamos el PDF dentro de un try/except por si acaso
    try:
        pdf_bytes = create_pdf()
        st.download_button(
            label="📄 Descargar Reporte Técnico (PDF)",
            data=pdf_bytes,
            file_name=f"reporte_tecnico.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error generando PDF: {e}")
    
    st.button("🔄 Nueva Auditoría", on_click=lambda: st.session_state.update(step=1))
