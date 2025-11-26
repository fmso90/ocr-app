import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Extractor Registral Literal", page_icon="⚖️", layout="wide")

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
def configurar_gemini(api_key):
    genai.configure(api_key=api_key)
    # CORRECCIÓN TÉCNICA: Añadimos 'models/' para que la librería antigua lo encuentre si falla la actualización
    return genai.GenerativeModel('models/gemini-1.5-flash')

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 3. TRANSCRIPCIÓN LITERAL ---
def transcribir_literalmente(modelo, archivo_bytes):
    prompt = """
    Actúa como un Oficial de Registro experto en mecanografía.
    Tu tarea es LEER el PDF adjunto y EXTRAER el texto LITERALMENTE, palabra por palabra.

    REGLAS DE ORO (INVIOLABLES):
    1. NO RESUMAS. NO uses viñetas. NO uses guiones. Copia el texto seguido en párrafos.
    2. LIMPIEZA VISUAL: Elimina ÚNICAMENTE el texto de los sellos ("TIMBRE DEL ESTADO", "NIHIL PRIUS", "0,15 €") que interrumpa las frases.
    3. DATOS SAGRADOS: Nombres, DNI, Lugares y Fincas deben copiarse EXACTAMENTE igual al original.

    Devuelve un objeto JSON con estas 3 secciones de TEXTO PURO:
    {
        "intervinientes": "Copia LITERALMENTE el bloque desde 'COMPARECEN' hasta 'INTERVIENEN'. Incluye nombres, DNIs y estados civiles seguidos.",
        "fincas": "Copia LITERALMENTE la descripción de las fincas. Desde 'RÚSTICA/URBANA' hasta el final de los linderos.",
        "texto_completo": "El texto ÍNTEGRO del documento unido en un solo bloque continuo."
    }
    """
    
    generation_config = genai.types.GenerationConfig(
        temperature=0.1,
        response_mime_type="application/json"
    )

    response = modelo.generate_content(
        [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
        generation_config=generation_config
    )
    return response.text

# --- 4. INTERFAZ ---
st.title("DIGITALIZADOR REGISTRAL")
st.markdown("### Transcripción Literal Inteligente")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

# Manejo de errores de conexión
try:
    model = configurar_gemini(st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error configuración: {e}")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("TRANSCRIBIR DOCUMENTO"):
        with st.spinner('🔍 Leyendo documento...'):
            try:
                bytes_data = uploaded_file.read()
                resultado_json = transcribir_literalmente(model, bytes_data)
                datos = json.loads(limpiar_json(resultado_json))
                
                st.success("✅ Transcripción Completada")
                
                st.subheader("👥 Intervinientes (Literal)")
                st.text_area("intervinientes", value=datos.get("intervinientes", ""), height=200, label_visibility="collapsed")
                
                st.subheader("🏡 Fincas (Literal)")
                st.text_area("fincas", value=datos.get("fincas", ""), height=300, label_visibility="collapsed")
                
                with st.expander("📄 Ver Documento Completo"):
                    st.text_area("completo", value=datos.get("texto_completo", ""), height=600, label_visibility="collapsed")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("⚠️ El servidor necesita actualizarse. Ve a 'Manage app' -> 'Reboot app'.")
