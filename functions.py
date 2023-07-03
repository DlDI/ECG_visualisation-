import streamlit as st
import pandas as pd
import glob
import os

import neurokit2 as nk
import numpy as np

def file_upload():
    st.markdown("# Open files 📂")
    with st.expander("Settings"):
        with st.form("my_form"):
            st.write("Change the settings here!")
            coll0, coll1, coll2, col3 = st.columns([1, 1, 1, 1], gap="small")
            CHOICES = {"seconds" : 1, "beats" : 2}
            segmentation = coll0.selectbox("Segmentation:", options=list(CHOICES.keys()))
            window_split = coll1.number_input("Window split:", 1, 300, value=30, key=1, step=1)
            step_by = coll2.number_input("Step by:", 1, 300, value=30, key=12, step=1)
            freq = col3.number_input("Frequency:", 0, 10000, value=1000, key=2, step=1)

            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            if submitted and step_by <= window_split:
                st.write("Parameters are taken")
                step_by = int(step_by)
                st.write(window_split)
                window_split = int(window_split)
                st.write(window_split)
            elif submitted and step_by > window_split:
                st.warning("Step_by parameter can't be greater than window split")

    path = st.text_input(
        "Enter the path of the files",
        value="",
        type="default",
        help="The path can be relative or absolute, and it can be a directory or a single file path.",
    )

    uploaded_files = st.file_uploader("Or choose .csv files", type=["csv"], accept_multiple_files=True)

    files_dict = {}

    for uploaded_file in uploaded_files:
        df = pd.read_csv(uploaded_file)
        name = uploaded_file.name
        files_dict[name] = df

    if path != "":
        all_files = glob.glob(path + "/**.csv")
        if all_files is not None:
            for filename in all_files:
                df = pd.read_csv(filename)
                head, tail = os.path.split(filename)
                files_dict[tail] = df

    settings = {"segmentation": segmentation, "window_split": window_split, "step_by": step_by, "freq": freq}
    return files_dict , settings




def peak_detection(ecg: pd.DataFrame, freq: int):
    ecg_1d = [i for i in ecg.squeeze()]
    (read_ecg, dict_info) = nk.ecg_process(
        ecg_1d, sampling_rate=freq, method="neurokit"
    )
    peaks = read_ecg["ECG_R_Peaks"]
    peak_index = [i*peaks[i] for i in range(len(peaks))]
    # remove the 0 values
    #peak_index = [i if i !=0 else None for i in peakindex ]

    

    peak_y = [ i*j for i,j in zip(peaks, ecg_1d)]
    
    # remoee the 0 values
    #peak_y = [i if i != 0 else None for i in peaky ]
    return pd.DataFrame(peak_index, columns=['peak_index']),pd.DataFrame(peak_y, columns=['peak_y']) 


def global_stats(ecg: pd.DataFrame):
    ecg_1d = ecg.squeeze()
    avg_distance = np.mean(np.diff(ecg_1d))
    return avg_distance

def analysis(peak_index: pd.DataFrame):
    stats = global_stats(peak_index)
    return stats

@st.cache_data 
def ecg_preprocessing(raw_data: dict, freq: int):
    dict_info = dict()

    for key, value in raw_data.items():
        # take the .csv from key name
        key = key.split(".")[0]
        # add the key to the dataframe$
        df = pd.DataFrame(columns=['y','peak_index','y_peaks','Analysis','x'])
        print("key is: ", key)  
        print("value is: ", value)
        df['y'] = value   
        df['peak_index'], df['y_peaks'] = peak_detection(value, freq)
        df['x'] = range(0, len(value))

        dict_info[key] = df
    return dict_info


