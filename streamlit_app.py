import streamlit as st
import google.generativeai as genai
import json
import os
import requests
import time

# --- CONFIGURACIÓN DE PÁGINA (DISEÑO) ---
st.set_page_config(
    page_title="F90 | Digitalizador",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS "LOOK F90 FOTO" (Minimalista Dark) ---
st.markdown("""
<style>
    /* Importamos fuente elegante (Montserrat) */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap');

    /* FONDO GENERAL Y TEXTOS */
    .stApp {
        background-color: #0e1117; /* Gris muy oscuro (Estilo Capture One) */
        color: #e0e0e0;
        font-family: 'Montserrat', sans-serif;
    }
    
    h1, h2, h3, h4, h5 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        color: #ffffff !important;
        text-align: center;
        letter-spacing: -0.5px;
    }

    /* BOTONES PRINCIPALES (Estilo minimalista blanco/negro) */
    .stButton > button {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #ffffff;
        border-radius: 4px; /* Bordes menos redondeados, más pro */
        padding: 0.6rem 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #000000;
        color: #ffffff;
        border: 1px solid #ffffff;
        box-shadow: 0 0 10px rgba(255,255,255,0.2);
    }
    
    /* LINK BUTTON (Para la suscripción) */
    a[href*="lemonsqueezy"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ffffff;
        display: block;
        text-align: center;
        padding: 12px;
        border-radius: 4px;
        text-decoration: none;
        font-weight: bold;
        text-transform: uppercase;
        margin-top: 10px;
    }

    /* CAJAS DE INFORMACIÓN (Success/Info/Error) */
    .stAlert {
        background-color: #1c1f26;
        color: #e0e0e0;
        border: 1px solid #333;
    }
    
    /* TARJETA DE PRECIO */
    .price-card {
        background-color: #161920;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .price-amount {
        font-size: 3rem;
        font-weight: 300;
        color: #ffffff;
    }
    
    /* OCULTAR ELEMENTOS DE STREAMLIT */
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
        # Modo silencioso para no romper la estética si falta la key
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
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    
    prompt = """
    Actúa como un Oficial de Registro. Tu misión es TRANSCRIBIR la escritura, pero SOLO LA PARTE DISPOSITIVA.
    INSTRUCCIONES DE CORTE:
    1. Transcribe desde el principio.
    2. DETENTE antes de "PROTECCIÓN DE DATOS" (o "DATOS PERSONALES").
    3. NO incluyas esa cláusula ni lo posterior.
    INSTRUCCIONES DE LIMPIEZA:
    - Literal palabra por palabra.
    - Elimina sellos/timbres.
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
# 🏠 PÁGINA 1: LANDING PAGE (Minimalista)
# ==========================================
def show_landing():
    st.write("##")
    # Título super limpio
    st.markdown("<h1 style='font-size: 3rem; font-weight: 300; letter-spacing: 2px;'>DIGITALIZADOR <span style='font-weight: 600;'>REGISTRAL</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; font-size: 1.2rem; letter-spacing: 1px;'>PRECISIÓN JURÍDICA. VELOCIDAD DIGITAL.</p>", unsafe_allow_html=True)
    st.write("---")

    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        st.write("##")
        st.markdown("### LA IMAGEN COMPLETA")
        st.markdown("""
        <div style="color: #ccc; font-weight: 300; line-height: 1.8;">
        Al igual que en fotografía, los detalles importan. He diseñado esta herramienta para eliminar el ruido (timbres, sellos, datos protegidos) y dejar solo lo esencial: <strong>la inscripción pura.</strong>
        <br><br>
        <ul>
            <li>Originalidad inalterada (Transcripción literal)</li>
            <li>Encuadre perfecto (Corte automático RGPD)</li>
            <li>Flujo de trabajo acelerado</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.write("##")
        st.info("💡 **WORKFLOW OPTIMIZADO**")
        st.markdown("""
        1. **IMPORTAR:** Arrastra tu PDF.
        2. **PROCESAR:** La IA revela el texto jurídico.
        3. **EXPORTAR:** Copia el resultado limpio.
        """)
        
        st.write("##")
        if st.button("VER PLANES & ACCEDER", type="primary"):
            navigate_to("subscription")

    st.write("##")
    st.write("---")
    st.markdown("<p style='text-align: center; color: #555; font-size: 0.8rem;'>DESIGNED BY F90 | ALMADÉN, SPAIN</p>", unsafe_allow_html=True)

# ==========================================
# 💳 PÁGINA 2: SUSCRIPCIÓN (Estilo Etiqueta)
# ==========================================
def show_subscription():
    st.write("##")
    st.title("PLAN PROFESIONAL")
    if st.button("← VOLVER"): navigate_to("landing")
    
    st.write("##")
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        # Tarjeta de precio personalizada con HTML
        st.markdown("""
        <div class="price-card">
            <h3 style="color: #888; text-transform: uppercase; letter-spacing: 2px;">Suscripción Mensual</h3>
            <div class="price-amount">19,90€</div>
            <p style="color: #666;">Sin permanencia. Cancelación inmediata.</p>
            <hr style="border-color: #333;">
            <ul style="text-align: left; color: #ccc; list-style: none; padding: 0;">
                <li style="margin-bottom: 10px;">✓ Transcripciones Ilimitadas</li>
                <li style="margin-bottom: 10px;">✓ Corte Inteligente RGPD</li>
                <li style="margin-bottom: 10px;">✓ Soporte Directo F90</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("##")
        # Enlace de Lemon Squeezy (REEMPLAZAR LINK)
        st.markdown('<a href="https://tu-tienda.lemonsqueezy.com/checkout" target="_blank">SUSCRIBIRSE AHORA</a>', unsafe_allow_html=True)

    st.write("---")
    st.markdown("### LOGIN DE USUARIO")
    
    c_log1, c_log2, c_log3 = st.columns([1, 2, 1])
    with c_log2:
        password = st.text_input("CLAVE DE LICENCIA", type="password")
        if st.button("INICIAR SESIÓN"):
            if password == "F90-ADMIN": 
                st.session_state.authenticated = True
                navigate_to("app")
            elif validate_lemon_license(password):
                st.session_state.authenticated = True
                navigate_to("app")
            else:
                st.error("LICENCIA NO VÁLIDA")

# ==========================================
# ⚙️ PÁGINA 3: WORKSPACE (Aplicación)
# ==========================================
def show_app():
    # Barra superior minimalista
    col_brand, col_out = st.columns([6, 1])
    with col_brand:
        st.markdown("<h3 style='text-align: left; margin: 0;'>F90 | WORKSPACE</h3>", unsafe_allow_html=True)
    with col_out:
        if st.button("LOGOUT"):
            st.session_state.authenticated = False
            navigate_to("landing")
    
    st.write("---")

    if not GOOGLE_API_KEY:
        st.error("⚠️ SISTEMA NO CONFIGURADO (Falta API Key)")
        st.stop()

    # Área de subida limpia
    uploaded_file = st.file_uploader("ARRASTRA TU ESCRITURA (PDF)", type=['pdf'])
    
    if uploaded_file:
        st.write("##")
        col_act, _ = st.columns([1, 3])
        with col_act:
            if st.button("REVELAR TEXTO (PROCESAR)"):
                with st.spinner("Procesando documento..."):
                    try:
                        bytes_data = uploaded_file.read()
                        resultado = transcribir_con_corte(bytes_data)
                        datos = json.loads(limpiar_json(resultado))
                        texto_final = datos.get("texto_cortado", "")
                        
                        st.success("PROCESO COMPLETADO")
                        st.text_area("TEXTO FINAL", value=texto_final, height=600)
                        st.download_button("DESCARGAR .TXT", texto_final, "escritura_f90.txt")
                    except Exception as e:
                        st.error(f"Error en el procesado: {e}")

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
