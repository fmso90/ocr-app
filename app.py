{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import re\
import json\
from google.cloud import vision\
from google.oauth2 import service_account\
\
# --- CONFIGURACI\'d3N DE LA P\'c1GINA ---\
st.set_page_config(\
    page_title="OCR Registral Pro",\
    page_icon="\uc0\u9878 \u65039 ",\
    layout="centered"\
)\
\
# --- ESTILOS CSS (Para que se vea profesional) ---\
st.markdown("""\
    <style>\
    .main \{\
        background-color: #f0f2f6;\
    \}\
    .stButton>button \{\
        width: 100%;\
        background-color: #4CAF50;\
        color: white;\
        font-weight: bold;\
    \}\
    .success-box \{\
        padding: 20px;\
        background-color: #dff0d8;\
        border-radius: 5px;\
        color: #3c763d;\
        margin-bottom: 20px;\
    \}\
    </style>\
""", unsafe_allow_html=True)\
\
# --- 1. L\'d3GICA DE LIMPIEZA (Tu Motor Validado v7.2) ---\
def limpiar_y_reconstruir(respuesta_json):\
    texto_final = ""\
    marcadores_timbre = [\
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES", \
        "CLASE 8", "CLASE 6", "0,15 \'80", "0,03 \'80", "EUROS",\
        "R.C.M.FN", "TU19", "TU20"\
    ]\
\
    try:\
        # Adaptaci\'f3n para leer la respuesta directa de la librer\'eda de Python\
        # Si viene como objeto, lo convertimos o accedemos a sus atributos\
        paginas = respuesta_json.full_text_annotation.pages\
        \
        for pagina in paginas:\
            for bloque in pagina.blocks:\
                texto_bloque = ""\
                for parrafo in bloque.paragraphs:\
                    for palabra in parrafo.words:\
                        palabra_texto = "".join([s.text for s in palabra.symbols])\
                        texto_bloque += palabra_texto + " "\
                \
                # Filtro Timbre\
                es_timbre = False\
                texto_bloque_upper = texto_bloque.upper()\
                \
                for marcador in marcadores_timbre:\
                    if marcador in texto_bloque_upper:\
                        es_timbre = True\
                        break\
                \
                if re.match(r'^[A-Z0-9]\{5,20\}\\s*$', texto_bloque.strip()):\
                    es_timbre = True\
\
                if not es_timbre:\
                    texto_final += texto_bloque + "\\n"\
            \
            texto_final += "\\n\\n"\
            \
    except Exception as e:\
        return f"Error procesando: \{str(e)\}"\
\
    # Pulido Regex\
    texto = texto_final\
    texto = re.sub(r'-\\s+', '', texto)\
    texto = re.sub(r'\\n', ' ', texto)\
    texto = re.sub(r'\\s+', ' ', texto)\
    texto = re.sub(r'\\s+([,.:;)])', r'\\1', texto)\
    texto = re.sub(r'(\\()\\s+', r'\\1', texto)\
    texto = re.sub(r'\\s+/\\s+', '/', texto)\
    texto = re.sub(r'(\\.)\\s+([A-Z\'c1\'c9\'cd\'d3\'da\'d1])', r'\\1\\n\\n\\2', texto)\
    texto = re.sub(r'(ESCRITURA)', r'\\n\\n\\1', texto)\
    texto = re.sub(r'(COMPARECEN)', r'\\n\\n\\1', texto)\
    texto = re.sub(r'(INTERVIENEN)', r'\\n\\n\\1', texto)\
    texto = re.sub(r'(EXPONEN)', r'\\n\\n\\1', texto)\
\
    return texto.strip()\
\
# --- 2. GESTI\'d3N DE CREDENCIALES ---\
def obtener_cliente_vision():\
    # En Streamlit Cloud, las credenciales se guardan en st.secrets\
    # Esto es seguro y gratuito.\
    if 'gcp_service_account' in st.secrets:\
        info = st.secrets['gcp_service_account']\
        credenciales = service_account.Credentials.from_service_account_info(info)\
        return vision.ImageAnnotatorClient(credentials=credenciales)\
    else:\
        st.error("\uc0\u9888 \u65039  No se encontraron las credenciales de Google Cloud.")\
        st.info("Configura los 'Secrets' en el panel de Streamlit.")\
        return None\
\
# --- 3. INTERFAZ DE USUARIO (Frontend) ---\
\
# A. Sidebar de Login Simple (Protecci\'f3n b\'e1sica)\
with st.sidebar:\
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910768.png", width=100)\
    st.title("Acceso Privado")\
    password = st.text_input("Contrase\'f1a de Acceso", type="password")\
    \
    # CONTRASE\'d1A MAESTRA (C\'e1mbiala aqu\'ed)\
    if password == "Registro2025": \
        acceso_concedido = True\
        st.success("\uc0\u9989  Conectado")\
    else:\
        acceso_concedido = False\
        st.warning("\uc0\u55357 \u56594  Introduce la clave para usar la herramienta")\
        st.markdown("---")\
        st.markdown("**\'bfNo tienes acceso?**")\
        st.markdown("Contacta con soporte para suscripciones.")\
\
# B. Pantalla Principal\
st.title("\uc0\u55356 \u57307 \u65039  OCR Registral Inteligente")\
st.markdown("Extrae texto limpio de escrituras notariales eliminando sellos y timbres autom\'e1ticamente.")\
\
if acceso_concedido:\
    uploaded_file = st.file_uploader("Sube tu escritura (PDF)", type="pdf")\
\
    if uploaded_file is not None:\
        st.info(f"\uc0\u55357 \u56516  Archivo cargado: \{uploaded_file.name\}")\
        \
        if st.button("\uc0\u10024  PROCESAR DOCUMENTO"):\
            with st.spinner('La IA est\'e1 leyendo y limpiando el documento...'):\
                client = obtener_cliente_vision()\
                \
                if client:\
                    try:\
                        # Leer archivo\
                        content = uploaded_file.read()\
                        image = vision.Image(content=content)\
                        \
                        # Llamada a Google\
                        response = client.document_text_detection(image=image)\
                        \
                        # Limpieza\
                        texto_limpio = limpiar_y_reconstruir(response)\
                        \
                        # \'c9xito\
                        st.balloons()\
                        st.markdown('<div class="success-box">\uc0\u9989  Procesamiento completado con \'e9xito</div>', unsafe_allow_html=True)\
                        \
                        # Vista Previa\
                        with st.expander("Ver Vista Previa del Texto"):\
                            st.text_area("Resultado", texto_limpio, height=300)\
                        \
                        # Bot\'f3n Descarga\
                        st.download_button(\
                            label="\uc0\u11015 \u65039  DESCARGAR TEXTO LIMPIO (.txt)",\
                            data=texto_limpio,\
                            file_name=f"LIMPIO_\{uploaded_file.name\}.txt",\
                            mime="text/plain"\
                        )\
                        \
                    except Exception as e:\
                        st.error(f"Ocurri\'f3 un error: \{e\}")\
    \
    st.markdown("---")\
    st.caption("Sistema optimizado para Registros de la Propiedad. v7.2 Gold Master")\
\
else:\
    st.info("\uc0\u55357 \u56392  Por favor, introduce tu clave de acceso en el men\'fa lateral.")}