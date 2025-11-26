import streamlit as st
import google.generativeai as genai
import json
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Digitalizador Registral",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div.block-container { max-width: 1000px; padding-top: 2rem; }
    .stTextArea textarea { background-color: #161b22; border: 1px solid #30363d; color: #c9d1d9; font-family: 'Courier New', monospace; }
    div.stButton > button { background-color: #238636; color: #fff; border: none; font-weight: 700; width: 100%; padding: 0.8rem; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTOR DE MODELOS (Fuerza Bruta) ---
def obtener_modelo_activo(api_key):
    genai.configure(api_key=api_key)
    
    # Lista de modelos a probar (del más rápido al más compatible)
    lista_modelos = [
        "gemini-1.5-flash-001",   # Nombre técnico exacto
        "models/gemini-1.5-flash", # Alias con prefijo
        "gemini-1.5-flash",       # Alias corto
        "gemini-1.5-pro",         # Alternativa potente
        "gemini-pro"              # El clásico (si todo falla)
    ]
    
    # Devolvemos el generador configurado con la lista
    return lista_modelos

def transcribir_con_reintentos(api_key, archivo_bytes, prompt, config):
    modelos = obtener_modelo_activo(api_key)
    error_log = []

    for nombre_modelo in modelos:
        try:
            # Intentamos conectar con este modelo
            model = genai.GenerativeModel(nombre_modelo)
            response = model.generate_content(
                [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
                generation_config=config
            )
            return response.text, nombre_modelo # ¡Éxito!
        except Exception as e:
            # Si falla, guardamos el error y probamos el siguiente
            error_log.append(f"{nombre_modelo}: {str(e)}")
            continue
            
    # Si llegamos aquí, han fallado todos
    raise Exception(f"No se pudo conectar con ningún modelo. Detalles: {error_log}")

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 3. INTERFAZ ---
st.title("DIGITALIZADOR REGISTRAL")
st.markdown("### Transcripción Literal Inteligente")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("TRANSCRIBIR DOCUMENTO"):
        # Barra de progreso indeterminada
        status_text = st.empty()
        status_text.info("🔄 Iniciando conexión con Google AI...")
        
        try:
            bytes_data = uploaded_file.read()
            
            # Prompt Literal
            prompt = """
            Actúa como un Oficial de Registro experto. Transcribe el PDF LITERALMENTE.
            
            REGLAS:
            1. COPIA el texto palabra por palabra en párrafos. NO resumas. NO uses viñetas.
            2. ELIMINA SOLO sellos, timbres ("TIMBRE DEL ESTADO", "0,15 €") y notas marginales.
            3. MANTÉN INTEGROS nombres, DNI, Fincas y Fechas.

            Devuelve JSON:
            {
                "intervinientes": "Texto literal del bloque de comparecencia e intervención.",
                "fincas": "Texto literal de la descripción de las fincas.",
                "texto_completo": "Texto íntegro del documento limpio."
            }
            """
            
            config = genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )

            # Llamada Inteligente con Reintentos
            status_text.info("🧠 Analizando documento (probando modelos)...")
            resultado_json, modelo_usado = transcribir_con_reintentos(st.secrets["GOOGLE_API_KEY"], bytes_data, prompt, config)
            
            # Éxito
            status_text.empty() # Borrar mensaje de carga
            st.success(f"✅ Transcripción completada usando: {modelo_usado}")
            
            datos = json.loads(limpiar_json(resultado_json))
            
            st.subheader("👥 Intervinientes (Literal)")
            st.text_area("intervinientes", value=datos.get("intervinientes", ""), height=200, label_visibility="collapsed")
            
            st.subheader("🏡 Fincas (Literal)")
            st.text_area("fincas", value=datos.get("fincas", ""), height=300, label_visibility="collapsed")
            
            with st.expander("📄 Documento Completo"):
                st.text_area("completo", value=datos.get("texto_completo", ""), height=600, label_visibility="collapsed")

        except Exception as e:
            status_text.empty()
            st.error(f"❌ Error: {str(e)}")
            st.warning("Si el error persiste, verifica que tu API Key sea válida en Google AI Studio.")
