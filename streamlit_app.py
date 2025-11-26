import streamlit as st
import google.generativeai as genai
import json

# --- 1. CONFIGURACIÓN VISUAL PREMIUM ---
st.set_page_config(
    page_title="Digitalizador Registral Pro",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS PARA DISEÑO DE DOCUMENTO
st.markdown("""
<style>
    /* Fondo General Oscuro */
    .stApp { background-color: #0e1117; }
    
    /* Estilo Tarjeta de Datos (Resumen) */
    .resumen-card {
        background-color: #1e2329;
        border-left: 4px solid #4ade80;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Estilo "Papel" para Texto Literal */
    .doc-paper {
        background-color: #fdfbf7; /* Color hueso suave */
        color: #1f1f1f; /* Texto oscuro para contraste */
        padding: 25px;
        border-radius: 4px;
        border: 1px solid #ccc;
        font-family: 'Georgia', serif; /* Fuente tipo legal */
        font-size: 15px;
        line-height: 1.6;
        white-space: pre-wrap; /* Respetar saltos de línea */
        max-height: 400px;
        overflow-y: auto;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
    }

    /* Títulos */
    h1, h2, h3 { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Botones */
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
    
    /* Ocultar elementos extra */
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. GESTOR DE MODELOS ---
def obtener_modelos_disponibles(api_key):
    genai.configure(api_key=api_key)
    modelos_prioritarios = [
        "models/gemini-pro-latest", # El que te ha funcionado bien
        "models/gemini-1.5-pro",
        "models/gemini-1.5-pro-002",
        "models/gemini-1.5-flash"
    ]
    return modelos_prioritarios

# --- 3. CEREBRO DE EXTRACCIÓN ---
def transcribir_y_resumir(api_key, nombre_modelo, archivo_bytes):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(nombre_modelo)
    
    prompt = """
    Actúa como Oficial de Registro. Tu misión es doble: 
    1. TRANSCRIBIR LITERALMENTE las descripciones.
    2. EXTRAER un LISTADO RESUMEN de las fincas.

    INSTRUCCIONES DE LIMPIEZA:
    - Elimina SOLO la "basura" visual (sellos, timbres, encabezados repetitivos).
    - NO corrijas ortografía. NO uses viñetas en los literales.

    Devuelve un JSON con esta estructura exacta:
    {
        "intervinientes_literal": "Texto literal completo del bloque de comparecencia.",
        
        "listado_fincas_resumen": [
            {
                "id": "1", 
                "registro": "Nº Finca Registral", 
                "municipio": "Municipio", 
                "precio": "Valor o Precio (solo el número y moneda, ej: 345 euros). Si no consta, pon 'Sin valoración'."
            }
        ],
        
        "descripcion_fincas_literal": "Texto literal completo de la descripción de TODAS las fincas, una tras otra separadas por doble salto de línea.",
        
        "texto_completo_limpio": "El texto íntegro del documento unido y limpio."
    }
    """
    
    config = genai.types.GenerationConfig(
        temperature=0.0, # Cero creatividad
        response_mime_type="application/json"
    )

    response = model.generate_content(
        [{'mime_type': 'application/pdf', 'data': archivo_bytes}, prompt],
        generation_config=config
    )
    return response.text

def limpiar_json(texto):
    return texto.replace("```json", "").replace("```", "").strip()

# --- 4. INTERFAZ ---
st.title("DIGITALIZADOR REGISTRAL")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⛔ Falta API Key en Secrets.")
    st.stop()

# Selector de modelo
lista_modelos = obtener_modelos_disponibles(st.secrets["GOOGLE_API_KEY"])
modelo_elegido = st.selectbox("Motor IA:", lista_modelos, index=0)

uploaded_file = st.file_uploader("Sube escritura (PDF)", type=['pdf'])
st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

if uploaded_file:
    if st.button("PROCESAR DOCUMENTO"):
        with st.spinner('🏗️ Extrayendo datos y limpiando texto...'):
            try:
                bytes_data = uploaded_file.read()
                resultado = transcribir_y_resumir(st.secrets["GOOGLE_API_KEY"], modelo_elegido, bytes_data)
                datos = json.loads(limpiar_json(resultado))
                
                st.success("✅ Documento Digitalizado")
                
                # --- SECCIÓN 1: TEXTO COMPLETO (DESCARGA) ---
                st.markdown("### 1. Documento Completo")
                st.download_button(
                    label="⬇️ DESCARGAR TEXTO ÍNTEGRO LIMPIO (.TXT)",
                    data=datos.get("texto_completo_limpio", ""),
                    file_name="escritura_completa.txt",
                    mime="text/plain",
                    key="btn_full"
                )
                
                st.markdown("---")

                # --- SECCIÓN 2: LISTADO RESUMEN (VISUAL + DESCARGA) ---
                st.markdown("### 2. Listado Resumen de Fincas")
                
                # Crear texto formateado para el listado
                texto_listado = ""
                listado = datos.get("listado_fincas_resumen", [])
                
                if listado:
                    for f in listado:
                        linea = f"Finca {f.get('registro', '?')} de {f.get('municipio', '?')}, {f.get('precio', '0')}."
                        texto_listado += linea + "\n"
                        # Visualización en tarjetas
                        st.markdown(f"""
                        <div class='resumen-card'>
                            <b>🏡 Finca Registral:</b> {f.get('registro', '?')} <br>
                            <b>📍 Municipio:</b> {f.get('municipio', '?')} <br>
                            <b>💰 Valoración:</b> {f.get('precio', '?')}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No se detectaron fincas estructuradas.")

                st.download_button(
                    label="⬇️ DESCARGAR LISTADO RESUMEN (.TXT)",
                    data=texto_listado,
                    file_name="listado_fincas.txt",
                    mime="text/plain",
                    key="btn_list"
                )

                st.markdown("---")

                # --- SECCIÓN 3: DESCRIPCIONES LITERALES (VISUAL BONITA + DESCARGA) ---
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 3. Intervinientes (Literal)")
                    st.markdown(f"<div class='doc-paper'>{datos.get('intervinientes_literal', '')}</div>", unsafe_allow_html=True)
                    st.download_button("⬇️ Descargar Intervinientes", datos.get("intervinientes_literal", ""), "intervinientes.txt")

                with col2:
                    st.markdown("### 4. Descripciones Fincas (Literal)")
                    st.markdown(f"<div class='doc-paper'>{datos.get('descripcion_fincas_literal', '')}</div>", unsafe_allow_html=True)
                    st.download_button("⬇️ Descargar Descripciones", datos.get("descripcion_fincas_literal", ""), "descripciones.txt")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
