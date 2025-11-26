import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(
    page_title="Extractor Registral Literal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo Dark Premium (Sin marcas)
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    
    /* Contenedor principal */
    div.block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }
    
    /* Títulos */
    h1, h2, h3 { color: #fff !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 600; }
    
    /* Áreas de texto (Look limpio para copiar) */
    .stTextArea textarea {
        background-color: #161b22;
        border: 1px solid #30363d;
        color: #c9d1d9;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.6;
    }
    
    /* Botones */
    div.stButton > button {
        background-color: #238636; /* Verde GitHub/Enterprise */
        color: #ffffff;
        border: none;
        font-weight: 700;
        width: 100%;
        padding: 0.8rem;
        border-radius: 6px;
        transition: background-color 0.2s;
    }
    div.stButton > button:hover { background-color: #2ea043; }
    
    /* Uploader */
    [data-testid="stFileUploader"] { background-color: #161b22; border: 1px dashed #30363d; border-radius: 6px; }
    
    /* Ocultar elementos extra */
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN DE LA IA ---
def configurar_gemini(api_key):
    genai.configure(api_key=api_key)
    # Usamos Flash por ser rápido y estable. Si tienes acceso a Pro, cambia a 'gemini-1.5-pro'
    return genai.GenerativeModel('gemini-1.5-flash')

def limpiar_respuesta_json(texto):
    """Limpia el formato Markdown que a veces añade la IA"""
    return texto.replace("```json", "").replace("```", "").strip()

# --- 3. CEREBRO DE TRANSCRIPCIÓN LITERAL ---
def transcribir_literalmente(modelo, archivo_bytes):
    
    # PROMPT DE ALTA PRECISIÓN PARA TRANSCRIPCIÓN
    prompt = """
    Actúa como un Oficial de Registro experto en mecanografía.
    Tu tarea es LEER el PDF adjunto y EXTRAER el texto LITERALMENTE, palabra por palabra.

    REGLAS DE ORO (INVIOLABLES):
    1. NO RESUMAS. NO uses viñetas. NO uses guiones. Copia el texto seguido en párrafos, tal cual aparece.
    2. LIMPIEZA VISUAL: Elimina ÚNICAMENTE el texto de los sellos, timbres, marcas de agua o notas al margen que interrumpen la lectura (ej: "TIMBRE DEL ESTADO", "NIHIL PRIUS", "0,15 €", números de protocolo laterales).
    3. DATOS SAGRADOS: Nombres, DNI, Lugares, Fechas, Referencias Catastrales y Fincas deben copiarse EXACTAMENTE igual al original. Si pone "D. Juan", pon "D. Juan".
    
    Devuelve un objeto JSON con estas 3 secciones de TEXTO PURO:

    {
        "intervinientes": "Copia aquí LITERALMENTE todo el bloque de texto referente a la COMPARECENCIA e INTERVENCIÓN. Desde 'COMPARECEN' hasta 'INTERVIENEN' (o 'TIENEN A MI JUICIO...'). Debe incluir todos los nombres, DNIs, estados civiles y domicilios seguidos, sin perder ni una coma.",
        
        "fincas": "Copia aquí LITERALMENTE la descripción de las fincas. Desde 'RÚSTICA/URBANA' hasta el final de los linderos y referencia catastral. Si hay varias, sepáralas por dos saltos de línea. NO lo conviertas en lista, mantén la prosa notarial.",
        
        "texto_completo": "El texto ÍNTEGRO del documento, uniendo todas las páginas en un solo bloque continuo, eliminando las interrupciones de cabecera/pie de página y sellos."
    }
    """
    
    # Configuración de generación para forzar JSON
    generation_config = genai.types.GenerationConfig(
        temperature=0.1, # Creatividad casi nula para asegurar literalidad
        response_mime_type="application/json"
    )

    response = modelo.generate_content(
        [
            {'mime_type': 'application/pdf', 'data': archivo_bytes},
            prompt
        ],
        generation_config=generation_config
    )
    return response.text

# --- 4. INTERFAZ DE USUARIO ---
st.title("DIGITALIZADOR REGISTRAL")
st.markdown("### Transcripción Literal Inteligente (Sin Resúmenes)")

# Verificación de Seguridad
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta la API Key en los Secrets.")
    st.stop()

# Inicialización del modelo
try:
    model = configurar_gemini(st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error de conexión con Google AI: {e}")
    st.stop()

# Zona de carga
uploaded_file = st.file_uploader("Arrastra tu escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    # Botón de acción
    if st.button("TRANSCRIBIR DOCUMENTO"):
        with st.spinner('🔍 Leyendo documento y eliminando sellos...'):
            try:
                bytes_data = uploaded_file.read()
                
                # 1. Llamada a la IA
                resultado_json = transcribir_literalmente(model, bytes_data)
                
                # 2. Procesar respuesta
                datos = json.loads(limpiar_respuesta_json(resultado_json))
                
                st.success("✅ Transcripción Completada")
                
                # --- SECCIÓN 1: INTERVINIENTES ---
                st.subheader("👥 Intervinientes (Texto Literal)")
                st.caption("Copia este bloque para pegar en tu software de gestión:")
                st.text_area(
                    label="intervinientes",
                    value=datos.get("intervinientes", "No detectado"),
                    height=200,
                    label_visibility="collapsed"
                )
                
                # --- SECCIÓN 2: FINCAS ---
                st.subheader("🏡 Descripción de Fincas (Texto Literal)")
                st.caption("Descripción completa, linderos y referencias:")
                st.text_area(
                    label="fincas",
                    value=datos.get("fincas", "No detectado"),
                    height=300,
                    label_visibility="collapsed"
                )
                
                # --- SECCIÓN 3: DOCUMENTO COMPLETO ---
                with st.expander("📄 Ver Documento Completo Limpio"):
                    st.text_area(
                        label="completo",
                        value=datos.get("texto_completo", "No detectado"),
                        height=600,
                        label_visibility="collapsed"
                    )

            except Exception as e:
                st.error(f"❌ Ocurrió un error: {str(e)}")
                if "404" in str(e):
                    st.warning("⚠️ Consejo: Ve a 'Manage app' -> 'Reboot app' para actualizar las librerías.")
