import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuración Visual ---
st.set_page_config(page_title="Levantamiento AFC Pro", layout="wide", page_icon="🚌")

# --- CSS para estilizar ---
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .tip-box { background-color: #f0f2f6; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .success-box { background-color: #d4edda; border-left: 5px solid #28a745; padding: 15px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- Inicializar Estado ---
if 'data' not in st.session_state:
    st.session_state.data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- Funciones de Lógica de Proveedores ---
def analyze_requirements(data):
    recommendations = {
        "hardware_telpo": [],
        "platform_strategy": [], # Masabi / Prodata
        "risks": []
    }
    
    # 1. Análisis Hardware (Telpo Focus)
    if "Tarjeta Bancaria (EMV/C-EMV)" in data.get("medios_pago", []):
        recommendations["hardware_telpo"].append("Modelo Requerido: Telpo T20 o T10 (Debe tener Certificación EMV L1/L2 & PCI).")
    elif "Código QR" in data.get("medios_pago", []):
        recommendations["hardware_telpo"].append("Modelo Sugerido: Telpo T20 (Lector QR dedicado) o T10 Lite.")
    else:
        recommendations["hardware_telpo"].append("Modelo Básico: Telpo F6 o similar (Solo tarjeta cerrada Mifare).")
        
    if data.get("ambiente_bus") == "Extremo (Polvo, Calor, Vibración fuerte)":
        recommendations["hardware_telpo"].append("⚠️ Accesorio: Case rugerizado IP65 y soportes con amortiguación extra.")

    # 2. Análisis Plataforma (Masabi/Prodata Focus)
    if data.get("modelo_tarifario") == "Account Based Ticketing (ABT) - Calculado en Nube":
        recommendations["platform_strategy"].append("Ideal para **Masabi Justride**. Permite 'Fare Capping' (Topes diarios/semanales).")
    elif data.get("modelo_tarifario") == "Card Based (Saldo en la tarjeta)":
        recommendations["platform_strategy"].append("Requiere desarrollo sobre SDK de Telpo o solución legacy de Prodata. Masabi NO se recomienda para 'Card Based' puro.")

    if "Integración con Metro/Tren" in data.get("integraciones", []):
        recommendations["platform_strategy"].append("Complejidad Alta: Se requiere definir quién es el 'Clearing House' (Cámara de compensación).")

    # 3. Riesgos
    if data.get("conectividad") == "Mala / Zonas Muertas" and "Account Based Ticketing" in str(data.get("modelo_tarifario")):
        recommendations["risks"].append("🔴 RIESGO ALTO: ABT requiere buena conexión. Se deben configurar listas blancas offline en el validador Telpo.")

    return recommendations

# --- Interfaz Principal ---

st.title("🚌 Herramienta de Levantamiento Técnico AFC")
st.markdown("Generador de Requisitos para Soluciones **Telpo + Masabi/Prodata**")
st.markdown("---")

with st.form("survey_form"):
    
    # SECCIÓN 1: EL CLIENTE
    st.header("1. Perfil del Cliente y Flota")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.data["cliente"] = st.text_input("Nombre del Operador/Autoridad:")
        st.session_state.data["flota_total"] = st.number_input("Cantidad Total de Vehículos:", min_value=1)
    with col2:
        st.session_state.data["tipo_vehiculo"] = st.multiselect("Tipo de Vehículos:", ["Bus Urbano (12m)", "Bus Articulado", "Minibús/Van", "Tranvía"])
        st.session_state.data["puertas"] = st.selectbox("Configuración de Validación:", ["Solo puerta delantera (Entry only)", "Validar al entrar y salir (Check-in/Check-out)", "Torniquete en piso (Estación)"])
    
    with st.expander("ℹ️ Ayuda para el Vendedor (Sección 1)"):
        st.info("""
        * **Check-in/Check-out:** Requiere el doble de validadores (uno por puerta) o validadores de bajada específicos.
        * **Minibús:** El espacio es reducido, quizás el Telpo T20 es muy grande y convenga un formato tablet o handheld.
        """)

    # SECCIÓN 2: INFRAESTRUCTURA
    st.header("2. Infraestructura y Entorno")
    col3, col4 = st.columns(2)
    with col3:
        st.session_state.data["conectividad"] = st.selectbox("Conectividad en Ruta:", ["4G/5G Estable", "Mala / Zonas Muertas", "Solo Wi-Fi en Patios"])
        st.session_state.data["ambiente_bus"] = st.selectbox("Condiciones ambientales:", ["Estándar (Urbano A/C)", "Extremo (Polvo, Calor, Vibración fuerte)"])
    with col4:
        st.session_state.data["cableado"] = st.radio("¿Tienen cableado estructurado en el bus?", ["Sí, Ethernet/Red disponible", "No, solo corriente (12/24V)", "No se sabe"])
        st.session_state.data["montaje"] = st.selectbox("Tipo de Tubos/Pasamanos:", ["Estándar (32-35mm)", "Delgados", "No tiene (requiere poste dedicado)"])

    with st.expander("ℹ️ Ayuda para el Vendedor (Sección 2)"):
        st.info("""
        * **Conectividad:** Masabi funciona mejor 'Online'. Si es mala, el validador Telpo debe tener más memoria para guardar transacciones localmente.
        * **Cableado:** Si no hay red, el validador Telpo necesitará su propia SIM Card (Datos móviles).
        """)

    # SECCIÓN 3: MODELO DE NEGOCIO (TARIFAS)
    st.header("3. Reglas de Negocio y Tarifas")
    st.session_state.data["modelo_tarifario"] = st.radio("Lógica Principal de Cobro:", 
        ["Tarifa Plana (Siempre el mismo precio)", 
         "Por Distancia (GPS o Zonas)", 
         "Account Based Ticketing (ABT) - Calculado en Nube",
         "Card Based (Saldo en la tarjeta)"])
    
    st.session_state.data["reglas_extra"] = st.multiselect("Reglas Especiales:", 
        ["Transbordos Gratuitos/Descuento", "Fare Capping (Tope de gasto diario)", "Gratuidad (Adulto mayor/Estudiantes)", "Zonificación compleja"])

    with st.expander("ℹ️ Ayuda para el Vendedor (Sección 3)"):
        st.info("""
        * **ABT:** Es lo que vende Masabi. La inteligencia está en la nube, no en la tarjeta. Permite usar tarjetas bancarias.
        * **Card Based:** Es el modelo antiguo (como tarjeta Bip! o SUBE clásica). Requiere grabar el saldo en el chip de la tarjeta.
        * **Fare Capping:** 'Viaja todo lo que quieras por $X al día'. Solo posible con ABT.
        """)

    # SECCIÓN 4: MEDIOS DE PAGO
    st.header("4. Experiencia de Usuario (Pagos)")
    st.session_state.data["medios_pago"] = st.multiselect("¿Qué debe leer el validador?", 
        ["Tarjeta Ciudad (Mifare/Desfire)", "Tarjeta Bancaria (EMV/C-EMV)", "Código QR (Celular)", "Código QR (Papel)", "Reconocimiento Facial"])
    
    st.session_state.data["efectivo"] = st.checkbox("¿El conductor recibe dinero en efectivo?")

    with st.expander("ℹ️ Ayuda para el Vendedor (Sección 4)"):
        st.info("""
        * **Tarjeta Bancaria:** Eleva el costo del validador Telpo (hardware seguro) y requiere pasarela de pagos (Masabi/Littlepay).
        * **QR Papel:** Requiere un escáner Telpo con buena luz para leer papel arrugado.
        * **Reconocimiento Facial:** Telpo tiene modelos (F6/T20) con cámaras binoculares para 'Liveness detection' (que no usen una foto para engañar).
        """)

    # SECCIÓN 5: INTEGRACIÓN
    st.header("5. Integraciones Tecnológicas")
    st.session_state.data["integraciones"] = st.multiselect("Sistemas a integrar:", 
        ["SAE/AVL (Gestión de Flota existente)", "GTFS (Información de rutas)", "Integración con Metro/Tren", "ERP/SAP del cliente"])

    submitted = st.form_submit_button("Generar Diagnóstico Preliminar")

# --- Generación del Reporte ---

if submitted:
    st.session_state.submitted = True
    analysis = analyze_requirements(st.session_state.data)
    
    st.divider()
    st.header("📊 Ficha de Anteproyecto")
    st.caption(f"Fecha: {datetime.now().strftime('%d/%m/%Y')} | Cliente: {st.session_state.data['cliente']}")

    # Resumen Ejecutivo
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.markdown("### 🛠️ Hardware Sugerido (Telpo)")
        if not analysis["hardware_telpo"]:
            st.write("Configuración estándar.")
        for item in analysis["hardware_telpo"]:
            st.success(f"**{item}**")
            
    with col_res2:
        st.markdown("### ☁️ Software & Plataforma (Masabi/Prodata)")
        if not analysis["platform_strategy"]:
            st.write("Dependerá de la definición final.")
        for item in analysis["platform_strategy"]:
            st.info(f"**{item}**")

    # Alertas de Riesgo
    if analysis["risks"]:
        st.markdown("### ⚠️ Riesgos Detectados")
        for risk in analysis["risks"]:
            st.error(risk)

    # Tabla completa de datos
    with st.expander("Ver Levantamiento Completo (Para copiar a Propuesta)"):
        st.json(st.session_state.data)

    st.markdown("---")
    st.markdown("**Siguientes Pasos:** Enviar este resumen al Ingeniero de Preventa para cotización formal.")
