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

# --- 2. LÓGICA DE LIMPIEZA V12.0 (SEGURIDAD JURÍDICA MÁXIMA) ---
def limpiar_texto_registral(texto_crudo):
    if not texto_crudo:
        return ""

    # A) PRE-PROCESADO: Despegar palabras pegadas (OCR Error)
    # realidad.TIMBRE -> realidad. TIMBRE
    texto_crudo = re.sub(r'(\.)([A-Z])', r'\1 \2', texto_crudo)
    # fincaTIMBRE -> finca TIMBRE
    texto_crudo = re.sub(r'([a-z])([A-Z]{3,})', r'\1 \2', texto_crudo)

    # B) DEFINICIÓN DE LISTAS (SANEADAS: SIN NOMBRES NI LUGARES)
    
    # 1. Palabras Tóxicas TÉCNICAS (Solo basura universal)
    # Eliminados: OLCINA, BOLAS, QUINTANAR, TOLEDO, etc.
    palabras_toxicas = [
        "TIMBRE", "PRIUS", "NIHIL", "FIDE", "IHIL", "1NIHIL", 
        "RCMFN", "R.C.M.FN", "EUROS", "CLASE", 
        "PAPEL", "EXCL", "EXCLUSIVO", 
        "DOCUMENTOS", "NOTARIALES"
    ]

    # 2. Frases Basura Completas
    frases_basura = [
        "TIMBRE DEL ESTADO", "DOCUMENTOS NOTARIALES",
        "0,15 €", "0,03 €", "NOTARIA DE", "NOTARÍA DE",
        "DEL ILUSTRE COLEGIO", "DISTRITO NOTARIAL"
    ]

    # 3. Inmunidad (Para proteger encabezados)
    frases_sagradas = [
        "ANTE MÍ", "ANTE MI", 
        "EN LA VILLA DE", "EN LA CIUDAD DE", 
        "COMPARECEN", "INTERVIENEN", "OTORGAN"
    ]

    lineas_limpias = []
    
    for linea in texto_crudo.split('\n'):
        linea_strip = linea.strip()
        linea_upper = linea.upper()
        
        # --- PASO 1: PROTECCIÓN ---
        es_linea_sagrada = False
        # Si la línea es corta (cabecera) y tiene palabras clave de inicio, no la tocamos.
        if len(linea_strip) < 120:
            # Detecta "EN [LUGAR]" o "ANTE MI"
            if re.search(r'\bEN\s+[A-ZÁÉÍÓÚÑ\s]+,', linea_upper) or "ANTE MÍ" in linea_upper or "ANTE MI" in linea_upper:
                es_linea_sagrada = True
        
        if es_linea_sagrada:
            lineas_limpias.append(linea)
            continue 

        # --- PASO 2: LIMPIEZA SEGURA ---
        linea_procesada = linea
        
        # 1. Borrar frases técnicas completas
        for frase in frases_basura:
            linea_procesada = re.sub(re.escape(frase), "", linea_procesada, flags=re.IGNORECASE)

        # 2. Borrar palabras tóxicas TÉCNICAS sueltas
        for palabra in palabras_toxicas:
            # Solo borramos la palabra exacta (con \b)
            linea_procesada = re.sub(r'\b' + re.escape(palabra) + r'\b', "", linea_procesada, flags=re.IGNORECASE)
        
        # 3. Borrar Códigos de Papel Universales (2 Letras + 6-12 Números)
        # Esto borra IU1953411, TU123456, AB000000... Sea cual sea la letra.
        linea_procesada = re.sub(r'\b[A-Z]{2}\d{6,}\b', "", linea_procesada)
        
        # 4. Borrar Fechas sueltas (MM/YYYY)
        linea_procesada = re.sub(r'\b\d{2}/\d{4}\b', "", linea_procesada)

        # 5. Borrar números de página sueltos (si son de 3 cifras y parecen basura)
        # Solo si están aislados
        linea_procesada = re.sub(r'\s\d{3}\s', " ", linea_procesada)

        # --- PASO 3: GUARDADO ---
        linea_procesada = re.sub(r'\s+', ' ', linea_procesada).strip()
        
        if len(linea_procesada) > 2:
            lineas_limpias.append(linea_procesada)

    texto = "\n".join(lineas_limpias)

    # C) PULIDO FINAL (Unión y DNI)
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
            bar.progress(80, "Limpieza Segura...")
            limpio = limpiar_texto_registral(sucio)
            bar.progress(100, "Listo")
            bar.empty()
            
            st.success("✅ Procesado correctamente")
            st.text_area("Resultado:", value=limpio, height=600)
            st.download_button("⬇️ DESCARGAR TXT", limpio, "escritura.txt")
        except Exception as e:
            st.error(f"Error: {e}")
