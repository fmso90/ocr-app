import streamlit as st
import re
import json
import base64
import requests

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="OCR Registral Pro",
    page_icon="⚖️",
    layout="centered"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; background-color: #4CAF50; color: white; font-weight: bold; }
    .success-box { padding: 20px; background-color: #dff0d8; border-radius: 5px; color: #3c763d; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 1. MOTOR DE LIMPIEZA v7.2 (Validado) ---
def limpiar_y_reconstruir(respuesta_json):
    texto_final = ""
    marcadores_timbre = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES", 
        "CLASE 8", "CLASE 6", "0,15 €", "0,03 €", "EUROS",
        "R.C.M.FN", "TU19", "TU20"
    ]

    try:
        # Estructura de respuesta REST API
        respuestas_paginas = respuesta_json.get('responses', [])[0].get('responses', [])
        
        for pagina_data in respuestas_paginas:
            full_annotation = pagina_data.get('fullTextAnnotation', {})
            paginas_fisicas = full_annotation.get('pages', [])
            
            for pagina in paginas_fisicas:
                for bloque in pagina.get('blocks', []):
                    texto_bloque = ""
                    for parrafo in bloque.get('paragraphs', []):
                        for palabra in parrafo.get('words', []):
                            palabra_texto = "".join([s.get('text', '') for s in palabra.get('symbols', [])])
                            texto_bloque += palabra_texto + " "
                    
                    # Filtro Timbre
                    es_timbre = False
                    texto_bloque_upper = texto_bloque.upper()
                    
                    for marcador in marcadores_timbre:
                        if marcador in texto_bloque_upper:
                            es_timbre = True
                            break
                    
                    if re.match(r'^[A-Z0-9]{5,20}\s*$', texto_bloque.strip()):
                        es_timbre = True

                    if not es_timbre:
                        texto_final += texto_bloque + "\n"
            
            texto_final += "\n\n"
            
    except Exception as e:
        return f"Error procesando: {str(e)}"

    # Pulido Regex
    texto = texto_final
    texto = re.sub(r'-\s+', '', texto)
    texto = re.sub(r'\n', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\s+([,.:;)])', r'\1', texto)
    texto = re.sub(r'(\()\s+', r'\1', texto)
    texto = re.sub(r'\s+/\s+', '/', texto)
    texto = re.sub(r'(\.)\s+([A-ZÁÉÍÓÚÑ])', r'\1\n\n\2', texto)
    texto = re.sub(r'(ESCRITURA)', r'\n\n\1', texto)
    texto = re.sub(r'(COMPARECEN)', r'\n\n\1', texto)
    texto = re.sub(r'(INTERVIENEN)', r'\n\n\1', texto)
    texto = re.sub(r'(EXPONEN)', r'\n\n\1', texto)

    return texto.strip()

# --- 2. CONEXIÓN CON GOOGLE (VÍA API KEY) ---
def procesar_con_google(contenido_pdf, api_key):
    # Codificar PDF a Base64
    contenido_base64 = base64.b64encode(contenido_pdf).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/files:annotate?key={api_key}"
    
    payload = {
        "requests": [{
            "inputConfig": {
                "content": contenido_base64, "mimeType": "application/pdf"
            },
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            "pages": [1, 2, 3, 4, 5] # Lee las primeras 5 páginas
        }]
    }
    
    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error de Google: {response.text}")
        return None

# --- 3. INTERFAZ DE USUARIO ---
with st.sidebar:
    st.title("🔐 Acceso Privado")
    password = st.text_input("Contraseña", type="password")
    if password == "Registro2025": 
        acceso_concedido = True
        st.success("✅ Conectado")
    else:
        acceso_concedido = False
        st.warning("Introduce clave de acceso")

st.title("🏛️ OCR Registral Pro")
st.markdown("Sistema de limpieza inteligente de escrituras notariales.")

if acceso_concedido:
    # Recuperamos la API Key de los secretos
    if 'GOOGLE_API_KEY' in st.secrets:
        api_key = st.secrets['GOOGLE_API_KEY']
    else:
        st.error("Falta configurar la API Key en los Secrets.")
        st.stop()

    uploaded_file = st.file_uploader("Sube tu escritura (PDF)", type="pdf")

    if uploaded_file is not None:
        if st.button("✨ PROCESAR DOCUMENTO"):
            with st.spinner('Procesando documento...'):
                content = uploaded_file.read()
                json_respuesta = procesar_con_google(content, api_key)
                
                if json_respuesta:
                    texto_limpio = limpiar_y_reconstruir(json_respuesta)
                    st.balloons()
                    st.success("✅ Procesamiento completado")
                    
                    with st.expander("Vista Previa"):
                        st.text_area("Resultado", texto_limpio, height=300)
                    
                    st.download_button(
                        "⬇️ DESCARGAR .TXT",
                        texto_limpio,
                        f"LIMPIO_{uploaded_file.name}.txt"
                    )
else:
    st.info("Introduce la contraseña en el menú lateral.")
