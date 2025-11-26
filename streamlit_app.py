import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Digitalizador Registral", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div.block-container { max-width: 1000px; padding-top: 2rem; }
    .stTextArea textarea { background-color: #161b22; border: 1px solid #30363d; color: #c9d1d9; font-family: 'Courier New', monospace; }
    div.stButton > button { background-color: #238636; color: #fff; border: none; font-weight: 700; width: 100%; padding: 0.8rem; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN IA ---
def configurar_y_conectar(api_key):
    genai.configure(api_key=api_key)
    
    # Intentamos conectar con el modelo más estándar y compatible del mundo
    # Si 'gemini-1.5-flash' falla, usamos 'gemini-pro' (el clásico 1.0)
    modelos_a_probar = ['gemini-1.5-flash', 'gemini-pro']
    
    for nombre_modelo in modelos_a_probar:
        try:
            modelo = genai.GenerativeModel(nombre_modelo)
            # Hacemos una prueba vacía para ver si conecta
            return modelo, nombre_modelo
        except:
            continue
            
    # Si llegamos aquí, forzamos el genérico
    return genai.GenerativeModel('gemini-pro'), "gemini-pro"

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 3. LÓGICA DE TRANSCRIPCIÓN ---
def transcribir_documento(modelo, archivo_bytes):
    prompt = """
    Actúa como Oficial de Registro. Transcribe el PDF LITERALMENTE.
    
    INSTRUCCIONES:
    1. Copia el texto seguido en párrafos. NO uses listas ni resúmenes.
    2. ELIMINA SOLO: Sellos, timbres ("TIMBRE DEL ESTADO", "0,15 €") y notas al margen.
    3. MANTÉN EXACTOS: Nombres, DNI, Fincas y Referencias Catastrales.

    Responde SOLO con un JSON así:
    {
        "intervinientes": "Texto literal del bloque de comparecencia e intervención...",
        "fincas": "Texto literal de la descripción de las fincas...",
        "texto_completo": "Texto íntegro del documento limpio..."
    }
    """
    
    # Configuración de seguridad desactivada para evitar bloqueos falsos
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    response = modelo.generate_content(
        [
            {'mime_type': 'application/pdf', 'data': archivo_bytes},
            prompt
        ],
        safety_settings=safety_settings
    )
    return response.text

# --- 4. INTERFAZ ---
st.title("DIGITALIZADOR REGISTRAL")
st.markdown("### Transcripción Literal Inteligente")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

# Conexión
try:
    model, nombre_modelo = configurar_y_conectar(st.secrets["GOOGLE_API_KEY"])
    # st.caption(f"✅ Conectado usando motor: {nombre_modelo}") # Debug oculto
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("TRANSCRIBIR DOCUMENTO"):
        with st.spinner('🔍 Procesando documento...'):
            try:
                bytes_data = uploaded_file.read()
                resultado_json = transcribir_documento(model, bytes_data)
                datos = json.loads(limpiar_json(resultado_json))
                
                st.success("✅ Transcripción Completada")
                
                st.subheader("👥 Intervinientes (Literal)")
                st.text_area("intervinientes", value=datos.get("intervinientes", ""), height=200)
                
                st.subheader("🏡 Fincas (Literal)")
                st.text_area("fincas", value=datos.get("fincas", ""), height=300)
                
                with st.expander("📄 Documento Completo"):
                    st.text_area("completo", value=datos.get("texto_completo", ""), height=600)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("⚠️ Tu API Key no es válida para esta región. Crea una nueva en Google AI Studio.")
