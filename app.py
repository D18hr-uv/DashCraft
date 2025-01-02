from flask import Flask, render_template, request, redirect
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Flask app
flask_app = Flask(__name__)

# Dash app
dash_app = dash.Dash(__name__, server=flask_app, url_base_pathname='/dashboard/')

# Placeholder for uploaded data
global_data = pd.DataFrame()

# Flask route for homepage
@flask_app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            global global_data
            global_data = pd.read_csv(file)
            return redirect('/dashboard/')
    return render_template('index.html')

# Dash layout
dash_app.layout = html.Div([
    html.H1("Interactive Data Visualization Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Select Columns for X-Axis"),
        dcc.Dropdown(id='x-axis-column', placeholder='Select X-Axis', multi=False),
        
        html.Label("Select Columns for Y-Axis"),
        dcc.Dropdown(id='y-axis-column', placeholder='Select Y-Axis', multi=True),
        
        html.Label("Select Plot Type"),
        dcc.RadioItems(
            id='plot-type',
            options=[
                {'label': 'Line Chart', 'value': 'line'},
                {'label': 'Scatter Plot', 'value': 'scatter'},
                {'label': 'Pie Chart', 'value': 'pie'}
            ],
            value='line',
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        ),
    ], style={'padding': '10px', 'border': '1px solid #ccc', 'borderRadius': '10px', 'margin': '10px'}),
    
    dcc.Graph(id='data-graph'),
])

# Dash callbacks
@dash_app.callback(
    [Output('x-axis-column', 'options'),
     Output('y-axis-column', 'options'),
     Output('data-graph', 'figure')],
    [Input('x-axis-column', 'value'),
     Input('y-axis-column', 'value'),
     Input('plot-type', 'value')]
)
def update_graph(x_column, y_columns, plot_type):
    global global_data

    # Dropdown options
    options = [{'label': col, 'value': col} for col in global_data.columns]
    
    # Initialize figure
    figure = {'data': [], 'layout': {'title': 'No data selected'}}

    # Plotting logic
    if x_column and y_columns:
        if plot_type == 'line':
            figure = {
                'data': [
                    {'x': global_data[x_column], 'y': global_data[y], 'type': 'line', 'name': y}
                    for y in y_columns
                ],
                'layout': {'title': f'Line Chart: {", ".join(y_columns)} vs {x_column}'}
            }
        elif plot_type == 'scatter':
            figure = {
                'data': [
                    {'x': global_data[x_column], 'y': global_data[y], 'mode': 'markers', 'name': y}
                    for y in y_columns
                ],
                'layout': {'title': f'Scatter Plot: {", ".join(y_columns)} vs {x_column}'}
            }
        elif plot_type == 'pie' and len(y_columns) == 1:
            figure = {
                'data': [{
                    'labels': global_data[x_column],
                    'values': global_data[y_columns[0]],
                    'type': 'pie'
                }],
                'layout': {'title': f'Pie Chart: {y_columns[0]} by {x_column}'}
            }
    
    return options, options, figure

# Run the app
if __name__ == '__main__':
    flask_app.run(debug=True)
