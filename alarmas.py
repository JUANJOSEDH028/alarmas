import pandas as pd
import sqlite3
from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.express as px

# Leer y limpiar los datos
file_path = r"\\servernas\Validaciones-Metrología\COORVSC-CALIFICACIONES\CALIFICACIONES\EQUIPOS\Secador de Lecho Fluido Glatt 600 kg N°4\Calificación 2025 V01\VSC\Prueba 23\AlarmHistory.csv"

data = pd.read_csv(
    file_path,
    encoding='latin1',
    skiprows=5,  # Ajusta según las líneas iniciales no relevantes
    names=["Timestamp", "Tipo de Alarma", "Codigo de Alarma", "Mensaje"]
)

# Filtrar filas relevantes
data = data[data["Timestamp"].str.contains(r"\d{2}-\d{2}-\d{4}", na=False)]
data.reset_index(drop=True, inplace=True)

# Convertir Timestamp a formato datetime
data["Timestamp"] = pd.to_datetime(data["Timestamp"])

# Extraer el usuario del campo "Mensaje"
data["Usuario"] = data["Mensaje"].str.extract(r"- por (.+)$", expand=True)
data["Mensaje"] = data["Mensaje"].str.replace(r" - Por .+$", "", regex=True)

# Conectar SQLite y realizar consultas
conn = sqlite3.connect("AlarmHistory.db")
data.to_sql("Alarmas", conn, if_exists="replace", index=False)

# Consulta principal
query_usuarios = """
SELECT Usuario, COUNT(*) as Frecuencia
FROM Alarmas
WHERE Usuario IS NOT NULL
GROUP BY Usuario
ORDER BY Frecuencia DESC
"""
result_usuarios = pd.read_sql_query(query_usuarios, conn)
total_alarmas = len(data)
conn.close()

# Dash App
app = Dash(__name__)
app.title = "Dashboard de Alarmas"

# Layout personalizado con estilo oscuro
app.layout = html.Div(style={'backgroundColor': '#121212', 'color': '#FFFFFF', 'padding': '20px'}, children=[
    html.H1("Dashboard de Alarmas", style={'textAlign': 'center', 'color': '#4CAF50'}),
    html.Div([
        html.Div([
            html.H3("Total de Alarmas", style={'color': '#FFC107'}),
            html.H2(f"{total_alarmas}", style={'color': '#FFC107'})
        ], style={'display': 'inline-block', 'width': '30%', 'textAlign': 'center'}),

        html.Div([
            html.H3("Usuario con Más Alarmas", style={'color': '#FF5722'}),
            html.H2(f"{result_usuarios.iloc[0]['Usuario']}", style={'color': '#FF5722'})
        ], style={'display': 'inline-block', 'width': '30%', 'textAlign': 'center'}),
    ], style={'display': 'flex', 'justifyContent': 'space-around'}),

    html.H3("Usuarios con Más Alarmas", style={'textAlign': 'center', 'marginTop': '20px', 'color': '#00BCD4'}),
    dcc.Graph(
        id="bar-usuarios",
        figure=px.bar(result_usuarios, x='Usuario', y='Frecuencia', 
                      title='Usuarios con Más Alarmas',
                      color_discrete_sequence=['#2196F3'])
    ),

    html.H3("Usuarios Únicos del Sistema (Gráfico de Pastel)", style={'marginTop': '20px', 'color': '#FF9800'}),
    dcc.Graph(
        id="pie-usuarios-unicos",
        figure=px.pie(result_usuarios, names='Usuario', values='Frecuencia', 
                      title="Distribución de Usuarios Únicos", color_discrete_sequence=px.colors.sequential.Viridis)
    ),

    html.H3("Filtro de Rango de Tiempo", style={'marginTop': '20px', 'color': '#FFEB3B'}),
    dcc.DatePickerRange(
        id='date-picker-range',
        start_date=data['Timestamp'].min(),
        end_date=data['Timestamp'].max(),
        display_format='YYYY-MM-DD',
        style={'color': '#000000'}
    ),

    html.H3("Tabla Completa de Alarmas", style={'marginTop': '20px', 'color': '#9C27B0'}),
    dash_table.DataTable(
        id='filtered-table',
        columns=[{"name": i, "id": i} for i in data.columns],
        style_table={'height': '400px', 'overflowY': 'auto', 'backgroundColor': '#1E1E1E'},
        style_header={'backgroundColor': '#333333', 'color': 'white'},
        style_cell={'backgroundColor': '#1E1E1E', 'color': 'white'}
    )
])

@app.callback(
    Output('filtered-table', 'data'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
)
def update_table(start_date, end_date):
    filtered_data = data[(data['Timestamp'] >= start_date) & (data['Timestamp'] <= end_date)]
    return filtered_data.to_dict('records')

# Ejecutar la app
if __name__ == '__main__':
    app.run_server(debug=True)
