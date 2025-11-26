import streamlit as st
import google.generativeai as genai
import json
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="F90 OCR",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. ESTILO DARK TECH (LIMPIO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    /* Fondo Negro */
    .stApp {
        background-color: #000000;
        font-family: 'Inter', sans-serif;
    }
    
    /* Título */
    .custom-title {
        font-size: 3.5rem;
        font-weight: 600;
        color: #ffffff;
        text-align: center;
        margin-top: 2rem;
        margin-bottom: 3rem;
        line-height: 1.1;
    }

    /* Uploader (Estilo Oscuro pero SIN iconos forzados) */
    [data-testid='stFileUploader'] {
        background-color: #111827;
        border: 2px dashed #3f3f46;
        border-radius: 20px;
        padding: 20px;
    }
    
    /* Botón Verde */
    .stButton > button {
        width: 100%;
        background-color: #22c55e;
        color: white;
        border: none;
        padding: 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        margin-top: 20px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #16a34a;
    }
    
    /* Área de Texto */
    .stTextArea textarea {
        background-color: #1c1c1c;
        color: #e5e5e5;
        border: 1px solid #333;
        border-radius: 8px;
        font-family: 'Georgia', serif;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="custom-title">Transforma tus PDFs<br>en texto limpio.</div>', unsafe_allow_html=True)

# --- 3. GESTIÓN DE CLAVES ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass

if not api_key:
    st.error("⛔ Error: Falta la API Key. Configúrala en Render.")
    st.stop()

# --- 4. LÓGICA ---
def transcribir_con_corte(key, archivo_bytes):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('models/gemini-1.5-pro')
    
    prompt = """
    Actúa como un Oficial de Registro. Tu misión es TRANSCRIBIR la escritura, pero SOLO LA PARTE DISPOSITIVA.

    INSTRUCCIONES DE CORTE (CRÍTICO):
    1. Comienza a transcribir desde el principio del documento.
    2. DETENTE INMEDIATAMENTE antes de llegar a la cláusula titulada "PROTECCIÓN DE DATOS" (o "DATOS PERSONALES").
    3. NO transcribas la cláusula de protección de datos.
    4. NO transcribas nada de lo que venga después (ni el Otorgamiento, ni Firmas, ni Anexos, ni Documentos Unidos).
    5. ¡IGNORA TODO EL RESTO DEL PDF A PARTIR DE ESE PUNTO!

    INSTRUCCIONES DE LIMPIEZA:
    - Copia literal palabra por palabra hasta el punto de corte.
    - Elimina los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS") que manchan el texto.
    - Los párrafos bien separados y estructurados como en la original
    Devuelve JSON: { "texto_cortado": "Texto limpio..." }
    """
    config = genai.types.GenerationConfig(temperature=0.0, response_mime_type="application/json")
    try:
        response = model.generate_content([{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt], generation_config=config)
        return response.text
    except Exception:
        return None

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 5. INTERFAZ ---

# Hemos quitado label_visibility="collapsed" para que se vea el texto nativo si quieres, 
# o puedes poner un texto simple aquí.
uploaded_file = st.file_uploader("Sube tu archivo PDF", type=['pdf'])

if uploaded_file:
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Analizando...'):
            try:
                bytes_data = uploaded_file.read()
                resultado = transcribir_con_corte(api_key, bytes_data)
                
                if resultado:
                    datos = json.loads(limpiar_json(resultado))
                    texto_final = datos.get("texto_cortado", "")
                    
                    if texto_final:
                        st.success("✅ Completado")
                        st.download_button(
                            label="⬇️ DESCARGAR TEXTO (.TXT)",
                            data=texto_final,
                            file_name="escritura_limpia.txt",
                            mime="text/plain"
                        )
                        st.text_area("Vista Previa", value=texto_final, height=600)
                    else:
                        st.warning("El documento parece vacío o ilegible.")
                else:
                    st.error("Error de conexión.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
