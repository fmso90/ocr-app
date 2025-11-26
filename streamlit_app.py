import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(
    page_title="Digitalizador Registral",
    page_icon="📄",
    layout="centered", # Centrado para enfocar la atención
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Fondo oscuro */
    .stApp { background-color: #0e1117; }
    
    /* Títulos y botones */
    h1, h2, h3 { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; text-align: center; }
    
    /* Botón de descarga gigante y verde */
    .stButton > button { 
        width: 100%; 
        font-weight: bold; 
        border-radius: 8px; 
        padding: 0.8rem; 
        background-color: #2ea043; 
        color: white; 
        border: none;
        font-size: 1.1rem;
    }
    .stButton > button:hover { background-color: #238636; }

    /* Área de texto estilo documento */
    .stTextArea textarea {
        background-color: #fdfbf7; /* Color papel hueso */
        color: #1f1f1f;
        border-radius: 4px;
        font-family: 'Georgia', serif;
        font-size: 15px;
        line-height: 1.6;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA INTELIGENTE ---
def transcribir_documento_entero(api_key, archivo_bytes):
    genai.configure(api_key=api_key)
    
    # MODELO SOLICITADO
    model = genai.GenerativeModel('models/gemini-pro-latest')
    
    prompt = """
    Actúa como un Oficial de Registro experto en mecanografía.
    Tu ÚNICA misión es: TRANSCRIBIR EL TEXTO LITERALMENTE.

    INSTRUCCIONES PRECISAS:
    1. Copia el texto palabra por palabra, párrafo por párrafo.
    2. NO RESUMAS NADA. NO uses viñetas. Mantén la prosa original.
    3. LIMPIEZA: Elimina el texto de los sellos ("TIMBRE DEL ESTADO", "0,15 €", "NIHIL PRIUS", "NOTARIA DE...") que mancha el documento.
    4. CONTINUIDAD: Une el texto de las páginas para que se lea seguido.

    Devuelve un JSON con un solo campo:
    {
        "texto_completo": "Aquí va todo el texto del documento, limpio y literal."
    }
    """
    
    config = genai.types.GenerationConfig(
        temperature=0.0, # Cero invención
        response_mime_type="application/json"
    )

    response = model.generate_content(
        [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
        generation_config=config
    )
    return response.text

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 3. INTERFAZ ---
st.title("DIGITALIZADOR REGISTRAL")
st.caption("Transcripción Literal • Limpieza de Sellos • Texto Íntegro")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

uploaded_file = st.file_uploader("Sube la escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("PROCESAR Y LIMPIAR"):
        with st.spinner('🧠 Leyendo documento completo con gemini-pro-latest...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada
                resultado = transcribir_documento_entero(st.secrets["GOOGLE_API_KEY"], bytes_data)
                datos = json.loads(limpiar_json(resultado))
                texto_final = datos.get("texto_completo", "")
                
                st.success("✅ Documento Procesado")
                
                # BOTÓN DE DESCARGA GRANDE
                st.download_button(
                    label="⬇️ DESCARGAR TEXTO COMPLETO (.TXT)",
                    data=texto_final,
                    file_name="escritura_completa.txt",
                    mime="text/plain"
                )
                
                # VISTA PREVIA
                st.markdown("### Vista Previa:")
                st.text_area("preview", value=texto_final, height=600, label_visibility="collapsed")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("El modelo 'gemini-pro-latest' no responde. Verifica tu API Key o región.")
