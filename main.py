import streamlit as st
import pandas as pd
import numpy as np
from scipy.misc import electrocardiogram
import plotly.graph_objects as go
from scipy.misc import electrocardiogram
import datetime
import neurokit2 as nk  # Load the package



st.set_page_config(
     page_title="ECG Visualisation",
     page_icon="🧊",
     layout="wide",
     initial_sidebar_state="collapsed",
     menu_items={
         'Get Help': 'https://www.extremelycoolapp.com/help',
         'Report a bug': "https://www.extremelycoolapp.com/bug",
         'About': "# This is a header. This is an *extremely* cool app!"
     }
 )


duration = 300
freq=100

simulated_ecg = nk.ecg_simulate(duration=duration, sampling_rate=freq, heart_rate=80)

# Load data
now = datetime.datetime.now()
conversion = datetime.timedelta(seconds=duration)



x = pd.date_range(start=now-conversion,end=now,periods=duration*freq).to_pydatetime().tolist()

# Create figure
fig = go.Figure()
fig.add_trace(
    go.Scatter(x=list(x), y=list(simulated_ecg)))

# Set title
fig.update_layout(
    title_text="Time series with range slider and selectors",height=600
)


st.title('ECG Visualisation')

with st.sidebar:
    uploaded_files = st.file_uploader("Choose a CSV file", accept_multiple_files=True)
    for uploaded_file in uploaded_files:
        bytes_data = uploaded_file.read()
        st.write("filename:", uploaded_file.name)
        st.write(bytes_data)
    ECG_visualisation = st.button('I agree')



with st.expander("Setings"):
    with st.form("my_form"):
        st.write("Change the settings here !")
        coll0, coll1, coll2 = st.columns([1,2, 1],gap="small")
        segmentation = coll0.selectbox(
     'Segmentation :',
     ('Seconds', 'Beats'))


        frame_width = coll1.number_input('Window split', 0, 1000, value=30 ,key=1)
     
        freq = coll2.number_input('Frequency', 0, 10000,value=1000,key=2)
        xmin= datetime.datetime(2015, 2, 17, 00, 00, 00) 
        xmax = xmin + datetime.timedelta(days = frame_width)
        def update_frame():  
            xmax = xmin + datetime.timedelta(days = frame_width)
            initial_range = [xmin, xmax ]
            fig['layout']['xaxis'].update(range=initial_range)
        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit")
        if submitted:
            update_frame()    
            
            

            
step = 200
     

col0, col1, col2, col3 = st.columns([1,9,1,3],gap="large")




col1.subheader("Chart")

col3.subheader("Statistics")

if ECG_visualisation :
    # Add range slider
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                bgcolor="#3C3C3C",
                activecolor='#777777',
                buttons=list([
                    dict(count=1,
                        label="1 s",
                        step="second",
                        stepmode="backward"),
                    dict(count=30,
                        label="30 s",
                        step="second",
                        stepmode="backward"),
                    dict(count=1,
                        label="1 min",
                        step="minute",
                        stepmode="backward"),
                    dict(count=5,
                        label="5 min",
                        step="minute",
                        stepmode="backward"),
                    dict(count=1,
                        label="Last munite",
                        step="minute",
                        stepmode="todate"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True,
            ),
            type="date"
        )
    )
        


    xmin= datetime.datetime(2022, 7, 17, 00, 00, 00) 
    xmax = xmin + datetime.timedelta(seconds = 30)

    fig.update_layout(
        updatemenus=[
            dict(
                type = "buttons",
                direction = "left",
                buttons=list([
                    dict(
                        
                        args=[{"xaxis.range":["2022/07/01","2022/07/03"]}],
                        label="previous",
                        method="relayout"
                    ),
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0,
                xanchor="right",
                y=-0.243,
                yanchor="bottom"
            ),
            dict(
                type = "buttons",
                direction = "left",
                buttons=list([
                    dict(
                        args=["xrange", "surface"],
                        label="next",
                        method="update"
                    ),
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=1.075,
                xanchor="right",
                y=-0.243,
                yanchor="bottom"
            ),
        ]
    )


    col1.plotly_chart(fig,use_container_width=True,key=33)



if col0.button("step backward"):
    print("full_fig.layout.xaxis.range: ", fig.full_figure_for_development().layout.xaxis.range)
    
    xmin= fig.full_figure_for_development().layout.xaxis.range[0] + datetime.timedelta(seconds = step)
    xmax = fig.full_figure_for_development().layout.xaxis.range[1] + datetime.timedelta(seconds = step)
    initial_range = [xmin, xmax ]
    fig['layout']['xaxis'].update(range=initial_range)
    print("full_fig.layout.xaxis.range: ", fig.full_figure_for_development().layout.xaxis.range)

if col2.button("step forward"):
    xmin= xmin - datetime.timedelta(days = step)
    xmax = xmax - datetime.timedelta(days = step)
    initial_range = [xmin, xmax ]
    fig['layout']['xaxis'].update(range=initial_range)

st.write(st.session_state)
