import streamlit as st
from datetime import datetime

# --- 1. BASE DE CONOCIMIENTO REGIONAL (HARDCODED) ---
LOCALE_CONFIG = {
    "Chile": {
        "currency": "CLP", 
        "card_example": "Bip! / TNE", 
        "regulator": "DTPM / MTT",
        "tech_note": "Estándar Mifare alto. Santiago requiere certificación DTPM estricta."
    },
    "Colombia": {
        "currency": "COP", 
        "card_example": "TuLlave / Cívica", 
        "regulator": "MinTransporte",
        "tech_note": "Bogotá usa lógica compleja (Angelcom/RB). Medellín es propietaria. Alta seguridad."
    },
    "México": {
        "currency": "MXN", 
        "card_example": "Tarjeta MI (Movilidad Integrada)", 
        "regulator": "Semovi",
        "tech_note": "⚠️ ATENCIÓN: Tarjeta MI usa estándar CALYPSO. Requiere SAM específico en validador Telpo."
    },
    "Perú": {
        "currency": "PEN", 
        "card_example": "Lima Pass / Metropolitano", 
        "regulator": "ATU",
        "tech_note": "Fragmentación de operadores. Se busca integración bajo ATU."
    },
    "Ecuador": {
        "currency": "USD", 
        "card_example": "Tarjeta Ciudad (Quito) / Metrovía", 
        "regulator": "Municipios / ANT",
        "tech_note": "Quito es líder en ABT (Cédula/QR/Bancaria). Guayaquil es más tradicional (Stored Value)."
    },
    "Panamá": {
        "currency": "USD / PAB", 
        "card_example": "Tarjeta MetroBus / Visa / MC", 
        "regulator": "ATTT / Metro de Panamá",
        "tech_note": "🔥 LÍDER OPEN LOOP: El pago con tarjeta bancaria directa es el estándar esperado."
    },
    "Otro/Genérico": {
        "currency": "USD", 
        "card_example": "Tarjeta Propietaria", 
        "regulator": "Autoridad Local",
        "tech_note": "Validar estándar ISO 14443 A/B."
    }
}

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Levantamiento AFC Latam", layout="wide", page_icon="🌎")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .header-style { font-size:22px; color: #004d99; font-weight: bold; border-bottom: 2px solid #004d99; margin-bottom: 15px; padding-top: 10px; }
    .country-tag { background-color: #004d99; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
    .warning-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 10px; font-size: 14px; margin-bottom: 5px; }
    .critical-box { background-color: #f8d7da; border-left: 5px solid #dc3545; padding: 10px; font-size: 14px; margin-bottom: 5px; }
    .success-box { background-color: #d4edda; border-left: 5px solid #28a745; padding: 10px; font-size: 14px; margin-bottom: 5px; }
    .info-box { background-color: #e2e3e5; border-left: 5px solid #383d41; padding: 10px; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- ESTADO ---
if 'data' not in st.session_state:
    st.session_state.data = {}
if 'country' not in st.session_state:
    st.session_state.country = "Chile" # Default

# --- BARRA LATERAL (PAÍS) ---
with st.sidebar:
    st.title("🌎 Región del Proyecto")
    selected_country = st.selectbox("Seleccione País:", list(LOCALE_CONFIG.keys()))
    st.session_state.country = selected_country
    
    ctx = LOCALE_CONFIG[selected_country]
    
    st.markdown("---")
    st.markdown(f"**Moneda:** {ctx['currency']}")
    st.markdown(f"**Referencia:** {ctx['card_example']}")
    st.info(f"💡 **Nota Técnica País:**\n{ctx['tech_note']}")
    st.caption("v5.0 Latam Edition")

# --- LÓGICA DE DIAGNÓSTICO EXPERTO ---
def analyze_project_latam(data, country):
    report = {
        "hardware": [],
        "platform": [],
        "country_alerts": [], # Alertas específicas por país
        "blockers": [],
        "financial_notes": []
    }
    
    ctx = LOCALE_CONFIG[country]

    # 1. ANÁLISIS DE HARDWARE (TELPO)
    hw_model = "Telpo F6 / T10 Lite" # Base
    if "Tarjeta Bancaria (cEMV)" in data.get("medios_pago", []):
        hw_model = "Telpo T20 (Certificado PCI/EMV)"
    elif "Biometría Facial" in data.get("medios_pago", []):
        hw_model = "Telpo T20 / F6 (Binocular 3D)"
    
    # SAMs Físicas (Hardware Constraint)
    if data.get("seguridad_sam") == "Cliente entrega SAMs Físicas":
        report["hardware"].append(f"🔌 **{hw_model}** con ranuras PSAM Físicas habilitadas.")
        report["country_alerts"].append("⚠️ Verificar compatibilidad de voltaje de la SAM del cliente (3V vs 5V).")
    else:
        report["hardware"].append(f"🚌 **{hw_model}** (Configuración estándar).")

    # 2. ANÁLISIS DE PLATAFORMA (MASABI vs PRODATA)
    # Lógica de Stored Value
    if data.get("logica_saldo") == "Stored Value (Saldo en Tarjeta)":
        report["platform"].append("✅ **Recomendado:** Prodata / Desarrollo Propio (Legacy).")
        report["blockers"].append("⛔ **Masabi Incompatible:** Masabi Justride NO gestiona saldo en chip (Stored Value).")
    elif data.get("logica_saldo") == "ABT (Saldo en Nube)":
        report["platform"].append("✅ **Recomendado:** Masabi Justride (SaaS/Cloud).")
        report["platform"].append("ℹ️ Opción secundaria: Prodata (Modo ABT).")

    # 3. REGLAS ESPECÍFICAS POR PAÍS (CÓDIGO DURO)
    
    # PANAMÁ 🇵🇦
    if country == "Panamá":
        if "Tarjeta Bancaria (cEMV)" not in data.get("medios_pago", []):
            report["country_alerts"].append("🇵🇦 **CRÍTICO:** Panamá tiene alta penetración de pagos Open Loop (Metro). ¿Seguro que no requieren lectura de Visa/Mastercard? Esto podría descalificarnos.")
        if data.get("logica_saldo") == "Stored Value (Saldo en Tarjeta)":
            report["country_alerts"].append("🇵🇦 **Observación:** Aunque MetroBus usa Stored Value, la tendencia en Panamá es ir hacia ABT completo. Sugerir migración.")

    # ECUADOR 🇪🇨
    if country == "Ecuador":
        if "Quito" in data.get("cliente", "") or "Metro" in data.get("cliente", ""):
            if data.get("logica_saldo") != "ABT (Saldo en Nube)":
                report["country_alerts"].append("🇪🇨 **Alerta Quito:** El Metro de Quito opera nativamente con ABT (Cuenta Ciudadana). Ofrecer Stored Value aquí es un retroceso tecnológico.")
    
    # MÉXICO 🇲🇽
    if country == "México":
        if "Tarjeta Ciudad" in str(data.get("medios_pago", [])):
            report["country_alerts"].append("🇲🇽 **Estándar Calypso:** La Tarjeta MI usa Calypso. Validar que el Telpo T20 incluya la licencia del stack Calypso o la SAM de Semovi.")

    # CHILE 🇨🇱
    if country == "Chile":
        if "Santiago" in data.get("cliente", "") or "RED" in data.get("cliente", ""):
            report["country_alerts"].append("🇨🇱 **Certificación DTPM:** Cualquier validador en Santiago requiere pasar pruebas de laboratorio DTPM (Complejidad Alta).")

    # 4. INFRAESTRUCTURA & COSTOS
    if data.get("hosting") == "On-Premise (Servidores Propios)":
        report["financial_notes"].append("💰 CAPEX Alto: Servidores Físicos.")
        if "Masabi" in str(report["platform"]):
            report["blockers"].append("⛔ **Masabi:** No instala On-Premise. Conflicto de arquitectura.")
    else:
        report["financial_notes"].append(f"☁️ OPEX: Cobro mensual recurrente en {ctx['currency']} o USD.")

    return report

# --- INTERFAZ DE FORMULARIO ---

st.title(f"Levantamiento AFC - {st.session_state.country}")
st.markdown(f'<span class="country-tag">{st.session_state.country}</span>', unsafe_allow_html=True)
st.markdown("---")

with st.form("latam_form"):
    
    # SECCIÓN 1: CLIENTE
    st.markdown('<div class="header-style">1. Perfil del Proyecto</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.data["cliente"] = st.text_input("Nombre Cliente / Licitación:")
        st.session_state.data["flota"] = st.number_input("Cantidad de Vehículos/Torniquetes:", min_value=1)
    with c2:
        st.session_state.data["tipo_transporte"] = st.selectbox("Modalidad:", ["Bus Urbano", "Bus Interprovincial", "Metro/Tren", "Teleférico"])
        st.session_state.data["hosting"] = st.radio("Infraestructura:", ["SaaS (Nube)", "On-Premise (Servidores Propios)"])

    # SECCIÓN 2: TECNOLOGÍA DE ACCESO (CORE)
    st.markdown('<div class="header-style">2. Medios de Acceso y Lógica</div>', unsafe_allow_html=True)
    
    # Medios de Pago
    opciones_pago = [
        "Tarjeta Propietaria/Ciudad", 
        "Tarjeta Bancaria (cEMV)", 
        "Código QR (App)", 
        "Código QR (Papel)", 
        "Biometría Facial"
    ]
    st.session_state.data["medios_pago"] = st.multiselect("¿Qué debe leer el validador?", opciones_pago)
    
    # Lógica de Saldo (Pregunta del Millón)
    st.markdown("#### 🧠 ¿Dónde vive el dinero?")
    st.session_state.data["logica_saldo"] = st.radio("Arquitectura de Saldo:", 
        ["Stored Value (Saldo en Tarjeta)", "ABT (Saldo en Nube)"],
        help="Stored Value = Tarjeta clásica. ABT = Sistema moderno (Masabi).")

    # Seguridad
    st.markdown("#### 🔐 Gestión de Llaves (SAM)")
    st.session_state.data["seguridad_sam"] = st.selectbox("Autenticación de Tarjetas:", 
        ["Nosotros generamos el mapa (SDK Telpo)", "Cliente entrega SAMs Físicas", "Lectura de UID (Sin seguridad)"])

    # SECCIÓN 3: SERVICIOS PERIFÉRICOS
    st.markdown('<div class="header-style">3. Ecosistema Comercial</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.session_state.data["retail_pos"] = st.checkbox("¿Requiere POS de Recarga (Telpo TPS900)?")
    with c4:
        st.session_state.data["mesa_ayuda"] = st.checkbox("¿Requiere Mesa de Ayuda a Pasajeros?")

    submitted = st.form_submit_button("Generar Diagnóstico Experto")

# --- VISUALIZACIÓN DE RESULTADOS ---

if submitted:
    analisis = analyze_project_latam(st.session_state.data, st.session_state.country)
    
    st.divider()
    st.header("📊 Diagnóstico Preliminar")
    
    # 1. ALERTAS CRÍTICAS (BLOCKERS)
    if analisis["blockers"]:
        st.subheader("⛔ Bloqueos de Arquitectura")
        for err in analisis["blockers"]:
            st.markdown(f'<div class="critical-box">{err}</div>', unsafe_allow_html=True)

    # 2. ALERTAS PAÍS (NUEVO)
    if analisis["country_alerts"]:
        st.subheader(f"🌍 Alertas Específicas: {st.session_state.country}")
        for alert in analisis["country_alerts"]:
            st.markdown(f'<div class="info-box">{alert}</div>', unsafe_allow_html=True)

    # 3. RECOMENDACIONES
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("🛠️ Hardware Sugerido")
        for h in analisis["hardware"]:
            st.markdown(h)
        if st.session_state.data["retail_pos"]:
            st.markdown("- 🏪 **POS:** Telpo TPS900 (Android) para red de carga.")

    with col_b:
        st.subheader("☁️ Plataforma")
        for p in analisis["platform"]:
            st.markdown(p)
    
    # 4. JSON
    with st.expander("Ver Datos Crudos (Para Copiar a Correo)"):
        st.json(st.session_state.data)
