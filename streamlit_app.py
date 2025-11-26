import streamlit as st
import google.generativeai as genai
import json
import os

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(
    page_title="Digitalizador Registral",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSONALIZADO (ESTILO DARK TECH) ---
st.markdown("""
<style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    .stApp { background-color: #000000; font-family: 'Inter', sans-serif; }
    
    /* Título estilo Foto */
    .custom-title {
        font-size: 3rem; font-weight: 700; color: #ffffff; 
        text-align: center; margin-top: 2rem; margin-bottom: 3rem; line-height: 1.2;
    }

    /* Botón Descarga */
    .stButton > button { 
        width: 100%; font-weight: 600; border-radius: 8px; padding: 12px; 
        background-color: #22c55e; color: white; border: none; font-size: 16px;
        transition: all 0.2s;
    }
    .stButton > button:hover { background-color: #16a34a; box-shadow: 0 0 15px rgba(34, 197, 94, 0.3); }

    /* Caja de texto */
    .stTextArea textarea {
        background-color: #1c1c1c; color: #e5e5e5; border-radius: 8px;
        font-family: 'Georgia', serif; font-size: 15px; line-height: 1.6;
        border: 1px solid #333;
    }
    
    /* Cajón de Upload (Estilo Foto) */
    [data-testid='stFileUploader'] {
        background-color: #111827; border: 2px dashed #3f3f46; border-radius: 16px; padding: 30px;
    }
    [data-testid='stFileUploader'] section > div:first-child { display: none; }
    [data-testid='stFileUploader'] section::before {
        content: "☁️ Arrastra tu PDF aquí"; color: #e5e5e5; font-size: 1.2rem; font-weight: 600;
        display: block; text-align: center; margin-bottom: 10px;
    }
    [data-testid='stFileUploader'] section::after {
        content: "Límite 200MB • PDF"; color: #71717a; font-size: 0.8rem;
        display: block; text-align: center; margin-bottom: 15px;
    }
    
    /* Login Box */
    .login-container {
        max-width: 400px; margin: 50px auto; padding: 30px;
        background-color: #111827; border: 1px solid #374151; border-radius: 16px; text-align: center;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE ACCESO (EL PORTERO) ---
def check_password():
    """Bloquea la app si no hay clave válida."""
    if st.session_state.get("password_correct", False):
        return True

    st.markdown('<div class="custom-title" style="font-size:2rem;">Acceso Profesional</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            password = st.text_input("Clave de Licencia", type="password", placeholder="XXXX-XXXX-XXXX")
            submit = st.form_submit_button("ENTRAR")
            
            if submit:
                # CLAVE MAESTRA: F90-ADMIN (O cualquier clave larga tipo Lemon Squeezy)
                if password == "F90-ADMIN" or (len(password) > 8 and "-" in password):
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("⛔ Clave no válida")
    return False

if not check_password():
    st.stop()

# --- 3. GESTIÓN API KEY (RENDER FIX) ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass

if not api_key:
    st.error("⛔ Error: Falta la API Key. Añádela en Render > Environment.")
    st.stop()

# --- 4. CEREBRO (TU LÓGICA ORIGINAL) ---
def transcribir_con_corte(key, archivo_bytes):
    genai.configure(api_key=key)
    
    # Usamos el modelo Pro Latest como pediste
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
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
    - Los párrafos bien separados y estructurados como en la original.

    Devuelve un JSON con un solo campo:
    {
        "texto_cortado": "El texto literal limpio hasta antes de Protección de Datos."
    }
    """
    
    config = genai.types.GenerationConfig(temperature=0.0, response_mime_type="application/json")

    response = model.generate_content(
        [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
        generation_config=config
    )
    return response.text

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 5. INTERFAZ PRINCIPAL ---
st.markdown('<div class="custom-title">Transforma tus PDFs<br>en texto limpio.</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

if uploaded_file:
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Transcribiendo...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada
                resultado = transcribir_con_corte(api_key, bytes_data)
                datos = json.loads(limpiar_json(resultado))
                texto_final = datos.get("texto_cortado", "")
                
                st.success("✅ Documento Recortado y Limpio")
                
                # BOTÓN DE DESCARGA
                st.download_button(
                    label="⬇️ DESCARGAR TEXTO (.TXT)",
                    data=texto_final,
                    file_name="escritura_cuerpo.txt",
                    mime="text/plain"
                )
                
                # VISTA PREVIA
                st.text_area("Vista Previa", value=texto_final, height=600, label_visibility="collapsed")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
