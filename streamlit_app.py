import streamlit as st
import requests
import base64
import json
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="OCR Registral", page_icon="⚖️")

# --- TU LÓGICA DE LIMPIEZA (Versión Python) ---
def limpiar_texto_registral(texto_crudo):
    if not texto_crudo:
        return ""

    marcadores_timbre = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES",
        "CLASE 8", "CLASE 6", "CLASE 4", "0,15 €", "0,03 €", "EUROS",
        "R.C.M.FN", "TU19", "TU20", "TU21", "TU22", "TU23", "TU24", "TU25"
    ]

    lineas_limpias = []
    for linea in texto_crudo.split('\n'):
        linea_upper = linea.upper()
        es_timbre = False
        
        # Filtro 1: Marcadores explícitos
        for marcador in marcadores_timbre:
            if marcador in linea_upper:
                es_timbre = True
                break
        
        # Filtro 2: Códigos sueltos (Regex equivalente a tu JS)
        if re.match(r'^[A-Z0-9]{5,25}\s*$', linea.strip()):
            es_timbre = True

        if not es_timbre:
            lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)

    # Pulido final (Regex equivalentes a tu JS)
    texto = re.sub(r'-\s+', '', texto) 
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto) 
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\s+([,.:;)])', r'\1', texto)
    texto = re.sub(r'(\()\s+', r'\1', texto)
    texto = re.sub(r'\s+\/\s+', '/', texto)
    texto = re.sub(r'(\.)\s+([A-ZÁÉÍÓÚÑ])', r'\1\n\n\2', texto)

    # Resaltar cabeceras
    titulos = ["ESCRITURA", "COMPARECEN", "INTERVIENEN", "EXPONEN", "OTORGAN"]
    for t in titulos:
        texto = re.sub(rf'({t})', r'\n\n\1', texto)

    return texto.strip()

# --- CONEXIÓN GOOGLE VISION (API KEY) ---
def procesar_con_api_key(content_bytes, api_key):
    # 1. Convertir PDF a Base64
    b64_content = base64.b64encode(content_bytes).decode('utf-8')
    
    # 2. URL de Google Vision
    url = f"https://vision.googleapis.com/v1/files:annotate?key={api_key}"
    
    # 3. Petición JSON
    payload = {
        "requests": [{
            "inputConfig": {
                "content": b64_content,
                "mimeType": "application/pdf"
            },
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            # Pide las primeras 5 páginas (ampliable)
            "pages": [1, 2, 3, 4, 5] 
        }]
    }

    # 4. Enviar
    response = requests.post(url, json=payload)
    
    if response.status_code != 200:
        return f"Error Google: {response.text}"
        
    data = response.json()
    
    # 5. Extraer texto
    texto_total = ""
    try:
        responses = data.get('responses', [])
        if responses:
            file_response = responses[0]
            paginas = file_response.get('responses', [])
            for pagina in paginas:
                full_text = pagina.get('fullTextAnnotation', {}).get('text', '')
                if full_text:
                    texto_total += full_text + "\n"
    except Exception as e:
        return f"Error leyendo JSON: {e}"

    if not texto_total:
        return "No se detectó texto (quizás es imagen pura sin OCR)."
        
    return texto_total

# --- INTERFAZ WEB ---
st.title("📄 Limpiador de Escrituras Pro")
st.info("Sistema inteligente para Registros: Elimina timbres y formatea párrafos.")

# Verificación de Seguridad
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ Error: No has configurado la API Key en los 'Secrets' de Streamlit.")
    st.stop()

uploaded_file = st.file_uploader("Sube la escritura (PDF)", type=['pdf'])

if uploaded_file is not None:
    if st.button("Limpiar Documento"):
        with st.spinner('Procesando...'):
            try:
                bytes_data = uploaded_file.read()
                
                # 1. Llamada a Google
                texto_sucio = procesar_con_api_key(bytes_data, api_key)
                
                # 2. Tu Limpieza
                texto_limpio = limpiar_texto_registral(texto_sucio)
                
                st.success("¡Procesado!")
                st.text_area("Resultado:", value=texto_limpio, height=400)
                
                st.download_button(
                    label="⬇️ Descargar .txt",
                    data=texto_limpio,
                    file_name="escritura_limpia.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error: {e}")
