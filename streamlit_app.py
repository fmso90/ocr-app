import streamlit as st
import google.generativeai as genai
import json
import os
import requests
import time

# --- CONFIGURACIÓN DE PÁGINA (DISEÑO) ---
st.set_page_config(
    page_title="Digitalizador",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS "LOOK F90 FOTO" (Minimalista Dark & Full Width) ---
st.markdown("""
<style>
    /* Importamos fuente elegante (Montserrat) */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap');

    /* RESET GENERAL DE STREAMLIT PARA QUE PAREZCA UNA WEB */
    .stApp {
        background-color: #121212; /* Negro suave estilo Squarespace */
        color: #f0f0f0;
        font-family: 'Montserrat', sans-serif;
    }
    
    /* QUITAR EL ESPACIO VACÍO DE ARRIBA (PADDING) */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px; /* Ancho máximo para que no se desparrame en pantallas grandes */
    }
    
    /* TIPOGRAFÍA */
    h1, h2, h3, h4, h5 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 500; /* Más fino, más elegante */
        color: #ffffff !important;
        text-transform: uppercase;
        letter-spacing: 2px; /* Espaciado entre letras estilo portfolio */
    }
    
    p, li, div {
        font-weight: 300;
        letter-spacing: 0.5px;
        line-height: 1.6;
    }

    /* BOTONES PRINCIPALES (Estilo minimalista F90) */
    .stButton > button {
        background-color: transparent;
        color: #ffffff;
        border: 1px solid #ffffff;
        border-radius: 0px; /* Botones cuadrados estilo Squarespace */
        padding: 0.8rem 2rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s ease;
        width: 100%;
        font-size: 0.9rem;
    }
    .stButton > button:hover {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #ffffff;
    }
    .stButton > button:active {
        color: #000000;
        background-color: #cccccc;
    }
    
    /* LINK BUTTON (Para la suscripción) */
    a[href*="lemonsqueezy"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ffffff;
        display: block;
        text-align: center;
        padding: 15px;
        border-radius: 0px; /* Cuadrado */
        text-decoration: none;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 10px;
    }
    a[href*="lemonsqueezy"]:hover {
        opacity: 0.9;
    }

    /* TARJETA DE PRECIO MINIMALISTA */
    .price-card {
        background-color: #1a1a1a;
        border: 1px solid #333;
        padding: 50px 30px;
        text-align: center;
        transition: transform 0.3s ease;
    }
    .price-card:hover {
        border-color: #555;
    }
    .price-amount {
        font-size: 3.5rem;
        font-weight: 200;
        color: #ffffff;
        margin: 20px 0;
    }
    
    /* INPUTS DE TEXTO (Formularios limpios) */
    .stTextInput > div > div > input {
        background-color: #1a1a1a;
        color: white;
        border: 1px solid #333;
        border-radius: 0px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #fff;
        box-shadow: none;
    }

    /* OCULTAR ELEMENTOS NATIVOS DE STREAMLIT */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE CLAVES (SECRETOS) ---
LS_API_KEY = os.environ.get("LS_API_KEY") or st.secrets.get("LS_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# --- FUNCIONES DE LÓGICA ---

def validate_lemon_license(license_key: str) -> bool:
    if not LS_API_KEY:
        return False
        
    url = "https://api.lemonsqueezy.com/v1/licenses/validate"
    headers = {
        "Accept": "application/vnd.api+json",
        "Authorization": f"Bearer {LS_API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"license_key": license_key}

    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status() 
        result = response.json()
        return result.get('valid', False)
    except:
        return False

def transcribir_con_corte(archivo_bytes):
    if not GOOGLE_API_KEY:
        raise ValueError("Falta API Key")
        
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('models/gemini-3-pro-preview')
    
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

    Devuelve JSON: { "texto_cortado": "..." }
    """
    
    config = genai.types.GenerationConfig(temperature=0.0, response_mime_type="application/json")
    response = model.generate_content([{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt], generation_config=config)
    return response.text

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- GESTIÓN DE ESTADO ---
if "page" not in st.session_state: st.session_state.page = "landing"
if "authenticated" not in st.session_state: st.session_state.authenticated = False

def navigate_to(page):
    st.session_state.page = page
    st.rerun()

# ==========================================
# 🏠 PÁGINA 1: LANDING PAGE (Estilo F90)
# ==========================================
def show_landing():
    # Logo o Título super minimalista
    st.markdown("<h4 style='text-align: left; color: #666; font-size: 0.8rem; letter-spacing: 3px;'>Productividad total</h4>", unsafe_allow_html=True)
    st.write("##") # Espacio

    # CABECERA GRANDE
    st.markdown("<h1 style='font-size: 4rem; font-weight: 200; text-align: left; line-height: 1.1;'>DIGITALIZACIÓN<br><span style='font-weight: 600;'>REGISTRAL</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: left; color: #aaa; font-size: 1.1rem; max-width: 600px; margin-top: 20px;'>Automatización inteligente para profesionales del registro. Transcripción literal y limpieza de datos con un solo clic.</p>", unsafe_allow_html=True)
    
    st.write("##")
    
    col_cta, col_vacia = st.columns([1, 2])
    with col_cta:
        if st.button("EMPEZAR AHORA", type="primary"):
            navigate_to("subscription")

    st.write("---")

    # SECCIÓN DE CARACTERÍSTICAS (Grid limpio)
    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("### 01. PRECISIÓN")
        st.markdown("<div style='color: #888; font-size: 0.9rem;'>Analiza el documento.</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 02. LIMPIEZA")
        st.markdown("<div style='color: #888; font-size: 0.9rem;'>Elimina timbres, saltos de línea erróneos y ruido visual. Entrega un texto plano listo para pegar.</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("### 03. PRIVACIDAD")
        st.markdown("<div style='color: #888; font-size: 0.9rem;'>Detecta automáticamente la cláusula RGPD y corta la transcripción antes de procesar datos sensibles.</div>", unsafe_allow_html=True)

    st.write("##")
    st.write("##")
    
    # FOOTER SUTIL
    st.markdown("<div style='text-align: center; color: #444; font-size: 0.7rem; letter-spacing: 2px; margin-top: 50px;'>Productividad Total © 2025 | ALMADÉN</div>", unsafe_allow_html=True)


# ==========================================
# 💳 PÁGINA 2: SUSCRIPCIÓN (Estilo Gallery)
# ==========================================
def show_subscription():
    st.markdown("<h4 style='text-align: left; color: #666; font-size: 0.8rem; letter-spacing: 3px;'>SUSCRIPCIÓN</h4>", unsafe_allow_html=True)
    
    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("← ATRÁS"): navigate_to("landing")
    
    st.write("##")
    
    # Centramos la tarjeta de precio
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        # Tarjeta de precio estilo Squarespace
        st.markdown("""
        <div class="price-card">
            <h3 style="color: #fff; font-size: 1rem; letter-spacing: 3px;">PROFESSIONAL LICENSE</h3>
            <div class="price-amount">XXXX €</div>
            <p style="color: #666; font-size: 0.8rem;">FACTURACIÓN MENSUAL</p>
            <hr style="border-color: #333; margin: 30px 0;">
            <div style="text-align: left; color: #ccc; font-size: 0.9rem; line-height: 2;">
                Acceso completo al motor IA<br>
                Soporte técnico prioritario<br>
                Actualizaciones incluidas
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enlace de Lemon Squeezy (REEMPLAZAR LINK)
        st.markdown('<a href="https://tu-tienda.lemonsqueezy.com/checkout" target="_blank">COMPRAR LICENCIA</a>', unsafe_allow_html=True)

    st.write("##")
    st.markdown("---")
    
    c_log1, c_log2, c_log3 = st.columns([1, 1, 1])
    with c_log2:
        st.markdown("<h3 style='font-size: 1rem;'>ÁREA DE CLIENTE</h3>", unsafe_allow_html=True)
        password = st.text_input("INTRODUCE TU CLAVE", type="password", label_visibility="collapsed", placeholder="Licencia...")
        if st.button("ACCEDER"):
            if password == "F90-ADMIN": 
                st.session_state.authenticated = True
                navigate_to("app")
            elif validate_lemon_license(password):
                st.session_state.authenticated = True
                navigate_to("app")
            else:
                st.error("LICENCIA INVÁLIDA")

# ==========================================
# ⚙️ PÁGINA 3: WORKSPACE (Aplicación)
# ==========================================
def show_app():
    # Header minimalista
    c_head1, c_head2 = st.columns([6, 1])
    with c_head1:
        st.markdown("<h4 style='margin:0; padding-top: 10px; letter-spacing: 2px;'>F90 WORKSPACE</h4>", unsafe_allow_html=True)
    with c_head2:
        if st.button("SALIR"):
            st.session_state.authenticated = False
            navigate_to("landing")
            
    st.markdown("---")

    if not GOOGLE_API_KEY:
        st.warning("⚠️ MODO DEMO: Falta API Key de Google")
    
    # Layout de trabajo: Izquierda (Subida) | Derecha (Resultado)
    col_izq, col_der = st.columns([1, 1], gap="large")
    
    with col_izq:
        st.markdown("### 1. DOCUMENTO")
        uploaded_file = st.file_uploader("Selecciona PDF", type=['pdf'], label_visibility="collapsed")
        
        if uploaded_file:
            st.success(f"Archivo cargado: {uploaded_file.name}")
            st.write("##")
            if st.button("INICIAR PROCESADO", type="primary"):
                st.session_state.procesando = True
                # Simulamos o procesamos
                if GOOGLE_API_KEY:
                    with st.spinner("Analizando estructura legal..."):
                        try:
                            bytes_data = uploaded_file.read()
                            resultado = transcribir_con_corte(bytes_data)
                            datos = json.loads(limpiar_json(resultado))
                            st.session_state.texto_resultado = datos.get("texto_cortado", "")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    # Simulación si no hay key
                    time.sleep(2)
                    st.session_state.texto_resultado = "EJEMPLO DE TEXTO TRANSCRITO...\n\n(Aquí aparecería el texto real si hubiera API Key)"

    with col_der:
        st.markdown("### 2. RESULTADO")
        if "texto_resultado" in st.session_state:
            st.text_area("Texto final", value=st.session_state.texto_resultado, height=500, label_visibility="collapsed")
            st.download_button("DESCARGAR .TXT", st.session_state.texto_resultado, "transcripcion.txt")
        else:
            st.markdown("""
            <div style='border: 1px dashed #444; height: 500px; display: flex; align-items: center; justify-content: center; color: #666;'>
                Esperando documento...
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# 🚦 ROUTER
# ==========================================
if st.session_state.authenticated:
    show_app()
else:
    if st.session_state.page == "landing":
        show_landing()
    elif st.session_state.page == "subscription":
        show_subscription()
