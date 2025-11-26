import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN DE PÁGINA (DISEÑO CENTRADO) ---
st.set_page_config(
    page_title="Transforma tus PDFs",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS PARA REPLICAR TU DISEÑO EXACTO ---
st.markdown("""
<style>
    /* Importar fuente moderna (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    /* 1. FONDO GENERAL (NEGRO PURO) */
    .stApp {
        background-color: #000000;
        font-family: 'Inter', sans-serif;
    }

    /* 2. TÍTULO PERSONALIZADO (GRANDE Y BLANCO) */
    .custom-title {
        font-size: 3.5rem;
        font-weight: 600;
        color: #ffffff;
        text-align: center;
        line-height: 1.1;
        margin-bottom: 2rem;
        margin-top: 2rem;
    }

    /* 3. CAJÓN DE UPLOAD (ESTILO TARJETA OSCURA) */
    /* Contenedor del uploader */
    [data-testid='stFileUploader'] {
        background-color: #111827; /* Gris azulado muy oscuro */
        border: 2px dashed #374151; /* Borde discontinuo gris */
        border-radius: 16px;
        padding: 30px;
        text-align: center;
    }
    
    /* Texto pequeño del uploader ("Limit 200MB...") */
    [data-testid='stFileUploader'] section {
        padding: 0;
    }
    
    /* Icono de subida (Nube) - Intentamos forzar color blanco/gris */
    [data-testid='stFileUploader'] svg {
        color: #9ca3af;
    }

    /* 4. BOTÓN DE ACCIÓN (VERDE VIBRANTE) */
    .stButton > button {
        width: 100%;
        background-color: #22c55e; /* Verde de la foto */
        color: white;
        border: none;
        padding: 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        margin-top: 20px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #16a34a;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.3);
    }

    /* 5. ÁREA DE RESULTADOS (PAPEL LIMPIO) */
    .stTextArea textarea {
        background-color: #fdfbf7; /* Color hueso suave */
        color: #1f1f1f;
        border-radius: 4px;
        border: 1px solid #444;
        font-family: 'Georgia', serif; /* Fuente legal */
        font-size: 15px;
        line-height: 1.6;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stToolbar"] { visibility: hidden; }
    
</style>
""", unsafe_allow_html=True)

# --- 3. TÍTULO VISUAL ---
st.markdown('<div class="custom-title">Transforma tus PDFs<br>en texto limpio.</div>', unsafe_allow_html=True)

# --- 4. LÓGICA DEL CEREBRO (MOTOR DE CORTE) ---
def transcribir_con_corte(api_key, archivo_bytes):
    genai.configure(api_key=api_key)
    
    # Usamos Gemini Pro Latest
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = """
    Actúa como un Oficial de Registro. Tu misión es TRANSCRIBIR la escritura, pero SOLO LA PARTE DISPOSITIVA.

    INSTRUCCIONES DE CORTE (CRÍTICO):
    1. Comienza a transcribir desde el principio del documento.
    2. DETENTE INMEDIATAMENTE antes de llegar a la cláusula titulada "PROTECCIÓN DE DATOS" (o "DATOS PERSONALES").
    3. NO transcribas la cláusula de protección de datos ni nada posterior.
    4. IGNORA todo el resto del PDF a partir de ese punto.

    INSTRUCCIONES DE LIMPIEZA:
    - Copia literal palabra por palabra hasta el punto de corte.
    - Elimina los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS", "NOTARIA DE...") que manchan el texto.
    - Une los párrafos para lectura continua.

    Devuelve un JSON con un solo campo:
    {
        "texto_cortado": "El texto literal limpio hasta antes de Protección de Datos."
    }
    """
    
    config = genai.types.GenerationConfig(
        temperature=0.0,
        response_mime_type="application/json"
    )

    response = model.generate_content(
        [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
        generation_config=config
    )
    return response.text

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 5. INTERFAZ DE USUARIO ---

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta la API Key en los Secrets.")
    st.stop()

# CAJÓN DE SUBIDA (Texto en Español)
uploaded_file = st.file_uploader("Arrastra tu PDF aquí", type=['pdf'], label_visibility="hidden")

if uploaded_file:
    # BOTÓN DE ACCIÓN
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Analizando y limpiando...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada al cerebro
                resultado = transcribir_con_corte(st.secrets["GOOGLE_API_KEY"], bytes_data)
                datos = json.loads(limpiar_json(resultado))
                texto_final = datos.get("texto_cortado", "")
                
                st.success("✅ Transformación completada")
                
                # BOTÓN DE DESCARGA
                st.download_button(
                    label="⬇️ DESCARGAR TEXTO (.TXT)",
                    data=texto_final,
                    file_name="escritura_limpia.txt",
                    mime="text/plain"
                )
                
                # VISTA PREVIA
                st.text_area("Vista Previa", value=texto_final, height=600, label_visibility="collapsed")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("Verifica tu API Key o reinicia la app.")
