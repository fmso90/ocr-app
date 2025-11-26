import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Extractor Registral AI", page_icon="🏘️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .data-card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px; }
    h1, h2, h3 { color: #fff !important; }
    div.stButton > button { background-color: #fff; color: #000; border: none; font-weight: 700; width: 100%; padding: 0.8rem; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN GEMINI ---
def configurar_gemini(api_key):
    genai.configure(api_key=api_key)
    # CAMBIO IMPORTANTE: Usamos 'gemini-1.5-flash-latest' que suele ser más estable en detección
    return genai.GenerativeModel('gemini-1.5-flash-latest')

def limpiar_json(texto):
    # Limpieza agresiva del formato Markdown que devuelve la IA
    return texto.replace("```json", "").replace("```", "").strip()

# --- 3. EXTRACCIÓN ---
def extraer_datos_inteligentes(modelo, archivo_bytes):
    prompt = """
    Actúa como un Oficial de Registro de la Propiedad experto. 
    Analiza la escritura adjunta (PDF) y extrae la información clave.
    
    Ignora totalmente los sellos, timbres y texto administrativo irrelevante ("NIHIL PRIUS FIDE", etc.).
    Céntrate en el contenido legal del documento.

    Devuelve ÚNICAMENTE un objeto JSON válido con la siguiente estructura exacta:
    {
        "documento": {
            "notario": "Nombre del notario",
            "fecha": "Fecha de otorgamiento",
            "protocolo": "Número de protocolo",
            "ciudad": "Lugar de firma"
        },
        "intervinientes": [
            {
                "rol": "VENDEDOR o COMPRADOR",
                "nombre": "Nombre completo",
                "dni": "DNI/NIF",
                "participacion": "% si se especifica"
            }
        ],
        "fincas": [
            {
                "numero_registral": "Número finca registral",
                "referencia_catastral": "Ref Catastral",
                "municipio": "Municipio",
                "descripcion_corta": "Ej: Rústica, secano, paraje La Vega...",
                "superficie": "Superficie",
                "linderos": "Norte..., Sur..."
            }
        ],
        "cargas": "Resumen breve de cargas o 'Libre de cargas'"
    }
    """
    
    response = modelo.generate_content([
        {'mime_type': 'application/pdf', 'data': archivo_bytes},
        prompt
    ])
    return response.text

# --- 4. INTERFAZ ---
st.title("EXTRACTOR DE DATOS REGISTRAL")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta la API Key en los Secrets.")
    st.stop()

# Configuración del modelo con manejo de errores
try:
    model = configurar_gemini(st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error al conectar con Google AI: {e}")
    st.stop()

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("EXTRAER DATOS"):
        with st.spinner('🧠 La IA está leyendo el documento...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada a la IA
                resultado_crudo = extraer_datos_inteligentes(model, bytes_data)
                
                # Procesar resultado
                json_str = limpiar_json(resultado_crudo)
                datos = json.loads(json_str)
                
                st.success("✅ Análisis Completado")
                
                # --- VISUALIZACIÓN ---
                
                # 1. Documento
                doc = datos.get("documento", {})
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Notario", doc.get("notario", "-"))
                c2.metric("Fecha", doc.get("fecha", "-"))
                c3.metric("Protocolo", doc.get("protocolo", "-"))
                c4.metric("Ciudad", doc.get("ciudad", "-"))
                
                st.markdown("---")
                
                # 2. Intervinientes
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

                # 3. Fincas
                st.subheader("🏡 Fincas")
                for f in datos.get("fincas", []):
                    with st.expander(f"Finca Registral: {f.get('numero_registral', 'S/N')} - {f.get('municipio')}", expanded=True):
                        st.markdown(f"**Ref. Catastral:** `{f.get('referencia_catastral')}`")
                        st.write(f"**Descripción:** {f.get('descripcion_corta')}")
                        st.write(f"**Superficie:** {f.get('superficie')}")
                        st.caption(f"Linderos: {f.get('linderos')}")

                # 4. Cargas
                st.subheader("⚠️ Cargas")
                st.warning(datos.get("cargas", "No consta"))
                
                # JSON Puro
                with st.expander("Ver JSON Técnico"):
                    st.json(datos)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("Consejo: Ve a 'Manage app' (abajo derecha) -> 'Reboot app' para que se instalen las nuevas librerías.")
