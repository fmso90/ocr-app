import streamlit as st
import google.generativeai as genai
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Digitalizador Registral (Selector)", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div.block-container { max-width: 1000px; padding-top: 2rem; }
    .stTextArea textarea { background-color: #161b22; border: 1px solid #30363d; color: #c9d1d9; font-family: 'Courier New', monospace; }
    div.stButton > button { background-color: #238636; color: #fff; border: none; font-weight: 700; width: 100%; padding: 0.8rem; }
    .success-box { padding: 1rem; background-color: #064e3b; border-radius: 8px; border: 1px solid #059669; margin-bottom: 1rem; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE IA ---
def obtener_modelos_disponibles(api_key):
    """Pregunta a Google qué modelos tienes activos en tu cuenta."""
    genai.configure(api_key=api_key)
    modelos = []
    try:
        for m in genai.list_models():
            # Filtramos solo los modelos que sirven para generar texto (Gemini)
            if 'generateContent' in m.supported_generation_methods:
                modelos.append(m.name)
        # Ordenamos para que los Pro salgan primero si es posible
        modelos.sort(reverse=True)
        return modelos
    except Exception as e:
        return []

def transcribir_literal(api_key, nombre_modelo, archivo_bytes):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(nombre_modelo)
    
    prompt = """
    Actúa como un Oficial de Registro experto. Transcribe el PDF LITERALMENTE.
    
    INSTRUCCIONES DE SEGURIDAD (TEMP 0.0):
    1. COPIA el texto palabra por palabra. NO resumas. NO uses viñetas.
    2. LIMPIEZA: Elimina SOLO los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS") y notas al margen.
    3. MANTÉN EXACTOS: Nombres, DNI, Fincas y Referencias Catastrales. Si algo no se lee, pon [ILEGIBLE].

    Devuelve JSON:
    {
        "intervinientes": "Texto literal del bloque de comparecencia e intervención.",
        "fincas": "Texto literal de la descripción de las fincas.",
        "texto_completo": "Texto íntegro del documento limpio."
    }
    """
    
    # Configuración "Robot" (Cero creatividad para evitar invenciones)
    config = genai.types.GenerationConfig(
        temperature=0.0,
        response_mime_type="application/json"
    )

    response = model.generate_content(
        [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
        generation_config=config
    )
    return response.text

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- INTERFAZ ---
st.title("DIGITALIZADOR REGISTRAL (SELECTOR)")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

# 1. CARGAR MODELOS DISPONIBLES
try:
    lista_modelos = obtener_modelos_disponibles(st.secrets["GOOGLE_API_KEY"])
    if not lista_modelos:
        st.error("❌ Tu API Key es válida, pero no tiene acceso a ningún modelo Gemini. Crea una nueva en Google AI Studio.")
        st.stop()
        
    # Selector de modelo en la barra lateral o arriba
    modelo_elegido = st.selectbox(
        "🧠 Selecciona el motor de Inteligencia Artificial:", 
        lista_modelos,
        index=0, # Por defecto elige el primero (suele ser el más nuevo)
        help="Elige 'gemini-1.5-pro' o superior para mejores resultados."
    )
    
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button(f"TRANSCRIBIR CON {modelo_elegido.upper()}"):
        with st.spinner(f'Leído con {modelo_elegido}...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Ejecutar transcripción
                resultado = transcribir_literal(st.secrets["GOOGLE_API_KEY"], modelo_elegido, bytes_data)
                datos = json.loads(limpiar_json(resultado))
                
                st.markdown(f"<div class='success-box'>✅ <b>Éxito usando:</b> {modelo_elegido}</div>", unsafe_allow_html=True)
                
                st.subheader("👥 Intervinientes (Literal)")
                st.text_area("intervinientes", value=datos.get("intervinientes", ""), height=200)
                
                st.subheader("🏡 Fincas (Literal)")
                st.text_area("fincas", value=datos.get("fincas", ""), height=300)
                
                with st.expander("📄 Texto Completo"):
                    st.text_area("completo", value=datos.get("texto_completo", ""), height=600)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.warning("Prueba a seleccionar otro modelo de la lista de arriba.")
