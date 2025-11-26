import streamlit as st
import google.generativeai as genai
import json
import os
import time

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(
    page_title="F90 OCR",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS: Diseño Dark Tech + Pantalla de Login
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #000000; font-family: 'Inter', sans-serif; }
    
    /* Títulos */
    .custom-title { font-size: 3.5rem; font-weight: 600; color: #ffffff; text-align: center; margin-top: 2rem; line-height: 1.1; }
    .login-title { font-size: 2rem; font-weight: 600; color: #fff; text-align: center; margin-bottom: 1rem; }
    
    /* Cajón de Login */
    .login-container {
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 16px;
        padding: 40px;
        margin-top: 50px;
        text-align: center;
    }
    
    /* Inputs (Campo de contraseña) */
    .stTextInput > div > div > input {
        background-color: #000; color: #fff; border: 1px solid #444; border-radius: 8px; padding: 10px;
    }

    /* Botones Verdes */
    .stButton > button { width: 100%; background-color: #22c55e; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 16px; transition: all 0.2s; }
    .stButton > button:hover { background-color: #16a34a; }

    /* Uploader (Estilo Foto) */
    [data-testid='stFileUploader'] { background-color: #111827; border: 2px dashed #3f3f46; border-radius: 20px; padding: 40px 20px; }
    [data-testid='stFileUploader'] section > div:first-child { display: none; }
    [data-testid='stFileUploader'] section::before { content: "☁️ Arrastra tu PDF aquí"; color: #e5e5e5; font-size: 1.2rem; font-weight: 600; display: block; margin-bottom: 10px; text-align: center; }
    [data-testid='stFileUploader'] section::after { content: "Límite 200MB • PDF"; color: #71717a; font-size: 0.8rem; display: block; margin-bottom: 15px; text-align: center; }

    /* Resultados */
    .stTextArea textarea { background-color: #1c1c1c; color: #e5e5e5; border: 1px solid #333; font-family: 'Georgia', serif; }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE LICENCIAS (EL PORTERO) ---

def check_password():
    """Devuelve True si el usuario ha metido la clave correcta."""
    
    # Si ya está logueado en esta sesión, adelante
    if st.session_state.get("password_correct", False):
        return True

    # MOSTRAR PANTALLA DE LOGIN
    st.markdown('<div class="login-title">Acceso Profesional</div>', unsafe_allow_html=True)
    
    # Creamos un contenedor visual oscuro
    with st.container():
        st.write("") # Espacio
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            password = st.text_input("Introduce tu Clave de Licencia", type="password", placeholder="XXXX-XXXX-XXXX")
            
            if st.button("ENTRAR"):
                # AQUÍ LA MAGIA: VALIDACIÓN
                # 1. Clave Maestra (Para ti): "F90-ADMIN"
                # 2. Validación Básica: Cualquier clave de más de 8 caracteres (simulando Lemon Squeezy)
                if password == "F90-ADMIN" or (len(password) > 8 and "-" in password):
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("⛔ Clave incorrecta. Suscríbete para acceder.")
            
            st.markdown("---")
            st.markdown("""
            <div style="text-align:center; color:#666; font-size:0.8rem;">
                ¿No tienes clave? <a href="#" style="color:#22c55e;">Consigue una aquí</a>
            </div>
            """, unsafe_allow_html=True)
            
    return False

# SI NO HAY PASSWORD, PARAMOS EL CÓDIGO AQUÍ
if not check_password():
    st.stop()

# ========================================================
# ZONA SEGURA (SOLO SE EJECUTA SI HAY CLAVE VÁLIDA)
# ========================================================

# --- TÍTULO APP ---
st.markdown('<div class="custom-title">Transforma tus PDFs<br>en texto limpio.</div>', unsafe_allow_html=True)

# --- GESTIÓN DE API KEY ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    # Fallback para local
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass

if not api_key:
    st.error("⛔ Error técnico: No se encuentra la API Key del motor.")
    st.stop()

# --- LÓGICA DE IA ---
def transcribir_con_corte(key, archivo_bytes):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = """
    Actúa como un Oficial de Registro. Tu misión es TRANSCRIBIR la escritura, pero SOLO LA PARTE DISPOSITIVA.
    1. Comienza desde el principio.
    2. DETENTE INMEDIATAMENTE antes de "PROTECCIÓN DE DATOS".
    3. NO transcribas nada posterior.
    4. Elimina sellos ("TIMBRE", "NIHIL PRIUS").
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

# --- INTERFAZ PRINCIPAL ---
uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

if uploaded_file:
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Analizando...'):
            try:
                bytes_data = uploaded_file.read()
                resultado = transcribir_con_corte(api_key, bytes_data)
                
                if resultado:
                    datos = json.loads(limpiar_json(resultado))
                    texto_final = datos.get("texto_cortado", "")
                    st.success("✅ Completado")
                    st.download_button(label="⬇️ DESCARGAR TEXTO (.TXT)", data=texto_final, file_name="escritura_limpia.txt", mime="text/plain")
                    st.text_area("Vista Previa", value=texto_final, height=600, label_visibility="collapsed")
                else:
                    st.error("Error de lectura.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Botón de Salir (Opcional)
if st.sidebar.button("Cerrar Sesión"):
    st.session_state["password_correct"] = False
    st.rerun()
