import streamlit as st
from datetime import datetime

# --- Configuración Visual ---
st.set_page_config(page_title="Levantamiento AFC Enterprise", layout="wide", page_icon="📝")

# --- CSS Personalizado ---
st.markdown("""
<style>
    .header-style { font-size:24px; color: #004d99; font-weight: bold; padding-top: 10px; }
    .sub-header { font-size:18px; color: #333; font-weight: bold; }
    .capex-box { background-color: #e6f7ff; border-left: 5px solid #007bff; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 14px;}
    .opex-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 14px;}
</style>
""", unsafe_allow_html=True)

# --- Estado de la Sesión ---
if 'data' not in st.session_state:
    st.session_state.data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- Lógica de Negocio (El Cerebro) ---
def analyze_project(data):
    report = {
        "hardware_bus": [],      # Telpo Validador
        "hardware_retail": [],   # Telpo POS/Kiosco
        "platform_arch": [],     # Masabi / Prodata
        "services_scope": [],    # Soporte / CIT
        "infra_model": ""        # Cloud vs On-Prem
    }
    
    # 1. Hardware a Bordo (CAPEX)
    if "Tarjeta Bancaria (EMV)" in data.get("medios_pago", []):
        report["hardware_bus"].append("Validador: Telpo T20 (Certificado EMV L1/L2).")
    elif "Biometría Facial" in data.get("medios_pago", []):
        report["hardware_bus"].append("Validador: Telpo F6/T20 con cámara binocular y detección de vida.")
    else:
        report["hardware_bus"].append("Validador: Telpo T10 Lite / F6 (Estándar Mifare).")

    # 2. Red de Carga (CAPEX + OPEX)
    if data.get("red_carga_pos") == "Sí, necesitamos proveer POS a comercios":
        report["hardware_retail"].append("POS Portátil: Telpo TPS900 o P8 (Android + Impresora).")
    if data.get("red_carga_tvm") == "Sí, máquinas en estaciones/paradas":
        report["hardware_retail"].append("Kiosco Autoservicio (TVM): Telpo K5 / K20 (Pantalla grande + Pinpad).")

    # 3. Infraestructura (CAPEX vs OPEX)
    if data.get("hosting_pref") == "Nube (SaaS / Cloud Público)":
        report["infra_model"] = "Modelo 100% OPEX (AWS/Azure). Ideal para Masabi Justride."
    elif data.get("hosting_pref") == "On-Premise (Servidores Propios)":
        report["infra_model"] = "Modelo CAPEX Intensivo (Servidores Físicos). Requiere licenciamiento perpetuo (Prodata)."
        report["platform_arch"].append("⚠️ Advertencia: Masabi NO suele instalarse On-Premise. Se forzaría solución 'Legacy'.")

    # 4. Servicios (OPEX Humano)
    if data.get("soporte_pasajeros") == "Proveedor (Nosotros ponemos el Call Center)":
        report["services_scope"].append("💰 OPEX ALTO: Contratación de ejecutivos Nivel 1 y Nivel 2.")
    if data.get("logistica_efectivo") == "Proveedor (Nosotros recolectamos)":
        report["services_scope"].append("🚨 RIESGO/OPEX: Requiere contrato con empresa de valores (Brinks/Prosegur) y seguros.")

    return report

# --- Formulario ---
st.title("📋 Diagnóstico AFC: Técnico, Comercial y Operativo")
st.markdown("Herramienta para dimensionamiento de CAPEX/OPEX y definición de arquitectura.")

with st.form("main_form"):

    # --- TAB 1: FLOTA Y CONTEXTO ---
    st.markdown('<div class="header-style">1. Contexto y Flota (Dimensionamiento Básico)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.data["cliente"] = st.text_input("Cliente (Operador/Autoridad):")
        st.session_state.data["cant_buses"] = st.number_input("Cantidad de Buses:", min_value=1)
    with c2:
        st.session_state.data["tipo_servicio"] = st.selectbox("Tipo de Servicio:", ["Urbano Masivo", "Interurbano/Rural", "Transporte de Personal", "Escolar"])
        st.session_state.data["fecha_go_live"] = st.date_input("Fecha estimada de inicio:")

    # --- TAB 2: INFRA A BORDO ---
    st.markdown('<div class="header-style">2. Hardware a Bordo (Validador)</div>', unsafe_allow_html=True)
    st.caption("Define el modelo Telpo a cotizar.")
    
    st.session_state.data["medios_pago"] = st.multiselect("Medios de Pago Requeridos:", 
        ["Tarjeta Mifare (Cerrada)", "Tarjeta Bancaria (EMV)", "Código QR (App)", "Código QR (Papel)", "Biometría Facial", "Efectivo (Alcancía)"])
    
    c3, c4 = st.columns(2)
    with c3:
        st.session_state.data["conectividad_bus"] = st.selectbox("Conectividad del Bus:", ["4G/5G Provisto por Cliente", "4G/5G Provisto por Nosotros (SIM)", "Offline (WiFi en patios)"])
    with c4:
        st.session_state.data["montaje_tipo"] = st.selectbox("Instalación Física:", ["Poste Vertical (Estándar)", "Montaje en Pared/Tablero", "Torniquete"])

    with st.expander("💡 Nota para Ventas (Hardware)"):
        st.markdown("""
        * **EMV (Bancaria):** Sube el precio del equipo (Telpo T20).
        * **Offline:** Si no hay 4G, el validador necesita mucha memoria para listas negras.
        * **SIM Cards:** Si nosotros ponemos el 4G, es un costo mensual (OPEX) por cada bus.
        """)

    # --- TAB 3: RED DE RECARGA Y RETAIL ---
    st.markdown('<div class="header-style">3. Red de Recarga (Puntos de Venta)</div>', unsafe_allow_html=True)
    st.caption("¿Cómo carga saldo la gente? Define si vendemos POS o Kioscos.")

    c5, c6 = st.columns(2)
    with c5:
        st.session_state.data["red_carga_pos"] = st.radio("¿Requieren POS para comercios?", ["No, solo digital/web", "Sí, necesitamos proveer POS a comercios", "El cliente ya tiene sus POS"])
    with c6:
        st.session_state.data["red_carga_tvm"] = st.radio("¿Requieren Máquinas de Autoservicio (TVM)?", ["No", "Sí, máquinas en estaciones/paradas", "Sí, máquinas a bordo del bus"])

    st.session_state.data["logistica_efectivo"] = st.selectbox("¿Quién recoge el dinero de los puntos de venta?", 
        ["El Cliente (Operador)", "Proveedor (Nosotros gestionamos CIT)", "No aplica (Todo es digital)"])

    with st.expander("💡 Nota para Ventas (Retail)"):
        st.markdown("""
        * **POS:** Si piden POS, cotizar **Telpo TPS900**.
        * **Logística Efectivo:** Si nosotros recogemos la plata, necesitamos contratar un camión de valores. ¡Costo altísimo! Tratar de que lo haga el cliente.
        """)

    # --- TAB 4: SOPORTE Y OPERACIÓN ---
    st.markdown('<div class="header-style">4. Soporte y Atención al Pasajero (Mesa de Ayuda)</div>', unsafe_allow_html=True)
    st.caption("Dimensionamiento de personal (RRHH).")

    st.session_state.data["soporte_pasajeros"] = st.selectbox("Atención al Usuario (Reclamos, Tarjetas bloqueadas):", 
        ["El Cliente (Ellos tienen su Call Center)", "Proveedor (Nosotros ponemos el Call Center y personal)", "Mixto"])
    
    st.session_state.data["personalizacion_tarjetas"] = st.selectbox("¿Quién imprime/personaliza las tarjetas?", 
        ["Imprenta masiva externa", "El Cliente en sus oficinas", "Nosotros (Servicio de personalización)"])

    # --- TAB 5: INFRAESTRUCTURA TI Y SOFTWARE ---
    st.markdown('<div class="header-style">5. Infraestructura TI y Hosting</div>', unsafe_allow_html=True)
    st.caption("Define arquitectura Cloud vs On-Premise.")

    c7, c8 = st.columns(2)
    with c7:
        st.session_state.data["hosting_pref"] = st.selectbox("Preferencia de Alojamiento:", ["Nube (SaaS / Cloud Público)", "On-Premise (Servidores Propios)", "Nube Privada / Híbrida"])
    with c8:
        st.session_state.data["propiedad_datos"] = st.radio("¿Existen leyes de soberanía de datos?", ["No, se puede alojar en AWS EE.UU.", "Sí, los datos deben quedarse en el país"])

    st.session_state.data["integraciones_extra"] = st.multiselect("Integraciones requeridas:", ["SAP/ERP", "Herramienta de BI (Tableau/PowerBI)", "App de Terceros (Moovit/Google Maps)"])

    submitted = st.form_submit_button("Generar Informe para Preventa")

# --- Generación del Reporte Final ---

if submitted:
    st.session_state.submitted = True
    analisis = analyze_project(st.session_state.data)
    
    st.divider()
    st.header(f"📂 Informe de Levantamiento: {st.session_state.data['cliente']}")
    st.caption("Copia este reporte y envíalo al Ingeniero de Preventa.")

    # Sección 1: Dimensionamiento Económico
    st.subheader("1. Impacto Económico (CAPEX vs OPEX)")
    col_eco1, col_eco2 = st.columns(2)
    
    with col_eco1:
        st.markdown('<div class="capex-box"><strong>🔵 CAPEX (Inversión Inicial)</strong><br>Elementos que requieren compra de activos:</div>', unsafe_allow_html=True)
        # Hardware Bus
        for item in analisis["hardware_bus"]:
            st.markdown(f"- {item}")
        # Hardware Retail
        if analisis["hardware_retail"]:
            for item in analisis["hardware_retail"]:
                st.markdown(f"- {item}")
        else:
            st.markdown("- No se requiere hardware de retail.")
        # Servidores
        if "On-Premise" in analisis["infra_model"]:
            st.markdown("- Compra de Servidores Físicos y Licencias de Base de Datos.")

    with col_eco2:
        st.markdown('<div class="opex-box"><strong>🟡 OPEX (Gasto Recurrente)</strong><br>Costos mensuales operativos:</div>', unsafe_allow_html=True)
        # Infraestructura
        if "Nube" in analisis["infra_model"]:
            st.markdown("- Hosting Mensual (AWS/Azure) + Servicios Masabi.")
        # Conectividad
        if "Nosotros (SIM)" in str(st.session_state.data.get("conectividad_bus")):
            st.markdown("- Planes de datos M2M (x cantidad de buses).")
        # Personal
        for svc in analisis["services_scope"]:
            st.markdown(f"- {svc}")

    # Sección 2: Arquitectura Técnica
    st.subheader("2. Definición de Arquitectura")
    st.info(f"**Estrategia de Hosting:** {analisis['infra_model']}")
    
    if "Tarjeta Bancaria (EMV)" in st.session_state.data.get("medios_pago", []):
        st.warning("💳 **Requisito Crítico:** Se requiere Gateway de Pagos (Masabi/Littlepay) y Validador Certificado PCI (Telpo T20). Esto tiene costos de transacción (%) bancaria.")

    # Sección 3: Datos Crudos
    with st.expander("Ver Respuestas Completas (JSON)"):
        st.json(st.session_state.data)
