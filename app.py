import streamlit as st
import json
from fpdf import FPDF
from datetime import datetime

# --- Configuración Inicial ---
st.set_page_config(page_title="FCS Field Auditor Pro", page_icon="🚍", layout="wide")

# --- Gestión de Estado Robusta (Persistencia) ---
if 'survey_data' not in st.session_state:
    st.session_state.survey_data = {
        # 1. Contexto
        "cliente": "", "ciudad": "", "flota_qty": 0,
        # 2. Tarifas
        "tipo_tarifa": "Plana", "beneficios": [], "transbordos": "No",
        # 3. Canales
        "red_recarga": [], "canales_digitales": [], "pasarela_pago": "No definida", "webs_autoatencion": False,
        # 4. Operación
        "fiscalizacion": "Manual", "integraciones": [], "conectividad": "4G", "voltaje": "24V",
        # 5. Demanda y Negocio (NUEVO)
        "pax_mensual": 0, "ticket_promedio": 0.0, "viajes_combinados_pct": 0,
        "evasion_pct": 0, "fraude_conductor_pct": 0, "recaudacion_estimada": 0.0,
        "uso_efectivo_pct": 0,
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

    # 1. Riesgo de Evasión (Negocio)
    if data["evasion_pct"] > 15:
        riesgos.append({
            "nivel": "CRITICO",
            "titulo": "Alta Evasión Detectada (>15%)",
            "msg": f"La evasión del {data['evasion_pct']}% hace insostenible el modelo 'Honor System'. Se recomienda instalar torniquetes (molinetes) o cámaras de conteo 3D obligatoriamente."
        })

    # 2. Riesgo de Fraude Interno (Conductor)
    if data["fraude_conductor_pct"] > 5:
        riesgos.append({
            "nivel": "ALTO",
            "titulo": "Fraude Operativo Interno",
            "msg": "Robo hormiga detectado. Es urgente eliminar el efectivo a bordo y digitalizar el 100% del recaudo."
        })

    # 3. Riesgo de Carga Transaccional (Clearing)
    if data["viajes_combinados_pct"] > 30:
        riesgos.append({
            "nivel": "MEDIO",
            "titulo": "Alta Complejidad de Clearing",
            "msg": f"El {data['viajes_combinados_pct']}% de viajes combinados requiere un motor de compensación (Clearing House) robusto para repartir el dinero entre operadores con precisión milimétrica."
        })

    # 4. Riesgo Técnico
    if "Recarga en efectivo a bordo" in data.get("red_recarga", []) and data["pax_mensual"] > 500000:
        riesgos.append({
            "nivel": "ALTO",
            "titulo": "Cuello de Botella Operativo",
            "msg": "Manejar efectivo a bordo con alto volumen de pasajeros ralentiza la operación (Dwell Time) y aumenta costos de transporte de valores."
        })

    st.session_state.survey_data["riesgos"] = riesgos

# --- Generador de PDF ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'FCS Auditor - Reporte de Viabilidad y Requerimientos', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, label, value):
        self.set_font('Arial', 'B', 10)
        self.cell(60, 8, label + ":", 0, 0)
        self.set_font('Arial', '', 10)
        
        if isinstance(value, list):
            val_str = ", ".join(value) if value else "Ninguno"
        else:
            val_str = str(value)
        
        try:
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
    pdf.chapter_body("Flota Total", f"{data['flota_qty']} unidades")

    # Sección 2: Demanda y Negocio (NUEVO)
    pdf.chapter_title("2. Métricas de Demanda y Negocio")
    pdf.chapter_body("Pasajeros Mensuales", f"{data['pax_mensual']:,}".replace(",", "."))
    pdf.chapter_body("Ticket Promedio", f"$ {data['ticket_promedio']}")
    pdf.chapter_body("Recaudación Mensual Est.", f"$ {data['recaudacion_estimada']:,}".replace(",", "."))
    pdf.chapter_body("Índice de Evasión", f"{data['evasion_pct']}%")
    pdf.chapter_body("Fraude Conductor Est.", f"{data['fraude_conductor_pct']}%")
    pdf.chapter_body("Uso de Efectivo Actual", f"{data['uso_efectivo_pct']}%")

    # Sección 3: Tarifas
    pdf.chapter_title("3. Modelo Tarifario")
    pdf.chapter_body("Tipo de Tarifa", data["tipo_tarifa"])
    pdf.chapter_body("Transbordos", data["transbordos"])
    pdf.chapter_body("Beneficios", data["beneficios"])

    # Sección 4: Técnico
    pdf.chapter_title("4. Aspectos Técnicos")
    pdf.chapter_body("Red de Recarga", data["red_recarga"])
    pdf.chapter_body("Integraciones", data["integraciones"])
    pdf.chapter_body("Fiscalización", data["fiscalizacion"])

    # Sección 5: Riesgos
    pdf.ln(5)
    pdf.set_text_color(200, 0, 0)
    pdf.chapter_title("5. Riesgos y Oportunidades")
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
st.markdown("Herramienta guiada para dimensionamiento de Sistemas de Recaudo.")

# Progress Bar (Ahora son 6 pasos)
pasos_totales = 6
st.progress(st.session_state.current_step / pasos_totales)

# --- PASO 1: CONTEXTO ---
if st.session_state.current_step == 1:
    st.header("Paso 1: Contexto del Cliente")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nombre del Operador/Autoridad", 
                      value=st.session_state.survey_data["cliente"],
                      key="w_cliente")
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
    
    tipo = st.selectbox("Estructura Tarifaria", 
                 ["Plana (Mismo precio siempre)", "Por tramo/distancia", "Zonificada", "Diferenciada por horario"],
                 index=0, key="w_tipo_tarifa")
    update_data("tipo_tarifa", tipo)

    transbordo = st.radio("Política de Transbordos",
             ["No, cada bus se paga aparte", "Sí, tarifa reducida", "Sí, ventana de tiempo gratuita"],
             key="w_transbordos")
    update_data("transbordos", transbordo)

    beneficios = st.multiselect("Beneficios a Pasajeros",
                   ["Estudiantes", "Adulto Mayor", "Discapacidad", "Fuerzas Armadas", "Gratuidad Total"],
                   default=st.session_state.survey_data["beneficios"],
                   key="w_beneficios")
    update_data("beneficios", beneficios)

    col1, col2 = st.columns([1,1])
    col1.button("⬅ Atrás", on_click=navigate, args=(-1,))
    col2.button("Siguiente ➡", on_click=navigate, args=(1,))

# --- PASO 3: CANALES DE VENTA ---
elif st.session_state.current_step == 3:
    st.header("Paso 3: Venta y Atención")
    
    red = st.multiselect("Canales de Recarga Físicos",
                   ["Taquillas Propias", "Red de Terceros (Retail)", "Máquinas TVM", "Recarga a bordo (Conductor)"],
                   default=st.session_state.survey_data["red_recarga"],
                   key="w_red_recarga")
    update_data("red_recarga", red)

    digital = st.multiselect("Canales Digitales",
                   ["App NFC", "App QR", "Web Recarga", "Chatbot"],
                   default=st.session_state.survey_data["canales_digitales"],
                   key="w_digital")
    update_data("canales_digitales", digital)

    web_auto = st.checkbox("¿Requieren Web de Autoatención?", 
                value=st.session_state.survey_data["webs_autoatencion"],
                key="w_web_auto")
    update_data("webs_autoatencion", web_auto)

    col1, col2 = st.columns([1,1])
    col1.button("⬅ Atrás", on_click=navigate, args=(-1,))
    col2.button("Siguiente ➡", on_click=navigate, args=(1,))

# --- PASO 4: OPERACIÓN TÉCNICA ---
elif st.session_state.current_step == 4:
    st.header("Paso 4: Operación Técnica")
    
    fisc = st.radio("Método de Fiscalización",
             ["Manual", "Inspectores con POS", "Torniquetes/Molinetes", "Cámaras conteo"],
             key="w_fiscalizacion")
    update_data("fiscalizacion", fisc)

    integ = st.multiselect("Integraciones Requeridas",
                   ["SAE/FMS", "PIS (Info Pasajero)", "ERP (SAP)", "Legacy", "Bancos/EMV"],
                   default=st.session_state.survey_data["integraciones"],
                   key="w_integraciones")
    update_data("integraciones", integ)

    col1, col2 = st.columns([1,1])
    col1.button("⬅ Atrás", on_click=navigate, args=(-1,))
    col2.button("Siguiente ➡", on_click=navigate, args=(1,))

# --- PASO 5: DEMANDA Y NEGOCIO (NUEVO) ---
elif st.session_state.current_step == 5:
    st.header("Paso 5: Demanda y Viabilidad Financiera")
    st.info("📊 Estos datos son cruciales para calcular el ROI y dimensionar los servidores.")

    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Volumetría")
        pax = st.number_input("Pasajeros Mensuales Estimados", min_value=0, step=1000, 
                        value=st.session_state.survey_data["pax_mensual"], key="w_pax")
        update_data("pax_mensual", pax)

        combinados = st.slider("% de Viajes Combinados (Transbordos)", 0, 100, 
                         st.session_state.survey_data["viajes_combinados_pct"], key="w_comb")
        update_data("viajes_combinados_pct", combinados)
        
        efectivo = st.slider("% Actual de Pago en Efectivo", 0, 100, 
                       st.session_state.survey_data["uso_efectivo_pct"], key="w_efectivo")
        update_data("uso_efectivo_pct", efectivo)

    with col_b:
        st.subheader("Finanzas")
        ticket = st.number_input("Valor Promedio del Pasaje (Ticket)", min_value=0.0, step=0.1, 
                           value=float(st.session_state.survey_data["ticket_promedio"]), key="w_ticket")
        update_data("ticket_promedio", ticket)

        # Cálculo automático de recaudación
        calc_recaudo = pax * ticket
        recaudo = st.number_input("Recaudación Mensual Promedio (Calculada)", min_value=0.0, 
                            value=float(calc_recaudo), help="Puedes editar este valor si la cifra real difiere de la calculada", key="w_recaudo")
        update_data("recaudacion_estimada", recaudo)

    st.markdown("---")
    st.subheader("Fugas de Ingresos (Pérdidas)")
    
    c_ev, c_fr = st.columns(2)
    with c_ev:
        evasion = st.slider("Estimación de Evasión (Pasajeros que no pagan)", 0, 50, 
                      st.session_state.survey_data["evasion_pct"], key="w_evasion", help="Sobre 15% es crítico")
        update_data("evasion_pct", evasion)
    
    with c_fr:
        fraude = st.slider("Estimación Fraude Interno (Conductor)", 0, 50, 
                     st.session_state.survey_data["fraude_conductor_pct"], key="w_fraude", help="Dinero que el conductor recibe pero no marca")
        update_data("fraude_conductor_pct", fraude)

    col1, col2 = st.columns([1,1])
    col1.button("⬅ Atrás", on_click=navigate, args=(-1,))
    col2.button("Analizar y Finalizar 🏁", on_click=navigate, args=(1,))

# --- PASO 6: RESUMEN Y EXPORTACIÓN ---
elif st.session_state.current_step == 6:
    st.header("Resultados del Levantamiento")
    
    analizar_riesgos()
    data = st.session_state.survey_data

    # Métricas Clave (Top Level)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Flota", f"{data['flota_qty']} buses")
    kpi2.metric("Recaudo Est.", f"${data['recaudacion_estimada']:,.0f}")
    kpi3.metric("Evasión", f"{data['evasion_pct']}%", delta_color="inverse", delta=f"{data['evasion_pct']}%")
    kpi4.metric("Riesgos", len(data["riesgos"]), delta_color="inverse")

    st.divider()

    # Matriz de Riesgos
    st.subheader("Diagnóstico de Riesgos y Oportunidades")
    if not data["riesgos"]:
        st.success("✅ El escenario técnico y de negocio es favorable.")
    else:
        for r in data["riesgos"]:
            color = "🔴" if r["nivel"] == "CRITICO" else "🟠" if r["nivel"] == "ALTO" else "🟡"
            with st.expander(f"{color} {r['titulo']} ({r['nivel']})", expanded=True):
                st.write(r['msg'])

    st.divider()
    
    # Descargas
    col_d1, col_d2 = st.columns(2)
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    col_d1.download_button("📥 Descargar Datos Crudos (JSON)", json_str, "data_campo.json", "application/json")

    try:
        pdf_bytes = generar_pdf()
        col_d2.download_button("📄 Descargar Reporte Ejecutivo (PDF)", pdf_bytes, "reporte_fcs.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error PDF: {e}")

    if st.button("Comenzar Nuevo Levantamiento"):
        st.session_state.clear()
        st.rerun()
