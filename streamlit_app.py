import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Extractor Registral AI", page_icon="🏘️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .data-card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
    h1, h2, h3 { color: #fff !important; }
    div.stButton > button { background-color: #fff; color: #000; border: none; font-weight: 700; width: 100%; padding: 0.8rem; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN GEMINI ---
def configurar_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 3. EXTRACCIÓN (AHORA MUESTRA EL ERROR REAL) ---
def extraer_datos_inteligentes(modelo, archivo_bytes):
    prompt = """
    Actúa como Oficial de Registro. Analiza el PDF adjunto.
    Extrae en JSON:
    {
        "documento": {"notario": "", "fecha": "", "protocolo": "", "ciudad": ""},
        "intervinientes": [{"rol": "VENDEDOR/COMPRADOR", "nombre": "", "dni": ""}],
        "fincas": [{"registral": "", "catastral": "", "descripcion": ""}],
        "cargas": ""
    }
    """
    
    # AQUÍ ESTABA EL "SILENCIADOR". LO QUITAMOS.
    # Si falla, Python lanzará el error y lo veremos en pantalla.
    response = modelo.generate_content([
        {'mime_type': 'application/pdf', 'data': archivo_bytes},
        prompt
    ])
    return response.text

# --- 4. INTERFAZ ---
st.title("EXTRACTOR DE DATOS REGISTRAL")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta la API Key en los Secrets.")
    st.stop()

# Intentamos configurar el modelo
try:
    model = configurar_gemini(st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error configurando la API Key: {e}")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("EXTRAER DATOS"):
        with st.spinner('Analizando...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada directa (sin try/except oculto)
                resultado_crudo = extraer_datos_inteligentes(model, bytes_data)
                
                # Procesar resultado
                json_str = limpiar_json(resultado_crudo)
                datos = json.loads(json_str)
                
                st.success("✅ Extracción Correcta")
                
                # Visor rápido de JSON
                st.json(datos)

            except Exception as e:
                # AQUÍ VEREMOS EL PROBLEMA REAL
                st.error(f"❌ ERROR TÉCNICO DETALLADO: {str(e)}")
                st.warning("Posibles causas: 1. API Key incorrecta (¿Es de AI Studio?). 2. PDF corrupto. 3. Versión de librería antigua.")
