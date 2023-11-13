import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np

# 加载数据
co2_data = pd.read_csv('CO2_EMISSION.csv')
forest_cover_data = pd.read_csv('ForestArea.csv')
temperature_change_data = pd.read_csv('temperature_data.csv')
df = pd.read_csv('natural.csv')  # 原始数据
df['Start Year'] = df['Start Year'].astype('int')
df = df[(df['Start Year'] >= 2000) & (df['Start Year'] <= 2020)]

app = dash.Dash(__name__)

# Create buttons for regions
button_style = {
    'background-color': '#007bff',
    'color': 'white',
    'border': 'none',
    'padding': '10px 20px',
    'text-align': 'center',
    'text-decoration': 'none',
    'display': 'inline-block',
    'font-size': '16px',
    'margin': '4px 10px',
    'transition-duration': '0.4s',
    'cursor': 'pointer',
    'border-radius': '12px'
}

button_hover_style = {
    'background-color': 'white',
    'color': 'black',
    'border': '2px solid #007bff'
}

# 假设 region_colors 是一个包含区域和颜色的字典
region_colors = {
    'Asia': '#6d77fa',  # 例: 区域名和颜色
    'Oceania': '#f16951',
    'Europe':'#39d4ae',
    'Americas':'#c08afc',
    'Africa':'#ffd5b4',
    'All': '#e5ecf4'  # 'All' 按钮的默认颜色
}

buttons = [html.Button(region, id=region, n_clicks=0, style={**button_style, 'background-color': region_colors.get(region, '#e5ecf4')}, className='button') for region in df['Region'].unique()]
buttons.append(html.Button("All", id="all", n_clicks=0, style=button_style, className='button'))

def cor_ma(df,co2_data,forest_cover_data,temperature_change_Data):
    # 数据格式转换
    disaster_type = df['Disaster Type'].unique()
    disaster_dict = {i: [] for i in disaster_type}

    year_list = list(df.groupby('Start Year'))
    for i in year_list:
        year = i[1].groupby('Disaster Type').size().reset_index(name='Count')

        year_dict = {}
        for j in range(len(year)):
            year_dict[year.iloc[j, 0]] = year.iloc[j, 1]

        for j in disaster_dict.keys():
            if j in year_dict.keys():
                disaster_dict[j].append(year_dict[j])
            else:
                disaster_dict[j].append(0)

    disaster = pd.DataFrame(disaster_dict)
    disaster['Year'] = [i for i in range(2000, 2021, 1)]
    disaster = disaster.merge(temperature_change_Data, on='Year', how='inner')

    sum_series = co2_data.drop(columns=['Year']).sum(axis=1)
    co2_data = pd.DataFrame({'Year': co2_data['Year'], 'CO2_Emission': sum_series})

    sum_series = forest_cover_data.drop(columns=['Year']).sum(axis=1)
    forest_cover_data = pd.DataFrame({'Year': forest_cover_data['Year'], 'Forest_Area': sum_series})

    disaster = disaster.merge(co2_data, on='Year', how='inner')
    disaster = disaster.merge(forest_cover_data, on='Year', how='inner')

    # 求sperman相关性矩阵
    spearman_dict = {}
    for i in disaster_type:
        spearman_dict[i] = []
        for j in ['Anomaly', 'CO2_Emission', 'Forest_Area']:
            spearman_corr = abs(disaster[j].corr(disaster[i], method='spearman'))
            spearman_dict[i].append(spearman_corr)

    cor_matrix = pd.DataFrame(spearman_dict)
    return cor_matrix

app.layout = html.Div([
    html.H1('Some Potential Causes for Natural Disasters', style={'text-align': 'center','height':'25%'}),

    html.Div(buttons, style={'display': 'flex', 'justify-content': 'center','height':'5%'}),

    html.Div([
        # 第一列
        html.Div([
            dcc.Graph(id='tree-map', style={'width': '100%','height': '50%'}),
            dcc.Graph(id='bar-chart', style={'width': '100%','height': '50%'})
        ], style={'display': 'flex', 'flex-direction': 'column', 'width': '30%','height':'70%'}),

        # 第二列
        html.Div([
            dcc.Graph(id='co2-line-chart', style={'height': '50%'}),
            dcc.Graph(id='forest-line-chart', style={'height': '50%'})
        ], style={'display': 'flex', 'flex-direction': 'column', 'width': '30%','height':'70%'}),

        # 第三列
        html.Div([
            dcc.Graph(id='temp-line-chart', style={'height': '40%'}),
            dcc.Graph(id='heatmap', style={'height': '60%'})
        ], style={'display': 'flex', 'flex-direction': 'column', 'width': '40%','height':'70%'})
    ], style={'display': 'flex'}),

], style={})

# Callback function to update graphs
@app.callback(
    [Output('tree-map', 'figure'), Output('bar-chart', 'figure'),
     Output('co2-line-chart', 'figure'), Output('forest-line-chart', 'figure'),
     Output('temp-line-chart', 'figure'), Output('heatmap', 'figure')],
    [Input(region, 'n_clicks') for region in df['Region'].unique()] + [Input("all", "n_clicks")]
)

def update_graphs(*args):
    ctx = dash.callback_context

    # Initialize button_id to handle the case when no button is clicked
    button_id = "all"

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Apply filters based on the button_id
    filtered_df = df if button_id == "all" else df[df['Region'] == button_id]
    # 数据格式转换
    disaster_type = filtered_df['Disaster Type'].unique()
    disaster_dict = {i: [] for i in disaster_type}

    year_list = list(df.groupby('Start Year'))
    for i in year_list:
        year = i[1].groupby('Disaster Type').size().reset_index(name='Count')

        year_dict = {}
        for j in range(len(year)):
            year_dict[year.iloc[j, 0]] = year.iloc[j, 1]

        for j in disaster_dict.keys():
            if j in year_dict.keys():
                disaster_dict[j].append(year_dict[j])
            else:
                disaster_dict[j].append(0)

    disaster = pd.DataFrame(disaster_dict)
    disaster['Year'] = [i for i in range(2000, 2021, 1)]
    disaster = disaster.merge(temperature_change_data, on='Year', how='inner')

    # Update tree-map and bar-chart
    grouped_df = filtered_df.groupby(['Region', 'Subregion']).size().reset_index(name='Disaster Count')
    tree_fig = px.treemap(grouped_df, path=['Region', 'Subregion'], values='Disaster Count')

    bar_df = filtered_df.groupby(['Start Year', 'Disaster Type']).size().reset_index(name='Count')
    bar_fig = px.bar(bar_df, x='Start Year', y='Count', color='Disaster Type', barmode='stack')

    # 更新布局设置X轴和Y轴的标题
    bar_fig.update_layout(
        xaxis_title='Year',  # X轴标题
        yaxis_title='Count'  # Y轴标题
    )

    cor_matrix = [[2,1],[7,9]]
    # Update line charts for CO2 Emissions and Forest Cover
    # Assuming that the region names in CO2 and Forest Cover datasets match the regions in your tree map
    if button_id != "all":
        co2_fig = px.line(co2_data, x='Year', y=[button_id])
        forest_fig = px.line(forest_cover_data, x='Year', y=[button_id])
        cor_matrix = cor_ma(filtered_df,co2_data[['Year'] + [button_id]],forest_cover_data[['Year'] + [button_id]],temperature_change_data)
        # 构造热图的数据
        heatmap_fig = go.Figure(data=go.Heatmap(
            z=cor_matrix,
            x = ['Drought','Flood', 'Extreme temperature', 'Volcanic activity', 'Storm', 'Wildfire', 'Earthquake'],
            y=['Temperature Change','CO2 Emission','Forest Area Decreasing'],
            colorscale='Viridis'
        ))
        co2_fig.update_layout(yaxis_title='CO2 Emission(KT)')
        forest_fig.update_layout(yaxis_title='Forest Area(Km2)')
        heatmap_fig.update_layout(xaxis_title='Disaster Type',
                                  yaxis_title='Effector')
    else:
        co2_fig = px.line(co2_data, x='Year', y=co2_data.columns[1:])
        forest_fig = px.line(forest_cover_data, x='Year', y=forest_cover_data.columns[1:])
        cor_matrix = cor_ma(filtered_df,co2_data,forest_cover_data,temperature_change_data)
        # 构造热图的数据
        heatmap_fig = go.Figure(data=go.Heatmap(
            z=cor_matrix,
            x = ['Drought','Flood', 'Extreme temperature', 'Volcanic activity', 'Storm', 'Wildfire', 'Earthquake'],
            y=['Temperature Change','CO2 Emission','Forest Area Decreasing'],
            colorscale='Viridis'
        ))
        co2_fig.update_layout(yaxis_title='CO2 Emission(KT)')
        forest_fig.update_layout(yaxis_title='Forest Area(Km2)')
        heatmap_fig.update_layout( yaxis_title='Effector',
                                  xaxis_title='Disaster Type')

    # Line chart for Temperature Anomaly
    temp_fig = px.line(temperature_change_data, x='Year', y='Anomaly')
    temp_fig.update_layout(yaxis_title='Temperature(℉)' )

    return tree_fig, bar_fig, co2_fig, forest_fig, temp_fig, heatmap_fig

# Run application
if __name__ == '__main__':
    app.run_server(debug=True)