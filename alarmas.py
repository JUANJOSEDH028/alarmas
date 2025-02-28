import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard de Alarmas", layout="wide")
st.title("Dashboard de Alarmas de Sistema")
st.markdown("Visualización interactiva de las alarmas registradas")

# Widget para cargar archivo CSV
uploaded_file = st.file_uploader("Seleccione el archivo CSV de Alarmas", type=["csv"])

if uploaded_file is not None:
    # Leer y limpiar los datos
    try:
        data = pd.read_csv(
            uploaded_file,
            encoding='latin1',
            skiprows=5,  # Ajustar según el formato del CSV
            names=["Timestamp", "Tipo de Alarma", "Codigo de Alarma", "Mensaje"]
        )
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # Filtrar filas que contengan fechas con el formato dd-mm-yyyy
    data = data[data["Timestamp"].str.contains(r"\d{2}-\d{2}-\d{4}", na=False)]
    data.reset_index(drop=True, inplace=True)

    # Convertir la columna Timestamp a formato datetime
    data["Timestamp"] = pd.to_datetime(data["Timestamp"])

    # Extraer el usuario del campo "Mensaje"
    data["Usuario"] = data["Mensaje"].str.extract(r"- por (.+)$", expand=True)
    # Limpiar el mensaje principal eliminando la parte "- Por ..."
    data["Mensaje"] = data["Mensaje"].str.replace(r" - Por .+$", "", regex=True)

    # Guardar los datos en una base de datos SQLite
    conn = sqlite3.connect("AlarmHistory.db")
    data.to_sql("Alarmas", conn, if_exists="replace", index=False)

    # Consulta para los usuarios con más alarmas
    query_usuarios = """
    SELECT Usuario, COUNT(*) as Frecuencia
    FROM Alarmas
    GROUP BY Usuario
    ORDER BY Frecuencia DESC
    """
    result_usuarios = pd.read_sql_query(query_usuarios, conn)

    # Métricas generales
    total_alarmas = len(data)
    alarmas_unicas = data["Mensaje"].dropna().unique()
    usuarios_unicos = data["Usuario"].dropna().unique()

    conn.close()

    # --- Visualización del Dashboard ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Alarmas", total_alarmas)
    col2.metric("Tipos de Alarmas Únicas", len(alarmas_unicas))
    col3.metric("Usuarios Únicos", len(usuarios_unicos))

    st.subheader("Alarmas Únicas")
    st.dataframe(pd.DataFrame(alarmas_unicas, columns=["Alarmas Únicas"]), use_container_width=True)

    st.subheader("Usuarios Únicos")
    st.dataframe(pd.DataFrame(usuarios_unicos, columns=["Usuarios Únicos"]), use_container_width=True)

    # Selector de rango de fechas
    st.subheader("Filtrar por Rango de Fechas")
    start_date, end_date = st.date_input(
        "Seleccione el rango de fechas:",
        [data["Timestamp"].min().date(), data["Timestamp"].max().date()],
        key="date_range_selector_alarmas"
    )
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filtrar los datos según el rango de fechas seleccionado
    filtered_data = data[(data["Timestamp"] >= start_date) & (data["Timestamp"] <= end_date)]
    st.subheader("Lista Completa de Alarmas Filtradas")
    st.dataframe(filtered_data, use_container_width=True)

    # Gráfico de pastel para los usuarios con más alarmas
    st.subheader("Usuarios con Más Alarmas")
    fig_pie_usuarios = px.pie(result_usuarios, names="Usuario", values="Frecuencia", title="Usuarios con Más Alarmas")
    st.plotly_chart(fig_pie_usuarios, use_container_width=True)

    # Histograma de alarmas por hora del día
    st.subheader("Distribución de Alarmas por Hora del Día")
    filtered_data["Hora"] = filtered_data["Timestamp"].dt.hour
    fig_histogram = px.histogram(filtered_data, x="Hora", nbins=24, title="Histograma de Alarmas por Hora del Día",
                                 labels={"Hora": "Hora del Día", "count": "Cantidad de Alarmas"})
    st.plotly_chart(fig_histogram, use_container_width=True)

    # Opción para exportar los datos filtrados
    st.subheader("Exportar Datos")
    st.download_button(
        label="Descargar Datos Filtrados (CSV)",
        data=filtered_data.to_csv(index=False).encode('utf-8'),
        file_name='datos_filtrados.csv',
        mime='text/csv'
    )
else:
    st.info("Cargue un archivo CSV para comenzar el análisis.")
