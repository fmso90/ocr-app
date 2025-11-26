import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN DE PÁGINA (DISEÑO CENTRADO) ---
st.set_page_config(
    page_title="F90 OCR",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS PARA REPLICAR EL DISEÑO DE LA FOTO ---
st.markdown("""
<style>
    /* Fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    /* FONDO NEGRO PURO */
    .stApp {
        background-color: #000000;
        font-family: 'Inter', sans-serif;
    }

    /* TÍTULO PERSONALIZADO (Grande y blanco como en la foto) */
    .custom-title {
        font-size: 3rem;
        font-weight: 600;
        color: #ffffff;
        text-align: center;
        line-height: 1.2;
        margin-top: 2rem;
        margin-bottom: 3rem;
    }

    /* ESTILO DEL CAJÓN DE SUBIDA (UPLOADER) */
    [data-testid='stFileUploader'] {
        background-color: #121316; /* Gris muy oscuro */
        border: 2px dashed #3f3f46; /* Borde discontinuo gris */
        border-radius: 20px;
        padding: 40px 20px;
        text-align: center;
    }

    /* HACK: OCULTAR TEXTO INGLÉS ORIGINAL */
    [data-testid='stFileUploader'] section > div:first-child {
        display: none;
    }
    
    /* HACK: INYECTAR TEXTO ESPAÑOL Y ICONO */
    [data-testid='stFileUploader'] section::before {
        content: "☁️ Arrastra tu PDF aquí"; 
        color: #e5e5e5;
        font-size: 1.3rem;
        font-weight: 600;
        display: block;
        text-align: center;
        margin-bottom: 10px;
    }
    
    [data-testid='stFileUploader'] section::after {
        content: "Límite 200MB • PDF"; 
        color: #71717a;
        font-size: 0.8rem;
        display: block;
        text-align: center;
        margin-bottom: 15px;
    }

    /* BOTÓN PRINCIPAL VERDE */
    .stButton > button {
        width: 100%;
        background-color: #22c55e; /* Verde brillante */
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        margin-top: 20px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #16a34a; /* Verde más oscuro */
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.3);
        color: white;
    }

    /* ÁREA DE TEXTO RESULTADO (Papel limpio) */
    .stTextArea textarea {
        background-color: #1c1c1c; /* Gris oscuro */
        color: #e5e5e5; /* Texto claro */
        border: 1px solid #333;
        border-radius: 8px;
        font-family: 'Georgia', serif;
        font-size: 15px;
        line-height: 1.6;
    }
    
    /* Ocultar elementos extra */
    #MainMenu, footer, header { visibility: hidden; }
    
</style>
""", unsafe_allow_html=True)

# --- 3. TÍTULO VISUAL HTML ---
st.markdown('<div class="custom-title">Transforma tus PDFs<br>en texto limpio.</div>', unsafe_allow_html=True)

# --- 4. TU LÓGICA DEL CEREBRO (INTACTA) ---
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

# --- 5. INTERFAZ LÓGICA ---

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta la API Key en los Secrets.")
    st.stop()

# El label está oculto ("collapsed") porque usamos el CSS para poner el texto en español encima
uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

if uploaded_file:
    # Botón de acción verde
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Analizando y limpiando...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada a tu lógica
                resultado = transcribir_con_corte(st.secrets["GOOGLE_API_KEY"], bytes_data)
                datos = json.loads(limpiar_json(resultado))
                texto_final = datos.get("texto_cortado", "")
                
                st.success("✅ Documento procesado")
                
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
