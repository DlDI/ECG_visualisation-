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
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://www.extremelycoolapp.com/help",
        "Report a bug": "https://www.extremelycoolapp.com/bug",
        "About": "# This is a header. This is an *extremely* cool app!",
    },
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
    st.write(data)
    process = False
    if len(data) > 0:
         if st.button("Preprocess") :
            dict_data = pd.DataFrame()
            dict_data = ecg_preprocessing(data, settings["freq"])
            process = True
    


with tab2:
    st.markdown("# Visualisation")
    if process:
        data_frame = dict_data['ecg']
        x = data_frame["x"]
        y = data_frame["y"]
        start = 0
        end = settings["window_split"]
        y_peaks = data_frame[data_frame["y_peaks"] != 0]["y_peaks"]
        st.write(y_peaks)
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
        data_stats = dict_data['ecg']
        freq = settings["freq"]
        x = data_stats["x"]
        y = data_stats["y"]
        start = 0
        end = settings["window_split"]
        y_peaks = data_stats["y_peaks"]
        window_split = settings["window_split"]
        segmentation = settings["segmentation"]
        peak_index = data_stats["peak_index"]
        #st.write(peak_index)
        #RR_time_intervale = 
        table = get_stats(window_split, freq, peak_index)
        # round to 2 decimal
        #heart_rate = round(60 / RR_time_intervale.mean(), 2)
        heart_rate = table.iloc[[4]].mean()
        
        stat_layout = get_stat_figure(x, y, start, end, y_peaks, window_split, freq, segmentation, peak_index, table)
        st.bokeh_chart(stat_layout, use_container_width=True)
        table_stat = add_stats(table)
        edit = st.bokeh_chart(table_stat, use_container_width=True)
with tab4:
    st.markdown("# EXPORT STATS")
    # Add code for exporting stats here