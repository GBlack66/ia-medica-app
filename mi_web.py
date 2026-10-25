import streamlit as st
from google import genai
import PyPDF2
import io

# 1. Configuración de la página
st.set_page_config(page_title="IA Médica", layout="wide")
st.title("📚 Mi Cuaderno Médico")

# 2. Inicializar variables de memoria
if "cliente" not in st.session_state:
    st.session_state.cliente = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
if "fuentes_texto" not in st.session_state:
    st.session_state.fuentes_texto = ""
if "mensajes_visuales" not in st.session_state:
    st.session_state.mensajes_visuales = []
if "mostrar_config_presentacion" not in st.session_state:
    st.session_state.mostrar_config_presentacion = False

# --- PANEL DE FUENTES (BARRA LATERAL) ---
st.sidebar.title("📄 Panel de Fuentes")
st.sidebar.write("Sube tus apuntes o PDFs. La IA los leerá temporalmente.")

archivos_subidos = st.sidebar.file_uploader("Cargar documentos (PDF)", type=["pdf"], accept_multiple_files=True)

if archivos_subidos:
    texto_extraido = ""
    for archivo in archivos_subidos:
        lector_pdf = PyPDF2.PdfReader(io.BytesIO(archivo.read()))
        for pagina in lector_pdf.pages:
            texto_extraido += pagina.extract_text() + "\n"
    st.session_state.fuentes_texto = texto_extraido
    st.sidebar.success(f"{len(archivos_subidos)} documento(s) procesado(s) en memoria.")

# --- PANEL DE ESTUDIO (BOTONES SUPERIORES) ---
st.write("### Generador de Material")
col1, col2, col3, col4 = st.columns(4)

prompt_rapido = None
texto_usuario_rapido = ""

if col1.button("📺 Presentación"):
    st.session_state.mostrar_config_presentacion = not st.session_state.mostrar_config_presentacion

if col2.button("🗂️ Mapa mental"):
    st.warning("Función de mapa mental en desarrollo.")

if col3.button("📇 Tarjetas didácticas"):
    if not st.session_state.fuentes_texto:
        st.error("Primero debes subir al menos un documento en el Panel de Fuentes.")
    else:
        texto_usuario_rapido = "Genera 5 tarjetas didácticas."
        prompt_rapido = f"Basado EXCLUSIVAMENTE en estas fuentes: {st.session_state.fuentes_texto[:5000]}... \nGenera 5 flashcards para Anki (Pregunta/Respuesta) sin casos clínicos."

if col4.button("❓ Cuestionario"):
    if not st.session_state.fuentes_texto:
        st.error("Primero debes subir al menos un documento en el Panel de Fuentes.")
    else:
        texto_usuario_rapido = "Genera un cuestionario de opción múltiple."
        prompt_rapido = f"Basado EXCLUSIVAMENTE en estas fuentes: {st.session_state.fuentes_texto[:5000]}... \nGenera un cuestionario de 3 preguntas de opción múltiple con su respuesta correcta al final."

# --- EJECUTAR BOTONES RÁPIDOS ---
if prompt_rapido:
    st.session_state.mensajes_visuales.append({"rol": "user", "texto": texto_usuario_rapido})
    try:
        respuesta = st.session_state.cliente.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt_rapido
        )
        st.session_state.mensajes_visuales.append({"rol": "assistant", "texto": respuesta.text})
    except Exception as e:
        st.error(f"Fallo en la API de Google: {e}")

# --- MENÚ DE PRESENTACIÓN ---
if st.session_state.mostrar_config_presentacion:
    with st.expander("📺 Personalizar presentación de diapositivas", expanded=True):
        col_form1, col_form2 = st.columns(2)
        
        formato = col_form1.radio("Formato", ["Presentación detallada", "Diapositivas del presentador"])
        idioma = col_form2.selectbox("Seleccionar idioma", ["español", "inglés"])
        duracion = col_form2.selectbox("Duración", ["Predeterminada", "Corto", "Largo"])
        
        descripcion = st.text_area("Describe la presentación que quieres crear", placeholder="Ej: Crea una presentación sobre fisiopatología...")
        
        if st.button("Generar ahora", type="primary"):
            if not st.session_state.fuentes_texto:
                st.error("Primero debes subir al menos un documento en el Panel de Fuentes.")
            else:
                prompt_presentacion = f"""
                Actúa como un creador de presentaciones médicas. 
                Utiliza ÚNICAMENTE la siguiente información de mis fuentes: {st.session_state.fuentes_texto[:5000]}...
                
                Instrucciones específicas:
                - Formato: {formato}
                - Idioma: {idioma}
                - Duración: {duracion}
                - Enfoque: {descripcion}
                
                Genera la estructura de las diapositivas separadas por '---' indicando Título y Puntos clave. No uses casos clínicos.
                """
                st.session_state.mensajes_visuales.append({"rol": "user", "texto": "Genera una presentación con mis configuraciones."})
                try:
                    respuesta = st.session_state.cliente.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt_presentacion
                    )
                    st.session_state.mensajes_visuales.append({"rol": "assistant", "texto": respuesta.text})
                    st.session_state.mostrar_config_presentacion = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Fallo en la API de Google: {e}")

# --- CHAT / RESULTADOS ---
st.divider()
st.write("### Resultados y Chat")
for msg in st.session_state.mensajes_visuales:
    with st.chat_message(msg["rol"]):
        st.markdown(msg["texto"])

pregunta_usuario = st.chat_input("Hazle una pregunta a tus documentos...")

if pregunta_usuario:
    contexto = f"Basado en estos documentos: {st.session_state.fuentes_texto[:5000]}... \nResponde: " if st.session_state.fuentes_texto else ""
    
    with st.chat_message("user"):
        st.markdown(pregunta_usuario)
    st.session_state.mensajes_visuales.append({"rol": "user", "texto": pregunta_usuario})
    
    try:
        with st.chat_message("assistant"):
            respuesta = st.session_state.cliente.models.generate_content(
                model='gemini-3.8-flash',
                contents=contexto + pregunta_usuario
            )
            st.markdown(respuesta.text)
        st.session_state.mensajes_visuales.append({"rol": "assistant", "texto": respuesta.text})
    except Exception as e:
        st.error(f"Fallo en la API de Google: {e}")