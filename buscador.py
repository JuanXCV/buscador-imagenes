import streamlit as st
import pandas as pd
import requests
from duckduckgo_search import DDGS
from io import BytesIO
import base64

# Configuración visual
st.set_page_config(page_title="Agrodolores | Buscador de Imágenes", layout="wide")

# CSS personalizado con margen superior para evitar solapamiento
st.markdown("""
<link href='https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap' rel='stylesheet'>
<style>
    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
        background-color: #f3f5ee;
    }
    .stButton>button {
        background-color: #1A4D3D;
        color: white;
        border-radius: 6px;
        padding: 0.5em 1.2em;
        font-weight: 600;
        border: none;
    }
    .stButton>button:hover {
        background-color: #F28C28;
        color: white;
    }
    .fixed-header {
        position: fixed;
        top: 3rem;
        left: 0;
        right: 0;
        background-color: #f3f5ee;
        z-index: 9999;
        padding: 0.5rem 1rem;
        border-bottom: 1px solid #ddd;
    }
    .header-spacer {
        height: 110px;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado fijo con espacio superior para evitar solapamiento con la barra de Streamlit
st.markdown("""
<div class='fixed-header'>
    <div style='display: flex; align-items: center;'>
        <img src='https://agrodolores.zenn.es/web/image/website/1/logo/Mi%20Agrodolores?unique=a108e66' style='height: 60px; margin-right: 20px;'>
        <div>
            <h2 style='margin: 0; color: #1A4D3D;'>Agrodolores</h2>
            <p style='margin: 0; font-size: 16px; color: #555;'>Súmate a la innovación agrícola</p>
        </div>
    </div>
</div>
<div class='header-spacer'></div>
""", unsafe_allow_html=True)

st.subheader("Paso 1: Cargar archivo Excel")

uploaded_file = st.file_uploader("Arrastra o selecciona tu archivo Excel de productos", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("Paso 2: Identificar columnas")
    col_nombre = st.selectbox("Columna: Nombre del producto", df.columns)
    col_composicion = st.selectbox("Columna: Composición", df.columns)
    col_cantidad = st.selectbox("Columna: Cantidad", df.columns)
    col_udm = st.selectbox("Columna: Unidad de medida", df.columns)

    if st.button("Iniciar búsqueda de imágenes") or 'resultados_urls' in st.session_state:
        if 'resultados_urls' not in st.session_state:
            st.session_state['resultados_urls'] = {}
            st.session_state['productos'] = df.to_dict(orient='records')
            st.session_state['consultas'] = {}
            st.session_state['imagenes'] = {}

        for idx, producto in enumerate(st.session_state['productos']):
            st.markdown(f"""
                <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); margin-bottom: 20px;'>
                    <h4 style='color:#1A4D3D;'>{producto[col_nombre]}</h4>
                    <p><strong>Composición:</strong> {producto[col_composicion]}</p>
                    <p><strong>Formato:</strong> {producto[col_cantidad]} {producto[col_udm]}</p>
            """, unsafe_allow_html=True)

            default_query = f"{producto[col_nombre]} {producto[col_composicion]} {producto[col_cantidad]} {producto[col_udm]}"
            consulta = st.text_input("Consulta personalizada para DuckDuckGo:", value=st.session_state['consultas'].get(idx, default_query), key=f"consulta_{idx}")
            st.session_state['consultas'][idx] = consulta

            if st.button("Buscar nuevas imágenes", key=f"buscar_{idx}") or f"imagenes_{idx}" not in st.session_state['imagenes']:
                with DDGS() as ddgs:
                    resultados = list(ddgs.images(consulta, max_results=4))
                    st.session_state['imagenes'][f"imagenes_{idx}"] = [r['image'] for r in resultados]

            opciones_urls = st.session_state['imagenes'].get(f"imagenes_{idx}", [])

            if opciones_urls:
                cols = st.columns(len(opciones_urls))
                opciones_mapeadas = {f"Opción {i+1}": url for i, url in enumerate(opciones_urls)}
                for i, (label, url) in enumerate(opciones_mapeadas.items()):
                    cols[i].image(url, width=220, caption=label)

                seleccion = st.radio(
                    "Selecciona la mejor imagen o deja en blanco:",
                    options=["Ninguna"] + list(opciones_mapeadas.keys()),
                    key=f"radio_{idx}"
                )
                st.session_state['resultados_urls'][idx] = "" if seleccion == "Ninguna" else opciones_mapeadas[seleccion]
            else:
                st.warning("No se encontraron imágenes. Puedes editar la consulta y volver a intentar.")
                st.session_state['resultados_urls'][idx] = ""

            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("Paso 3: Generar Excel con imágenes seleccionadas")
        if st.button("Generar archivo Excel final"):
            df['URL Imagen'] = df.index.map(lambda idx: st.session_state['resultados_urls'].get(idx, ""))

            st.write("Vista previa del archivo:")
            st.dataframe(df.head())

            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            b64 = base64.b64encode(output.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="productos_con_imagenes.xlsx">Descargar archivo con imágenes</a>'
            st.markdown(href, unsafe_allow_html=True)

# Pie de página corporativo
st.markdown("""
---
<p style='text-align: center; color: gray;'>© 2024 Agrodolores. Todos los derechos reservados.</p>
""", unsafe_allow_html=True)
