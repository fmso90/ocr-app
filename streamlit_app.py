import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN (DISEÑO DE ESCRITORIO) ---
st.set_page_config(
    page_title="PDF a Texto Limpio",
    page_icon="☁️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS PARA IMITAR CUSTOMTKINTER ---
st.markdown("""
<style>
    /* Fuente Roboto (como en tu código) */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    /* FONDO NEGRO PURO (self.configure(fg_color="black")) */
    .stApp {
        background-color: #000000;
        font-family: 'Roboto', sans-serif;
    }

    /* TÍTULO PRINCIPAL (self.header_label) */
    .custom-title {
        font-family: 'Roboto', sans-serif;
        font-size: 32px;
        font-weight: 500; /* Medium */
        color: #ffffff;
        text-align: center;
        margin-top: 60px;
        margin-bottom: 40px;
        white-space: pre-wrap; /* Para respetar el salto de línea */
    }

    /* CAJÓN DE UPLOAD (self.drop_frame) */
    [data-testid='stFileUploader'] {
        background-color: #111111;
        border: 2px dashed #444444;
        border-radius: 15px;
        padding: 40px;
        text-align: center;
        min-height: 300px; /* Altura fija como en tu código */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    /* ICONO NUBE (self.icon_label) */
    [data-testid='stFileUploader']::before {
        content: "☁️";
        font-size: 64px;
        display: block;
        margin-bottom: 10px;
    }

    /* TEXTO DE INSTRUCCIÓN (self.text_label) */
    [data-testid='stFileUploader']::after {
        content: "Arrastra tu PDF aquí";
        color: #AAAAAA;
        font-size: 18px;
        font-family: 'Roboto', sans-serif;
        display: block;
        margin-top: 10px;
    }

    /* OCULTAR TEXTOS NATIVOS DE STREAMLIT (Para que solo se vea lo tuyo) */
    [data-testid='stFileUploader'] section > div:first-child {
        display: none;
    }
    [data-testid='stFileUploader'] section {
        padding: 0;
    }
    /* Ocultar el texto pequeño de límite */
    [data-testid='stFileUploader'] .uploadedFile {
        display: none;
    }

    /* BOTÓN DE ACCIÓN (Estilo Botón CTK) */
    .stButton > button {
        background-color: #000000; /* Fondo negro */
        color: white;
        border: 1px solid #555555;
        border-radius: 8px;
        padding: 10px 20px;
        font-family: 'Roboto', sans-serif;
        font-size: 14px;
        margin-top: 20px;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #333333;
        border-color: #777;
    }

    /* ÁREA DE TEXTO RESULTADO */
    .stTextArea textarea {
        background-color: #111111;
        color: #e0e0e0;
        border: 1px solid #444;
        font-family: 'Courier New', monospace;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. INTERFAZ VISUAL ---

# Título exacto de tu código
st.markdown('<div class="custom-title">Transforma tus PDFs\nen texto limpio.</div>', unsafe_allow_html=True)

# --- 4. LÓGICA DEL CEREBRO ---
def transcribir_con_corte(api_key, archivo_bytes):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = """
    Actúa como un Oficial de Registro. Tu misión es TRANSCRIBIR la escritura, pero SOLO LA PARTE DISPOSITIVA.
    1. Comienza a transcribir desde el principio.
    2. DETENTE INMEDIATAMENTE antes de la cláusula "PROTECCIÓN DE DATOS".
    3. NO transcribas nada posterior.
    4. Elimina los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS").
    5. Une los párrafos.
    Devuelve JSON: { "texto_cortado": "Texto limpio..." }
    """
    
    config = genai.types.GenerationConfig(temperature=0.0, response_mime_type="application/json")
    
    try:
        response = model.generate_content(
            [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
            generation_config=config
        )
        return response.text
    except Exception as e:
        return None

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 5. LOGICA DE LA APP ---

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key.")
    st.stop()

# Cajón de subida
uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

if uploaded_file:
    # Simulación del status_label de tu código
    status_placeholder = st.empty()
    status_placeholder.info(f"Procesando: {uploaded_file.name}...")
    
    try:
        bytes_data = uploaded_file.read()
        
        # Procesar
        resultado = transcribir_con_corte(st.secrets["GOOGLE_API_KEY"], bytes_data)
        
        if resultado:
            datos = json.loads(limpiar_json(resultado))
            texto_final = datos.get("texto_cortado", "")
            
            status_placeholder.success(f"✅ ¡Listo! Procesado: {uploaded_file.name}")
            
            # Botón de descarga (Estilizado)
            st.download_button(
                label="⬇️ DESCARGAR TEXTO LIMPIO (.TXT)",
                data=texto_final,
                file_name=f"{uploaded_file.name}_limpio.txt",
                mime="text/plain"
            )
            
            # Vista previa
            st.text_area("Vista Previa", value=texto_final, height=500, label_visibility="collapsed")
        else:
            status_placeholder.error("❌ Error: La IA no devolvió respuesta.")
            
    except Exception as e:
        status_placeholder.error(f"❌ Error: {str(e)}")
