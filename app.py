import re

def limpiar_texto_registral(texto_crudo):
    """
    Traducción a Python de tu lógica de limpieza JavaScript v7.2
    """
    if not texto_crudo:
        return ""

    # 1. LISTA NEGRA (TIMBRES Y SELLOS)
    marcadores_timbre = [
        "TIMBRE DEL ESTADO", "PAPEL EXCLUSIVO", "DOCUMENTOS NOTARIALES",
        "CLASE 8", "CLASE 6", "CLASE 4", "0,15 €", "0,03 €", "EUROS",
        "R.C.M.FN", "TU19", "TU20", "TU21", "TU22", "TU23", "TU24", "TU25"
    ]

    lineas_limpias = []
    
    # Procesamos línea a línea para quitar los timbres
    for linea in texto_crudo.split('\n'):
        linea_upper = linea.upper()
        es_timbre = False
        
        # Filtro 1: Marcadores explícitos
        for marcador in marcadores_timbre:
            if marcador in linea_upper:
                es_timbre = True
                break
        
        # Filtro 2: Códigos sueltos (Ej: A45H7...)
        # Tu regex JS era: /^[A-Z0-9]{5,25}\s*$/
        if re.match(r'^[A-Z0-9]{5,25}\s*$', linea.strip()):
            es_timbre = True

        if not es_timbre:
            lineas_limpias.append(linea)

    texto = "\n".join(lineas_limpias)

    # 2. PULIDO FINAL (Tus reemplazos regex)
    
    # Quitar guiones de separación de sílabas al final de línea
    texto = re.sub(r'-\s+', '', texto)
    
    # Unificar saltos de línea (convertir saltos simples en espacios, mantener dobles)
    # Esta parte es delicada en Python, una aproximación segura para escrituras:
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto) 
    
    # Quitar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto)
    
    # Arreglar puntuación pegada
    texto = re.sub(r'\s+([,.:;)])', r'\1', texto)
    texto = re.sub(r'(\()\s+', r'\1', texto)
    
    # Barras
    texto = re.sub(r'\s+\/\s+', '/', texto)
    
    # Punto y seguido vs Punto y aparte (Detectar mayúscula después de punto)
    # Tu regex: replace(/(\.)\s+([A-ZÁÉÍÓÚÑ])/g, '$1\n\n$2')
    texto = re.sub(r'(\.)\s+([A-ZÁÉÍÓÚÑ])', r'\1\n\n\2', texto)

    # 3. RESALTAR PALABRAS CLAVE (CABECERAS)
    titulos = ["ESCRITURA", "COMPARECEN", "INTERVIENEN", "EXPONEN", "OTORGAN"]
    for t in titulos:
        texto = re.sub(rf'({t})', r'\n\n\1', texto)

    return texto.strip()
