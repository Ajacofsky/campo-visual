import streamlit as st
import cv2
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image

st.set_page_config(layout="wide")
st.title("🎯 Calibración por Clics (Centro y 60°)")

# --- INICIALIZACIÓN DE MEMORIA ---
if "puntos" not in st.session_state:
    st.session_state.puntos = []

def borrar_puntos():
    st.session_state.puntos = []

st.sidebar.button("🗑️ Borrar y Reintentar", on_click=borrar_puntos)

file = st.sidebar.file_uploader("Subir Campo Visual", type=['jpg', 'png', 'jpeg'])

if file:
    img_pil = Image.open(file)
    w, h = img_pil.size
    
    # Instrucciones dinámicas
    if len(st.session_state.puntos) == 0:
        st.info("📍 PASO 1: Hacé clic en el **CENTRO** del gráfico.")
    elif len(st.session_state.puntos) == 1:
        st.warning("📏 PASO 2: Hacé clic sobre la marca de **60°** (en el eje horizontal).")
    else:
        st.success("✅ Calibración lista. Usá el botón de la izquierda si necesitás corregir.")

    # Captura de coordenadas
    # Ajustamos el ancho para que sea cómodo clickear
    coords = streamlit_image_coordinates(img_pil, key="interaccion")

    if coords:
        nuevo_punto = (coords["x"], coords["y"])
        
        # Solo agregamos si el punto es nuevo y no tenemos ya los 2 necesarios
        if len(st.session_state.puntos) < 2:
            if not st.session_state.puntos or nuevo_punto != st.session_state.puntos[-1]:
                st.session_state.puntos.append(nuevo_punto)
                st.rerun()

    # --- PROCESAMIENTO Y DIBUJO ---
    # Convertimos para usar OpenCV
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    if len(st.session_state.puntos) >= 1:
        cx, cy = st.session_state.puntos[0]
        # Dibujamos el centro siempre
        cv2.drawMarker(img_cv, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 30, 3)

    if len(st.session_state.puntos) == 2:
        cx, cy = st.session_state.puntos[0]
        px60, py60 = st.session_state.puntos[1]
        
        # Calculamos radio basado en la distancia entre los dos clics
        r60 = int(np.sqrt((px60 - cx)**2 + (py60 - cy)**2))
        paso = r60 / 6.0
        
        # Dibujamos anillos rojos equidistantes
        for i in range(1, 7):
            r = int(i * paso)
            cv2.circle(img_cv, (cx, cy), r, (0, 0, 255), 4)
            cv2.putText(img_cv, f"{i*10}", (cx + r + 5, cy - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Ejes
        cv2.line(img_cv, (cx, 0), (cx, h), (0, 0, 255), 2)
        cv2.line(img_cv, (0, cy), (w, cy), (0, 0, 255), 2)

    # Mostrar la imagen con los cambios aplicados
    st.image(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB), use_container_width=True)

else:
    st.info("Subí la imagen para comenzar.")
