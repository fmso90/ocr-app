import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN (FONDO NEGRO) ---
st.set_page_config(
    page_title="F90 OCR",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. EL CSS "MÁGICO" (TRADUCCIÓN VISUAL) ---
st.markdown("""
<style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    /* FONDO GENERAL NEGRO PURO */
    .stApp {
        background-color: #000000;
        font-family: 'Inter', sans-serif;
    }

    /* TÍTULO PRINCIPAL */
    .custom-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        line-height: 1.1;
        margin-top: 3rem;
        margin-bottom: 3rem;
    }

    /* --- HACK PARA EL UPLOADER (ESTILO FOTO) --- */
    
    /* 1. El contenedor del cajón */
    [data-testid='stFileUploader'] {
        background-color: #111827; /* Gris muy oscuro */
        border: 2px dashed #374151; /* Borde discontinuo gris */
        border-radius: 20px;
        padding: 20px;
    }
    
    /* 2. OCULTAR el texto original en inglés (Drag and drop...) */
    [data-testid='stFileUploader'] section > div:first-child {
        display: none;
    }
    
    /* 3. INYECTAR el texto en ESPAÑOL y el icono */
    [data-testid='stFileUploader'] section::before {
        content: "☁️ Arrastra tu PDF aquí"; 
        color: #e5e5e5;
        font-size: 1.2rem;
        font-weight: 600;
        display: block;
        text-align: center;
        margin-bottom: 10px;
        margin-top: 10px;
    }
    
    /* 4. Pequeño texto debajo */
    [data-testid='stFileUploader'] section::after {
        content: "Límite 200MB • PDF"; 
        color: #6b7280;
        font-size: 0.8rem;
        display: block;
        text-align: center;
        margin-bottom: 10px;
    }

    /* 5. El botón "Browse files" es difícil de traducir por CSS, 
       pero lo hacemos más discreto y estilo botón */
    [data-testid='stFileUploader'] button {
        border: 1px solid #444;
        color: white;
        background-color: #000;
        border-radius: 8px;
        margin: 0 auto;
        display: block;
    }

    /* --- BOTÓN VERDE DE ACCIÓN --- */
    .stButton > button {
        width: 100%;
        background-color: #22c55e; /* Verde de tu foto */
        color: white;
        font-weight: 600;
        border: none;
        padding: 15px;
        border-radius: 8px;
        font-size: 18px;
        margin-top: 20px;
    }
    .stButton > button:hover {
        background-color: #16a34a;
        color: white;
    }
    
    /* ÁREA DE TEXTO LIMPIA */
    .stTextArea textarea {
        background-color: #1c1c1c;
        color: #e5e5e5;
        border: 1px solid #333;
        font-family: 'Georgia', serif;
    }

    /* OCULTAR ELEMENTOS EXTRA */
    #MainMenu, footer, header { visibility: hidden; }
    
</style>
""", unsafe_allow_html=True)

# --- 3. TÍTULO VISUAL ---
st.markdown('<div class="custom-title">Transforma tus PDFs<br>en texto limpio.</div>', unsafe_allow_html=True)

# --- 4. LÓGICA DEL CEREBRO (MOTOR V16) ---
def transcribir_con_corte(api_key, archivo_bytes):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = """
    Actúa como un Oficial de Registro. Tu misión es TRANSCRIBIR la escritura, pero SOLO LA PARTE DISPOSITIVA.
    
    INSTRUCCIONES CRÍTICAS:
    1. Comienza a transcribir desde el principio.
    2. DETENTE antes de la cláusula "PROTECCIÓN DE DATOS" (o "DATOS PERSONALES").
    3. NO transcribas nada posterior (ni firmas, ni anexos).
    
    LIMPIEZA:
    - Copia literal palabra por palabra.
    - Elimina los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS") dentro del texto.
    - Une los párrafos.

    Devuelve JSON:
    {
        "texto_cortado": "El texto literal limpio hasta el corte."
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

# --- 5. INTERFAZ ---

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta la API Key en los Secrets.")
    st.stop()

# Uploader invisible (el CSS se encarga de pintarlo bonito en español)
uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

if uploaded_file:
    # Botón verde gigante
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Analizando y limpiando...'):
            try:
                bytes_data = uploaded_file.read()
                
                resultado = transcribir_con_corte(st.secrets["GOOGLE_API_KEY"], bytes_data)
                datos = json.loads(limpiar_json(resultado))
                texto_final = datos.get("texto_cortado", "")
                
                st.success("✅ Transformación completada")
                
                st.download_button(
                    label="⬇️ DESCARGAR TEXTO (.TXT)",
                    data=texto_final,
                    file_name="escritura_limpia.txt",
                    mime="text/plain"
                )
                
                st.text_area("Vista Previa", value=texto_final, height=600, label_visibility="collapsed")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("Verifica tu API Key.")
