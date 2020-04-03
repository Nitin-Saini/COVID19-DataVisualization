from flask import Flask, render_template
import plotly
import plotly.graph_objs as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import requests
import pandas as pd
import numpy as np
import json

app = Flask(__name__)

url = 'https://www.worldometers.info/coronavirus/#countries'
header = {
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
  "X-Requested-With": "XMLHttpRequest"
}
r = requests.get(url, headers=header)
corona = pd.read_html(r.text)[1]
corona.fillna(0, inplace=True)
corona['CountryCode'] = corona['Country,Other'].str[:3].str.upper() 
# Taking top 10 affected countries due to coronavirus
corona_data = corona.sort_values(by=['TotalCases'], ascending=False).iloc[1:11, :]
for x in ['NewCases','TotalCases','TotalDeaths','NewDeaths','TotalRecovered']:
    if corona_data[x].dtype != 'int64':
        corona_data[x] = corona_data[x].replace(',','', regex=True).astype('int')

# Set up the chart first 2 charts

def create_plot1():
    fig = make_subplots(rows=1, cols=3, subplot_titles = ['Total & New Cases','Total Recovered','Total Deaths'])
    
    fig.append_trace(
        go.Bar(
            x=corona_data['Country,Other'],
            y=corona_data.TotalDeaths,
            name='Deaths',
            marker={'color':'black'},
        ),
    row=1, col=3)

    fig.append_trace(
        go.Bar(
            x=corona_data['Country,Other'],
            y=corona_data.TotalRecovered,
            name='Recovered',
            marker={'color':'green'}
        ), 
    row=1, col=2)

    fig.append_trace(
        go.Bar(
            x=corona_data['Country,Other'],
            y=corona_data.TotalCases,
            name='Total Cases',
            marker={'color':'orange'}
        ),
    row=1, col=1)
    fig.add_trace(
        go.Bar(
            x=corona_data['Country,Other'],
            y=corona_data.NewCases,
            name='New Cases',
            marker={'color':'red'}
        ),
    row=1, col=1)
    # fig.update_xaxes(title_text="Country")
    fig.update_layout(
        barmode='group',
        title_text="Nitin Saini's Dashboard"
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def create_plot2():
    # Line Data
    total_link = 'https://covid.ourworldindata.org/data/ecdc/total_cases.csv'
    total_file = pd.read_csv(total_link)
    total_case = pd.DataFrame(total_file.iloc[20:,0:2])
    total_case['New_Case']=total_case['World'].diff()
    total_case=pd.DataFrame(total_case.iloc[1:,:])
    total_case = total_case.rename(columns={"date": "Date","World": "Total_Case"})
    total_case['Date']= pd.to_datetime(total_case['Date'])

    ntdoy_URL = "https://finance.yahoo.com/quote/NTDOY/history?period1=1579564800&period2=1585872000&interval=1d&filter=history&frequency=1d"
    ntdoy = pd.read_html(ntdoy_URL)[0]
    ntdoy = ntdoy.drop(["Open","High", "Low", "Adj Close**",  "Volume"], axis=1)
    ntdoy = ntdoy.iloc[:-1,:]
    ntdoy["Date"] = pd.to_datetime(ntdoy['Date'])
    ntdoy['Close*']= ntdoy['Close*'].astype("float")
    ntdoy = ntdoy.rename(columns={"Close*":"Close"})
    ntdoy.sort_values("Date")
    total_case
    line_plot = total_case.merge(ntdoy, on="Date")
    
    # US Map Data
    url = 'https://www.worldometers.info/coronavirus/country/us/'
    r = requests.get(url)
    us_data = pd.read_html(r.text)[1]
    us_data = us_data.fillna(0)

    x = ["Diamond Princess Cruise","Wuhan Repatriated","Puerto Rico",
         "Alaska","Guam", "Northern Mariana Islands","United States Virgin Islands",
         "Hawaii", "District Of Columbia", "Total:"]

    us_data = us_data[~us_data['USAState'].isin(x)]
    us_data = us_data.rename(columns={'USAState': 'State'})

    df = pd.read_csv('https://raw.githubusercontent.com/jasperdebie/VisInfo/master/us-state-capitals.csv')
    df = df.drop("description", axis=1)
    x = ['Alaska', 'Hawaii']
    df = df[~df['name'].isin(x)]
    df = df.rename(columns= {"name":"State"})

    bubble_data = df.merge(us_data, on="State")
    bubble_data['text'] = bubble_data['State'] + '<br>TotalCases:' + (bubble_data['TotalCases']).astype(str)
    bubble_data = bubble_data.sort_values(by = ["TotalCases"], ascending=False)

    limits = [(0,1),(2,10),(11,20),(21,30),(31,48)] # Ranking
    colors = ["maroon","red","orange","grey","lightgrey"]
    names = ["Top 1", "Top 10", "11~20","21~30","30~48"]
    scale = 30
    #plots
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "geo"}, {"secondary_y": True,"type": "xy"}]],
        subplot_titles=("US states Confirmed Cases", "Nintendo Stock Price with Rising Covid19 Cases"))

    for i in range(len(limits)):
        lim = limits[i]
        df_sub = bubble_data[lim[0]:lim[1]]
        fig.add_trace(go.Scattergeo(
            locationmode = 'USA-states',
            lon = df_sub['longitude'],
            lat = df_sub['latitude'],
            text = df_sub['text'],
            marker = dict(
                size = df_sub['TotalCases']/scale,
                color = colors[i],
                line_color='rgb(40,40,40)',
                line_width=0.5,
                sizemode = 'area'),
            showlegend=True,
            name = names[i]
            ),row=1,col=1)

    fig.add_trace(
        go.Scatter(
            x=line_plot['Date'], 
            y=line_plot['Total_Case'],
            mode='lines+markers', 
            name='Total Cases'),
        secondary_y = False,
        row=1,col=2
    )
    fig.add_trace(
        go.Scatter(
            x=line_plot['Date'], 
            y=line_plot['Close'],
            mode='lines+markers',
            name='Nintendo Price'),
        secondary_y=True,
        row=1,col=2
    )
    # Set x-axis title
    fig.update_xaxes(title_text="Date")
    # Set y-axes titles
    fig.update_yaxes(title_text="Total Cases(World)", secondary_y=False)
    fig.update_yaxes(title_text="Nintendo Price", secondary_y=True)
    fig.update_layout(
        # width=1750,
        title_text = "Luca Chuang's Dashboard",
        showlegend = True,
        legend=dict(x = 0.4,y = 0.5),
        geo = dict(
            scope = 'usa',
            landcolor = 'rgb(217, 217, 217)')
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

#Data for Smrishi Mangla
def create_plot3():

    #download confirmed cases data from JHU dashboard
    url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    df_confirmed = pd.read_csv(url)

    #top ten impacted countries 
    df_tmp_subset = df_confirmed.drop(['Province/State','Lat','Long'],axis=1)
    df_tmp_subset = pd.DataFrame(df_tmp_subset.groupby(['Country/Region'],as_index=False).sum())
    df_tmp_subset = df_tmp_subset.sort_values(by=df_confirmed.columns[len(df_confirmed.columns)-1], ascending=False)
    df_topten_countries = df_tmp_subset[0:10]

    x_axis = df_topten_countries.columns
    fig = make_subplots(
        rows=1, 
        cols=1,
        subplot_titles=["US states Confirmed Cases"]
    )
    for i in range(0,10,1):
        y = df_topten_countries.iloc[i,1:].values.flatten().tolist()
        fig.add_trace(
            go.Scatter(
                x=x_axis[1:],
                y=y,
                mode='lines+markers',
                name=df_topten_countries.iloc[i,0]
            ),
            row=1, col=1
        )

    # Title
    fig.update_layout(
        title_text = "Smridhi Mangla's Dashboard")
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def create_plot4():
    
    url = 'https://www.worldometers.info/coronavirus/country/us/'
    header = {
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
      "X-Requested-With": "XMLHttpRequest"
    }
    r = requests.get(url, headers=header)
    Covid_cases = pd.read_html(r.text)[1]

    # Fill null values with zero
    Covid_cases.fillna(0, inplace=True)
    #cleaning data
    x = ['Diamond Princess Cruise',
         'Wuhan Repatriated',
         'Total:',
         'Grand Princess', 
         'District Of Columbia',
         'Puerto Rico', 
         'Guam',
         'Northern Mariana Islands',
         'United States Virgin Islands']
    Covid_cases = Covid_cases[~Covid_cases['USAState'].isin(x)]
    #creating a new column Recovered cases
    Covid_cases['RecoveredCases'] = Covid_cases['TotalCases'] - (Covid_cases['TotalDeaths'] + Covid_cases['ActiveCases'])
    #subsetting top 10 countries
    Covid_cases10 = Covid_cases.iloc[:10]
    names = Covid_cases10['USAState']
    totals = [i+j+k for i,j,k in zip(Covid_cases10['RecoveredCases'], Covid_cases10['TotalDeaths'], Covid_cases10['ActiveCases'])]
    RecoveredCases = [i / j * 100 for i,j in zip(Covid_cases10['RecoveredCases'], totals)]
    TotalDeaths = [i / j * 100 for i,j in zip(Covid_cases10['TotalDeaths'], totals)]
    ActiveCases = [i / j * 100 for i,j in zip(Covid_cases10['ActiveCases'], totals)]

    #Creating dataframe Popluation
    population = pd.DataFrame({'USAState':['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware',
                                     'District of Columbia','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas',
                                     'Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri',
                                     'Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina',
                                     'North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota',
                                     'Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'],
                               'Pop':[4903185,731545,7278717,3017804,39512223,5758736,3565287,973764,705749,21477737,10617423,1415872,1787065,
                                   12671821,6732219,3155070,2913314,4467673,4648794,1344212,6045680,6892503,9986857,5639632,2976149,6137428,
                                   1068778,1934408,3080156,1359711,8882190,2096829,19453561,10488084,762062,11689100,3956971,4217737,12801989,
                                   1059361,5148714,884659,6829174,28995881,3205958,623989,8535519,7614893,1792147,5822434,578759]})
    population=population[~population['USAState'].isin(x)]
    #merging the datasets Population and Covid_cases
    df = pd.merge(Covid_cases, population, how='left', on='USAState')
    #calculating Population%
    df['pop%'] = (df['TotalCases']/df['Pop'])*100
    df['pop%'] = round(df['pop%'],4)

    fig = make_subplots(rows=1, cols=2, subplot_titles = ['% Cases Recovered, Deaths and Active cases for top 10 states affected in US','% Population affected in each US state'])
    fig.append_trace(
        go.Bar(
            name='Recovered Cases', 
            x=names, 
            y=RecoveredCases, 
            marker_color='#4C516D'
        ),
    row=1,col=1)

    fig.append_trace(
        go.Bar(
            name='Total Deaths', 
            x=names, 
            y=TotalDeaths, 
            marker_color='#588BAE'
        ),
    row=1,col=1)

    fig.append_trace(   
        go.Bar(
            name='Active Cases', 
            x=names, 
            y=ActiveCases, 
            marker_color='#B0DFE5'
        ),
    row=1,col=1)

    fig.append_trace(   
        go.Scatter(
            name='% Affected',
            mode="markers", 
            x=df['USAState'], 
            y=df['pop%'], 
            marker_size=15),
    row=1,col=2)
    fig.update_xaxes(title_text="US States")
    fig.update_layout(
        barmode='group',
        title_text="Aanchal Gargi's dashboard"
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

@app.route('/')

def index():
    plot1 = create_plot1()
    plot2 = create_plot2()
    plot3 = create_plot3()
    plot4 = create_plot4()
    return render_template('index.html', plot1=plot1, plot2=plot2, plot3=plot3, plot4=plot4)

if __name__ == '__main__':
    app.run()


