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

# --- 2. LÓGICA DE LIMPIEZA V7.0 (SIGLAS + LIMPIEZA PROFUNDA) ---
def limpiar_texto_registral(texto_crudo):
    if not texto_crudo:
        return ""

    # A) PRE-PROCESADO: ARREGLO DE SIGLAS (D. N. I. -> D.N.I.)
    # Primero arreglamos los espacios entre puntos de siglas comunes
    # Patrón: Letra + Punto + Espacio + Letra + Punto
    texto_crudo = re.sub(r'([A-Z])\.\s+([A-Z])\.', r'\1.\2.', texto_crudo)
    # Ejecutamos una segunda vez para casos de 3 letras (N. I. F. -> N.I.F.)
    texto_crudo = re.sub(r'([A-Z])\.\s+([A-Z])\.', r'\1.\2.', texto_crudo)
    
    # Arreglo específico para DNI/NIF pegados con barras si Google falla
    texto_crudo = re.sub(r'D\.\s*N\.\s*I\.', 'D.N.I.', texto_crudo, flags=re.IGNORECASE)
    
    # B) PRE-PROCESADO: DESPEGAR BASURA DEL TEXTO
    # "realidad.TIMBRE" -> "realidad. TIMBRE"
    texto_crudo = re.sub(r'(\.)([A-Z])', r'\1 \2', texto_crudo)
    # "fincaTIMBRE" -> "finca TIMBRE"
    texto_crudo = re.sub(r'([a-z])([A-Z]{3,})', r'\1 \2', texto_crudo)

    # C) DEFINICIÓN DE LISTAS
    
    # Inmunidad: Líneas que NO se tocan (Encabezados legales)
    frases_sagradas = [
        "ANTE MÍ", "ANTE MI", 
        "COMPARECEN", "INTERVIENEN", "EXPONEN", "OTORGAN",
        "EN LA VILLA DE", "EN LA CIUDAD DE", "EN " # "En Quintanar..."
    ]

    # Lista Negra: Basura a eliminar quirúrgicamente
    marcadores_basura = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES",
        "CLASE 8", "CLASE 6", "CLASE 4", "0,15 €", "0,03 €", "EUROS",
        "R.C.M.FN", "RCMFN", 
        "NIHIL PRIUS FIDE", "PRIUS FIDE", "NIHIL", "IHIL", "1NIHIL", 
        "IU1953", 
        # Fragmentos sueltos detectados en tus pruebas:
        "RESA BOLAS", "BOLAS OLCINA", "OLCINA PAPEL", "PAPEL EXCL",
        "QUINTANARDELA", "QUINTANARDEL", "RDEN (TOLEDO)", "DEN TOLEDO",
        "DE DONA M", "DE DONA"
    ]

    lineas_limpias = []
    
    for linea in texto_crudo.split('\n'):
        linea_strip = linea.strip()
        linea_upper = linea.upper()
        
        # 1. Chequeo de Inmunidad
        es_linea_sagrada = False
        if linea_upper.startswith("EN ") or "ANTE MÍ" in linea_upper or "ANTE MI" in linea_upper:
            es_linea_sagrada = True
        
        if es_linea_sagrada:
            # Solo limpieza mínima al final de la línea sagrada
            linea = re.sub(r'IU\d{6,}.*', '', linea) 
            lineas_limpias.append(linea)
            continue 

        # 2. Limpieza Quirúrgica (Borrar basura DENTRO de la línea)
        # Esto soluciona la línea 93: "realidad. TIMBRE DEL ESTADO..."
        linea_procesada = linea
        for marcador in marcadores_basura:
            # Reemplazamos el marcador por vacío, ignorando mayúsculas
            linea_procesada = re.sub(re.escape(marcador), "", linea_procesada, flags=re.IGNORECASE)
        
        # Limpieza de patrones sueltos
        linea_procesada = re.sub(r'\s[A-Z]{2}\d{6,}', "", linea_procesada) # Códigos IU sueltos
        linea_procesada = re.sub(r'\s\d{2}/\d{4}', "", linea_procesada)    # Fechas sueltas 05/2025

        # 3. Filtro final: ¿Quedó la línea vacía o inservible?
        if len(linea_procesada.strip()) > 2:
            # Un último arreglo de espacios dobles creados al borrar palabras
            linea_procesada = re.sub(r'\s+', ' ', linea_procesada).strip()
            lineas_limpias.append(linea_procesada)

    texto = "\n".join(lineas_limpias)

    # D) PULIDO Y FORMATO FINAL
    
    texto = re.sub(r'-\s+', '', texto) 
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto) 
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\s+([,.:;)])', r'\1', texto)
    texto = re.sub(r'(\()\s+', r'\1', texto)
    texto = re.sub(r'\s+\/\s+', '/', texto)
    
    # RECONSTRUCCIÓN DE PÁRRAFOS (Respetando D.N.I.)
    # Solo salta línea si hay punto Y NO está precedido por mayúscula (D.) ni seguido por número
    texto = re.sub(r'(?<![A-Z])\.\s+([A-ZÁÉÍÓÚÑ])', r'.\n\n\1', texto)
    
    # Corrección estética para Don/Doña
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
            bar.progress(80, "Limpieza Final...")
            limpio = limpiar_texto_registral(sucio)
            bar.progress(100, "Listo")
            bar.empty()
            
            st.success("✅ Procesado correctamente")
            st.text_area("Resultado:", value=limpio, height=600)
            st.download_button("⬇️ DESCARGAR TXT", limpio, "escritura.txt")
        except Exception as e:
            st.error(f"Error: {e}")
