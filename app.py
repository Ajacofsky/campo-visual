import streamlit as st
import cv2
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image

st.set_page_config(layout="wide")
st.title("🎯 Calibración por Clic (Centro y 60°)")

# Inicializar estados de clics
if "centro" not in st.session_state:
    st.session_state.centro = None
if "punto_60" not in st.session_state:
    st.session_state.punto_60 = None

def reset_puntos():
    st.session_state.centro = None
    st.session_state.punto_60 = None

st.sidebar.button("Limpiar Clics", on_click=reset_puntos)

file = st.sidebar.file_uploader("Subir Campo Visual", type=['jpg', 'png', 'jpeg'])

if file:
    img_pil = Image.open(file)
    w, h = img_pil.size
    
    st.write("### 🖱️ Instrucciones:")
    if st.session_state.centro is None:
        st.info("Hacé clic en el **CENTRO** exacto del gráfico.")
    elif st.session_state.punto_60 is None:
        st.info("Ahora hacé clic sobre la marca de **60°** (en el eje horizontal).")
    else:
        st.success("Calibración completada. Podés ajustar con los clics de nuevo si es necesario.")

    # Mostrar imagen interactiva
    value = streamlit_image_coordinates(img_pil, key="coords")

    if value:
        x, y = value["x"], value["y"]
        
        # Lógica de guardado de clics
        if st.session_state.centro is None:
            st.session_state.centro = (x, y)
            st.rerun()
        elif st.session_state.punto_60 is None:
            st.session_state.punto_60 = (x, y)
            st.rerun()

    # Procesar y dibujar si tenemos los datos
    if st.session_state.centro:
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        cx, cy = st.session_state.centro
        
        # Dibujar cruz de centro
        cv2.drawMarker(img_cv, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 30, 3)
        
        if st.session_state.punto_60:
            px60, py60 = st.session_state.punto_60
            # Radio total (distancia entre clics)
            r60 = int(np.sqrt((px60 - cx)**2 + (py60 - cy)**2))
            paso = r60 / 6.0
            
            # Dibujar anillos rojos equidistantes
            for i in range(1, 7):
                r = int(i * paso)
                cv2.circle(img_cv, (cx, cy), r, (0, 0, 255), 4)
                cv2.putText(img_cv, f"{i*10}", (cx + r + 5, cy - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Ejes
            cv2.line(img_cv, (cx, 0), (cx, h), (0, 0, 255), 2)
            cv2.line(img_cv, (0, cy), (w, cy), (0, 0, 255), 2)

        # Mostrar resultado final procesado
        st.image(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB), use_container_width=True)

else:
    st.info("Por favor, subí la imagen para empezar la calibración táctil.")
