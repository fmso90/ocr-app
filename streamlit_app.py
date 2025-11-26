import streamlit as st
import requests
import base64
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="OCR Registral Pro", 
    page_icon="⚖️",
    layout="centered"
)

# --- FUNCIÓN DE LIMPIEZA MAESTRA (V2.0 - REGISTROS) ---
def limpiar_texto_registral(texto_crudo):
    """
    Elimina timbres, sellos notariales, códigos de papel y reconstruye párrafos.
    """
    if not texto_crudo:
        return ""

    # 1. LISTA NEGRA: Frases exactas que aparecen en los sellos y cabeceras
    marcadores_basura = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES",
        "CLASE 8", "CLASE 6", "CLASE 4", "0,15 €", "0,03 €", "EUROS",
        "R.C.M.FN", "RCMFN", 
        "NIHIL PRIUS FIDE", "PRIUS FIDE", "NIHIL", # Lema del sello notarial
        "NOTARIA DE", "NOTARÍA DE", "DEL ILUSTRE COLEGIO",
        "DISTRITO NOTARIAL"
    ]

    lineas_limpias = []
    
    # Procesamos el texto línea a línea
    for linea in texto_crudo.split('\n'):
        linea_upper = linea.upper().strip()
        es_basura = False
        
        # A) Filtro por frases prohibidas (Sellos y Timbres)
        for marcador in marcadores_basura:
            if marcador in linea_upper:
                es_basura = True
                break
        
        # B) Filtro por Código de Papel Notarial (Ej: IU1953412)
        # Patrón: Empieza por 2 letras mayúsculas + 6 o más números
        if re.search(r'^[A-Z]{2}\s*\d{6,}', linea_upper):
            es_basura = True

        # C) Filtro por Fechas aisladas de cabecera (Ej: 05/2025)
        if re.match(r'^\d{1,2}\/\d{4}$', linea_upper):
            es_basura = True
            
        # D) Filtro por Códigos alfanuméricos "huerfanos" (ruido del OCR)
        if re.match(r'^[A-Z0-9]{5,25}$', linea_upper):
            es_basura = True

        # Si pasa todos los filtros, la guardamos
        if not es_basura:
            lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)

    # --- 2. PULIDO Y FORMATO (Reconstrucción de frases) ---
    
    # Quitar guiones de silabeo al final de línea (Ej: hipo- teca -> hipoteca)
    texto = re.sub(r'-\s+', '', texto) 
    
    # Unir líneas que el OCR cortó indebidamente (Saltos de línea simples -> Espacios)
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto) 
    
    # Eliminar espacios dobles o triples
    texto = re.sub(r'\s+', ' ', texto)
    
    # Arreglar puntuación que quedó pegada o separada
    texto = re.sub(r'\s+([,.:;)])', r'\1', texto) # Quitar espacio antes de punto
    texto = re.sub(r'(\()\s+', r'\1', texto)      # Quitar espacio tras paréntesis
    texto = re.sub(r'\s+\/\s+', '/', texto)        # Arreglar barras 2024 / 2025
    
    # Detectar Puntos y Aparte reales (Punto seguido de Mayúscula)
    # Esto devuelve la estructura de párrafos al documento
    texto = re.sub(r'(\.)\s+([A-ZÁÉÍÓÚÑ])', r'\1\n\n\2', texto)

    # 3. RESALTAR CABECERAS JURÍDICAS
    # Añadimos doble salto de línea antes de palabras clave
    titulos = ["ESCRITURA", "COMPARECEN", "INTERVIENEN", "EXPONEN", "OTORGAN", "ESTIPULACIONES"]
    for t in titulos:
        texto = re.sub(rf'({t})', r'\n\n\1', texto)

    return texto.strip()

# --- CONEXIÓN MOTOR GOOGLE VISION (API KEY) ---
def procesar_con_api_key(content_bytes, api_key):
    """Envía el archivo a Google y recibe el texto sucio"""
    
    # 1. Convertir PDF a Base64 (formato que pide Google)
    b64_content = base64.b64encode(content_bytes).decode('utf-8')
    
    # 2. Preparar la llamada
    url = f"https://vision.googleapis.com/v1/files:annotate?key={api_key}"
    
    payload = {
        "requests": [{
            "inputConfig": {
                "content": b64_content,
                "mimeType": "application/pdf"
            },
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            # Leemos las primeras 5 páginas por defecto
            "pages": [1, 2, 3, 4, 5] 
        }]
    }

    # 3. Enviar petición
    response = requests.post(url, json=payload)
    
    # Control de errores básicos
    if response.status_code != 200:
        return f"Error de conexión con Google: {response.text}"
        
    data = response.json()
    
    # 4. Extraer el texto del JSON complejo de Google
    texto_total = ""
    try:
        responses = data.get('responses', [])
        if responses:
            file_response = responses[0]
            # Google devuelve un array de respuestas, una por página
            paginas = file_response.get('responses', [])
            for pagina in paginas:
                full_text = pagina.get('fullTextAnnotation', {}).get('text', '')
                if full_text:
                    texto_total += full_text + "\n"
    except Exception as e:
        return f"Error leyendo la respuesta: {e}"

    if not texto_total:
        return "⚠️ No se detectó texto. Puede que el PDF sea una imagen de muy mala calidad."
        
    return texto_total

# --- INTERFAZ WEB (FRONTEND) ---
st.title("🏛️ Limpiador de Escrituras - F90")
st.markdown("""
    **Herramienta especializada para Registros de la Propiedad.** *Sube una escritura escaneada y obtén el texto limpio, sin timbres ni sellos.*
""")

# --- AVISO DE PRIVACIDAD (IMPORTANTE) ---
st.info("🔒 **Privacidad:** Los documentos se procesan en memoria volátil y se eliminan al instante. No se almacenan copias.")

# 1. Recuperar la clave secreta
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⛔ ERROR CRÍTICO: No se ha configurado la API Key en los 'Secrets'.")
    st.stop()

# 2. Botón de subida
uploaded_file = st.file_uploader("Arrastra aquí la escritura (PDF)", type=['pdf'])

# 3. Lógica principal
if uploaded_file is not None:
    if st.button("✨ Procesar y Limpiar"):
        with st.spinner('Analizando escritura con IA y eliminando sellos...'):
            try:
                # Leer archivo
                bytes_data = uploaded_file.read()
                
                # Paso A: OCR Puro (Google)
                texto_sucio = procesar_con_api_key(bytes_data, api_key)
                
                # Paso B: Limpieza Registral (Tu algoritmo)
                texto_limpio = limpiar_texto_registral(texto_sucio)
                
                # Mostrar resultado
                st.success("✅ Documento procesado correctamente")
                
                st.subheader("Texto Resultante (Editable)")
                st.text_area("Copia el texto de aquí:", value=texto_limpio, height=500)
                
                # Botón de descarga
                st.download_button(
                    label="⬇️ Descargar en .txt",
                    data=texto_limpio,
                    file_name="escritura_limpia.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Ocurrió un error inesperado: {e}")
