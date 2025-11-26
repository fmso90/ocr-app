import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(
    page_title="Digitalizador Registral Pro",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Fondo oscuro */
    .stApp { background-color: #0e1117; }
    
    /* Tarjeta verde para listado de fincas */
    .finca-card {
        background-color: #1e2329;
        border-left: 5px solid #10b981;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 6px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Papel virtual para textos literales */
    .doc-paper {
        background-color: #fdfbf7;
        color: #1f1f1f;
        padding: 25px;
        border-radius: 4px;
        font-family: 'Georgia', serif;
        font-size: 15px;
        line-height: 1.6;
        white-space: pre-wrap;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #ccc;
    }

    /* Títulos y botones */
    h1, h2, h3 { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; }
    .stButton > button { width: 100%; font-weight: bold; border-radius: 6px; padding: 0.6rem; }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA INTELIGENTE ---
def transcribir_y_extraer(api_key, archivo_bytes):
    genai.configure(api_key=api_key)
    
    # USAMOS DIRECTAMENTE EL MODELO MÁS POTENTE Y ACTUAL
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    
    prompt = """
    Actúa como Oficial de Registro. Tu misión es DIGITALIZAR esta escritura.

    1. TRANSCRIPCIÓN LITERAL:
       - Copia el texto palabra por palabra.
       - ELIMINA SOLO la "basura" de los sellos (timbres, precios, lemas en latín) que interrumpe las frases.
       - NO borres nombres de notarios ni lugares si son parte del texto legal.

    2. EXTRACCIÓN ESTRUCTURADA:
       - Genera un listado resumen de las fincas.

    Devuelve un JSON exacto con:
    {
        "texto_completo_limpio": "El texto ÍNTEGRO de todo el documento unido, sin sellos.",
        
        "listado_fincas": [
            {
                "registro": "Nº Finca Registral", 
                "municipio": "Municipio", 
                "precio": "Valor (con moneda) o 'Sin valoración'"
            }
        ],
        
        "intervinientes_literal": "Texto literal del bloque de comparecencia.",
        "fincas_literal": "Texto literal de la descripción de las fincas."
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
st.title("DIGITALIZADOR REGISTRAL | PRO")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

uploaded_file = st.file_uploader("Sube la escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🧠 Gemini Pro está leyendo y estructurando el documento...'):
            try:
                bytes_data = uploaded_file.read()
                
                # Llamada directa al modelo hardcodeado
                resultado = transcribir_y_extraer(st.secrets["GOOGLE_API_KEY"], bytes_data)
                datos = json.loads(limpiar_json(resultado))
                
                st.success("✅ Proceso Terminado")
                
                # --- A. DESCARGA COMPLETA (PRIORIDAD) ---
                st.subheader("📂 Documento Completo")
                texto_full = datos.get("texto_completo_limpio", "")
                
                col_dl, col_view = st.columns([1, 3])
                with col_dl:
                    st.download_button(
                        label="⬇️ DESCARGAR TXT COMPLETO",
                        data=texto_full,
                        file_name="escritura_completa.txt",
                        mime="text/plain",
                        type="primary" # Botón destacado
                    )
                with col_view:
                    with st.expander("Vista previa del texto completo"):
                        st.text_area("Full Text", value=texto_full, height=200)

                st.markdown("---")

                # --- B. LISTADO DE FINCAS (TU FORMATO) ---
                st.subheader("🏡 Listado de Fincas")
                
                lista_fincas = datos.get("listado_fincas", [])
                txt_listado = ""
                
                if lista_fincas:
                    # Generar string para descarga y mostrar tarjetas
                    for f in lista_fincas:
                        # Formato visual
                        st.markdown(f"""
                        <div class='finca-card'>
                            <span style='float:right; color:#4ade80; font-weight:bold'>{f.get('precio', '0')}</span>
                            <b>Finca {f.get('registro', '?')}</b> de {f.get('municipio', '?')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Formato texto para el archivo: "1-3456 de Almadén, 345 euros"
                        txt_listado += f"{f.get('registro', '?')} de {f.get('municipio', '?')}, {f.get('precio', '?')}.\n"
                    
                    st.download_button("⬇️ Descargar Listado (.txt)", txt_listado, "listado_fincas.txt")
                else:
                    st.info("No se detectaron fincas en el resumen.")

                st.markdown("---")

                # --- C. LITERALES (INTERVINIENTES Y DESCRIPCIONES) ---
                c1, c2 = st.columns(2)
                
                with c1:
                    st.subheader("👥 Intervinientes")
                    txt_int = datos.get("intervinientes_literal", "")
                    st.download_button("⬇️ Descargar", txt_int, "intervinientes.txt")
                    st.markdown(f"<div class='doc-paper'>{txt_int}</div>", unsafe_allow_html=True)

                with c2:
                    st.subheader("📜 Descripciones")
                    txt_desc = datos.get("fincas_literal", "")
                    st.download_button("⬇️ Descargar", txt_desc, "descripciones_fincas.txt")
                    st.markdown(f"<div class='doc-paper'>{txt_desc}</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "404" in str(e):
                    st.warning("El modelo 'gemini-1.5-pro-latest' no responde. Verifica tu API Key.")
