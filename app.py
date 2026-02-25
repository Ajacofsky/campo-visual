import streamlit as st
import cv2
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image

st.set_page_config(layout="wide")
st.title("📊 Peritaje: Calibración y Cálculo de Incapacidad")

# Memoria de clics
if "puntos" not in st.session_state:
    st.session_state.puntos = []

def reset():
    st.session_state.puntos = []

st.sidebar.button("🗑️ Reiniciar Todo", on_click=reset)
umbral = st.sidebar.slider("Sensibilidad de Negros", 0, 255, 120)
sensibilidad_area = st.sidebar.slider("Umbral de Área (Regla 70%)", 1, 100, 30, help="Si los cuadraditos son pequeños, usa un valor bajo (ej. 20-30%) para que los detecte")

file = st.sidebar.file_uploader("Subir Campo Visual", type=['jpg', 'png', 'jpeg'])

if file:
    img_pil = Image.open(file).convert("RGB")
    w, h = img_pil.size
    
    # --- FASE 1: CALIBRACIÓN ---
    if len(st.session_state.puntos) < 2:
        st.subheader("📍 Paso 1: Calibrar Centro y 60°")
        if len(st.session_state.puntos) == 0:
            st.info("Hacé clic en el **CENTRO** del gráfico.")
        else:
            st.warning("Ahora hacé clic en la marca de **60°**.")
        
        coords = streamlit_image_coordinates(img_pil, key="calibrar")
        if coords:
            p = (coords["x"], coords["y"])
            if not st.session_state.puntos or p != st.session_state.puntos[-1]:
                st.session_state.puntos.append(p)
                st.rerun()
    
    # --- FASE 2: DIBUJO Y CÁLCULO ---
    else:
        st.subheader("✅ Análisis de Sectores")
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, binaria = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY_INV)
        
        cx, cy = st.session_state.puntos[0]
        px60, py60 = st.session_state.puntos[1]
        r60 = int(np.sqrt((px60 - cx)**2 + (py60 - cy)**2))
        paso = r60 / 6.0
        
        puntos_perdidos = 0
        
        # 1. Analizar cada sector
        for i in range(1, 7): # 6 anillos
            r_ext = int(i * paso)
            r_int = int((i - 1) * paso)
            for s in range(12): # 12 sectores por anillo
                ang = s * 30
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.ellipse(mask, (cx, cy), (r_ext, r_ext), 0, ang, ang + 30, 255, -1)
                cv2.circle(mask, (cx, cy), r_int, 0, -1)
                
                # Cálculo de área negra
                pixel_count = cv2.bitwise_and(binaria, mask)
                negros = np.count_nonzero(pixel_count)
                total = np.count_nonzero(mask)
                
                if total > 0 and (negros / total * 100) >= sensibilidad_area:
                    puntos_perdidos += 1
                    # Pintar sector
                    overlay = img_cv.copy()
                    cv2.ellipse(overlay, (cx, cy), (r_ext, r_ext), 0, ang, ang + 30, (0, 255, 255), -1)
                    img_cv = cv2.addWeighted(overlay, 0.4, img_cv, 0.6, 0)

        # 2. Dibujar Grilla Roja Final
        for i in range(1, 7):
            cv2.circle(img_cv, (cx, cy), int(i * paso), (0, 0, 255), 3)
        cv2.line(img_cv, (cx, 0), (cx, h), (0, 0, 255), 2)
        cv2.line(img_cv, (0, cy), (w, cy), (0, 0, 255), 2)
        cv2.drawMarker(img_cv, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)

        # 3. Mostrar Resultados
        col1, col2 = st.columns([3, 1])
        with col1:
            st.image(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB), use_container_width=True)
        with col2:
            st.metric("Sectores Afectados", puntos_perdidos)
            # Cálculo de incapacidad (72 sectores totales: 6 anillos * 12 sectores)
            incap = (puntos_perdidos / 72) * 100
            st.metric("% Incapacidad", f"{round(incap, 1)}%")
            st.write("---")
            st.write("Detección de negros:")
            st.image(binaria, width=150)

else:
    st.info("Subí la imagen para comenzar.")
