import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import io
from reportlab.pdfgen import canvas

def init_dashboard(flask_app):
    # Cria o aplicativo Dash integrado ao Flask, na subrota /dashboard/
    dash_app = dash.Dash(
        server=flask_app,
        routes_pathname_prefix='/dashboard/'
    )
    
    # Dados fictícios "base" (sem filtro)
    df_especialidade_base = pd.DataFrame({
        'Especialidade': ['Psiquiatria', 'Psicologia', 'Pediatria', 'Neuropediatria', 'Neuropsiquiatria'],
        'Quantidade': [120, 90, 150, 80, 110]
    })

    df_medicos_base = pd.DataFrame({
        'Médico': ['Dr. Silva', 'Dra. Oliveira', 'Dr. Souza', 'Dra. Lima', 'Dr. Pereira'],
        'Consultas': [60, 75, 50, 90, 65]
    })

    df_avaliacao_base = pd.DataFrame({
        'Nota': [1, 2, 3, 4, 5],
        'Avaliacoes': [5, 15, 40, 30, 10]
    })

    # Função para simular dados fictícios diferentes para filtros (ex.: ano 2024)
    def get_data_for_filters(month, year):
        if year == 2024:
            factor = (month / 12.0) + 0.5 if month is not None else 1.0
        else:
            factor = 1.0
        
        df_especialidade = df_especialidade_base.copy()
        df_especialidade['Quantidade'] = df_especialidade['Quantidade'] * factor

        df_medicos = df_medicos_base.copy()
        df_medicos['Consultas'] = df_medicos['Consultas'] * factor

        df_avaliacao = df_avaliacao_base.copy()
        df_avaliacao['Avaliacoes'] = df_avaliacao['Avaliacoes'] * factor

        return df_especialidade, df_medicos, df_avaliacao

    def gerar_graficos(df_especialidade, df_medicos, df_avaliacao):
        fig_especialidade = px.pie(
            df_especialidade, 
            names='Especialidade', 
            values='Quantidade', 
            title='Consultas por Especialidade',
            template='plotly_dark'
        )

        fig_medicos = px.bar(
            df_medicos, 
            x='Médico', 
            y='Consultas', 
            title='Médicos Mais Ativos',
            labels={'Consultas': 'Número de Consultas'},
            template='plotly_dark'
        )

        fig_avaliacao = px.line(
            df_avaliacao, 
            x='Nota', 
            y='Avaliacoes', 
            title='Avaliação do Atendimento', 
            markers=True,
            template='plotly_dark'
        )
        return fig_especialidade, fig_medicos, fig_avaliacao

    # Layout do Dashboard com visual dark, filtros e botões para atualizar e baixar o arquivo Excel
    dash_app.layout = html.Div(
        children=[
            html.H1("Relatório das Consultas Médicas", style={'textAlign': 'center', 'color': '#fff'}),

            # Filtros e botões
            html.Div(
                children=[
                    html.Div(
                        children=[  
                            html.Label("Mês:", style={'color': '#fff'}),
                            dcc.Dropdown(
                                id="month-filter",
                                options=[{'label': f'{i:02d}', 'value': i} for i in range(1, 13)],
                                placeholder="Selecione o mês",
                                style={'backgroundColor': '#fff', 'color': '#444'}
                            )
                        ],
                        style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}
                    ),
                    html.Div(
                        children=[
                            html.Label("Ano:", style={'color': '#fff'}),
                            dcc.Dropdown(
                                id="year-filter",
                                options=[{'label': str(year), 'value': year} for year in range(2020, 2025)],
                                placeholder="Selecione o ano",
                                style={'backgroundColor': '#fff', 'color': '#444'}
                            )
                        ],
                        style={'width': '30%', 'display': 'inline-block'}
                    ),
                    html.Div(
                        children=[
                            html.Br(),
                            html.Button(
                                "Atualizar Dados", 
                                id="update-data-button", 
                                n_clicks=0,
                                style={
                                    'backgroundColor': '#3498db',
                                    'border': 'none',
                                    'padding': '10px 20px',
                                    'color': '#fff',
                                    'borderRadius': '5px',
                                    'cursor': 'pointer',
                                    'fontSize': '16px',
                                    'marginRight': '10px'
                                }
                            ),
                            html.Button(
                                "Baixar Excel", 
                                id="download-excel-button", 
                                n_clicks=0,
                                style={
                                    'backgroundColor': '#1abc9c',
                                    'border': 'none',
                                    'padding': '10px 20px',
                                    'color': '#fff',
                                    'borderRadius': '5px',
                                    'cursor': 'pointer',
                                    'fontSize': '16px'
                                }
                            )
                        ],
                        style={'width': '30%', 'display': 'inline-block', 'textAlign': 'right'}
                    )
                ],
                style={'margin': '20px'}
            ),

            # Linha com os gráficos: duas colunas para Consultas por Especialidade e Médicos Mais Ativos
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.H3("", style={'color': '#fff'}),
                            dcc.Graph(id="especialidade-graph")
                        ],
                        style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}
                    ),
                    html.Div(
                        children=[
                            html.H3("", style={'color': '#fff'}),
                            dcc.Graph(id="medicos-graph")
                        ],
                        style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}
                    )
                ],
                style={'display': 'flex', 'justifyContent': 'space-between'}
            ),

            # Gráfico de Avaliação do Atendimento
            html.Div(
                children=[
                    html.H3("", style={'color': '#fff'}),
                    dcc.Graph(id="avaliacao-graph")
                ],
                style={'marginTop': '40px'}
            ),

            # Componente para download do arquivo Excel
            dcc.Download(id="download-dataframe-excel")
        ],
        style={'padding': '20px', 'backgroundColor': '#2b2b2b', 'minHeight': '100vh'}
    )

    # Callback para atualizar os gráficos ao clicar no botão "Atualizar Dados"
    @dash_app.callback(
        [Output("especialidade-graph", "figure"),
         Output("medicos-graph", "figure"),
         Output("avaliacao-graph", "figure")],
        Input("update-data-button", "n_clicks"),
        [State("month-filter", "value"),
         State("year-filter", "value")]
    )
    def update_graphs(n_clicks, month, year):
        df_especialidade, df_medicos, df_avaliacao = get_data_for_filters(month, year)
        return gerar_graficos(df_especialidade, df_medicos, df_avaliacao)

    # Callback para gerar o Excel e iniciar o download ao clicar no botão "Baixar Excel"
    @dash_app.callback(
        Output("download-dataframe-excel", "data"),
        Input("download-excel-button", "n_clicks"),
        [State("month-filter", "value"),
         State("year-filter", "value")],
        prevent_initial_call=True
    )
    def generate_excel(n_clicks, month, year):
        # Gerar os dados conforme os filtros aplicados
        df_especialidade, df_medicos, df_avaliacao = get_data_for_filters(month, year)
        
        # Combinar os dados em um arquivo Excel com múltiplas abas
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_especialidade.to_excel(writer, sheet_name='Especialidades', index=False)
            df_medicos.to_excel(writer, sheet_name='Medicos', index=False)
            df_avaliacao.to_excel(writer, sheet_name='Avaliacoes', index=False)
        excel_bytes = output.getvalue()
        output.close()
        
        # Retorna o arquivo para download com extensão .xlsx
        return dcc.send_bytes(excel_bytes, "relatorio.xlsx")

    return dash_app
