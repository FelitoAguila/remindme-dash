from dash import Dash, html, dcc, Input, Output, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import os
from config import Config
from metrics import calculate_metrics
from pymongo import MongoClient

# Inicializar MongoDB client
client = MongoClient(Config.MONGO_URI)
db = client['RemindMe-test']
collection = db['reminders']

# Inicialización de la aplicación Dash
app = Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

# Establecer el diseño de la aplicación
app.layout = html.Div([
    html.H1("Dashboard de Recordatorios", style={'textAlign': 'center', 'margin': '20px 0'}),
    
    # Selector de fechas
    html.Div([
        html.Div([
            html.Label("Fecha de inicio:"),
            dcc.DatePickerSingle(
                id='start-date-picker',
                date=datetime.now() - timedelta(days=30),
                display_format='YYYY-MM-DD',
                style={'marginBottom': '10px'}
            ),
        ], style={'margin': '10px', 'flex': '1'}),
        
        html.Div([
            html.Label("Fecha de fin:"),
            dcc.DatePickerSingle(
                id='end-date-picker',
                date=datetime.now(),
                display_format='YYYY-MM-DD',
                style={'marginBottom': '10px'}
            ),
        ], style={'margin': '10px', 'flex': '1'}),
        
        html.Div([
            html.Label("Vista:"),
            dcc.RadioItems(
                id='view-selector',
                options=[
                    {'label': 'Diario', 'value': 'daily'},
                    {'label': 'Mensual', 'value': 'monthly'}
                ],
                value='daily',
                style={'display': 'flex', 'gap': '10px'}
            ),
        ], style={'margin': '10px', 'flex': '1'})
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'margin': '20px'}),
    
    # Tarjetas de métricas principales
    html.Div([
        html.Div([
            html.H3("Total Usuarios"),
            html.H2(id='total-users', children='0'),
        ], className='metric-card'),
        
        html.Div([
            html.H3("Total Recordatorios Creados"),
            html.H2(id='total-reminds-created', children='0'),
        ], className='metric-card'),
        
        html.Div([
            html.H3("Total Recordatorios Enviados"),
            html.H2(id='total-reminds-sent', children='0'),
        ], className='metric-card'),
        
        html.Div([
            html.H3("Recordatorios Creados por Usuario"),
            html.H2(id='per-user-reminds-created', children='0'),
        ], className='metric-card'),
        
        html.Div([
            html.H3("Recordatorios Enviados por Usuario"),
            html.H2(id='per-user-reminds-sent', children='0'),
        ], className='metric-card'),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'gap': '15px', 'margin': '20px'}),
    
    # Gráficos
    html.Div([
        html.Div([
            html.H3("Usuarios Activos", style={'textAlign': 'center'}),
            dcc.Graph(id='users-graph')
        ], style={'flex': '1', 'minWidth': '45%', 'margin': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '10px'}),
        
        html.Div([
            html.H3("Recordatorios Creados", style={'textAlign': 'center'}),
            dcc.Graph(id='reminds-created-graph')
        ], style={'flex': '1', 'minWidth': '45%', 'margin': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '10px'}),
        
        html.Div([
            html.H3("Recordatorios Enviados", style={'textAlign': 'center'}),
            dcc.Graph(id='reminds-sent-graph')
        ], style={'flex': '1', 'minWidth': '45%', 'margin': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '10px'}),
        
        html.Div([
            html.H3("Comparación Creados vs Enviados", style={'textAlign': 'center'}),
            dcc.Graph(id='comparison-graph')
        ], style={'flex': '1', 'minWidth': '45%', 'margin': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '10px'})
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around', 'margin': '20px'}),
    
    # Estadísticas adicionales
    html.Div([
        html.H3("Estadísticas Adicionales", style={'textAlign': 'center'}),
        
        # Primera fila de métricas
        html.Div([
            html.Div([
                html.H4("Promedio Diario"),
                html.Div([
                    html.P(id='avg-daily-users', children='Usuarios: 0'),
                    html.P(id='avg-daily-reminds-created', children='Recordatorios Creados: 0'),
                    html.P(id='avg-daily-reminds-sent', children='Recordatorios Enviados: 0')
                ])
            ], style={'flex': '1', 'minWidth': '30%', 'margin': '10px', 'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px'}),
            
            html.Div([
                html.H4("Promedio Mensual"),
                html.Div([
                    html.P(id='avg-monthly-users', children='Usuarios: 0'),
                    html.P(id='avg-monthly-reminds-created', children='Recordatorios Creados: 0'),
                    html.P(id='avg-monthly-reminds-sent', children='Recordatorios Enviados: 0')
                ])
            ], style={'flex': '1', 'minWidth': '30%', 'margin': '10px', 'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px'}),
            
            html.Div([
                html.H4("Promedio por Usuario"),
                html.Div([
                    html.P(id='avg-per-user-daily-reminds-created', children='Recordatorios Creados Diarios: 0'),
                    html.P(id='avg-per-user-daily-reminds-sent', children='Recordatorios Enviados Diarios: 0'),
                    html.P(id='avg-per-user-monthly-reminds-created', children='Recordatorios Creados Mensuales: 0'),
                    html.P(id='avg-per-user-monthly-reminds-sent', children='Recordatorios Enviados Mensuales: 0')
                ])
            ], style={'flex': '1', 'minWidth': '30%', 'margin': '10px', 'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around'})
    ], style={'margin': '20px'})
], style={'fontFamily': 'Arial, sans-serif', 'margin': '0 auto', 'maxWidth': '1400px', 'padding': '20px'})

# Estilos CSS adicionales
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Dashboard de Recordatorios</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            .metric-card {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                min-width: 180px;
                text-align: center;
                flex: 1;
            }
            .metric-card h3 {
                margin: 0;
                font-size: 1rem;
                color: #666;
            }
            .metric-card h2 {
                margin: 10px 0 0;
                font-size: 2rem;
                color: #333;
            }
            @media (max-width: 768px) {
                .metric-card {
                    min-width: 120px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Callbacks
@app.callback(
    [
        Output('total-users', 'children'),
        Output('total-reminds-created', 'children'),
        Output('total-reminds-sent', 'children'),
        Output('per-user-reminds-created', 'children'),
        Output('per-user-reminds-sent', 'children'),
        Output('users-graph', 'figure'),
        Output('reminds-created-graph', 'figure'),
        Output('reminds-sent-graph', 'figure'),
        Output('comparison-graph', 'figure'),
        Output('avg-daily-users', 'children'),
        Output('avg-daily-reminds-created', 'children'),
        Output('avg-daily-reminds-sent', 'children'),
        Output('avg-monthly-users', 'children'),
        Output('avg-monthly-reminds-created', 'children'),
        Output('avg-monthly-reminds-sent', 'children'),
        Output('avg-per-user-daily-reminds-created', 'children'),
        Output('avg-per-user-daily-reminds-sent', 'children'),
        Output('avg-per-user-monthly-reminds-created', 'children'),
        Output('avg-per-user-monthly-reminds-sent', 'children')
    ],
    [
        Input('start-date-picker', 'date'),
        Input('end-date-picker', 'date'),
        Input('view-selector', 'value')
    ]
)
def update_metrics(start_date, end_date, view):
    # Verificar que las fechas sean válidas
    if not start_date or not end_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    start_date = start_date[:10] if start_date else (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = end_date[:10] if end_date else datetime.now().strftime('%Y-%m-%d')

    # Calcular métricas
    metrics = calculate_metrics(start_date, end_date)
    
    # Formatear números para mostrar
    total_users = f"{metrics['total_users']:,}"
    total_reminds_created = f"{metrics['total_reminds_created']:,}"
    total_reminds_sent = f"{metrics['total_reminds_sent']:,}"
    per_user_reminds_created = f"{metrics['per_user_reminds_created']:.2f}"
    per_user_reminds_sent = f"{metrics['per_user_reminds_sent']:.2f}"
    
    # Crear gráficos según la vista seleccionada
    if view == 'daily':
        # Gráfico de usuarios diarios
        users_df = metrics['daily_users']
        users_fig = px.bar(
            users_df,
            x='date_time',
            y='count',
            title='Usuarios Activos por Día',
            labels={'date_time': 'Fecha', 'count': 'Número de Usuarios'},
            color_discrete_sequence=['#3366CC']
        )
        
        # Gráfico de recordatorios creados por día
        created_df = metrics['daily_reminds_created']
        created_fig = px.bar(
            created_df,
            x='date_time',
            y='count',
            title='Recordatorios Creados por Día',
            labels={'date_time': 'Fecha', 'count': 'Número de Recordatorios'},
            color_discrete_sequence=['#FF9900']
        )
        
        # Gráfico de recordatorios enviados por día
        sent_df = metrics['daily_reminds_sent']
        sent_fig = px.bar(
            sent_df,
            x='date_time',
            y='count',
            title='Recordatorios Enviados por Día',
            labels={'date_time': 'Fecha', 'count': 'Número de Recordatorios'},
            color_discrete_sequence=['#109618']
        )
        
        # Gráfico de comparación
        if not metrics['daily_reminds_created'].empty or not metrics['daily_reminds_sent'].empty:
            # Crear un dataframe combinado para la comparación
            df_created = metrics['daily_reminds_created'].rename(columns={'count': 'Creados'})
            df_sent = metrics['daily_reminds_sent'].rename(columns={'count': 'Enviados'})
            
            # Combinar dataframes
            df_comparison = pd.merge(df_created, df_sent, on='date_time', how='outer').fillna(0)
            
            # Crear figura de comparación
            comparison_fig = go.Figure()
            comparison_fig.add_trace(go.Bar(
                x=df_comparison['date_time'],
                y=df_comparison['Creados'],
                name='Creados',
                marker_color='#FF9900'
            ))
            comparison_fig.add_trace(go.Bar(
                x=df_comparison['date_time'],
                y=df_comparison['Enviados'],
                name='Enviados',
                marker_color='#109618'
            ))
            
            comparison_fig.update_layout(
                title='Comparación: Recordatorios Creados vs Enviados por Día',
                xaxis_title='Fecha',
                yaxis_title='Número de Recordatorios',
                barmode='group'
            )
        else:
            comparison_fig = go.Figure()
            comparison_fig.update_layout(
                title='No hay datos para mostrar en el período seleccionado',
                xaxis_title='Fecha',
                yaxis_title='Número de Recordatorios'
            )
    else:  # view == 'monthly'
        # Gráfico de usuarios mensuales
        users_df = metrics['monthly_users']
        users_fig = px.bar(
            users_df,
            x='mes',
            y='count',
            title='Usuarios Activos por Mes',
            labels={'mes': 'Mes', 'count': 'Número de Usuarios'},
            color_discrete_sequence=['#3366CC']
        )
        users_fig.update_xaxes(type='category')

        # Gráfico de recordatorios creados por mes
        created_df = metrics['monthly_reminds_created']
        created_fig = px.bar(
            created_df,
            x='month',
            y='count',
            title='Recordatorios Creados por Mes',
            labels={'month': 'Mes', 'count': 'Número de Recordatorios'},
            color_discrete_sequence=['#FF9900']
        )
        created_fig.update_xaxes(type='category')

        # Gráfico de recordatorios enviados por mes
        sent_df = metrics['monthly_reminds_sent']
        sent_fig = px.bar(
            sent_df,
            x='month',
            y='count',
            title='Recordatorios Enviados por Mes',
            labels={'month': 'Mes', 'count': 'Número de Recordatorios'},
            color_discrete_sequence=['#109618']
        )
        sent_fig.update_xaxes(type='category')
        
        # Gráfico de comparación
        if not metrics['monthly_reminds_created'].empty or not metrics['monthly_reminds_sent'].empty:
            # Crear un dataframe combinado para la comparación
            df_created = metrics['monthly_reminds_created'].rename(columns={'count': 'Creados'})
            df_sent = metrics['monthly_reminds_sent'].rename(columns={'count': 'Enviados'})
            
            # Combinar dataframes
            df_comparison = pd.merge(df_created, df_sent, on='month', how='outer').fillna(0)
            
            # Crear figura de comparación
            comparison_fig = go.Figure()
            comparison_fig.add_trace(go.Bar(
                x=df_comparison['month'],
                y=df_comparison['Creados'],
                name='Creados',
                marker_color='#FF9900'
            ))
            comparison_fig.add_trace(go.Bar(
                x=df_comparison['month'],
                y=df_comparison['Enviados'],
                name='Enviados',
                marker_color='#109618'
            ))
            comparison_fig.update_xaxes(type='category')

            comparison_fig.update_layout(
                title='Comparación: Recordatorios Creados vs Enviados por Mes',
                xaxis_title='Mes',
                yaxis_title='Número de Recordatorios',
                barmode='group'
            )
        else:
            comparison_fig = go.Figure()
            comparison_fig.update_layout(
                title='No hay datos para mostrar en el período seleccionado',
                xaxis_title='Mes',
                yaxis_title='Número de Recordatorios'
            )

    # Formatear estadísticas adicionales
    avg_daily_users = f"Usuarios: {metrics['average_daily_users']:.2f}"
    avg_daily_reminds_created = f"Recordatorios Creados: {metrics['average_daily_reminds_created']:.2f}"
    avg_daily_reminds_sent = f"Recordatorios Enviados: {metrics['average_daily_reminds_sent']:.2f}"
    
    avg_monthly_users = f"Usuarios: {metrics['average_monthly_users']:.2f}"
    avg_monthly_reminds_created = f"Recordatorios Creados: {metrics['average_monthly_reminds_created']:.2f}"
    avg_monthly_reminds_sent = f"Recordatorios Enviados: {metrics['average_monthly_reminds_sent']:.2f}"
    
    avg_per_user_daily_reminds_created = f"Recordatorios Creados Diarios: {metrics['average_per_user_daily_reminds_created']:.2f}"
    avg_per_user_daily_reminds_sent = f"Recordatorios Enviados Diarios: {metrics['average_per_user_daily_reminds_sent']:.2f}"
    avg_per_user_monthly_reminds_created = f"Recordatorios Creados Mensuales: {metrics['average_per_user_monthly_reminds_created']:.2f}"
    avg_per_user_monthly_reminds_sent = f"Recordatorios Enviados Mensuales: {metrics['average_per_user_monthly_reminds_sent']:.2f}"
    
    return (
        total_users,
        total_reminds_created,
        total_reminds_sent,
        per_user_reminds_created,
        per_user_reminds_sent,
        users_fig,
        created_fig,
        sent_fig,
        comparison_fig,
        avg_daily_users,
        avg_daily_reminds_created,
        avg_daily_reminds_sent,
        avg_monthly_users,
        avg_monthly_reminds_created,
        avg_monthly_reminds_sent,
        avg_per_user_daily_reminds_created,
        avg_per_user_daily_reminds_sent,
        avg_per_user_monthly_reminds_created,
        avg_per_user_monthly_reminds_sent
    )

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)