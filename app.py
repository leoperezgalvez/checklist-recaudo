import streamlit as st
from datetime import datetime

# --- CONFIGURACIÓN CULTURAL Y LOCALIZACIÓN ---
LOCALE_CONFIG = {
    "Chile": {
        "currency": "CLP", 
        "card_example": "Bip!, TNE", 
        "tax": "IVA (19%)",
        "regulator": "MTT / DTPM"
    },
    "Colombia": {
        "currency": "COP", 
        "card_example": "Tullave, Cívica", 
        "tax": "IVA (19%)",
        "regulator": "MinTransporte"
    },
    "México": {
        "currency": "MXN", 
        "card_example": "Tarjeta MI, Feria", 
        "tax": "IVA (16%)",
        "regulator": "Semovi"
    },
    "Perú": {
        "currency": "PEN", 
        "card_example": "Lima Pass, Metropolitano", 
        "tax": "IGV (18%)",
        "regulator": "ATU"
    },
    "Otro/Genérico": {
        "currency": "USD", 
        "card_example": "Tarjeta Ciudad", 
        "tax": "Impuestos Locales",
        "regulator": "Autoridad de Transporte"
    }
}

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Levantamiento AFC Expert", layout="wide", page_icon="🌎")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .header-style { font-size:22px; color: #004d99; font-weight: bold; border-bottom: 2px solid #004d99; margin-bottom: 15px; padding-top: 10px; }
    .warning-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 10px; font-size: 14px; }
    .critical-box { background-color: #f8d7da; border-left: 5px solid #dc3545; padding: 10px; font-size: 14px; }
    .success-box { background-color: #d4edda; border-left: 5px solid #28a745; padding: 10px; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAR ESTADO ---
if 'data' not in st.session_state:
    st.session_state.data = {}
if 'country' not in st.session_state:
    st.session_state.country = "Otro/Genérico"

# --- SIDEBAR: CONTEXTO CULTURAL ---
with st.sidebar:
    st.header("🌎 Configuración Regional")
    selected_country = st.selectbox("Selecciona el País del Proyecto:", list(LOCALE_CONFIG.keys()))
    st.session_state.country = selected_country
    
    ctx = LOCALE_CONFIG[selected_country]
    st.info(f"""
    **Contexto Activo:**
    - Moneda: {ctx['currency']}
    - Tarjeta Ref: {ctx['card_example']}
    - Regulador Ref: {ctx['regulator']}
    """)
    st.markdown("---")
    st.caption("v4.0 Final Stable")

# --- LÓGICA DE NEGOCIO AVANZADA (EL CEREBRO) ---
def analyze_project_expert(data, country_ctx):
    report = {
        "hardware_telpo": [],
        "platform_match": [],
        "security_reqs": [],
        "capex_opex_notes": [],
        "blockers": []
    }
    
    # 1. ANÁLISIS DE MEDIOS DE ACCESO Y SEGURIDAD (CRÍTICO)
    is_stored_value = data.get("logica_tarjeta") == "Stored Value (Saldo en el Chip de la tarjeta)"
    is_abt = data.get("logica_tarjeta") == "ABT (Saldo en la Nube)"
    
    # 2. LOGICA PROVEEDOR (Masabi vs Prodata vs Custom)
    if is_stored_value:
        report["platform_match"].append("✅ **Opción Recomendada:** Prodata (Soporta Stored Value Nativo) o Desarrollo Propio sobre SDK Telpo.")
        report["blockers"].append("⛔ **Incompatibilidad Masabi:** Masabi Justride NO soporta 'Stored Value' (saldo en chip). Es una plataforma 100% ABT. Si el cliente exige saldo en tarjeta, Masabi queda descartado.")
    elif is_abt:
        report["platform_match"].append("✅ **Opción Recomendada:** Masabi Justride (Líder en ABT/SaaS) o Prodata (Modo ABT).")
        report["platform_match"].append("ℹ️ **Nota:** Masabi es ideal si se busca despliegue rápido en modo SaaS.")

    # 3. GESTIÓN DE LLAVES Y SAM (Secure Access Module)
    if data.get("gestion_seguridad") == "Cliente entrega las SAM (Hardware)":
        report["hardware_telpo"].append("🔌 **Requisito Hardware:** El Validador Telpo debe tener ranuras PSAM físicas disponibles y accesibles (T20/F6 Pro).")
        report["security_reqs"].append("El integrador deberá implementar la lógica de lectura usando las SAMs del cliente (Desafío técnico medio).")
    elif data.get("gestion_seguridad") == "Nosotros generamos el Mapa y Llaves":
        report["security_reqs"].append("🔐 **Requiere KMS:** Necesitamos un Sistema de Gestión de Llaves (KMS) propio o provisto por Prodata.")
        report["capex_opex_notes"].append("CAPEX/OPEX: Considerar costo de licenciamiento de KMS o servicio de inyección de llaves.")

    # 4. HARDWARE TELPO
    if "Tarjeta Bancaria (EMV)" in data.get("medios_pago", []):
        report["hardware_telpo"].append("💳 **Modelo:** Telpo T20 (Obligatorio por certificación PCI/EMV L1/L2).")
    elif "Biometría" in data.get("medios_pago", []):
        report["hardware_telpo"].append("👁️ **Modelo:** Telpo T20 o F6 (Versión Binocular 3D).")
    else:
        report["hardware_telpo"].append("🚌 **Modelo:** Telpo T10 Lite o F6 (Estándar).")

    # 5. ESTRATEGIA DE SERVIDORES
    if data.get("infraestructura") == "SaaS (Nube)":
        report["capex_opex_notes"].append(f"Modelado OPEX: Cobro mensual por bus activo ({country_ctx['currency']}).")
    else:
        report["capex_opex_notes"].append("Modelado CAPEX: Compra de servidores físicos. Nota: Masabi NO ofrece instalación On-Premise.")

    return report

# --- INTERFAZ DEL FORMULARIO ---

st.title(f"Levantamiento AFC - {st.session_state.country}")
st.markdown("Herramienta de Diagnóstico Técnico-Comercial para Soluciones de Recaudo.")

with st.form("expert_form"):
    
    # TAB 1: OPERACIÓN
    st.markdown('<div class="header-style">1. Operación y Flota</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.data["cliente"] = st.text_input("Nombre Cliente/Licitación:")
        st.session_state.data["flota"] = st.number_input("Tamaño de Flota:", min_value=1, help="Total de buses a equipar")
    with c2:
        st.session_state.data["tipo_flota"] = st.selectbox("Tipo de Vehículo:", ["Bus Estándar", "Bus Articulado", "Minibús/Combi", "Metro/Tren"])
        st.session_state.data["conectividad"] = st.selectbox("Conectividad:", ["Online (4G/5G)", "Offline / Batch (WiFi Patios)", "Híbrida"])

    # TAB 2: EL NÚCLEO (MEDIOS DE ACCESO) - AQUÍ ESTÁ LA MAGIA NUEVA
    st.markdown('<div class="header-style">2. Medios de Acceso y Seguridad (Crítico)</div>', unsafe_allow_html=True)
    
    st.session_state.data["medios_pago"] = st.multiselect("Tecnologías a leer:", 
        [f"Tarjeta Ciudad ({LOCALE_CONFIG[st.session_state.country]['card_example']})", 
         "Tarjeta Bancaria (cEMV)", "Código QR", "Biometría Facial"])

    # Pregunta de Profundidad Técnica
    st.markdown("#### 🧠 Lógica de la Tarjeta de Transporte")
    st.session_state.data["logica_tarjeta"] = st.radio(
        "¿Dónde reside el saldo del usuario?",
        ["ABT (Saldo en la Nube)", "Stored Value (Saldo en el Chip de la tarjeta)"],
        help="ABT = Masabi/Prodata Cloud. Stored Value = Modelo tradicional (Mifare Desfire/Classic)."
    )

    if "Tarjeta Ciudad" in str(st.session_state.data["medios_pago"]):
        st.markdown("#### 🔐 Seguridad y Mapeo (SAM)")
        col_sec1, col_sec2 = st.columns(2)
        with col_sec1:
            st.session_state.data["gestion_seguridad"] = st.selectbox("¿Cómo autenticamos la tarjeta?", 
                ["Cliente entrega las SAM (Hardware)", 
                 "Nosotros generamos el Mapa y Llaves", 
                 "Sin seguridad (Solo leemos UID - No recomendado)"])
        with col_sec2:
            st.session_state.data["formato_mapping"] = st.selectbox("¿Tenemos acceso al Mapa de Memoria?", 
                ["Sí, nos entregan el SDK/Documentación", 
                 "No, es caja negra (Reverse Engineering requerido)", 
                 "Nosotros definimos el mapa nuevo"])

    # TAB 3: INFRAESTRUCTURA
    st.markdown('<div class="header-style">3. Infraestructura y Hosting</div>', unsafe_allow_html=True)
    st.session_state.data["infraestructura"] = st.radio("Modelo de Alojamiento:", ["SaaS (Nube)", "On-Premise (Servidores Propios)"])
    
    # TAB 4: RED DE CARGA Y SERVICIOS
    st.markdown('<div class="header-style">4. Ecosistema de Recarga y Servicios</div>', unsafe_allow_html=True)
    col_ret1, col_ret2 = st.columns(2)
    with col_ret1:
        st.session_state.data["retail"] = st.checkbox("¿Requiere red de carga externa (POS)?")
        st.session_state.data["cit"] = st.checkbox("¿Requiere transporte de valores (CIT)?")
    with col_ret2:
        st.session_state.data["soporte"] = st.selectbox("Nivel de Soporte Requerido:", ["Solo Garantía Hardware", "Soporte Técnico N2/N3", "Operación Completa (Mesa de Ayuda)"])

    submitted = st.form_submit_button("Generar Diagnóstico Experto")

# --- REPORTE DE SALIDA ---
if submitted:
    ctx = LOCALE_CONFIG[st.session_state.country]
    analisis = analyze_project_expert(st.session_state.data, ctx)
    
    st.divider()
    st.header(f"📊 Diagnóstico Preliminar: {st.session_state.data['cliente']}")
    st.caption(f"Configuración Regional: {st.session_state.country} | Moneda Base: {ctx['currency']}")

    # 1. ALERTA DE BLOQUEO (CRUCIAL)
    if analisis["blockers"]:
        for blocker in analisis["blockers"]:
            st.markdown(f'<div class="critical-box">{blocker}</div>', unsafe_allow_html=True)
            st.write("") # Espacio

    # 2. COLUMNAS DE RECOMENDACIÓN
    col_res1, col_res2, col_res3 = st.columns(3)

    with col_res1:
        st.subheader("🛠️ Hardware (Telpo)")
        for item in analisis["hardware_telpo"]:
            st.markdown(f"- {item}")
        if st.session_state.data["retail"]:
            st.markdown("- **Retail:** POS Telpo TPS900 (Android).")

    with col_res2:
        st.subheader("☁️ Plataforma")
        for item in analisis["platform_match"]:
            st.markdown(f"- {item}")
        st.caption(f"Modelo: {st.session_state.data['infraestructura']}")

    with col_res3:
        st.subheader("🔐 Seguridad & SAM")
        if not analisis["security_reqs"]:
            st.write("Estándar / No especificado.")
        for item in analisis["security_reqs"]:
            st.warning(item)

    # 3. NOTAS FINANCIERAS
    st.markdown("---")
    st.subheader("💰 Consideraciones de Costo (CAPEX/OPEX)")
    for note in analisis["capex_opex_notes"]:
        st.info(note)
    
    if st.session_state.data["cit"]:
        st.error(f"⚠️ **ALERTA OPEX:** El servicio de transporte de valores (CIT) en {st.session_state.country} es de alto costo y riesgo. Intentar derivar al cliente.")

    # 4. JSON RAW
    with st.expander("Ver Datos Crudos del Levantamiento"):
        st.json(st.session_state.data)
