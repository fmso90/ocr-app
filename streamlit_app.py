import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Extractor Registral AI (G3)", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .data-card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
    h1, h2, h3 { color: #fff !important; }
    div.stButton > button { background-color: #fff; color: #000; border: none; font-weight: 700; width: 100%; padding: 0.8rem; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN GEMINI 3 ---
def configurar_gemini(api_key):
    genai.configure(api_key=api_key)
    
    # CONFIGURACIÓN ESPECÍFICA PARA GEMINI 3
    # Usamos generation_config para darle "presupuesto de pensamiento" si fuera necesario
    generation_config = {
        "temperature": 0.1, # Muy bajo para máxima precisión legal
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json", # Forzamos JSON nativo
    }
    
    # Invocamos al modelo PREVIEW
    return genai.GenerativeModel(
        model_name='models/gemini-3-pro-preview', # La joya de la corona
        generation_config=generation_config
    )

# --- 3. EXTRACCIÓN ---
def extraer_datos_inteligentes(modelo, archivo_bytes):
    prompt = """
    Eres un Oficial de Registro de la Propiedad de élite.
    Tu misión es extraer datos con precisión quirúrgica del PDF adjunto.
    
    INSTRUCCIONES CRÍTICAS:
    1. Ignora sellos, timbres ("TIMBRE DEL ESTADO", "NIHIL PRIUS") y texto administrativo.
    2. Si un dato no está claro, pon null. No inventes.
    3. Extrae la REFERENCIA CATASTRAL y el Nº DE FINCA con total exactitud.
    
    Devuelve el JSON cumpliendo este esquema (sin markdown, solo JSON):
    {
        "documento": {
            "notario": "Nombre completo",
            "fecha": "DD/MM/AAAA",
            "protocolo": "Número",
            "ciudad": "Ciudad"
        },
        "intervinientes": [
            {
                "rol": "VENDEDOR / COMPRADOR",
                "nombre": "Nombre completo",
                "dni": "DNI/NIF",
                "participacion": "% propiedad"
            }
        ],
        "fincas": [
            {
                "numero_registral": "Número",
                "referencia_catastral": "Ref Catastral",
                "municipio": "Municipio",
                "descripcion": "Descripción breve",
                "superficie": "Superficie",
                "linderos": "Norte, Sur, Este, Oeste"
            }
        ],
        "cargas": "Resumen de cargas o 'Libre'"
    }
    """
    
    response = modelo.generate_content([
        {'mime_type': 'application/pdf', 'data': archivo_bytes},
        prompt
    ])
    return response.text

# --- 4. INTERFAZ ---
st.title("EXTRACTOR REGISTRAL | GEMINI 3 PRO")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta la API Key en los Secrets.")
    st.stop()

# Manejo de errores de conexión con el modelo nuevo
try:
    model = configurar_gemini(st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error configurando Gemini 3: {e}")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("ANALIZAR CON GEMINI 3"):
        with st.spinner('✨ Gemini 3 está razonando sobre el documento...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada a la IA
                resultado_json = extraer_datos_inteligentes(model, bytes_data)
                
                # Al usar response_mime_type="application/json", la respuesta ya viene limpia
                datos = json.loads(resultado_json)
                
                st.success("✅ Análisis de Alta Precisión Completado")
                
                # --- VISUALIZACIÓN ---
                doc = datos.get("documento", {})
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Notario", doc.get("notario", "-"))
                c2.metric("Fecha", doc.get("fecha", "-"))
                c3.metric("Protocolo", doc.get("protocolo", "-"))
                c4.metric("Ciudad", doc.get("ciudad", "-"))
                
                st.markdown("---")
                
                st.subheader("👥 Intervinientes")
                col_ven, col_comp = st.columns(2)
                with col_ven:
                    st.markdown("#### VENDEDORES")
                    for p in datos.get("intervinientes", []):
                        if "VENDEDOR" in p.get("rol", "").upper():
                            st.info(f"**{p.get('nombre')}**\n\n🆔 {p.get('dni')}")
                with col_comp:
                    st.markdown("#### COMPRADORES")
                    for p in datos.get("intervinientes", []):
                        if "COMPRADOR" in p.get("rol", "").upper():
                            st.success(f"**{p.get('nombre')}**\n\n🆔 {p.get('dni')}")

                st.subheader("🏡 Fincas")
                for f in datos.get("fincas", []):
                    with st.expander(f"Finca Registral: {f.get('numero_registral', 'S/N')} - {f.get('municipio')}", expanded=True):
                        st.markdown(f"**Ref. Catastral:** `{f.get('referencia_catastral')}`")
                        st.write(f"**Descripción:** {f.get('descripcion')}")
                        st.write(f"**Superficie:** {f.get('superficie')}")
                        st.caption(f"Linderos: {f.get('linderos')}")

                st.subheader("⚠️ Cargas")
                st.warning(datos.get("cargas", "No consta"))
                
                with st.expander("Ver JSON Técnico"):
                    st.json(datos)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("⚠️ Tu API Key no tiene acceso a 'Gemini 3 Preview' o el modelo no está disponible en tu región. Prueba cambiando en el código a 'models/gemini-1.5-pro'.")
                elif "429" in str(e):
                    st.warning("⚠️ Límite de cuota excedido. Los modelos Preview tienen límites más estrictos.")
