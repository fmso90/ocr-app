import streamlit as st
import google.generativeai as genai
import json
import os

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(
    page_title="Digitalizador",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    h1, h2, h3, h4 { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; text-align: center; }
    
    /* Botón Descarga */
    .stButton > button { 
        width: 100%; 
        font-weight: bold; 
        border-radius: 8px; 
        padding: 0.8rem; 
        background-color: #2ea043; 
        color: white; 
        border: none;
        font-size: 1.1rem;
    }
    .stButton > button:hover { background-color: #238636; }

    /* Caja de texto */
    .stTextArea textarea {
        background-color: #fdfbf7;
        color: #1f1f1f;
        border-radius: 4px;
        font-family: 'Georgia', serif;
        font-size: 15px;
        line-height: 1.6;
        border: 1px solid #444;
    }
    
    /* Estilo para el Login */
    .login-input input {
        background-color: #111 !important;
        color: white !important;
        border: 1px solid #444 !important;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 0. SISTEMA DE ACCESO (CON SUSCRIPCIÓN) ---
def check_password():
    """Pide clave antes de mostrar nada."""
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("<br><br><h3 style='text-align:center;'>🔐 Acceso Privado</h3>", unsafe_allow_html=True)
    
    password = st.text_input("Introduce la Clave de Acceso", type="password", key="login_input")
    
    if st.button("ENTRAR"):
        # CLAVE MAESTRA: F90-ADMIN
        if password == "F90-ADMIN" or (len(password) > 8 and "-" in password):
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("⛔ Clave incorrecta")

    # --- AÑADIDO: BOTÓN DE SUSCRIPCIÓN ---
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center; color:#aaa; font-size:0.9rem;">
            ¿No tienes licencia? 
            <a href="TU_ENLACE_DE_PAGO_DE_LEMON_SQUEEZY" target="_blank" style="color:#2ea043; font-weight:bold; text-decoration:none;">
                Suscríbete aquí
            </a>
        </div>
        """, 
        unsafe_allow_html=True
    )
    # -------------------------------------
            
    return False

# SI NO HAY CLAVE, PARAMOS AQUÍ EL CÓDIGO
if not check_password():
    st.stop()

# --- 2. CEREBRO CON "FRENO DE MANO" ---
def transcribir_con_corte(api_key, archivo_bytes):
    genai.configure(api_key=api_key)
    
    # Usamos el modelo Pro para asegurar que entiende la instrucción de parada
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
    - Los párrafos bien separados y estructurados como en la original

    Devuelve un JSON con un solo campo:
    {
        "texto_cortado": "El texto literal limpio hasta antes de Protección de Datos."
    }
    """
    
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

# --- 3. INTERFAZ ---
st.title("Convierte PDF en texto listo para usar")
st.markdown("#### Transcripción Literal de documentos")

# --- AÑADIDO: DETECTOR DE CLAVE (RENDER + LOCAL) ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass

if not api_key:
    st.error("⛔ Falta API Key. Añádela en Render > Environment.")
    st.stop()
# ---------------------------------------------------

uploaded_file = st.file_uploader("Sube la escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Transcribiendo'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada (usando la api_key detectada arriba)
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
                if "404" in str(e):
                    st.warning("Verifica tu API Key.")
