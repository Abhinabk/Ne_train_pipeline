
import streamlit as st
import duckdb 
import plotly.express as px


@st.cache_resource
def get_connection():
    return duckdb.connect('data/database/ne_pipeline.db')

@st.cache_data
def get_overview_data():
    con = get_connection()
    data = con.execute("""
    SELECT
        COUNT(*) AS total_records,
        COUNT(DISTINCT train_no) AS total_trains,
        COUNT(DISTINCT station_code) AS total_stations,
        ROUND(AVG(delay_minutes),1) AS avg_delay,
        MIN(date) AS min_date,
        MAX(date) AS max_date
    FROM merged_view        
    """).fetchone()
    return data

@st.cache_data
def get_delay_data():
    con = get_connection()
    delay_df = con.execute("""
    SELECT 
        delay_minutes
    FROM merged_view
    WHERE delay_minutes IS NOT NULL AND delay_minutes BETWEEN 10 AND 500
    """).fetchdf()
    return delay_df

@st.cache_data
def get_train_delay_data():
    con = get_connection()
    train_data = con.execute("""
        SELECT 
            train_no,
            ROUND(AVG(delay_minutes),1) AS avg_delay,
            ROUND(MEDIAN(delay_minutes), 2) AS median_delay,
            MAX(delay_minutes) as worst_delay
        FROM merged_view
        group by train_no 
        LIMIT 10
    """).fetchdf()
    return train_data


def overview():
    '''
    total records
    total trains
    total stations
    avg delay
    date range'''

    data = get_overview_data()
    total_records, total_trains, total_stations, avg_delay, min_date, max_date = data
    delay_df = get_delay_data()
    st.header("OVERVIEW")

    st.write(f"Data from {min_date} to {max_date}")
    
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


def main():
    st.set_page_config(layout="wide")
    st.title("Northeast India Train Delay Analytics")
    st.write(
        """
        Analysis of train delays across stations and weather conditions
        to identify operational bottlenecks and temporal patterns.
        """
    )

    overview()
    st.divider()
    train_anlysis()


if __name__ == "__main__":
    con = get_connection()
    main()
