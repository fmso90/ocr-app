import streamlit as st
import time

# --- CONFIGURACIÓN DE PÁGINA (Lo primero de todo) ---
st.set_page_config(
    page_title="Digitalizador Registral",
    page_icon="⚖️",
    layout="wide", # Usamos 'wide' para que la landing respire mejor
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS PARA QUE SE VEA PROFESIONAL ---
st.markdown("""
<style>
    /* Ocultar menú de hamburguesa y footer de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Estilo para el botón principal (CTA) */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    
    /* Títulos centrados */
    h1, h2, h3 {
        text-align: center; 
    }
    
    /* Cajas de precios */
    .price-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #d1d5db;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DEL ESTADO (Navegación entre páginas) ---
if "page" not in st.session_state:
    st.session_state.page = "landing"

def navigate_to(page):
    st.session_state.page = page
    st.rerun()

# ==========================================
# 🏠 PÁGINA 1: LANDING PAGE (Venta)
# ==========================================
def show_landing():
    # --- HERO SECTION (Cabecera) ---
    st.write("##") # Espacio en blanco
    st.title("⚖️ Digitalizador Registral IA")
    st.subheader("De oficial de registro, para oficiales de registro.")
    st.markdown("<h4 style='text-align: center; color: gray;'>Deja de copiar manualmente. Transcribe escrituras en segundos, sin errores y sin datos protegidos.</h4>", unsafe_allow_html=True)
    
    st.write("---")

    # --- COLUMNAS PRINCIPALES ---
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### ❌ El Problema")
        st.error("""
        * **Pérdida de tiempo:** Copiar folios enteros a mano.
        * **Riesgo RGPD:** Copiar por error la cláusula de Protección de Datos.
        * **Formato Sucio:** Timbres, sellos y saltos de línea molestos.
        """)
        
        st.write("##") # Espacio
        
        st.markdown("### ✅ La Solución")
        st.success("""
        * **Transcripción Literal:** IA entrenada para leer lenguaje jurídico.
        * **Corte de Seguridad:** Detecta y corta automáticamente antes de "Protección de Datos".
        * **Limpieza Total:** Elimina el ruido visual (timbres, euros, sellos).
        """)

    with col2:
        # Aquí simulamos una imagen o una demo
        st.info("💡 **¿Cómo funciona?**")
        st.markdown("""
        1. Subes el PDF de la escritura.
        2. Nuestra IA (Gemini Pro) lee y extrae la parte dispositiva.
        3. Obtienes un texto limpio listo para copiar a tu software de gestión.
        """)
        
        # ESPACIO PARA EL BOTÓN DE ACCIÓN
        st.write("##")
        st.write("##")
        if st.button("🚀 VER PLANES Y PRECIOS", type="primary"):
            navigate_to("subscription")

    st.write("---")
    
    # --- AUTORIDAD (Quién eres tú) ---
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: #262730; border-radius: 10px; color: white;">
            <small>CREADO POR</small><br>
            <strong>Felipe | F90</strong><br>
            <em>Profesional del Registro de la Propiedad & Editor Certificado Capture One.</em><br>
            <br>
            "He creado la herramienta que yo necesitaba usar cada día en Almadén."
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 💳 PÁGINA 2: SUSCRIPCIÓN (Precios)
# ==========================================
def show_subscription():
    st.title("💎 Elige tu Plan")
    if st.button("⬅️ Volver al inicio"):
        navigate_to("landing")
        
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Plan Mensual
    with col2:
        st.markdown("""
        <div style="background-color: #d1fae5; padding: 20px; border-radius: 10px; border: 2px solid #10b981; text-align: center; color: black;">
            <h3>PLAN PROFESIONAL</h3>
            <h1 style="color: #047857;">19,90€ <span style="font-size: 1rem;">/mes</span></h1>
            <ul style="text-align: left; list-style-position: inside;">
                <li>✅ Transcripciones Ilimitadas</li>
                <li>✅ Corte automático RGPD</li>
                <li>✅ Soporte prioritario</li>
                <li>✅ Cancelación cuando quieras</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("##")
        
        # AQUÍ VA TU ENLACE DE LEMON SQUEEZY
        link_pago = "https://tu-tienda.lemonsqueezy.com/checkout/buy/..." 
        
        st.link_button("👉 SUSCRIBIRSE AHORA", link_pago, type="primary", use_container_width=True)
        
        st.caption("Al pagar, recibirás una **Clave de Licencia** en tu email. Úsala para acceder a la herramienta.")

    st.write("---")
    
    # Zona de Login si ya tiene clave
    st.markdown("### ¿Ya tienes tu licencia?")
    col_login, _ = st.columns([1, 2])
    with col_login:
        password = st.text_input("Introduce tu Licencia aquí", type="password")
        if st.button("ENTRAR AL SISTEMA"):
            # AQUÍ IRÍA TU LÓGICA DE VALIDACIÓN (validate_lemon_license)
            # Para este ejemplo, usamos una clave simple o simulamos éxito
            if password == "F90-ADMIN" or len(password) > 5:
                st.session_state.authenticated = True
                navigate_to("app")
            else:
                st.error("Licencia no válida")

# ==========================================
# ⚙️ PÁGINA 3: LA APLICACIÓN (Tu herramienta)
# ==========================================
def show_app():
    st.title("📂 Tu Espacio de Trabajo")
    
    # Barra superior con botón de salir
    col_saludo, col_logout = st.columns([4, 1])
    with col_saludo:
        st.success("Licencia Activa ✅")
    with col_logout:
        if st.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            navigate_to("landing")
            
    st.write("---")
    
    # TU CÓDIGO ORIGINAL DE PROCESAMIENTO
    uploaded_file = st.file_uploader("Arrastra aquí tu escritura (PDF)", type=['pdf'])
    
    if uploaded_file:
        st.info("📄 Archivo cargado correctamente: " + uploaded_file.name)
        
        if st.button("⚡ TRANSCRIBIR Y LIMPIAR"):
            with st.spinner("La IA está leyendo el documento..."):
                time.sleep(2) # Simulación de espera
                
                # Aquí iría tu llamada real a Gemini
                # resultado = transcribir_con_corte(...)
                
                st.subheader("Resultado:")
                texto_simulado = "EN SU VIRTUD, OTORGAN:\n\nPRIMERO.- COMPRAVENTA.\nDon Fulanito vende a Doña Menganita..."
                st.text_area("Texto listo para copiar:", value=texto_simulado, height=300)
                st.success("✅ Texto limpio de protección de datos.")

# ==========================================
# 🚦 CONTROLADOR DE TRÁFICO (ROUTER)
# ==========================================

# 1. Comprobar si está autenticado para ir directo a la app
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 2. Decidir qué página mostrar
if st.session_state.authenticated:
    show_app()
else:
    if st.session_state.page == "landing":
        show_landing()
    elif st.session_state.page == "subscription":
        show_subscription()
