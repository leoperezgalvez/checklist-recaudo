import streamlit as st
import json
from fpdf import FPDF
from datetime import datetime

# --- Configuración Inicial ---
st.set_page_config(page_title="FCS Field Auditor Pro", page_icon="🚍", layout="wide")

# --- Gestión de Estado Robusta (Persistencia) ---
# Esta estructura es la fuente de la verdad. El PDF leerá de aquí, no de los widgets.
if 'survey_data' not in st.session_state:
    st.session_state.survey_data = {
        # General
        "cliente": "", "ciudad": "", "flota_qty": 0,
        # Tarifario
        "tipo_tarifa": "Plana", "beneficios": [], "transbordos": "No",
        # Canales
        "red_recarga": [], "canales_digitales": [], "pasarela_pago": "No definida",
        # Operación
        "fiscalizacion": "Manual", "webs_autoatencion": False,
        # Técnico
        "voltaje": "24V", "integraciones": [], "conectividad": "4G",
        # Riesgos calculados
        "riesgos": [] 
    }

if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

# --- Funciones Auxiliares ---

def update_data(key, value):
    """Actualiza el diccionario maestro inmediatamente"""
    st.session_state.survey_data[key] = value

def navigate(direction):
    st.session_state.current_step += direction

# --- Lógica de Negocio (El Cerebro) ---
def analizar_riesgos():
    data = st.session_state.survey_data
    riesgos = []

    # 1. Riesgo de Integración Compleja
    if "ERP (SAP/Oracle)" in data.get("integraciones", []) and "Legacy (Sistemas Antiguos)" in data.get("integraciones", []):
        riesgos.append({
            "nivel": "ALTO", 
            "titulo": "Integración Compleja (ERP + Legacy)",
            "msg": "Conectar sistemas legacy con ERPs modernos suele retrasar proyectos 3-6 meses. Se requiere middleware."
        })

    # 2. Riesgo Tarifario (Hardware)
    if data.get("tipo_tarifa") in ["Por tramo/distancia", "Zonificada (Check-in/Check-out)"]:
        riesgos.append({
            "nivel": "MEDIO",
            "titulo": "Requerimiento de GPS de Alta Precisión",
            "msg": "Las tarifas por distancia requieren validadores con GPS muy preciso y lógica compleja a bordo."
        })

    # 3. Riesgo de Canales
    if "Recarga en efectivo a bordo" in data.get("red_recarga", []):
        riesgos.append({
            "nivel": "CRITICO",
            "titulo": "Manejo de Efectivo a Bordo",
            "msg": "El recaudo moderno busca eliminar el efectivo. Mantenerlo aumenta costos operativos y riesgo de robo."
        })

    st.session_state.survey_data["riesgos"] = riesgos

# --- Generador de PDF (Corregido) ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'FCS Auditor - Reporte de Levantamiento Integral', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, label, value):
        self.set_font('Arial', 'B', 10)
        self.cell(50, 8, label + ":", 0, 0)
        self.set_font('Arial', '', 10)
        
        # Limpieza de datos para evitar errores de codificación
        if isinstance(value, list):
            val_str = ", ".join(value) if value else "Ninguno"
        else:
            val_str = str(value)
        
        try:
            # Reemplazar caracteres problemáticos para Latin-1
            safe_str = val_str.encode('latin-1', 'replace').decode('latin-1')
        except:
            safe_str = val_str

        self.multi_cell(0, 8, safe_str)

def generar_pdf():
    data = st.session_state.survey_data
    pdf = PDFReport()
    pdf.add_page()

    # Sección 1: General
    pdf.chapter_title("1. Contexto del Cliente")
    pdf.chapter_body("Cliente", data["cliente"])
    pdf.chapter_body("Ciudad", data["ciudad"])
    pdf.chapter_body("Flota Total", data["flota_qty"])

    # Sección 2: Tarifas
    pdf.chapter_title("2. Modelo de Negocio y Tarifas")
    pdf.chapter_body("Tipo de Tarifa", data["tipo_tarifa"])
    pdf.chapter_body("Política de Transbordos", data["transbordos"])
    pdf.chapter_body("Beneficios/Subsidios", data["beneficios"])

    # Sección 3: Canales
    pdf.chapter_title("3. Canales de Venta y Atención")
    pdf.chapter_body("Red de Recarga", data["red_recarga"])
    pdf.chapter_body("Canales Digitales", data["canales_digitales"])
    pdf.chapter_body("Web Autoatención", "Sí" if data["webs_autoatencion"] else "No")
    
    # Sección 4: Técnico
    pdf.chapter_title("4. Aspectos Técnicos y Operativos")
    pdf.chapter_body("Fiscalización", data["fiscalizacion"])
    pdf.chapter_body("Integraciones", data["integraciones"])
    pdf.chapter_body("Conectividad", data["conectividad"])

    # Sección 5: Riesgos
    pdf.ln(5)
    pdf.set_text_color(200, 0, 0)
    pdf.chapter_title("5. Riesgos Detectados")
    pdf.set_text_color(0, 0, 0)
    
    if not data["riesgos"]:
        pdf.multi_cell(0, 10, "No se detectaron riesgos críticos.")
    else:
        for r in data["riesgos"]:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, f"[{r['nivel']}] {r['titulo']}", 0, 1)
            pdf.set_font('Arial', '', 9)
            pdf.multi_cell(0, 6, r['msg'].encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFAZ DE USUARIO (WIZARD) ---

st.title("Sistema de Levantamiento Técnico FCS")
st.markdown("Herramienta guiada para ejecutivos comerciales. Los datos se guardan automáticamente.")

# Progress Bar
pasos_totales = 5
st.progress(st.session_state.current_step / pasos_totales)

# --- PASO 1: CONTEXTO ---
if st.session_state.current_step == 1:
    st.header("Paso 1: Contexto del Cliente")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nombre del Operador/Autoridad", 
                      value=st.session_state.survey_data["cliente"],
                      on_change=update_data, args=("cliente", st.session_state.survey_data["cliente"]), # Hack para refrescar
                      key="w_cliente")
        # Actualizamos manualmente al salir del widget para asegurar persistencia
        update_data("cliente", st.session_state.w_cliente)

    with col2:
        st.text_input("Ciudad y País", 
                      value=st.session_state.survey_data["ciudad"],
                      key="w_ciudad")
        update_data("ciudad", st.session_state.w_ciudad)

    st.number_input("Tamaño total de la flota", min_value=0, 
                    value=st.session_state.survey_data["flota_qty"],
                    key="w_flota")
    update_data("flota_qty", st.session_state.w_flota)

    st.button("Siguiente ➡", on_click=navigate, args=(1,))

# --- PASO 2: REGLAS DE NEGOCIO (TARIFAS) ---
elif st.session_state.current_step == 2:
    st.header("Paso 2: Modelo Tarifario")
    st.info("💡 **Tip Educativo:** El tipo de tarifa define la complejidad del validador. Las tarifas por distancia requieren GPS y cálculos complejos a bordo.")

    tipo = st.selectbox("Estructura Tarifaria", 
                 ["Plana (Mismo precio siempre)", 
                  "Por tramo/distancia (Cobra según km recorridos)", 
                  "Zonificada (Anillos o Zonas de color)", 
                  "Diferenciada por horario (Punta/Valle)"],
                 index=0, key="w_tipo_tarifa")
    update_data("tipo_tarifa", tipo)

    transbordo = st.radio("¿Existe política de Transbordos/Integración?",
             ["No, cada bus se paga aparte", 
              "Sí, tarifa reducida en el segundo bus", 
              "Sí, ventana de tiempo gratuita (ej. 60 min)"],
             key="w_transbordos")
    update_data("transbordos", transbordo)

    beneficios = st.multiselect("Beneficios a Pasajeros (Subsidios)",
                   ["Estudiantes", "Adulto Mayor", "Personas con Discapacidad", "Policía/Bomberos", "Gratuidad Total"],
                   default=st.session_state.survey_data["beneficios"],
                   key="w_beneficios")
    update_data("beneficios", beneficios)

    col1, col2 = st.columns([1,1])
    col1.button("⬅ Atrás", on_click=navigate, args=(-1,))
    col2.button("Siguiente ➡", on_click=navigate, args=(1,))

# --- PASO 3: CANALES DE VENTA ---
elif st.session_state.current_step == 3:
    st.header("Paso 3: Venta y Atención al Cliente")
    st.info("💡 **Tip:** Entre más canales digitales, menor es el costo operativo de manejar efectivo (CIT).")

    st.subheader("Red Física")
    red = st.multiselect("¿Dónde cargan saldo los usuarios?",
                   ["Taquillas Propias (Estaciones)", "Red de Terceros (Tiendas de barrio/Farmacias)", 
                    "Máquinas de Autoatención (TVM)", "Recarga en efectivo a bordo (Conductor)", "Venta a bordo (Inspectores)"],
                   default=st.session_state.survey_data["red_recarga"],
                   key="w_red_recarga")
    update_data("red_recarga", red)

    st.subheader("Canales Digitales")
    digital = st.multiselect("Tecnologías disponibles para el usuario",
                   ["App Móvil (Recarga NFC)", "App Móvil (Código QR)", "Web de Recarga", "Chatbot (WhatsApp)"],
                   default=st.session_state.survey_data["canales_digitales"],
                   key="w_digital")
    update_data("canales_digitales", digital)

    web_auto = st.checkbox("¿Requieren Portal Web de Autoatención (Gestión de tarjetas, bloqueos, facturas)?", 
                value=st.session_state.survey_data["webs_autoatencion"],
                key="w_web_auto")
    update_data("webs_autoatencion", web_auto)

    pasarela = st.text_input("¿Qué Pasarela de Pagos (Gateway) usan o prefieren? (Ej: Transbank, MercadoPago, Stripe)",
                  value=st.session_state.survey_data["pasarela_pago"],
                  key="w_pasarela")
    update_data("pasarela_pago", pasarela)

    col1, col2 = st.columns([1,1])
    col1.button("⬅ Atrás", on_click=navigate, args=(-1,))
    col2.button("Siguiente ➡", on_click=navigate, args=(1,))

# --- PASO 4: OPERACIÓN E INTEGRACIÓN ---
elif st.session_state.current_step == 4:
    st.header("Paso 4: Operación Técnica")
    
    st.subheader("Fiscalización")
    fisc = st.radio("¿Cómo controlan la evasión?",
             ["Manual (Ojo del conductor)", "Inspectores con POS/PDA", "Torniquetes/Molinetes", "Cámaras de conteo de pasajeros"],
             key="w_fiscalizacion")
    update_data("fiscalizacion", fisc)

    st.subheader("Integraciones de Sistema")
    st.warning("⚠️ Las integraciones suelen ser la causa #1 de retrasos.")
    integ = st.multiselect("¿Con qué otros sistemas debemos conectarnos?",
                   ["SAE/FMS (Gestión de Flota)", "Información al Pasajero (PIS)", "ERP (SAP/Oracle)", 
                    "Legacy (Sistemas Antiguos)", "Bancos/Financieras (EMV)", "Gobierno/Regulador"],
                   default=st.session_state.survey_data["integraciones"],
                   key="w_integraciones")
    update_data("integraciones", integ)

    col1, col2 = st.columns([1,1])
    col1.button("⬅ Atrás", on_click=navigate, args=(-1,))
    col2.button("Analizar y Finalizar 🏁", on_click=navigate, args=(1,))

# --- PASO 5: RESUMEN Y EXPORTACIÓN ---
elif st.session_state.current_step == 5:
    st.header("Resultados del Levantamiento")
    
    # Ejecutar análisis
    analizar_riesgos()
    data = st.session_state.survey_data

    # Mostrar Resumen Visual
    st.success("Levantamiento completado. Revisa los datos antes de exportar.")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Flota", data["flota_qty"])
    c2.metric("Tarifa", "Compleja" if data["tipo_tarifa"] != "Plana" else "Simple")
    c3.metric("Riesgos Detectados", len(data["riesgos"]))

    with st.expander("Ver Matriz de Riesgos", expanded=True):
        if not data["riesgos"]:
            st.write("✅ Sin riesgos críticos evidentes.")
        for r in data["riesgos"]:
            color = "🔴" if r["nivel"] == "CRITICO" else "🟠" if r["nivel"] == "ALTO" else "🟡"
            st.write(f"**{color} {r['titulo']}**")
            st.caption(r['msg'])

    st.divider()

    col_d1, col_d2 = st.columns(2)
    
    # Botón JSON
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    col_d1.download_button("📥 Descargar JSON (Crudo)", json_str, "levantamiento.json", "application/json")

    # Botón PDF (Ahora robusto)
    try:
        pdf_bytes = generar_pdf()
        col_d2.download_button("📄 Descargar Reporte PDF", pdf_bytes, "reporte_comercial.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error generando PDF: {e}")

    if st.button("Comenzar Nuevo Levantamiento"):
        st.session_state.clear()
        st.rerun()
