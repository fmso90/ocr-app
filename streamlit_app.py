import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN ---
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

# --- 2. CONEXIÓN CON EL MODELO POTENTE ---
def configurar_gemini(api_key):
    genai.configure(api_key=api_key)
    # Usamos el modelo PRO (el más potente para seguir instrucciones complejas)
    return genai.GenerativeModel('models/gemini-1.5-pro')

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 3. CEREBRO DE TRANSCRIPCIÓN LITERAL ---
def transcribir_literalmente(modelo, archivo_bytes):
    prompt = """
    Actúa como un Oficial de Registro experto.
    Tu tarea es LEER el PDF y TRANSCRIBIRLO LITERALMENTE palabra por palabra.

    INSTRUCCIONES ESTRICTAS:
    1. COPIA los párrafos tal cual aparecen. NO RESUMAS. NO uses listas ni viñetas.
    2. LIMPIEZA: Omite ÚNICAMENTE el texto de los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS", "NOTARIA DE...") que mancha el texto.
    3. MANTÉN TODO LO DEMÁS: Nombres, DNI, Fechas, Fincas, Referencias Catastrales y Linderos deben ser exactos al original.

    Devuelve un JSON con 3 campos de TEXTO PURO (Strings):
    {
        "intervinientes": "Texto literal del bloque de comparecencia e intervención (desde COMPARECEN hasta INTERVIENEN/EXPONEN).",
        "fincas": "Texto literal de la descripción de las fincas (Situación, linderos, cabida, referencia). Si hay varias, sepáralas con doble salto de línea.",
        "texto_completo": "El texto íntegro del documento unido y limpio de sellos."
    }
    """
    
    # Configuración para forzar JSON y creatividad baja (literalidad)
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
st.title("DIGITALIZADOR REGISTRAL (MODELO PRO)")
st.markdown("### Transcripción Literal con Gemini 1.5 Pro")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta la API Key en los Secrets.")
    st.stop()

try:
    model = configurar_gemini(st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error de configuración: {e}")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("TRANSCRIBIR DOCUMENTO"):
        with st.spinner('🧠 Gemini Pro está leyendo y limpiando el documento...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada a la IA
                resultado_json = transcribir_literalmente(model, bytes_data)
                
                # Procesar
                datos = json.loads(limpiar_json(resultado_json))
                
                st.success("✅ Transcripción Completada")
                
                st.subheader("👥 Intervinientes (Literal)")
                st.text_area("intervinientes", value=datos.get("intervinientes", ""), height=200, label_visibility="collapsed")
                
                st.subheader("🏡 Fincas (Literal)")
                st.text_area("fincas", value=datos.get("fincas", ""), height=300, label_visibility="collapsed")
                
                with st.expander("📄 Ver Documento Completo Limpio"):
                    st.text_area("completo", value=datos.get("texto_completo", ""), height=600, label_visibility="collapsed")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("⚠️ Error de modelo no encontrado. Asegúrate de haber hecho 'Reboot App' tras cambiar el requirements.txt.")
                if "429" in str(e):
                    st.warning("⚠️ Has superado la cuota gratuita de Gemini Pro por minuto. Espera un poco.")
