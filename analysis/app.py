import streamlit as st
import plotly.express as px
import pydeck as pdk
import pandas as pd

from data  import (
    get_overview_data,
    get_train_delay_data,
    get_delay_data,
    get_station_delay_data,
    get_season_delay_data,
    get_temporal_delay_data,
    get_weather_data
    )
def overview():
    '''
    total records
    total trains
    total stations
    avg delay
    date range'''

    data = get_overview_data()
    if data:
        total_records, total_trains, total_stations, avg_delay, min_date, max_date = data
    delay_df = get_delay_data()
    st.header("OVERVIEW")

    st.info(f"Data from {min_date} to {max_date}")
    
    c1,c2,c3,c4 = st.columns(4)

    with c1:
        st.metric(label='Total Records',value=f"{total_records:,}")
    with c2:
        st.metric(label='Trains',value=total_trains)
    with c3:
        st.metric(label='Stations',value=total_stations)
    with c4:
        st.metric(label='AVG Delay',value=f"{avg_delay} min")  
    c_hist = st.container()

    with c_hist:
        fig = px.histogram(
            delay_df,
            x = "delay_minutes",
            nbins=50,
            title="Distribution of train delay"
        )
        fig.update_layout(
        xaxis_title="Delay Minutes",
        yaxis_title="Frequency"
        )
        st.plotly_chart(fig,width='stretch')
        st.caption("Extreme outliers > 500 minutes and < 10 min are hidden ") 
         
    st.info(f""" Most train delays are concentrated below 100 minutes.
            Across {total_trains} trains and {total_stations} stations, the network averages {avg_delay} min per stop
    """)  

def train_anlysis():
    '''
    average delay by train
    median delay by train
    top worst trains
    '''
    train_df = get_train_delay_data()
    train_df = train_df.sort_values("avg_delay")

    st.header("Worst Train Delays")

    #wide to long format
    grouped_df = train_df.melt(
    id_vars="train_no",
    value_vars=["avg_delay", "median_delay"],
    var_name="metric",
    value_name="delay")
    c_bar,c_grouped = st.columns([0.5,0.5])

    with c_bar:
        fig = px.bar(
            train_df,
            x="avg_delay",
            y="train_no",
            orientation="h",
            color="avg_delay",
            color_continuous_scale="Blues",
            title="Worst Train Delay by Train"
        )
        fig.update_layout(coloraxis_showscale=False)
        fig.update_yaxes(type='category')
        st.plotly_chart(fig)

    with c_grouped:
        fig = px.bar(
        grouped_df,
        x="delay",
        y="train_no",
        color="metric",
        barmode="group",
        orientation="h",
        title="Average vs Median Delay by Train"
        )
        fig.update_layout(
        xaxis_title="Delay (Minutes)",
        yaxis_title="Train Number"
        )
        fig.update_yaxes(type='category')
        st.plotly_chart(fig,width='stretch')

    worst_train = train_df.iloc[-1]
    st.info(
    f"""
    Train {worst_train['train_no']} has the highest average delay
    at {worst_train['avg_delay']} minutes.

    The gap between average and median delay suggests
    occasional severe disruptions rather than uniformly late operation.
    """
    )
    with st.expander("View Detailed Train Statistics"):
        st.dataframe(train_df,hide_index=True)

def station_analysis():
    station_df = get_station_delay_data()
    st.header("Worst Station Delays")
    c_map,c_grouped = st.columns([0.5,0.5])

    # Define a layer to display on a map
    layer = pdk.Layer(
            "ScatterplotLayer",
            data=station_df,
            get_position='[longitude, latitude]',
            get_radius='avg_delay * 100',
            get_fill_color='''
                avg_delay > 120 ? [255, 0, 0, 200] :
                avg_delay > 60 ? [255, 165, 0, 180] :
                avg_delay > 20 ? [255, 255, 0, 160] :
                [0, 128, 255, 140]''',
            pickable=True,
    )
    #inital view
    view_state = pdk.ViewState(
                latitude=20.5937,
                longitude=78.9629,
                zoom=5,
                )
    #final deck init
    deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "Station: {station_code}\nAvg Delay: {avg_delay} min"}, # type: ignore
                )
    with c_map:
        st.pydeck_chart(deck)
    
    top10_df = (
                station_df
                .sort_values("avg_delay", ascending=False)
                .head(10)
                )   
    grouped_df = top10_df.melt(id_vars='station_code',
                                 value_vars=['avg_delay','median_delay'],
                                 var_name='metric',
                                 value_name='delay')
    with c_grouped:
        fig = px.bar(grouped_df,
                    x="delay",
                    y="station_code",
                    color="metric",
                    barmode="group",
                    orientation="h",
                    title="Average vs Median Delay by Stations"
                    )
        fig.update_layout(
        xaxis_title="Delay (Minutes)",
        yaxis_title="Station Code"
        )
        st.plotly_chart(fig, width='stretch')

    worst_station = station_df.loc[station_df['avg_delay'].idxmax(),'station_code']
    max_delay = station_df['avg_delay'].max()
    
    st.info(f"""
        Northern railway corridors show the highest delay severity, 
        with top stations like {worst_station} averaging nearly {max_delay:.0f} minutes of delay.
        """
        )
    fig = px.histogram(
            station_df,
            x="avg_delay",
            nbins=30,
            title="Distribution of Average Station Delays"
            )
    st.plotly_chart(fig, width='stretch')
    st.info(
    """Most stations fall within the 40–80 minute average delay range, 
    while a small number of stations exceed 140+ minutes, indicating concentrated delay hotspots.  
    """)

def season_analysis():
    season_df = get_season_delay_data()
    month_vs_week_df = get_temporal_delay_data()
    season_df = season_df.sort_values("avg_delay")
    
    st.header("Temporal Delays")
    
    fig = px.bar(
            season_df,
            x="avg_delay",
            y="season",
            color="avg_delay",
            text="avg_delay",
            title="Average Delay by Season",
            color_continuous_scale="Blues",
        )

    fig.update_layout(
            xaxis_title="Average Delay (Minutes)",
            yaxis_title="Season",
            coloraxis_showscale=False
        )
    winter_delay = season_df.loc[season_df['season'] == 'Winter','avg_delay'].iloc[0]
    monsoon_delay = season_df.loc[season_df['season'] == 'Monsoon','avg_delay'].iloc[0]
    
    st.plotly_chart(fig, width='stretch')

    pivot_df = month_vs_week_df.pivot(
        index="month",
        columns="weekday",
        values="avg_delay"
    )
    months_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December']
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    pivot_df = pivot_df.reindex(months_order)
    pivot_df = pivot_df[weekday_order]
    fig = px.imshow(
        pivot_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Average Delay Heatmap by Month and Weekday"
    )
    st.plotly_chart(fig, width='stretch')


    st.info(f""" Winter records the highest average delays {winter_delay}min during Jan and Dec, more than double monsoon delays {monsoon_delay}min. 
        This suggests low-visibility winter conditions such as fog may disrupt railway operations more significantly than rainfall.
        """)
def weather():
    st.header("Weather delay patterns")
    weather_df = get_weather_data()
    weather_df = weather_df[weather_df['delay_minutes'] < 1000]
    c1, c2 = st.columns(2)
    c3,c4 = st.columns(2)
    c5,c6 = st.columns(2)

    with c1:
        fig = px.scatter(
                weather_df,
                x="temperature_2m_mean",
                y="delay_minutes",
                opacity=0.3,
                trendline="ols",
                title="Temperature vs Train Delay",

                hover_data=[
                    "station_code",
                    "train_no"
                ]
            )
        fig.update_traces(
            selector=dict(mode="lines"),
            line=dict(color="#B0E0E6", width=3)
        )
        st.plotly_chart(fig, width='stretch')
    with c2:
        fig = px.scatter(
            weather_df,
            x="rain_sum",
            y="delay_minutes",
            opacity=0.3,
            trendline="ols",
            title="Rainfall vs Train Delay"
            )
        fig.update_traces(
            selector=dict(mode="lines"),
            line=dict(color="#B0E0E6", width=3)
        )
        st.plotly_chart(fig, width='stretch')
    with c3:
        fig = px.scatter(
            weather_df,
            x="relative_humidity_2m_mean",
            y="delay_minutes",
            opacity=0.3,
            trendline="ols",
            title="Humidity vs Train Delay"
            )
        fig.update_traces(
            selector=dict(mode="lines"),
            line=dict(color="#B0E0E6", width=3)
        )
        st.plotly_chart(fig, width='stretch')
    with c4:
        fig = px.scatter(
            weather_df,
            x="wind_speed_10m_max",
            y="delay_minutes",
            opacity=0.3,
            trendline="ols",
            title="Wind vs Train Delay"
            )
        fig.update_traces(
            selector=dict(mode="lines"),
            line=dict(color="#B0E0E6", width=3)
        )
        st.plotly_chart(fig, width='stretch')

    with c5:
        weather_df['temp_category'] = pd.cut(
        weather_df['temperature_2m_mean'],
            bins=[0, 10, 20, 30, 50],
            labels=[
                'Cold',
                'Cool',
                'Warm',
                'Hot'
            ]
        )
        fig = px.violin(
            weather_df,
            x="temp_category",
            y="delay_minutes"
        )
        st.plotly_chart(fig, width='stretch')

    corr_df = weather_df[
            [
                'delay_minutes',
                'temperature_2m_mean',
                'rain_sum',
                'wind_speed_10m_max',
                'relative_humidity_2m_mean'
            ]
    ]
    corr = corr_df.corr()
    with c6:
        fig = px.imshow(
                corr,
                text_auto=".2f", # type: ignore
                color_continuous_scale="Blues",
                aspect="auto",
                title="Weather Variable Correlation Heatmap"
        )

        fig.update_layout(
            coloraxis_showscale=False,
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font_color="white"
        )

        st.plotly_chart(fig, width='stretch')

    st.info(
    """
    Temperature shows the strongest relationship with train delays (-0.22 correlation), 
    while rainfall ,humidity, wind speed  has comparatively weaker effects. 
    Although delays occur across all rainfall levels, severe delays are not consistently concentrated during high-rain conditions, 
    suggesting rainfall alone is not a dominant predictor of disruption.
    No-rain conditions (~73 min average delay) exhibit delay levels comparable to extreme rainfall events (~75 min),
    suggesting low-visibility winter conditions such as fog may impact railway operations more significantly than rainfall.
    """
    )
def pages():
    return st.sidebar.radio(
        "Sections",
        [
            "Overview",
            "Train Analysis",
            "Station Analysis",
            "Temporal Analysis",
            "Weather Analysis"
        ])

def main():
    st.set_page_config(layout="wide")
    st.title("Northeast India Train Delay Analytics")
    st.write(
        """
        Analysis of train delays across stations and weather conditions
        to identify operational bottlenecks and temporal patterns.
        """
    )

    page = pages()
    if page == "Overview":
        overview()

    elif page == "Train Analysis":
        train_anlysis()

    elif page == "Station Analysis":
        station_analysis()

    elif page == "Temporal Analysis":
        season_analysis()

    elif page == "Weather Analysis":
        weather()
if __name__ == "__main__":
    main()
