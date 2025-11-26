import streamlit as st
import google.generativeai as genai

st.title("🚑 Diagnóstico de Conexión")

# 1. Verificamos la clave
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ No detecto la API Key en los Secrets.")
    st.stop()
else:
    st.success("✅ API Key detectada.")

# 2. Configuramos la librería
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"❌ Error al configurar la clave: {e}")

# 3. Botón para listar modelos
if st.button("🔍 VERIFICAR MODELOS DISPONIBLES"):
    st.info("Preguntando a Google qué modelos tienes activos...")
    try:
        modelos = []
        for m in genai.list_models():
            # Filtramos solo los que sirven para generar texto
            if 'generateContent' in m.supported_generation_methods:
                modelos.append(m.name)
        
        if modelos:
            st.success("✅ Conexión exitosa. Tu clave tiene acceso a:")
            for modelo in modelos:
                st.code(modelo) # Copia el nombre que salga aquí
        else:
            st.warning("⚠️ Conectado, pero no aparecen modelos disponibles.")
            
    except Exception as e:
        st.error(f"❌ Error grave de conexión: {e}")
        st.write("Pista: Si el error dice '403', tu API Key no es válida o tiene restricciones.")
        st.write("Pista: Si el error dice 'module not found', falla el requirements.txt")
