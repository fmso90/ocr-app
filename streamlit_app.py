import streamlit as st
import requests
import base64
import re

# --- 1. CONFIGURACIÓN DE PÁGINA Y MODO OSCURO ---
st.set_page_config(
    page_title="Herramienta OCR Registral", # Título genérico
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inyectamos CSS para el Diseño "Dark Premium"
st.markdown("""
<style>
    /* Fondo General Negro */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Contenedor principal (Tarjeta oscura) */
    div.block-container {
        background-color: #121212; /* Gris casi negro */
        padding: 3rem;
        border-radius: 15px;
        border: 1px solid #333333;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        max-width: 800px;
        margin-top: 2rem;
    }

    /* Títulos y Textos */
    h1 {
        color: #ffffff !important;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    h3 {
        color: #a0a0a0 !important;
        font-size: 1.1rem;
        font-weight: 400;
        text-align: center;
        margin-bottom: 2rem;
    }
    p, label, div {
        color: #e0e0e0;
    }

    /* Botones (Blanco/Gris para contraste elegante en fondo negro) */
    div.stButton > button {
        background-color: #ffffff;
        color: #000000;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 700;
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #cccccc;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
        color: #000000;
    }

    /* Área de texto (Look Terminal moderno) */
    .stTextArea textarea {
        background-color: #0a0a0a;
        border: 1px solid #333333;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        color: #00ff41; /* Verde terminal suave o blanco? Ponemos gris claro para seriedad */
        color: #d1d5db;
    }

    /* Uploader (Zona de carga) */
    [data-testid="stFileUploader"] {
        border: 1px dashed #555;
        border-radius: 10px;
        padding: 20px;
        background-color: #1a1a1a;
    }
    
    /* Mensajes de éxito/error */
    .stSuccess {
        background-color: #064e3b;
        color: #a7f3d0;
    }
    
    /* Ocultar elementos de marca de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE LIMPIEZA V4.0 (SEPARADOR MOLECULAR) ---
def limpiar_texto_registral(texto_crudo):
    if not texto_crudo:
        return ""

    # A) PRE-PROCESADO: Despegar palabras que el OCR une por error
    # Ejemplo: "realidad.TIMBRE" -> "realidad. TIMBRE"
    texto_crudo = re.sub(r'([a-z])\.([A-Z])', r'\1. \2', texto_crudo)
    # Ejemplo: "fincaTIMBRE" -> "finca TIMBRE"
    texto_crudo = re.sub(r'([a-z])([A-Z]{3,})', r'\1 \2', texto_crudo)

    # B) LISTA NEGRA AMPLIADA
    marcadores_basura = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES",
        "CLASE 8", "CLASE 6", "CLASE 4", "0,15 €", "0,03 €", "EUROS",
        "R.C.M.FN", "RCMFN", 
        "NIHIL PRIUS FIDE", "PRIUS FIDE", "NIHIL", "IHIL", "1NIHIL", "2NIHIL",
        "NOTARIA DE", "NOTARÍA DE", "DEL ILUSTRE COLEGIO",
        "DISTRITO NOTARIAL", 
        "BOLAS OLCINA", "RESA BOLAS", "MARÍA TERESA BOLÁS", 
        "PAPEL EXCL", "DEL ESTADO", "DE DONA",
        "QUINTANAR DE LA ORDEN", "QUINTANARDEL", "QUINTANARDELA", "RDEN (TOLEDO)",
        "TIMBRE PRIUS", "DEN TOLEDO"
    ]

    lineas_limpias = []
    
    for linea in texto_crudo.split('\n'):
        # Normalizamos espacios
        linea = re.sub(r'\s+', ' ', linea).strip()
        linea_upper = linea.upper()
        
        es_basura_total = False
        
        # Filtro 1: Líneas que son puramente basura técnica
        if len(linea) < 40 and (
            re.search(r'\d{2}/\d{4}', linea) or 
            re.search(r'^[A-Z]{2}\d+', linea_upper) or
            "TIMBRE" in linea_upper or
            "PRIUS" in linea_upper
        ):
            es_basura_total = True
        
        if not es_basura_total:
            # Filtro 2: Borrado quirúrgico dentro de líneas de texto
            for marcador in marcadores_basura:
                if marcador in linea_upper:
                    linea = re.sub(re.escape(marcador), "", linea, flags=re.IGNORECASE)
            
            # Limpieza residual (fechas sueltas o códigos que quedaron tras borrar palabras)
            linea = re.sub(r'\s\d{2}/\d{4}\s', " ", linea) 
            linea = re.sub(r'[A-Z]{2}\d{6,}', "", linea)   
            
            # Solo guardamos si queda texto útil
            if len(linea.strip()) > 3:
                lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)

    # --- 3. PULIDO FINAL DE TEXTO ---
    texto = re.sub(r'-\s+', '', texto) 
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto) 
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\s+([,.:;)])', r'\1', texto)
    texto = re.sub(r'(\()\s+', r'\1', texto)
    texto = re.sub(r'\s+\/\s+', '/', texto)
    
    # Reconstrucción de párrafos
    texto = re.sub(r'(\.)\s+([A-ZÁÉÍÓÚÑ])', r'\1\n\n\2', texto)

    # Resaltado de Cabeceras
    titulos = ["ESCRITURA", "COMPARECEN", "INTERVIENEN", "EXPONEN", "OTORGAN", "ESTIPULACIONES"]
    for t in titulos:
        texto = re.sub(rf'({t})', r'\n\n\1', texto)

    return texto.strip()

# --- 4. CONEXIÓN GOOGLE VISION ---
def procesar_con_api_key(content_bytes, api_key):
    try:
        b64_content = base64.b64encode(content_bytes).decode('utf-8')
        url = f"https://vision.googleapis.com/v1/files:annotate?key={api_key}"
        
        payload = {
            "requests": [{
                "inputConfig": {
                    "content": b64_content,
                    "mimeType": "application/pdf"
                },
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "pages": [1, 2, 3, 4, 5] 
            }]
        }

        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            return f"Error Google Cloud: {response.text}"
            
        data = response.json()
        
        texto_total = ""
        responses = data.get('responses', [])
        if responses:
            file_response = responses[0]
            paginas = file_response.get('responses', [])
            for pagina in paginas:
                full_text = pagina.get('fullTextAnnotation', {}).get('text', '')
                if full_text:
                    texto_total += full_text + "\n"
        
        if not texto_total:
            return "⚠️ No se detectó texto. El PDF podría ser una imagen de baja calidad."
            
        return texto_total

    except Exception as e:
        return f"Error de conexión: {e}"

# --- 5. INTERFAZ DE USUARIO (FRONTEND) ---

# Encabezado (Sin F90)
st.title("OCR REGISTRAL")
st.markdown("### Limpiador Inteligente de Escrituras")

# Verificación de Seguridad
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Error: Falta la API Key en los Secrets.")
    st.stop()
else:
    api_key = st.secrets["GOOGLE_API_KEY"]

# Área de carga
uploaded_file = st.file_uploader("Sube tu escritura (PDF)", type=['pdf'])

# Separador visual oscuro
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file is not None:
    # Botón principal
    if st.button("PROCESAR DOCUMENTO"):
        
        progress_text = "Analizando documento con IA..."
        my_bar = st.progress(0, text=progress_text)

        try:
            # 1. Lectura
            my_bar.progress(30, text="Leyendo PDF en la nube...")
            bytes_data = uploaded_file.read()
            
            # 2. OCR Google
            my_bar.progress(60, text="Extrayendo texto crudo...")
            texto_sucio = procesar_con_api_key(bytes_data, api_key)
            
            # 3. Limpieza V4
            my_bar.progress(85, text="Aplicando limpieza quirúrgica...")
            texto_limpio = limpiar_texto_registral(texto_sucio)
            
            my_bar.progress(100, text="¡Finalizado!")
            my_bar.empty() 

            # --- RESULTADO ---
            st.success("✅ Proceso completado")
            
            st.text_area("Texto Resultante:", value=texto_limpio, height=500)
            
            # Columnas para centrar el botón de descarga
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="⬇️ DESCARGAR (.TXT)",
                    data=texto_limpio,
                    file_name="escritura_limpia.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# Pie de página simple y limpio
st.markdown(
    """
    <div style='text-align: center; color: #555; font-size: 0.8em; margin-top: 3rem;'>
        Privacidad: No se almacenan copias de los documentos.
    </div>
    """, 
    unsafe_allow_html=True
)
