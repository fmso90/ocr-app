import streamlit as st
import requests
import base64
import re

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="OCR Registral Pro",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Dark Mode (Estilo Premium)
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    div.block-container {
        background-color: #121212;
        padding: 3rem;
        border-radius: 15px;
        border: 1px solid #333;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        max-width: 800px;
    }
    h1 { color: #fff !important; font-family: 'Helvetica Neue', sans-serif; }
    h3 { color: #a0a0a0 !important; font-weight: 400; }
    div.stButton > button {
        background-color: #fff; color: #000; border: none; font-weight: 700;
        transition: all 0.3s;
    }
    div.stButton > button:hover { background-color: #ccc; box-shadow: 0 0 10px rgba(255,255,255,0.2); }
    .stTextArea textarea {
        background-color: #0a0a0a; border: 1px solid #333;
        font-family: 'Courier New', monospace; color: #d1d5db;
    }
    [data-testid="stFileUploader"] { background-color: #1a1a1a; border: 1px dashed #555; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE LIMPIEZA V9.0 (GENÉRICA Y UNIVERSAL) ---
def limpiar_texto_registral(texto_crudo):
    if not texto_crudo:
        return ""

    # A) PRE-PROCESADO: Despegar palabras pegadas (OCR Error)
    # realidad.TIMBRE -> realidad. TIMBRE
    texto_crudo = re.sub(r'(\.)([A-Z])', r'\1 \2', texto_crudo)
    # fincaTIMBRE -> finca TIMBRE
    texto_crudo = re.sub(r'([a-z])([A-Z]{3,})', r'\1 \2', texto_crudo)

    # B) DEFINICIÓN DE LISTAS GENÉRICAS (Sin nombres propios)
    
    # 1. INMUNIDAD: Protegemos el encabezado legítimo donde se nombra al notario
    frases_sagradas = [
        "ANTE MÍ", "ANTE MI", 
        "EN LA VILLA DE", "EN LA CIUDAD DE", "EN EL MUNICIPO DE",
        "COMPARECEN", "INTERVIENEN", "OTORGAN"
    ]

    # 2. LISTA NEGRA UNIVERSAL (Solo elementos fijos de papelería notarial)
    marcadores_basura = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES",
        "CLASE 8", "CLASE 6", "CLASE 4", 
        "0,15 €", "0,15€", "0,03 €", "0,03€", "EUROS", # Precios del timbre
        "R.C.M.FN", "RCMFN", # Casa de la Moneda
        "NIHIL PRIUS FIDE", "PRIUS FIDE", "NIHIL", "IHIL", "1NIHIL", # Lema latín
        "NOTARIA DE", "NOTARÍA DE", # Texto del anillo del sello
        "DEL ILUSTRE COLEGIO", "COLEGIO NOTARIAL",
        "DISTRITO DE", "DISTRITO NOTARIAL"
    ]

    lineas_limpias = []
    
    for linea in texto_crudo.split('\n'):
        linea_strip = linea.strip()
        linea_upper = linea.upper()
        
        # --- FILTRO 1: INMUNIDAD ---
        es_linea_sagrada = False
        # Si la línea es corta (menos de 120 caracteres) y empieza por "EN ..." o tiene "ANTE MI"
        # La protegemos para no borrar el nombre del notario real del texto.
        if len(linea_strip) < 120: 
            if re.search(r'\bEN\s+[A-ZÁÉÍÓÚÑ\s]+,', linea_upper) or "ANTE MÍ" in linea_upper or "ANTE MI" in linea_upper:
                es_linea_sagrada = True
        
        if es_linea_sagrada:
            # Solo limpiamos el código de papel si aparece al final
            linea = re.sub(r'[A-Z]{2}\d{6,}.*', '', linea) 
            lineas_limpias.append(linea)
            continue 

        # --- FILTRO 2: LIMPIEZA QUIRÚRGICA ---
        linea_procesada = linea
        
        # 1. Borrar frases exactas de basura
        for marcador in marcadores_basura:
            linea_procesada = re.sub(re.escape(marcador), "", linea_procesada, flags=re.IGNORECASE)
        
        # 2. BORRADO DE CÓDIGOS UNIVERSALES (REGEX)
        # Borra códigos tipo IU1953411, IM5241499, AB123456 (2 letras + 6-12 dígitos)
        linea_procesada = re.sub(r'\s[A-Z]{2}\s*\d{6,}', "", linea_procesada)
        # Borra códigos si están pegados al principio o final
        linea_procesada = re.sub(r'\b[A-Z]{2}\d{6,}\b', "", linea_procesada)
        
        # 3. Borrar Fechas sueltas de cabecera (MM/YYYY)
        linea_procesada = re.sub(r'\s\d{2}/\d{4}', "", linea_procesada)    

        # --- FILTRO 3: VALIDACIÓN FINAL ---
        # Si tras borrar la basura, la línea queda vacía o con 1-2 letras, la descartamos.
        # Esto elimina líneas que solo contenían el nombre del notario del sello (ej: "D. PEDRO")
        if len(linea_procesada.strip()) > 3:
            # Limpiar espacios dobles
            linea_procesada = re.sub(r'\s+', ' ', linea_procesada).strip()
            lineas_limpias.append(linea_procesada)

    texto = "\n".join(lineas_limpias)

    # C) PULIDO Y UNIÓN (REPARACIÓN DE DNI Y PÁRRAFOS)
    
    texto = re.sub(r'-\s+', '', texto) 
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto) # Unir líneas simples
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\s+([,.:;)])', r'\1', texto)
    texto = re.sub(r'(\()\s+', r'\1', texto)
    texto = re.sub(r'\s+\/\s+', '/', texto)
    
    # Reparación de DNI (Une D. N. I. y N. I. F.)
    texto = re.sub(r'D\.\s*N\.\s*I\.', 'D.N.I.', texto, flags=re.IGNORECASE)
    texto = re.sub(r'N\.\s*I\.\s*F\.', 'N.I.F.', texto, flags=re.IGNORECASE)
    # Patrón general de siglas: L. L. L. -> L.L.L.
    texto = re.sub(r'([A-Z])\.\s+([A-Z])\.', r'\1.\2.', texto)

    # Reconstrucción de Párrafos (Evitando romper D.N.I.)
    # Salto de línea solo si hay punto y NO hay mayúscula delante
    texto = re.sub(r'(?<![A-Z])\.\s+([A-ZÁÉÍÓÚÑ])', r'.\n\n\1', texto)
    
    # Estética: Don/Doña
    texto = re.sub(r'\bD\.\n\n', 'D. ', texto)

    # Resaltado de Cabeceras
    titulos = ["ESCRITURA", "COMPARECEN", "INTERVIENEN", "EXPONEN", "OTORGAN", "ESTIPULACIONES"]
    for t in titulos:
        texto = re.sub(rf'({t})', r'\n\n\1', texto)

    return texto.strip()

# --- 3. CONEXIÓN GOOGLE VISION ---
def procesar_con_api_key(content_bytes, api_key):
    try:
        b64_content = base64.b64encode(content_bytes).decode('utf-8')
        url = f"https://vision.googleapis.com/v1/files:annotate?key={api_key}"
        
        payload = {
            "requests": [{
                "inputConfig": { "content": b64_content, "mimeType": "application/pdf" },
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "pages": [1, 2, 3, 4, 5] 
            }]
        }

        response = requests.post(url, json=payload)
        if response.status_code != 200: return f"Error Google: {response.text}"
        
        data = response.json()
        texto_total = ""
        responses = data.get('responses', [])
        if responses:
            for pagina in responses[0].get('responses', []):
                full_text = pagina.get('fullTextAnnotation', {}).get('text', '')
                if full_text: texto_total += full_text + "\n"
        
        return texto_total if texto_total else "⚠️ No se detectó texto."

    except Exception as e: return f"Error: {e}"

# --- 4. INTERFAZ ---
st.title("OCR REGISTRAL")
st.markdown("### Procesamiento Seguro de Escrituras")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("PROCESAR DOCUMENTO"):
        bar = st.progress(0, "Iniciando...")
        try:
            bar.progress(30, "Leyendo...")
            raw = uploaded_file.read()
            bar.progress(60, "OCR Google...")
            sucio = procesar_con_api_key(raw, st.secrets["GOOGLE_API_KEY"])
            bar.progress(80, "Limpieza Universal...")
            limpio = limpiar_texto_registral(sucio)
            bar.progress(100, "Listo")
            bar.empty()
            
            st.success("✅ Procesado correctamente")
            st.text_area("Resultado:", value=limpio, height=600)
            st.download_button("⬇️ DESCARGAR TXT", limpio, "escritura.txt")
        except Exception as e:
            st.error(f"Error: {e}")
