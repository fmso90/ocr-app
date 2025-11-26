import streamlit as st
import google.generativeai as genai
import json
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="F90 OCR",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. ESTILO DARK TECH (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    /* Fondo Negro */
    .stApp {
        background-color: #000000;
        font-family: 'Inter', sans-serif;
    }
    
    /* Títulos */
    .custom-title {
        font-size: 3.5rem;
        font-weight: 600;
        color: #ffffff;
        text-align: center;
        margin-top: 2rem;
        margin-bottom: 3rem;
        line-height: 1.1;
    }

    /* Uploader (Estilo Oscuro Limpio) */
    [data-testid='stFileUploader'] {
        background-color: #111827;
        border: 2px dashed #3f3f46;
        border-radius: 20px;
        padding: 30px;
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
    
    /* Inputs (Login) */
    .stTextInput > div > div > input {
        background-color: #111827;
        color: #ffffff;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 10px;
    }

    /* Área de Texto */
    .stTextArea textarea {
        background-color: #1c1c1c;
        color: #e5e5e5;
        border: 1px solid #333;
        border-radius: 8px;
        font-family: 'Georgia', serif;
        font-size: 15px;
        line-height: 1.6;
    }
    
    /* Ocultar elementos extra */
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. SISTEMA DE LOGIN (EL PORTERO) ---
def check_password():
    """Si devuelve False, detiene la app."""
    if st.session_state.get("password_correct", False):
        return True

    # Diseño de la pantalla de bloqueo
    st.markdown('<div style="text-align:center; margin-top:100px; margin-bottom:20px;"><h2 style="color:white;">Acceso Profesional</h2></div>', unsafe_allow_html=True)
    
    password = st.text_input("Introduce tu Licencia", type="password", placeholder="XXXX-XXXX-XXXX")
    
    if st.button("ENTRAR"):
        # CLAVES VÁLIDAS:
        # 1. Tu clave maestra: F90-ADMIN
        # 2. Simulación Lemon Squeezy: Cualquier texto largo con guiones (ej: 1234-ABCD)
        if password == "F90-ADMIN" or (len(password) > 8 and "-" in password):
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("⛔ Licencia no válida")
            
    return False

# ¡AQUÍ ESTÁ EL CANDADO! Si no pasa, se para todo.
if not check_password():
    st.stop()

# ======================================================
#  SI LLEGA AQUÍ, ES QUE HA ENTRADO (ZONA PRIVADA)
# ======================================================

# Título Principal
st.markdown('<div class="custom-title">Transforma tus PDFs<br>en texto limpio.</div>', unsafe_allow_html=True)

# --- 4. GESTIÓN DE CLAVES (RENDER) ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass

if not api_key:
    st.error("⛔ Error: Falta la API Key. Configúrala en Render.")
    st.stop()

# --- 5. LÓGICA DEL CEREBRO ---
def transcribir_con_corte(key, archivo_bytes):
    genai.configure(api_key=key)
    # Usamos 1.5 Pro para máxima calidad y cero errores vacíos
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = """
    Actúa como un Oficial de Registro. Tu misión es TRANSCRIBIR la escritura, pero SOLO LA PARTE DISPOSITIVA.
    1. Comienza a transcribir desde el principio.
    2. DETENTE INMEDIATAMENTE antes de "PROTECCIÓN DE DATOS".
    3. NO transcribas nada posterior.
    4. Elimina sellos ("TIMBRE", "NIHIL PRIUS") del texto.
    5. Copia literal.
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

# --- 6. INTERFAZ DE LA HERRAMIENTA ---
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
                        st.warning("El documento parece vacío o no legible.")
                else:
                    st.error("Error de conexión con la IA.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Botón discreto para cerrar sesión (abajo)
if st.button("Cerrar Sesión", type="secondary"):
    st.session_state["password_correct"] = False
    st.rerun()
