import streamlit as st
import pandas as pd

# --- Configuración de la Página ---
st.set_page_config(page_title="Configurador de Sistema de Recaudo", layout="centered")

# --- Estado de la Sesión (Base de datos temporal en memoria) ---
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# --- Definición de las Preguntas ---
questions = [
    # Sección 1: Flota y Operación
    {
        "id": "fleet_size",
        "section": "1. Flota y Operación",
        "question": "¿Cuál es el tamaño aproximado de la flota a equipar?",
        "type": "radio",
        "options": ["1 - 50 buses", "51 - 200 buses", "Más de 200 buses", "Por definir"]
    },
    {
        "id": "connectivity",
        "section": "1. Flota y Operación",
        "question": "¿Cómo es la conectividad en la ruta?",
        "type": "radio",
        "options": ["4G/5G Estable (Online)", "Intermitente / Zonas muertas", "Solo WiFi en patios (Offline)", "No sé"]
    },
    # Sección 2: Política Tarifaria
    {
        "id": "fare_model",
        "section": "2. Política Tarifaria",
        "question": "¿Cuál es el modelo de cobro principal?",
        "type": "radio",
        "options": ["Tarifa Plana (Monto fijo)", "Por Distancia (GPS/Secciones)", "Por Tiempo", "Mixto / Complejo"]
    },
    # Sección 3: Tecnología y Pagos
    {
        "id": "payment_methods",
        "section": "3. Medios de Pago",
        "question": "¿Qué medios de pago deben aceptar los validadores? (Seleccione todos los que apliquen)",
        "type": "multiselect",
        "options": ["Tarjeta Cerrada (Mifare/Desfire)", "Código QR (Celular/Papel)", "Tarjeta Bancaria (EMV Contactless)", "Biometría Facial"]
    },
    # Sección 4: Control y Auditoría
    {
        "id": "apc_need",
        "section": "4. Control de Evasión (APC)",
        "question": "¿Requieren conteo automático de pasajeros para auditar la recaudación?",
        "type": "radio",
        "options": ["No, no es prioridad", "Sí, precisión estándar (>95%)", "Sí, alta precisión certificada (>99% - LiDAR/ToF)"]
    },
     # Sección 5: Software
    {
        "id": "software_model",
        "section": "5. Gestión y Software",
        "question": "¿Cómo prefieren gestionar el software?",
        "type": "radio",
        "options": ["SaaS (Nube, pago mensual)", "On-Premise (Servidores propios del cliente)", "Indiferente / Lo que recomienden"]
    }
]

# --- Lógica de Recomendación ---
def generate_recommendation(answers):
    rec = {
        "hardware_tier": "Estándar",
        "validator_features": [],
        "apc_sensor": "No requerido",
        "software_focus": [],
        "alert": []
    }

    # 1. Análisis de Conectividad
    if answers.get('connectivity') in ["Intermitente / Zonas muertas", "Solo WiFi en patios (Offline)"]:
        rec["alert"].append("⚠️ **Crítico:** Se requiere arquitectura 'Offline-First'. Los validadores deben tener alta capacidad de almacenamiento para listas negras y transacciones locales.")
    
    # 2. Análisis de Medios de Pago (Hardware)
    payments = answers.get('payment_methods', [])
    if "Tarjeta Bancaria (EMV Contactless)" in payments:
        rec["hardware_tier"] = "Premium (Certificado)"
        rec["validator_features"].append("Certificación EMV L1/L2 & PCI (Costo Hardware +$$$)")
    if "Código QR (Celular/Papel)" in payments:
        rec["validator_features"].append("Lector QR dedicado de alta velocidad")
    if "Biometría Facial" in payments:
        rec["hardware_tier"] = "High-Performance"
        rec["validator_features"].append("Cámara Binocular + Procesador Quad-Core para IA")

    # 3. Análisis de Tarifas
    if answers.get('fare_model') == "Por Distancia (GPS/Secciones)":
        rec["software_focus"].append("Módulo de Matriz de Paradas y Geocercas")
        rec["validator_features"].append("GPS de Alta Precisión integrado")
        rec["alert"].append("ℹ️ **Nota:** Cobro por distancia usualmente requiere validación a la SALIDA (Check-out) o interacción del conductor.")

    # 4. Análisis de APC (Contador de Pasajeros)
    apc = answers.get('apc_need')
    if "alta precisión" in str(apc):
        rec["apc_sensor"] = "Sensor 3D Time-of-Flight (ToF) - (Ej. Streamax/Hella)"
        rec["software_focus"].append("Módulo de Auditoría: Comparativo Recaudo vs. Pasajeros")
    elif "estándar" in str(apc):
        rec["apc_sensor"] = "Cámara Binocular Estándar"

    # 5. Tamaño de Flota y Software
    if answers.get('fleet_size') == "Más de 200 buses" and answers.get('software_model') != "SaaS (Nube, pago mensual)":
        rec["alert"].append("🏢 Para flotas grandes, evaluar infraestructura de servidores robusta si eligen On-Premise.")

    return rec

# --- Interfaz de Usuario ---

st.title("🚌 Asistente de Diseño AFC")
st.markdown("Herramienta preliminar para levantamiento de requisitos de Sistema de Recaudo.")

# Barra de progreso
progress = (st.session_state.step / len(questions))
st.progress(progress)

if st.session_state.step < len(questions):
    # Mostrar Pregunta Actual
    q = questions[st.session_state.step]
    
    st.subheader(f"{q['section']}")
    st.write(f"**{q['question']}**")
    
    # Renderizar input según tipo
    answer = None
    if q['type'] == 'radio':
        answer = st.radio("Seleccione una opción:", q['options'], key=q['id'])
    elif q['type'] == 'multiselect':
        answer = st.multiselect("Seleccione opciones:", q['options'], key=q['id'])
    
    st.write("")
    
    # Botones de Navegación
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.session_state.step > 0:
            if st.button("⬅️ Anterior"):
                st.session_state.step -= 1
                st.rerun()
    with col2:
        if st.button("Siguiente ➡️"):
            # Guardar respuesta
            st.session_state.answers[q['id']] = answer
            # Avanzar
            st.session_state.step += 1
            st.rerun()

else:
    # --- Pantalla Final: Resultados ---
    st.success("✅ Levantamiento completado")
    
    final_answers = st.session_state.answers
    recommendation = generate_recommendation(final_answers)
    
    st.divider()
    st.header("📋 Sugerencia Preliminar de Proyecto")
    
    # Mostrar Alertas Críticas primero
    if recommendation["alert"]:
        for alert in recommendation["alert"]:
            st.warning(alert)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("🛠️ Hardware Recomendado")
        st.info(f"**Nivel de Equipo:** {recommendation['hardware_tier']}")
        st.markdown("**Características del Validador:**")
        if recommendation["validator_features"]:
            for feat in recommendation["validator_features"]:
                st.markdown(f"- {feat}")
        else:
            st.markdown("- Validador Estándar (Tarjeta Mifare)")
            
        st.markdown("**Sistema de Conteo (APC):**")
        st.markdown(f"- {recommendation['apc_sensor']}")

    with col_b:
        st.subheader("💻 Software y Lógica")
        st.markdown("**Módulos Críticos:**")
        st.markdown("- Gestión de Flota y Tarifas")
        for sw in recommendation["software_focus"]:
            st.markdown(f"- {sw}")
            
    # Resumen de respuestas (Input del cliente)
    with st.expander("Ver respuestas originales del cliente"):
        st.json(final_answers)

    if st.button("🔄 Iniciar Nuevo Levantamiento"):
        st.session_state.step = 0
        st.session_state.answers = {}
        st.rerun()
