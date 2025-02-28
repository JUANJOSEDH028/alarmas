import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px
import os

# Ruta del archivo CSV relativa (ajusta si fuera necesario)
file_path = "https://github.com/JUANJOSEDH028/alarmas/raw/main/AlarmHistory1.csv"

# Leer y limpiar los datos
data = pd.read_csv(
    file_path,
    encoding='latin1',
    skiprows=5,  # Ajusta según las líneas iniciales no relevantes en tu CSV
    names=["Timestamp", "Tipo de Alarma", "Codigo de Alarma", "Mensaje"]
)

# Filtrar filas relevantes (solo las que tienen formato de fecha dd-mm-yyyy)
data = data[data["Timestamp"].str.contains(r"\d{2}-\d{2}-\d{4}", na=False)]
data.reset_index(drop=True, inplace=True)

# Convertir la columna Timestamp a datetime
data["Timestamp"] = pd.to_datetime(data["Timestamp"])

# Extraer el usuario del campo "Mensaje"
data["Usuario"] = data["Mensaje"].str.extract(r"- por (.+)$", expand=True)

# Limpiar el mensaje principal (eliminar " - Por ...")
data["Mensaje"] = data["Mensaje"].str.replace(r" - Por .+$", "", regex=True)

# --- FILTRO para eliminar registros sin usuario ---
data = data[
    data["Usuario"].notna() &
    (data["Usuario"].str.strip() != "") &
    (data["Usuario"].str.lower() != "none")
]

# Guardar en SQLite
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

# Cerrar conexión SQLite
conn.close()

# --- Configuración de la App en Streamlit ---
st.set_page_config(page_title="Dashboard de Alarmas", layout="wide")

# --- Encabezado ---
st.title("Dashboard de Alarmas de Sistema")
st.markdown("## Visualización interactiva de las alarmas registradas")

# --- Métricas ---
col1, col2, col3 = st.columns(3)
col1.metric("Total de Alarmas", total_alarmas)
col2.metric("Tipos de Alarmas Únicas", len(alarmas_unicas))
col3.metric("Usuarios Únicos", len(usuarios_unicos))

# --- Tabla de Alarmas Únicas ---
st.subheader("Alarmas Únicas")
st.dataframe(pd.DataFrame(alarmas_unicas, columns=["Alarmas Únicas"]), use_container_width=True)

# --- Tabla de Usuarios Únicos ---
st.subheader("Usuarios Únicos")
st.dataframe(pd.DataFrame(usuarios_unicos, columns=["Usuarios Únicos"]), use_container_width=True)

# --- Selector de rango de fechas ---
st.subheader("Filtrar por Rango de Fechas")
start_date, end_date = st.date_input(
    "Seleccione el rango de fechas:",
    [data["Timestamp"].min().date(), data["Timestamp"].max().date()],
    key="date_range_selector_alarmas"
)
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filtrar los datos por rango de fechas
filtered_data = data[(data["Timestamp"] >= start_date) & (data["Timestamp"] <= end_date)]

# Mostrar los datos filtrados
st.subheader("Lista Completa de Alarmas Filtradas")
st.dataframe(filtered_data, use_container_width=True)

# --- Gráfico de Pastel para Usuarios con Más Alarmas ---
st.subheader("Usuarios con Más Alarmas")
fig_pie_usuarios = px.pie(
    result_usuarios,
    names="Usuario",
    values="Frecuencia",
    title="Usuarios con Más Alarmas"
)
st.plotly_chart(fig_pie_usuarios, use_container_width=True)

# --- Histograma de Alarmas por Hora ---
st.subheader("Distribución de Alarmas por Hora del Día")
filtered_data["Hora"] = filtered_data["Timestamp"].dt.hour

fig_histogram = px.histogram(
    filtered_data,
    x="Hora",
    nbins=24,
    title="Histograma de Alarmas por Hora del Día",
    labels={"Hora": "Hora del Día", "count": "Cantidad de Alarmas"}
)
st.plotly_chart(fig_histogram, use_container_width=True)

# --- Opción de Guardar Datos ---
st.subheader("Exportar Datos")
st.download_button(
    label="Descargar Datos Filtrados (CSV)",
    data=filtered_data.to_csv(index=False).encode('utf-8'),
    file_name='datos_filtrados.csv',
    mime='text/csv'
)

# Si usas Streamlit, normalmente ejecutas con: streamlit run tu_archivo.py
# Este bloque se usa con otros frameworks o si deseas un modo particular de ejecución.
# Lo dejamos aquí si tu entorno lo requiere:
if __name__ == '__main__':
    # Ejemplo de ejecución (puede ajustarse o eliminarse según tu necesidad)
    # app.run_server(debug=True)
    pass

