import streamlit as st
import google.generativeai as genai
import json
import os
import requests # <-- Nuevo: Necesario para hacer llamadas a la API externa

# --- CONFIGURACIÓN DE CLAVES PARA LEMON SQUEEZY ---
# Se busca la clave API de Lemon Squeezy en los secretos de Streamlit o en variables de entorno
LS_API_KEY = os.environ.get("LS_API_KEY")
if not LS_API_KEY:
    try:
        # Usar .get() para evitar error si 'LS_API_KEY' no existe en st.secrets
        LS_API_KEY = st.secrets.get("LS_API_KEY") 
    except:
        LS_API_KEY = None

def validate_lemon_license(license_key: str, ls_api_key: str) -> bool:
    """
    Función para validar la clave de licencia contra el API de Lemon Squeezy.
    Devuelve True si la licencia es válida y activa.
    """
    if not ls_api_key:
        # Si no hay clave de configuración, no podemos validar con LS
        st.warning("⚠️ Aviso: Falta la LS_API_KEY para validar la licencia de pago.")
        return False
        
    url = "https://api.lemonsqueezy.com/v1/licenses/validate"
    headers = {
        "Accept": "application/vnd.api+json",
        "Authorization": f"Bearer {ls_api_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "license_key": license_key,
        # Opcional: 'instance_name' puede ser útil para vincular el uso
        # "instance_name": "Digitalizador_Streamlit_App"
    }

    try:
        # Petición a la API de Lemon Squeezy
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status() 

        result = response.json()
        
        # El campo 'valid' indica si la licencia es válida y activa
        valid = result.get('valid', False)
        
        if valid:
            # Opcional: Puedes añadir lógica para revocar o comprobar la expiración aquí
            return True
        else:
            # La API de Lemon Squeezy ha devuelto un resultado no válido
            return False

    except requests.exceptions.RequestException as e:
        # Captura errores de red, HTTP, timeout, etc.
        st.error(f"❌ Error de conexión al validar licencia: {e}")
        return False
    except json.JSONDecodeError:
        st.error("❌ Error al procesar la respuesta de la API de Lemon Squeezy.")
        return False


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

# --- 0. SISTEMA DE ACCESO (AÑADIDO: EL PORTERO) ---
def check_password():
    """Pide clave antes de mostrar nada."""
    global LS_API_KEY # Acceder a la clave de Lemon Squeezy definida globalmente
    
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("<br><br><h3 style='text-align:center;'>🔐 Acceso Privado</h3>", unsafe_allow_html=True)
    
    # Se ajusta el texto para incluir la licencia de Lemon Squeezy
    password = st.text_input("Introduce la Clave de Acceso (o Licencia Lemon Squeezy)", type="password", key="login_input")
    
    if st.button("ENTRAR"):
        # 1. CLAVE MAESTRA: F90-ADMIN
        if password == "F90-ADMIN":
            st.session_state["password_correct"] = True
            st.rerun()
        
        # 2. VALIDACIÓN CON LEMON SQUEEZY (si la clave está configurada)
        elif LS_API_KEY and validate_lemon_license(password, LS_API_KEY):
            st.session_state["password_correct"] = True
            st.rerun()
            
        else:
            st.error("⛔ Clave incorrecta o Licencia no válida/expirada.")
            
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

# --- DETECTOR DE CLAVE DE GOOGLE (RENDER + LOCAL) ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass

if not api_key:
    # Mensaje de error más específico
    st.error("⛔ Falta API Key de Google. Añádela en Render > Environment.") 
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
