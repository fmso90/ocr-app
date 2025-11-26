import streamlit as st
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Extractor Registral AI",
    page_icon="🏘️",
    layout="wide", # Usamos pantalla ancha para ver datos mejor
    initial_sidebar_state="collapsed"
)

# CSS Dark Mode Premium
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    div.block-container {
        max-width: 1200px;
        padding-top: 2rem;
    }
    /* Tarjetas de datos */
    .data-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    h1, h2, h3 { color: #fff !important; font-family: 'Helvetica Neue', sans-serif; }
    .label { color: #888; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; }
    .value { color: #fff; font-size: 1.1em; font-weight: 500; margin-bottom: 10px; }
    .highlight { color: #4ade80; font-weight: bold; }
    
    /* Botones */
    div.stButton > button {
        background-color: #fff; color: #000; border: none; font-weight: 700;
        width: 100%; padding: 0.8rem;
    }
    div.stButton > button:hover { background-color: #ccc; }
    
    /* Ocultar elementos */
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN DE GEMINI ---
def configurar_gemini(api_key):
    genai.configure(api_key=api_key)
    # Usamos Gemini 1.5 Flash: Rápido, barato y ventana de contexto enorme (lee todo el PDF)
    return genai.GenerativeModel('gemini-1.5-flash')

def limpiar_json_markdown(texto):
    """Limpia si la IA devuelve ```json ... ```"""
    texto = texto.replace("```json", "").replace("```", "").strip()
    return texto

# --- 3. EL CEREBRO (PROMPT DE EXTRACCIÓN) ---
def extraer_datos_inteligentes(modelo, archivo_bytes):
    
    # Instrucción Maestra para el Oficial Virtual
    prompt = """
    Actúa como un Oficial de Registro de la Propiedad experto. 
    Analiza la escritura adjunta (PDF) y extrae la información clave ignorando totalmente los sellos, 
    timbres, marcas de agua y texto administrativo irrelevante ("NIHIL PRIUS FIDE", etc.).

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
                "superficie": "Superficie en m2 o Ha",
                "linderos": "Norte..., Sur..."
            }
        ],
        "cargas": "Resumen breve de cargas (Hipoteca, servidumbres) o 'Libre de cargas'"
    }
    
    Si algún dato no aparece, pon "No consta". Se preciso con los DNI y Nombres.
    """

    # Enviamos el PDF (bytes) y el texto (prompt) a la vez
    try:
        # Gemini soporta bytes de PDF directamente como 'mime_type': 'application/pdf'
        response = modelo.generate_content([
            {'mime_type': 'application/pdf', 'data': archivo_bytes},
            prompt
        ])
        return response.text
    except Exception as e:
        return None

# --- 4. INTERFAZ GRÁFICA ---

st.title("EXTRACTOR DE DATOS REGISTRAL")
st.markdown("### 🤖 Análisis Inteligente de Escrituras con Gemini AI")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key de Google en Secrets.")
    st.stop()

model = configurar_gemini(st.secrets["GOOGLE_API_KEY"])

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])

st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("EXTRAER DATOS ESTRUCTURADOS"):
        with st.spinner('🧠 La IA está leyendo y analizando la escritura...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada a la IA
                resultado_crudo = extraer_datos_inteligentes(model, bytes_data)
                
                if resultado_crudo:
                    # Parsear JSON
                    json_str = limpiar_json_markdown(resultado_crudo)
                    datos = json.loads(json_str)
                    
                    st.success("✅ Extracción Completada")
                    
                    # --- MOSTRAR DATOS EN TARJETAS ---
                    
                    # 1. Cabecera del Documento
                    doc = datos.get("documento", {})
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Notario", doc.get("notario", "-"))
                    col2.metric("Fecha", doc.get("fecha", "-"))
                    col3.metric("Protocolo", doc.get("protocolo", "-"))
                    col4.metric("Ciudad", doc.get("ciudad", "-"))
                    
                    st.markdown("---")
                    
                    # 2. Intervinientes (Dos columnas: Vendedores / Compradores)
                    st.subheader("👥 Intervinientes")
                    intervinientes = datos.get("intervinientes", [])
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("<div class='data-card'><h4>VENDEDORES</h4>", unsafe_allow_html=True)
                        for p in intervinientes:
                            if "VENDEDOR" in p.get("rol", "").upper():
                                st.markdown(f"**{p['nombre']}**<br><span style='color:#aaa'>{p['dni']}</span>", unsafe_allow_html=True)
                                st.markdown("<hr style='margin:5px 0; border-color:#444'>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    with c2:
                        st.markdown("<div class='data-card'><h4>COMPRADORES</h4>", unsafe_allow_html=True)
                        for p in intervinientes:
                            if "COMPRADOR" in p.get("rol", "").upper():
                                st.markdown(f"**{p['nombre']}**<br><span style='color:#aaa'>{p['dni']}</span>", unsafe_allow_html=True)
                                st.markdown("<hr style='margin:5px 0; border-color:#444'>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 3. Fincas
                    st.subheader("🏡 Fincas y Propiedades")
                    for finca in datos.get("fincas", []):
                        st.markdown(f"""
                        <div class='data-card'>
                            <div style='display:flex; justify-content:space-between;'>
                                <div><span class='label'>REF. CATASTRAL:</span> <span class='highlight'>{finca.get('referencia_catastral')}</span></div>
                                <div><span class='label'>Nº REGISTRAL:</span> <span class='value'>{finca.get('numero_registral')}</span></div>
                            </div>
                            <br>
                            <div><span class='label'>DESCRIPCIÓN:</span><br>{finca.get('descripcion_corta')}</div>
                            <br>
                            <div><span class='label'>SUPERFICIE:</span> {finca.get('superficie')} | <span class='label'>MUNICIPIO:</span> {finca.get('municipio')}</div>
                            <br>
                            <div style='font-size:0.9em; color:#888'><i>Linderos: {finca.get('linderos')}</i></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # 4. Cargas
                    st.subheader("⚠️ Estado de Cargas")
                    st.info(datos.get("cargas", "No consta información"))
                    
                    # 5. JSON Puro (Para copiar)
                    with st.expander("Ver JSON Técnico (Para copiar a otro software)"):
                        st.json(datos)

                else:
                    st.error("La IA no pudo procesar el documento. Intenta de nuevo.")

            except Exception as e:
                st.error(f"Error técnico: {e}")
