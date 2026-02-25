import streamlit as st
import cv2
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image

st.set_page_config(layout="wide")
st.title("📊 Sistema de Peritaje Visual")

# --- ESTADO DE LA APLICACIÓN ---
if "puntos" not in st.session_state:
    st.session_state.puntos = []
if "ejecutar_analisis" not in st.session_state:
    st.session_state.ejecutar_analisis = False

def reiniciar():
    st.session_state.puntos = []
    st.session_state.ejecutar_analisis = False

# --- SIDEBAR ---
st.sidebar.title("Configuración")
st.sidebar.button("🔄 Reiniciar Calibración", on_click=reiniciar)
umbral = st.sidebar.slider("Sensibilidad de Negros", 0, 255, 120)
area_min = st.sidebar.slider("Umbral de Área (%)", 1, 100, 25)

file = st.sidebar.file_uploader("Subir Informe", type=['jpg', 'png', 'jpeg'])

if file:
    img_pil = Image.open(file).convert("RGB")
    w, h = img_pil.size
    
    # FASE 1: CLICS (Solo si no se ha ejecutado el análisis)
    if not st.session_state.ejecutar_analisis:
        if len(st.session_state.puntos) == 0:
            st.info("📍 PASO 1: Hacé clic en el **CENTRO** del gráfico.")
        elif len(st.session_state.puntos) == 1:
            st.warning("📏 PASO 2: Hacé clic en la marca de **60°**.")
        
        # Imagen interactiva para clics
        coords = streamlit_image_coordinates(img_pil, key="clics")
        
        if coords:
            p = (coords["x"], coords["y"])
            if not st.session_state.puntos or p != st.session_state.puntos[-1]:
                st.session_state.puntos.append(p)
                st.rerun()

        # Si ya tenemos los 2 puntos, mostrar botón de procesar
        if len(st.session_state.puntos) == 2:
            st.success("Calibración lista.")
            if st.button("🚀 CALCULAR INCAPACIDAD"):
                st.session_state.ejecutar_analisis = True
                st.rerun()

    # FASE 2: CÁLCULO Y RESULTADOS
    else:
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, binaria = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY_INV)
        
        cx, cy = st.session_state.puntos[0]
        px60, py60 = st.session_state.puntos[1]
        r60 = int(np.sqrt((px60 - cx)**2 + (py60 - cy)**2))
        paso = r60 / 6.0
        
        perdidos = 0
        # Analizamos 6 anillos y 12 sectores (72 sectores en total)
        for i in range(1, 7):
            r_ext = int(i * paso)
            r_int = int((i - 1) * paso)
            for s in range(12):
                ang = s * 30
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.ellipse(mask, (cx, cy), (r_ext, r_ext), 0, ang, ang + 30, 255, -1)
                cv2.circle(mask, (cx, cy), r_int, 0, -1)
                
                res = cv2.bitwise_and(binaria, mask)
                if np.count_nonzero(mask) > 0:
                    porcentaje = (np.count_nonzero(res) / np.count_nonzero(mask)) * 100
                    if porcentaje >= area_min:
                        perdidos += 1
                        overlay = img_cv.copy()
                        cv2.ellipse(overlay, (cx, cy), (r_ext, r_ext), 0, ang, ang + 30, (0, 255, 255), -1)
                        img_cv = cv2.addWeighted(overlay, 0.4, img_cv, 0.6, 0)

        # Dibujo de grilla final
        for i in range(1, 7):
            cv2.circle(img_cv, (cx, cy), int(i * paso), (0, 0, 255), 2)
        cv2.line(img_cv, (cx, 0), (cx, h), (0, 0, 255), 1)
        cv2.line(img_cv, (0, cy), (w, cy), (0, 0, 255), 1)

        # Mostrar imagen y métricas
        col1, col2 = st.columns([3, 1])
        with col1:
            st.image(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB), use_container_width=True)
        with col2:
            st.metric("Sectores Afectados", perdidos)
            incap = (perdidos / 72) * 100
            st.metric("% Incapacidad", f"{round(incap, 1)}%")
            st.write("Detección de negros:")
            st.image(binaria, width=150)

else:
    st.info("Subí un informe para comenzar.")
