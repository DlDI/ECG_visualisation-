import streamlit as st
import pandas as pd
import glob
import os
from streamlit_lottie import st_lottie
from streamlit_lottie import st_lottie_spinner
import requests
from functions import file_upload, ecg_preprocessing
from visualisation import get_figure
from statistics_1 import get_stat_figure, get_stats, add_stats
import neurokit2 as nk
from streamlit import experimental_data_editor
import numpy as np
import numpy 


def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


lottie_url_hello = "https://assets6.lottiefiles.com/private_files/lf30_ddqfreea.json"
lottie_hello = load_lottieurl(lottie_url_hello)

##### Streamlit settings #####

st.set_page_config(
    page_title="ECG Visualisation",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Sidebar title and animation
a, b = st.columns([5, 1])
a.markdown("## ECG VISUALISATION")

# Load animation using Lottie
lottie_url_hello = "https://assets6.lottiefiles.com/private_files/lf30_ddqfreea.json"
lottie_hello = load_lottieurl(lottie_url_hello)

# Display animation in sidebar
with b:
    st_lottie(lottie_hello, key="hello", height=100, width=200, quality="high")

# Custom CSS to hide unnecessary elements
hide_img_fs = """
    <style>
        button[title="View fullscreen"] {
            visibility: hidden;
        }
        #MainMenu {
            visibility: hidden;
        }
        footer {
            visibility: hidden;
        }
        .bk-logo {
            display: none !important;
        }
    </style>
"""
st.markdown(hide_img_fs, unsafe_allow_html=True)


##### File Upload #####
tab1, tab2, tab3, tab4 = st.tabs(
    ["file upload", "visualisation", "stats", "Export Stats"]
)


with tab1:
    st.markdown("# File Upload")
    data, settings = file_upload()
    with st.sidebar:
        selected = st.radio("Select the type of data", data.keys())
    st.write("You selected", selected)
    if selected != None :
        key = selected.split(".")[0]
    process = False
    if len(data) > 0:
        dict_data = pd.DataFrame()
        dict_data = ecg_preprocessing(data, settings["freq"])
        keys = dict_data.keys()
        process = True
    


with tab2:
    st.markdown("# Visualisation")
    if process:
        data_frame = dict_data[key]
        x = data_frame["x"]
        y = data_frame["y"]
        start = 0
        end = settings["window_split"]
        y_peaks = data_frame[data_frame["y_peaks"] != 0]["y_peaks"]
        window_split = settings["window_split"]
        freq = settings["freq"]
        segmentation = settings["segmentation"]
        peak_index = data_frame[data_frame["peak_index"] != 0]["peak_index"]
        st.write(peak_index)
        layout = get_figure(x, y, start, end, y_peaks, window_split, freq, segmentation, peak_index)
        st.bokeh_chart(layout, use_container_width=True)
    #layout = get_figure(x, y, start, end, y_peaks, window_split, freq, segmentation, peak_index)
    #st.bokeh_chart(layout, use_container_width=True)
    # Add visualization code here
with tab3:
    st.markdown("# Statistics")
    if process:
        data_stats = dict_data[key]
        freq = settings["freq"]
        x = data_stats["x"]
        y = data_stats["y"]
        start = 0
        end = settings["window_split"]
        y_peaks = data_stats["y_peaks"]
        window_split = settings["window_split"]
        segmentation = settings["segmentation"]
        peak_index = data_stats["peak_index"]

        table, time_domain_df, geometrical_df, frequency_domain_df, non_linear_df = get_stats(window_split, freq, peak_index)
        hr = round(table.iloc[[4]].values.mean())
        heart_rate = str(hr) + " BPM"# np.nanmean(table.iloc[[4]].values )
        str_heart_rate = str(heart_rate) + " bpm"
        st.metric(label="Heart Rate", value=str_heart_rate)
        stat_layout = get_stat_figure(x, y, start, end, y_peaks, window_split, freq, segmentation, peak_index, table)
        st.bokeh_chart(stat_layout, use_container_width=True)
        table_stat = add_stats(table)
        edit = st.bokeh_chart(table_stat, use_container_width=True)
        st.write("Time Domain stats")
        st.dataframe(time_domain_df)
        columna, columnb = st.columns(2)
        columna.write("Geometrical Domain stats")
        columna.dataframe(geometrical_df)
        columnb.write("Non Linear Domain stats")
        columnb.dataframe(non_linear_df)
with tab4:
    st.markdown("# EXPORT STATS")
    if process:
        st.write("Time Domain stats")
        st.dataframe(time_domain_df)
        columna, columnb = st.columns(2)
        columna.write("Geometrical Domain stats")
        columna.dataframe(geometrical_df)
        columnb.write("Non Linear Domain stats")
        columnb.dataframe(non_linear_df)
        # export csv
        
        # export all dataframes with many sheets in one excel file
        with pd.ExcelWriter('stats.xlsx') as writer:
            time_domain_df.to_excel(writer, sheet_name='Time Domain')
            geometrical_df.to_excel(writer, sheet_name='Geometrical Domain')
            non_linear_df.to_excel(writer, sheet_name='Non Linear Domain')
        st.write("Exported to stats.xlsx")

        with open('stats.xlsx', 'rb') as f:
            data = f.read()
        st.download_button(label='Download', data=data, file_name='stats.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        # Add code for exporting stats here