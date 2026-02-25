import streamlit as st
import cv2
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image

st.set_page_config(layout="wide")
st.title("📊 Análisis de Incapacidad - Regla del 70%")

if "puntos" not in st.session_state:
    st.session_state.puntos = []

def borrar_puntos():
    st.session_state.puntos = []

st.sidebar.button("🗑️ Reiniciar Calibración", on_click=borrar_puntos)
umbral_negro = st.sidebar.slider("Sensibilidad detección de negros", 0, 255, 120, help="Ajustá esto si el sistema no 've' los cuadraditos")
porcentaje_limite = st.sidebar.slider("Umbral de área para pérdida (%)", 10, 100, 70, help="Regla del 70% (podés bajarlo si los cuadraditos son chicos)")

file = st.sidebar.file_uploader("Subir Campo Visual", type=['jpg', 'png', 'jpeg'])

if file:
    img_pil = Image.open(file)
    w, h = img_pil.size
    
    if len(st.session_state.puntos) < 2:
        st.info("📍 Calibración necesaria: 1° Clic en CENTRO, 2° Clic en marca 60°")
        coords = streamlit_image_coordinates(img_pil, key="calibracion")
        if coords:
            nuevo_punto = (coords["x"], coords["y"])
            if not st.session_state.puntos or nuevo_punto != st.session_state.puntos[-1]:
                st.session_state.puntos.append(nuevo_punto)
                st.rerun()
    
    # PROCESAMIENTO
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    img_gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    # Detectamos negros (binarización)
    _, binaria = cv2.threshold(img_gris, umbral_negro, 255, cv2.THRESH_BINARY_INV)

    if len(st.session_state.puntos) == 2:
        cx, cy = st.session_state.puntos[0]
        px60, py60 = st.session_state.puntos[1]
        r60 = int(np.sqrt((px60 - cx)**2 + (py60 - cy)**2))
        paso = r60 / 6.0
        
        puntos_perdidos = 0
        total_sectores = 0

        # Analizamos anillos del 1 al 6 (de 10° a 60°)
        for i in range(1, 7):
            r_ext = int(i * paso)
            r_int = int((i - 1) * paso)
            
            # Dividimos en 12 sectores (cada 30°) para mayor precisión pericial
            for s in range(12):
                ang_inicio = s * 30
                total_sectores += 1
                
                # Crear máscara del sector
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.ellipse(mask, (cx, cy), (r_ext, r_ext), 0, ang_inicio, ang_inicio + 30, 255, -1)
                cv2.circle(mask, (cx, cy), r_int, 0, -1)
                
                # Contar píxeles negros en el sector
                pixeles_sector = cv2.bitwise_and(binaria, mask)
                area_negra = np.count_nonzero(pixeles_sector)
                area_total = np.count_nonzero(mask)
                
                if area_total > 0:
                    ocupacion = (area_negra / area_total) * 100
                    
                    if ocupacion >= porcentaje_limite:
                        puntos_perdidos += 1
                        # Pintar sector perdido en AMARILLO transparente
                        overlay = img_cv.copy()
                        cv2.ellipse(overlay, (cx, cy), (r_ext, r_ext), 0, ang_inicio, ang_inicio + 30, (0, 255, 255), -1)
                        img_cv = cv2.addWeighted(overlay, 0.3, img_cv, 0.7, 0)

        # Dibujar grilla roja final encima
        for i in range(1, 7):
            cv2.circle(img_cv, (cx, cy), int(i * paso), (0, 0, 255), 2)
        cv2.line(img_cv, (cx, 0), (cx, h), (0, 0, 255), 1)
        cv2.line(img_cv, (0, cy), (w, cy), (0, 0, 255), 1)

        # MOSTRAR RESULTADOS
        c1, c2 = st.columns([3, 1])
        with c1:
            st.image(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB), use_container_width=True)
        with c2:
            st.metric("Sectores Perdidos", puntos_perdidos)
            incapacidad = (puntos_perdidos / total_sectores) * 100
            st.metric("Incapacidad Estimada", f"{round(incapacidad, 1)}%")
            st.write("---")
            st.write("**Vista de detección:**")
            st.image(binaria, caption="Lo que el sistema detecta como negro", width=200)
    else:
        st.image(img_pil, use_container_width=True)

else:
    st.info("Subí el informe para analizar.")
