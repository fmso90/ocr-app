import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN DE PÁGINA (MODO DARK TECH) ---
st.set_page_config(
    page_title="F90 OCR",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS PARA REPLICAR TU FOTO EXACTA ---
st.markdown("""
<style>
    /* Importar fuente moderna (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    /* Fondo Negro Absoluto */
    .stApp {
        background-color: #000000;
        font-family: 'Inter', sans-serif;
    }

    /* Título Gigante Centrado (Como en la foto) */
    .custom-title {
        color: #ffffff;
        font-size: 3.5rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.2rem;
        line-height: 1.1;
    }
    .custom-subtitle {
        color: #a1a1aa; /* Gris claro */
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 400;
    }

    /* Cajón de Subida (El borde discontinuo de la foto) */
    [data-testid='stFileUploader'] {
        background-color: #121316; /* Gris muy oscuro */
        border: 2px dashed #3f3f46; /* Borde discontinuo */
        border-radius: 16px;
        padding: 40px 20px;
        text-align: center;
        transition: border-color 0.3s ease;
    }
    
    [data-testid='stFileUploader']:hover {
        border-color: #71717a; /* Se ilumina al pasar el ratón */
    }

    /* Ocultar textos por defecto de Streamlit para limpiar */
    [data-testid='stFileUploader'] section > span {
        color: #a1a1aa;
    }
    
    /* Botón de Acción (Verde y Ancho) */
    .stButton > button {
        width: 100%;
        background-color: #22c55e; /* Verde vibrante */
        color: white;
        border: none;
        padding: 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        margin-top: 20px;
    }
    .stButton > button:hover {
        background-color: #16a34a;
    }

    /* Área de texto resultado (Papel limpio) */
    .stTextArea textarea {
        background-color: #fdfbf7;
        color: #1f1f1f;
        border-radius: 4px;
        font-family: 'Georgia', serif;
        font-size: 15px;
        line-height: 1.6;
        border: 1px solid #333;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. TÍTULO PERSONALIZADO (HTML) ---
st.markdown('<div class="custom-title">Transforma tus PDFs<br>en texto limpio.</div>', unsafe_allow_html=True)
st.markdown('<div class="custom-subtitle">Arrastra tu escritura y obtén solo la parte dispositiva.</div>', unsafe_allow_html=True)

# --- 4. LÓGICA INTELIGENTE (MOTOR V16 - RECORTE) ---
def transcribir_con_corte(api_key, archivo_bytes):
    genai.configure(api_key=api_key)
    
    # Usamos el modelo Pro Latest
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = """
    Actúa como un Oficial de Registro. Tu misión es TRANSCRIBIR la escritura, pero SOLO LA PARTE DISPOSITIVA.

    INSTRUCCIONES DE CORTE (CRÍTICO):
    1. Comienza a transcribir desde el principio del documento.
    2. DETENTE INMEDIATAMENTE antes de llegar a la cláusula titulada "PROTECCIÓN DE DATOS" (o "DATOS PERSONALES").
    3. NO transcribas la cláusula de protección de datos.
    4. NO transcribas nada de lo que venga después (ni el Otorgamiento, ni Firmas, ni Anexos, ni Documentos Unidos).
    5. ¡IGNORA TODO EL RESTO DEL PDF A PARTIR DE ESE PUNTO!

    INSTRUCCIONES DE LIMPIEZA:
    - Copia literal palabra por palabra hasta el punto de corte.
    - Elimina los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS") que manchan el texto.
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

# --- 5. INTERFAZ FUNCIONAL ---

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

# Uploader minimalista (sin etiqueta visible para que quede como la foto)
uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

if uploaded_file:
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Analizando y recortando...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada
                resultado = transcribir_con_corte(st.secrets["GOOGLE_API_KEY"], bytes_data)
                datos = json.loads(limpiar_json(resultado))
                texto_final = datos.get("texto_cortado", "")
                
                # Mensaje discreto
                st.success("✅ Listo")
                
                # BOTÓN DE DESCARGA
                st.download_button(
                    label="⬇️ DESCARGAR TEXTO (.TXT)",
                    data=texto_final,
                    file_name="escritura_cuerpo.txt",
                    mime="text/plain"
                )
                
                # VISTA PREVIA
                st.text_area("Vista Previa", value=texto_final, height=600, label_visibility="collapsed")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("Verifica tu API Key.")
