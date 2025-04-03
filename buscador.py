import streamlit as st
import pandas as pd
import requests
from duckduckgo_search import DDGS
from io import BytesIO
import base64

st.set_page_config(page_title="Buscador de Imágenes para Productos Fitosanitarios", layout="wide")
st.title("Buscador Automático de Imágenes para Productos Fitosanitarios")

st.write("## Paso 1: Cargar archivo Excel")

uploaded_file = st.file_uploader("Arrastra o selecciona tu archivo Excel de productos", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("## Paso 2: Identificar columnas")
    col_nombre = st.selectbox("Selecciona la columna para el nombre del producto:", df.columns)
    col_composicion = st.selectbox("Selecciona la columna para la composición:", df.columns)
    col_cantidad = st.selectbox("Selecciona la columna para la cantidad:", df.columns)
    col_udm = st.selectbox("Selecciona la columna para la unidad de medida:", df.columns)

    if st.button("Iniciar búsqueda de imágenes") or 'resultados_urls' in st.session_state:
        if 'resultados_urls' not in st.session_state:
            st.session_state['resultados_urls'] = {}
            st.session_state['productos'] = df.to_dict(orient='records')
            st.session_state['consultas'] = {}
            st.session_state['imagenes'] = {}

        for idx, producto in enumerate(st.session_state['productos']):
            st.write(f"### Producto {idx + 1} — {producto[col_nombre]}")
            st.write(f"**Composición**: {producto[col_composicion]}")
            st.write(f"**Formato**: {producto[col_cantidad]} {producto[col_udm]}")

            # Crear o recuperar consulta editable
            default_query = f"{producto[col_nombre]} {producto[col_composicion]} {producto[col_cantidad]} {producto[col_udm]}"
            consulta = st.text_input(f"Consulta de búsqueda para DuckDuckGo", value=st.session_state['consultas'].get(idx, default_query), key=f"consulta_{idx}")
            st.session_state['consultas'][idx] = consulta

            if st.button(f"🔄 Buscar nuevas imágenes", key=f"buscar_{idx}") or f"imagenes_{idx}" not in st.session_state['imagenes']:
                with DDGS() as ddgs:
                    resultados = list(ddgs.images(consulta, max_results=4))
                    st.session_state['imagenes'][f"imagenes_{idx}"] = [r['image'] for r in resultados]

            opciones_urls = st.session_state['imagenes'].get(f"imagenes_{idx}", [])

            if opciones_urls:
                st.image(opciones_urls, width=150, caption=[f"Opción {i+1}" for i in range(len(opciones_urls))])
                seleccion = st.radio(
                    f"Selecciona la mejor imagen para '{producto[col_nombre]}' o deja en blanco:",
                    options=["Ninguna"] + opciones_urls,
                    key=f"radio_{idx}"
                )
                st.session_state['resultados_urls'][idx] = "" if seleccion == "Ninguna" else seleccion
            else:
                st.warning("No se encontraron imágenes. Puedes editar la consulta y volver a intentar.")
                st.session_state['resultados_urls'][idx] = ""

        st.write("## Paso 3: Generar Excel con URLs seleccionadas")
        if st.button("Generar archivo Excel final"):
            df['URL Imagen'] = df.index.map(lambda idx: st.session_state['resultados_urls'].get(idx, ""))

            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            b64 = base64.b64encode(output.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="productos_con_imagenes.xlsx">Descargar archivo con imágenes</a>'
            st.markdown(href, unsafe_allow_html=True)
