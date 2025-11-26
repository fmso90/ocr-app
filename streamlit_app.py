import streamlit as st
import google.generativeai as genai
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Digitalizador Registral Pro", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div.block-container { max-width: 1000px; padding-top: 2rem; }
    .stTextArea textarea { background-color: #161b22; border: 1px solid #30363d; color: #c9d1d9; font-family: 'Courier New', monospace; }
    div.stButton > button { background-color: #238636; color: #fff; border: none; font-weight: 700; width: 100%; padding: 0.8rem; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN IA ---
def configurar_modelo(api_key):
    genai.configure(api_key=api_key)
    # Usamos el modelo PRO (el más potente de Google)
    # Si falla, puedes probar a cambiar esta línea por 'gemini-1.5-pro-latest'
    return genai.GenerativeModel('models/gemini-1.5-pro')

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- CEREBRO TRANSCRIPTOR ---
def transcribir_literal(modelo, archivo_bytes):
    prompt = """
    Actúa como Oficial de Registro. Transcribe el PDF LITERALMENTE.
    
    INSTRUCCIONES DE ORO:
    1. COPIA el texto palabra por palabra. NO resumas. NO uses viñetas.
    2. LIMPIEZA: Elimina SOLO los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS") y notas al margen.
    3. MANTÉN INTEGROS: Nombres, DNI, Fincas y Referencias Catastrales.

    Devuelve JSON:
    {
        "intervinientes": "Texto literal del bloque de comparecencia...",
        "fincas": "Texto literal de la descripción de las fincas...",
        "texto_completo": "Texto íntegro del documento limpio..."
    }
    """
    
    # Temperatura 0.1 para máxima literalidad (robot mecanógrafo)
    config = genai.types.GenerationConfig(
        temperature=0.1,
        response_mime_type="application/json"
    )

    response = modelo.generate_content(
        [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
        generation_config=config
    )
    return response.text

# --- INTERFAZ ---
st.title("DIGITALIZADOR REGISTRAL (MODELO PRO)")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

try:
    model = configurar_modelo(st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error configuración: {e}")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("TRANSCRIBIR DOCUMENTO"):
        with st.spinner('🧠 Gemini Pro está leyendo el documento...'):
            try:
                bytes_data = uploaded_file.read()
                resultado = transcribir_literal(model, bytes_data)
                datos = json.loads(limpiar_json(resultado))
                
                st.success("✅ Transcripción Completada")
                
                st.subheader("👥 Intervinientes (Literal)")
                st.text_area("intervinientes", value=datos.get("intervinientes", ""), height=200)
                
                st.subheader("🏡 Fincas (Literal)")
                st.text_area("fincas", value=datos.get("fincas", ""), height=300)
                
                with st.expander("📄 Texto Completo"):
                    st.text_area("completo", value=datos.get("texto_completo", ""), height=600)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("⚠️ IMPORTANTE: Tu API Key no tiene acceso al modelo Pro. 1) Crea una clave nueva en aistudio.google.com. 2) Dale a 'Reboot App'.")
