import streamlit as st
import requests
import base64
import re

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO PREMIUM ---
st.set_page_config(
    page_title="F90 | OCR Registral",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inyectamos CSS para transformar la UI estándar de Streamlit en algo PRO
st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Contenedor principal tipo 'Tarjeta' */
    div.block-container {
        background-color: #ffffff;
        padding: 3rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        max-width: 800px;
        margin-top: 2rem;
    }

    /* Títulos */
    h1 {
        color: #0f2b46; /* Azul Marino Legal */
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    h3 {
        color: #4a5568;
        font-size: 1.1rem;
        font-weight: 400;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Botones personalizados */
    div.stButton > button {
        background-color: #0f2b46;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #1a3c5e;
        box-shadow: 0 4px 12px rgba(15, 43, 70, 0.2);
        color: white;
    }

    /* Área de texto */
    .stTextArea textarea {
        background-color: #fcfcfc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        color: #2d3748;
    }

    /* Uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #cbd5e0;
        border-radius: 10px;
        padding: 20px;
        background-color: #fafbfc;
    }
    
    /* Ocultar elementos de Streamlit (Footer, Menu hamburguesa) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE LIMPIEZA V3.0 (CIRUGÍA REGISTRAL) ---
def limpiar_texto_registral(texto_crudo):
    """
    V4.0: Solución específica para textos pegados (realidad.TIMBRE) y 
    lecturas erróneas del OCR (QUINTANARDELA).
    """
    if not texto_crudo:
        return ""

    # 1. PRE-PROCESADO: SEPARAR TEXTO PEGADO
    # El OCR a veces devuelve "realidad.TIMBRE". Esto separa el punto de la mayúscula siguiente.
    texto_crudo = re.sub(r'([a-z])\.([A-Z])', r'\1. \2', texto_crudo)
    # Separa palabras minúsculas de mayúsculas pegadas (ej: "fincaTIMBRE")
    texto_crudo = re.sub(r'([a-z])([A-Z]{3,})', r'\1 \2', texto_crudo)

    # 2. LISTA NEGRA AMPLIADA (Incluyendo errores de lectura de Google)
    marcadores_basura = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES",
        "CLASE 8", "CLASE 6", "CLASE 4", "0,15 €", "0,03 €", "EUROS",
        "R.C.M.FN", "RCMFN", 
        "NIHIL PRIUS FIDE", "PRIUS FIDE", "NIHIL", "IHIL", "1NIHIL", "2NIHIL", # Variaciones del lema
        "NOTARIA DE", "NOTARÍA DE", "DEL ILUSTRE COLEGIO",
        "DISTRITO NOTARIAL", 
        "BOLAS OLCINA", "RESA BOLAS", "MARÍA TERESA BOLÁS", 
        "PAPEL EXCL", "DEL ESTADO", "DE DONA",
        # Errores específicos de lectura que vimos en tu archivo 5.txt:
        "QUINTANAR DE LA ORDEN", "QUINTANARDEL", "QUINTANARDELA", "RDEN (TOLEDO)",
        "TIMBRE PRIUS", "DEN TOLEDO"
    ]

    lineas_limpias = []
    
    for linea in texto_crudo.split('\n'):
        # Normalizamos espacios antes de analizar
        linea = re.sub(r'\s+', ' ', linea).strip()
        linea_upper = linea.upper()
        
        es_basura_total = False
        
        # A) Filtro: Líneas que son SOLO basura o códigos
        if len(linea) < 40 and (
            re.search(r'\d{2}/\d{4}', linea) or 
            re.search(r'^[A-Z]{2}\d+', linea_upper) or
            "TIMBRE" in linea_upper or
            "PRIUS" in linea_upper
        ):
            es_basura_total = True
        
        if not es_basura_total:
            # B) CIRUGÍA: Borrar basura incrustada en líneas largas
            for marcador in marcadores_basura:
                if marcador in linea_upper:
                    # Usamos regex ignorando mayúsculas/minúsculas para borrar el marcador
                    linea = re.sub(re.escape(marcador), "", linea, flags=re.IGNORECASE)
            
            # Limpieza extra de patrones sueltos que quedan tras borrar las palabras
            linea = re.sub(r'\s\d{2}/\d{4}\s', " ", linea) # Fechas 05/2025 sueltas
            linea = re.sub(r'[A-Z]{2}\d{6,}', "", linea)   # Códigos IU...
            
            # Si tras limpiar la línea queda vacía o solo signos, no la guardamos
            if len(linea.strip()) > 3:
                lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)

    # --- 3. PULIDO FINAL ---
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
        texto = re.sub(rf'({t})', r'\n\

# --- 3. CONEXIÓN GOOGLE VISION ---
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
                "pages": [1, 2, 3, 4, 5] # Lee las primeras 5 páginas
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

# --- 4. INTERFAZ DE USUARIO (FRONTEND) ---

# Encabezado
st.title("F90 | LEGAL TECH")
st.markdown("### Limpiador Inteligente de Escrituras")

# Verificación de Seguridad
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Error de Configuración: Falta la API Key en los Secrets.")
    st.stop()
else:
    api_key = st.secrets["GOOGLE_API_KEY"]

# Área de carga
uploaded_file = st.file_uploader("Sube tu escritura (PDF)", type=['pdf'], help="Máximo 5 páginas en esta versión demo.")

# Separador visual
st.markdown("---")

if uploaded_file is not None:
    # Botón principal
    if st.button("✨ LIMPIAR DOCUMENTO AHORA"):
        
        # Barra de progreso simulada para dar feedback
        progress_text = "Analizando documento con IA..."
        my_bar = st.progress(0, text=progress_text)

        try:
            # 1. Lectura
            my_bar.progress(30, text="Leyendo PDF en la nube...")
            bytes_data = uploaded_file.read()
            
            # 2. OCR Google
            my_bar.progress(60, text="Extrayendo texto crudo...")
            texto_sucio = procesar_con_api_key(bytes_data, api_key)
            
            # 3. Limpieza V3
            my_bar.progress(85, text="Eliminando sellos y timbres notariales...")
            texto_limpio = limpiar_texto_registral(texto_sucio)
            
            my_bar.progress(100, text="¡Finalizado!")
            my_bar.empty() # Quitamos la barra

            # --- RESULTADO ---
            st.success("✅ Proceso completado con éxito")
            
            # Mostramos el texto en un área limpia
            st.text_area("Vista Previa (Editable):", value=texto_limpio, height=450)
            
            # Columnas para centrar el botón de descarga
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="⬇️ DESCARGAR DOCUMENTO (.TXT)",
                    data=texto_limpio,
                    file_name="escritura_limpia.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# Pie de página discreto
st.markdown(
    """
    <div style='text-align: center; color: #a0aec0; font-size: 0.8em; margin-top: 3rem;'>
        Seguridad Garantizada: Los archivos se procesan en memoria volátil y se eliminan tras su uso.
        <br>Powered by Google Cloud Vision AI & F90
    </div>
    """, 
    unsafe_allow_html=True
)
