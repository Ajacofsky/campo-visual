import streamlit as st
import cv2
import numpy as np

st.set_page_config(layout="wide")
st.title("🔴 Calibrador Pericial - Líneas Rojas")

file = st.sidebar.file_uploader("Subir Campo Visual", type=['jpg', 'png', 'jpeg'])

if file:
    # Leer imagen
    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    h, w = img.shape[:2]

    # Controles
    st.sidebar.header("⚙️ Configuración")
    cx = st.sidebar.slider("Centro X", 0, w, w // 2)
    cy = st.sidebar.slider("Centro Y", 0, h, h // 2)
    # Este slider controla la equidistancia:
    r60 = st.sidebar.slider("Radio hasta Marca 60°", 10, w // 2, 200)

    # Matemática de equidistancia
    paso = r60 / 6.0
    img_res = img.copy()

    # Dibujar anillos ROJOS (BGR: 0, 0, 255)
    for i in range(1, 7):
        r = int(i * paso)
        cv2.circle(img_res, (cx, cy), r, (0, 0, 255), 3) # Grosor 3
        cv2.putText(img_res, f"{i*10}", (cx + r, cy - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    # Ejes
    cv2.line(img_res, (cx, 0), (cx, h), (0, 0, 255), 1)
    cv2.line(img_res, (0, cy), (w, cy), (0, 0, 255), 1)

    st.image(cv2.cvtColor(img_res, cv2.COLOR_BGR2RGB), use_container_width=True)
else:
    st.info("Subí una imagen para ver los anillos rojos.")
