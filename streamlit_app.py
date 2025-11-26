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

# CSS Dark Mode
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

# --- 2. LÓGICA DE LIMPIEZA V10.0 (GOLD MASTER) ---
def limpiar_texto_registral(texto_crudo):
    if not texto_crudo:
        return ""

    # A) PRE-PROCESADO: Despegar palabras
    texto_crudo = re.sub(r'(\.)([A-Z])', r'\1 \2', texto_crudo)
    texto_crudo = re.sub(r'([a-z])([A-Z]{3,})', r'\1 \2', texto_crudo)

    # B) DEFINICIÓN DE LISTAS
    frases_sagradas = [
        "ANTE MÍ", "ANTE MI", 
        "EN LA VILLA DE", "EN LA CIUDAD DE", "EN QUINTANAR", "EN MADRID", "EN TOLEDO"
    ]

    marcadores_basura = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES",
        "CLASE 8", "CLASE 6", "CLASE 4", "0,15 €", "0,03 €", "EUROS",
        "R.C.M.FN", "RCMFN", 
        "NIHIL PRIUS FIDE", "PRIUS FIDE", "NIHIL", "IHIL", "1NIHIL", 
        "IU1953", "TU1953",
        "OLCINA NOTARIA", "OLCINA LA ORDEN", 
        "RESA BOLAS", "QUINTANARDEL", "QUINTANARDELA", "RDEN (TOLEDO)", "DEN TOLEDO",
        "DE DONA M", "DE DONA", "DONA M", 
        "NOTARIA DE", "PARA DE DONA", "ESA BOLAS" # Nuevos fragmentos detectados
    ]

    lineas_limpias = []
    
    for linea in texto_crudo.split('\n'):
        linea_strip = linea.strip()
        linea_upper = linea.upper()
        
        # 1. Inmunidad
        es_linea_sagrada = False
        if len(linea_strip) < 100:
            if linea_upper.startswith("EN ") or "ANTE MÍ" in linea_upper:
                es_linea_sagrada = True
        
        if es_linea_sagrada:
            lineas_limpias.append(linea)
            continue 

        # 2. Limpieza Quirúrgica
        linea_procesada = linea
        for marcador in marcadores_basura:
            linea_procesada = re.sub(re.escape(marcador), "", linea_procesada, flags=re.IGNORECASE)
        
        # Limpieza de patrones sueltos
        linea_procesada = re.sub(r'\s[A-Z]{2}\d{6,}', "", linea_procesada)
        # Regex mejorado para fechas sueltas (05/2025)
        linea_procesada = re.sub(r'\b\d{2}/\d{4}\b', "", linea_procesada) 

        # 3. FILTRO EXTRA "FRANCOTIRADOR"
        # Si la línea contiene una secuencia larga de mayúsculas sin sentido (residuo de sello)
        # Ej: "PAPEL EXCL DONA M PRIUS"
        # Borramos palabras de 2-4 letras mayúsculas consecutivas que no sean DNI
        if len(linea_procesada) > 200: # Solo aplicamos en párrafos largos para no romper nombres
             linea_procesada = re.sub(r'\b(PRIUS|FIDE|DONA|RESA|BOLAS|OLCINA)\b', "", linea_procesada, flags=re.IGNORECASE)

        # 4. Guardar
        if len(linea_procesada.strip()) > 2:
            linea_procesada = re.sub(r'\s+', ' ', linea_procesada).strip()
            lineas_limpias.append(linea_procesada)

    texto = "\n".join(lineas_limpias)

    # C) PULIDO FINAL
    texto = re.sub(r'-\s+', '', texto) 
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto) 
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\s+([,.:;)])', r'\1', texto)
    texto = re.sub(r'(\()\s+', r'\1', texto)
    texto = re.sub(r'\s+\/\s+', '/', texto)
    
    # DNI FIX
    texto = re.sub(r'D\.\s*N\.\s*I\.', 'D.N.I.', texto, flags=re.IGNORECASE)
    texto = re.sub(r'N\.\s*I\.\s*F\.', 'N.I.F.', texto, flags=re.IGNORECASE)
    texto = re.sub(r'([A-Z])\.\s+([A-Z])\.', r'\1.\2.', texto)

    # Párrafos
    texto = re.sub(r'(?<![A-Z])\.\s+([A-ZÁÉÍÓÚÑ])', r'.\n\n\1', texto)
    texto = re.sub(r'\bD\.\n\n', 'D. ', texto)

    # Cabeceras
    titulos = ["ESCRITURA", "COMPARECEN", "INTERVIENEN", "EXPONEN", "OTORGAN", "ESTIPULACIONES"]
    for t in titulos:
        texto = re.sub(rf'({t})', r'\n\n\1', texto)

    return texto.strip()

# --- 3. CONEXIÓN GOOGLE ---
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
            bar.progress(80, "Limpieza Final...")
            limpio = limpiar_texto_registral(sucio)
            bar.progress(100, "Listo")
            bar.empty()
            
            st.success("✅ Procesado correctamente")
            st.text_area("Resultado:", value=limpio, height=600)
            st.download_button("⬇️ DESCARGAR TXT", limpio, "escritura.txt")
        except Exception as e:
            st.error(f"Error: {e}")
