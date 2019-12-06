import collections
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import networkx as nx
from CreateEdges import *

conns = create_edges(False)

# graphData contains all the objects for creating the graph. It is a list of go.scatter objects
graphData = []
studentInfo = {}

for edge in conns:
    studentInfo[edge[1]] = edge[3]

# Function that returns all the objects for creating the graph
def make_graph(range, user_id, assignment):

    # graphdatafun as local variable contains all the objects for creating the graph. It is a list of go.scatter objects
    graphdatafun = []
    edges = []
    scores = collections.defaultdict(int)

    # select edges and nodes needed according to the different graph view - (All students OR one student)
    if user_id == -1 and assignment == '-1':
        for conn in conns:
            if conn[2] <= range[1] and conn[2] >= range[0]:
                edges.append((conn[0], conn[1]))
                # scores is for looking up the grades between student nodes and assignment nodes
                scores[(conn[0], conn[1])] = conn[2]
                scores[(conn[1], conn[0])] = conn[2]
    elif user_id == -1 and assignment != '-1':
        for conn in conns:
            if conn[2] <= range[1] and conn[2] >= range[0]:
                if conn[0] == assignment:
                    edges.append((conn[0], conn[1]))
                    scores[(conn[0], conn[1])] = conn[2]
                    scores[(conn[1], conn[0])] = conn[2]
    elif user_id != -1 and assignment == '-1':
        for conn in conns:
            if conn[1] == user_id:
                if conn[2] <= range[1] and conn[2] >= range[0]:
                    edges.append((conn[0], conn[1]))
                    scores[(conn[0], conn[1])] = conn[2]
                    scores[(conn[1], conn[0])] = conn[2]

    # create graph G
    G = nx.Graph()
    G.add_edges_from(edges)

    # get a x,y position for each node
    pos = nx.layout.spring_layout(G)

    # add a pos attribute to each node
    for node in G.nodes:
        G.nodes[node]['pos'] = list(pos[node])

    pos=nx.get_node_attributes(G,'pos')

    dmin=1
    ncenter=0
    for n in pos:
        x,y=pos[n]
        d=(x-0.5)**2+(y-0.5)**2
        if d<dmin:
            ncenter=n
            dmin=d

    p=nx.single_source_shortest_path_length(G,ncenter)

    # A function that returns a go.scatter object which is the singel edge
    def make_edge(x, y, width):
        """
            Args:
            x: a tuple of the x from and to, in the form: tuple([x0, x1, None])
            y: a tuple of the y from and to, in the form: tuple([y0, y1, None])
            width: The width of the line

            Returns:
            a Scatter plot which represents a line between the two points given.
            """
        return  go.Scatter(
                           x=x,
                           y=y,
                           line=dict(width=width,color='#000000'),
                           hoverinfo='none',
                           mode='lines')

    # Assign weights and create edges objects.
    for edge in G.edges():
        x0, y0 = G.node[edge[0]]['pos']
        x1, y1 = G.node[edge[1]]['pos']

        # Different weight for grades
        ranges = {0.1 : [0,54], 0.5 : [55, 60],
                  0.9 : [61,64], 1.3 : [65,70],
                  1.7 : [71,74], 2.1 : [75,80],
                  2.5 : [81,84], 2.9 : [85,90],
                  3.3 : [91,94], 3.7 : [95,101]}

        # Find the corresponding weight for the current grade, if not found, return 0.5 as default value
        gra = next((key for key, (low, high) in ranges.items() if low <= scores[edge] <= high), 0.5)

        # Append the new edge
        graphdatafun.append(make_edge(tuple([x0, x1, None]), tuple([y0, y1, None]), gra))


    # Create nodes for the graph
    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='Rainbow',
            reversescale=True,
            color=[],
            size=[],
            colorbar=dict(
                thickness=15,
                title='Number of connected components',
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=2)))

    for node in G.nodes():
        x, y = G.node[node]['pos']
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])

    # Differential nodes
    for node, adjacencies in enumerate(G.adjacency()):

        # Add size to nodes according to the # of connections between them
        tmp = 10 + len(adjacencies[1])
        node_trace['marker']['size'] += tuple([tmp])

        # Make the size of student nodes larger
        student = str(adjacencies[0])
        if student.isnumeric():
            node_trace['marker']['color']+=(15,)
        else:
            node_trace['marker']['color']+=tuple([len(adjacencies[1])])

        # Add information for hover over
        tp = str(adjacencies[0])
        if tp.isnumeric():
            node_info = 'Id: ' + str(adjacencies[0]) + ':<br>Name: ' + studentInfo[int(tp)] + '<br># of connections: '+str(len(adjacencies[1]))
        else:
            node_info = 'Name: ' + str(adjacencies[0]) + '<br># of connections: '+str(len(adjacencies[1]))

        node_trace['text']+=tuple([node_info])

    # Append all the nodes objects
    graphdatafun.append(node_trace)

    return (graphdatafun, len(G.nodes), len(G.edges))

################### START OF DASH APP ###################

app = dash.Dash()
server = app.server

# Fetch CSS file to add style format and ability to use columns
app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

# Setup the HTML layout of the webpage
app.layout = html.Div([

                # New section (top-left graph and its slider)
                html.Div([
                    dcc.Graph(
                        id='Graph',
                        hoverData = {}
                    ),
                    dcc.RangeSlider(
                        id='my-slider',
                        min=50, max=100, value=[50,60],
                        step=None,
                        marks={50: '50', 60: '60', 70: '70', 80: '80', 90: '90', 100: '100'} # edit here
                    ),
                ], style={'width': '49%', 'display': 'inline-block'}),

                # New section (top-right graph)
                html.Div([
                    dcc.Graph(id='single-student-graph'),
                ], style={'display': 'inline-block', 'width': '49%'}),

                # New row under the two graphs
                html.Div(className='row', children=[

                    # Column 1: data status information
                    html.Div([html.H3('Overall Data'),
                              html.P('Number of nodes: ' + '', id='num_nodes'),
                              html.P('Number of edges: ' + '', id='num_edges')],
                              className='three columns'),

                    # Column 2: add nodes interface
                    html.Div([
                            html.H3('Add Nodes'),
                            dcc.Input(id='input-box', type='text'),
                            html.Button('Add Connection', id='add-button'),
                        ], className='three columns'),

                    # Column 3: select nodes interface (multi-select dropdown box)
                    html.Div([
                    		html.H3('Select Nodes'),
                    		dcc.Dropdown(
                    			id='check',

                                # default options - can be replaced with assignments
                    			options=[
                    				{'label': 'A1', 'value': 'A1'},
                    				{'label': 'A2', 'value': 'A2'},
                    				{'label': 'A3', 'value': 'A3'},
                    				{'label': 'B1', 'value': 'B1'},
                    				{'label': 'B2', 'value': 'B2'},
                    				{'label': 'B3', 'value': 'B3'},
                    				{'label': 'C1', 'value': 'C1'},
                    				{'label': 'C2', 'value': 'C2'},
                    				{'label': 'C3', 'value': 'C3'}
                    			],
                    			value = [],
                    			multi=True),

                            # Select all button to select all of the nodes
                    		html.Button('Select All', id='select-all')
                    			],className='three columns'),

                    # Column 4: Update buttons
                    html.Div([
                    		html.H3('Update'),
                    		html.Button('Refresh graph', id='update-graph'),
                    		html.Button('Refresh data', id='pull-canvas')
                    ], className='three columns')

                    ])
                ])

##### APP CALLBACKS ####

# App callback to add text entered in 'add nodes' interface to 'select nodes' options
@app.callback(
	dash.dependencies.Output('check', 'options'),
	[dash.dependencies.Input('add-button', 'n_clicks')],
	[dash.dependencies.State('input-box', 'value'), dash.dependencies.State('check', 'options')])
def update_options(n_clicks, new_value, current_options):
	if not n_clicks:
		return current_options
	current_options.append({'label': new_value, 'value': new_value})
	return current_options

# App callback that takes sliderrange input and outputs an updated graph
@app.callback(
    [dash.dependencies.Output('Graph', "figure"),
    dash.dependencies.Output('num_nodes', "children"),
    dash.dependencies.Output('num_edges', "children")],
    [dash.dependencies.Input('my-slider', "value")])
def update_graph(n):
    global graphData
    graphData, nodes, edges = make_graph(n, -1, '-1')
    fig = go.Figure(data=graphData,
                 layout=go.Layout(
                    title='<b>{}</b><br>'.format('Systems Curriculum'),
                    titlefont=dict(size=36),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=60),
                    annotations=[ dict(
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 ) ],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    return fig, 'Num of Nodes: ' + str(nodes), 'Num of Edges: ' + str(edges)

# App callback that selects all available options when 'select all' button clicked
@app.callback(
    dash.dependencies.Output('check', 'value'),
    [dash.dependencies.Input('select-all', 'n_clicks')],
    [dash.dependencies.State('check', 'options')])
def update_selections(n_clicks, current_options):
    new_value = []
    for elem in current_options:
        new_value.append(elem['value'])
    return new_value

# App callback that updates the single-view graph when hovering over data point on main graph
@app.callback(
    dash.dependencies.Output('single-student-graph', 'figure'),
    [dash.dependencies.Input('Graph', 'hoverData'),
    dash.dependencies.Input('my-slider', "value")])
def update_single_student_graph(hoverData, n):
    global graphData
    print('Hover Data: {}'.format(hoverData))
    print('n: {}'.format(n))
    flag = False
    user_id = -1
    assignment = '-1'
    try:
        sep = '#'
        rest = hoverData['points'][0]['text'].split(sep, 1)[0]
        print(rest + 'rest end')
        sep = ":"
        print(rest.split(":",2)[1])
        user_id = int(rest.split(sep, 2)[1])
        flag = True
    except ValueError:
        print('Error: This is not a Student Node')
    except KeyError:
        print('Error: Could not locate dictionary key')

    #Not flag = Assignment Node
    if not flag:
        try:
            sep = '#'
            rest = hoverData['points'][0]['text'].split(sep, 1)[0]
            sep = ": "
            assignment = rest.split(sep, 1)[1][: -4]
        except ValueError:
            print('Error: This is not an Assignment Node')
        except KeyError:
            print('Error: Could not locate dictionary key')


    graphData, nodes, edges = make_graph(n, user_id, assignment)
    fig = go.Figure(data=graphData,
                 layout=go.Layout(
                    title='<b>User: {}</b><br>'.format(studentInfo[user_id]),
                    titlefont=dict(size=24),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=60),
                    annotations=[ dict(
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 ) ],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    return fig

# MAIN METHOD - starts the server with the dash app
if __name__ == '__main__':
    app.run_server(debug=True)
