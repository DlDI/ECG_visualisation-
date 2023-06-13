from bokeh.plotting import figure
from bokeh.models import (
    DatetimeTickFormatter,
    RangeTool,
    Button,
    CustomJS,
    Spinner,
    Toggle,
    BoxSelectTool,
    ColumnarDataSource,
    BoxAnnotation,
)
from bokeh import events
from bokeh.models import DataTable, ColumnDataSource, NumberFormatter, CustomJS, TableColumn, StringEditor, NumberEditor, StringFormatter, NumberFormatter   
from bokeh.models.tools import BoxZoomTool
from bokeh.layouts import row, grid
import streamlit as st
import pandas as pd
import numpy as np
import random
from hrvanalysis import remove_outliers, remove_ectopic_beats, interpolate_nan_values
from bokeh.layouts import layout
from hrvanalysis import get_time_domain_features, get_frequency_domain_features, get_geometrical_features, get_poincare_plot_features, get_nn_intervals


def get_stat_figure(x,y,start, end, y_peaks, window_split, freq, segmentation, peak_index, table):
    duration = len(x) / freq

    p = figure(
        max_height=250,
        min_width=700,
        x_range=(start, end*freq ),
        align="center",
        x_axis_type="datetime",
        tools="",
        x_minor_ticks=5,
        output_backend="webgl",
        title="ECG signal",
        sizing_mode="stretch_width",
    )

    p.xaxis.formatter = DatetimeTickFormatter(
        seconds="%M:%S",
        minutes="%M:%S",
        milliseconds="%M:%S",
        minsec="%M:%S",
        years="%M:%S",
    )

    p.yaxis.axis_label = "Amplitude"
    p.xaxis.axis_label = "Time"

    p.line(x=x, y=y, line_color="#428bca")

    p.background_fill_color = "#FFFFFF"
    p.border_fill_color = "whitesmoke"
    p.outline_line_color = "black"

    
    select_box = BoxZoomTool(dimensions="width")
    p.add_tools(select_box)
    box_select = BoxSelectTool(dimensions="width")
    p.add_tools(box_select)

    peaks_figure = p.scatter(
        x=peak_index,
        y=y_peaks,
        size=5,
        line_color=None,
        fill_color="red",
        name="peaks",
        muted_alpha=0.2,
    )
    select = figure(
        title="Click on the range to see it in detail (double click to reset)",
        plot_height=150,
        plot_width=700,
        y_range=p.y_range,
        x_range=(0, len(x) ),
        x_axis_type="datetime",
        tools="",
        background_fill_color="#efefef",
        sizing_mode="stretch_width",
    )
    ls = [i for i in range(0, len(x), window_split * freq)]
    select.js_on_event(
        events.Tap,
        display_event(
            freq,
            window_split,
            ls,
            p,
        ),
    )

    select.line(x=x, y=y, line_color="#428bca")

    heart_rate_column = table.iloc[[4]].values.flatten().tolist()

    add_select_segments(window_split, heart_rate_column, freq, select)

    datafr= get_stats(window_split, freq, peak_index)[0]

    table = DataTable( columns=[TableColumn(field=Ci, title=Ci) for Ci in datafr.columns], source=ColumnDataSource(datafr), width=400, height=280, selectable=True, editable=True, reorderable=True, index_position=None, sizing_mode="stretch_width",)
    
    

    layout = grid([[p], [select]], sizing_mode="stretch_width")

    return layout

def get_nn_interval(rrinterval):
    # This remove outliers from signal
    rr_intervals_without_outliers = remove_outliers(
        rr_intervals=rrinterval, low_rri=300, high_rri=2000
    )
    # This replace outliers nan values with linear interpolation
    interpolated_rr_intervals = interpolate_nan_values(
        rr_intervals=rr_intervals_without_outliers, interpolation_method="linear"
    )

    # This remove ectopic beats from signal
    nn_intervals_list = remove_ectopic_beats(
        rr_intervals=interpolated_rr_intervals, method="malik"
    )
    # This replace ectopic beats nan values with linear interpolation
    # interpolated_nn_intervals = interpolate_nan_values(rr_intervals=nn_intervals_list)
    return nn_intervals_list

def get_stats(window_split, freq, peak_index):
    peak_index = peak_index[peak_index > 0].index.to_frame()
    stat_df = pd.DataFrame(columns=[f"Segment_{i}" for i in range(0, len(peak_index), window_split)], index=["RR_mean", "RR_std", "RR_min", "RR_max", "heart_rate"])
    time_domain_df = pd.DataFrame(columns=[f"Segment_{i}" for i in range(0, len(peak_index), window_split)], index=["mean_nni", "sdnn", "sdsd", "nni_50", "pnni_50", "nni_20", "pnni_20", "rmssd", "median_nni", "range_nni", "cvsd", "cvnni", "mean_hr", "max_hr", "min_hr", "std_hr"])
    geometrical_df = pd.DataFrame(columns=[f"Segment_{i}" for i in range(0, len(peak_index), window_split)], index=["triangular_index"])
    frequency_domain_df = pd.DataFrame(columns=[f"Segment_{i}" for i in range(0, len(peak_index), window_split)], index=["total_power", "vlf", "lf", "hf", "lf_hf_ratio", "lfnu", "hfnu"])
    non_linear_df = pd.DataFrame(columns=[f"Segment_{i}" for i in range(0, len(peak_index), window_split)], index=["sd1", "sd2", "ratio_sd2_sd1"])
    for i in range(0, len(peak_index), window_split):
        window_peak_index = peak_index[i:i + window_split]
        RR_interval = window_peak_index.diff()
        RR_time_intervale = RR_interval / freq
        heart_rate = round(60 / RR_time_intervale.mean(), 2)
        # rr_interval to list
        arr =  RR_interval.values.flatten()
        arr = arr[~np.isnan(arr)]
        print(arr)
        print(type(arr))
        nninterval = get_nn_interval(arr)
        print(nninterval)
        time_domain_features = get_time_domain_features(nninterval)
        geometrical_features = get_geometrical_features(nninterval)
        frequency_domain_features = pd.DataFrame()
        poincare_plot_features = get_poincare_plot_features(nninterval)

        # add dict to dataframe
        time_domain_df[f"Segment_{i}"] = pd.Series(time_domain_features, index=["mean_nni", "sdnn", "sdsd", "nni_50", "pnni_50", "nni_20", "pnni_20", "rmssd", "median_nni", "range_nni", "cvsd", "cvnni", "mean_hr", "max_hr", "min_hr", "std_hr"])
        geometrical_df[f"Segment_{i}"] = pd.Series(geometrical_features, index=["triangular_index"])
        #frequency_domain_df[f"Segment_{i}"] = pd.Series(frequency_domain_features, index=["total_power", "vlf", "lf", "hf", "lf_hf_ratio", "lfnu", "hfnu"])
        non_linear_df[f"Segment_{i}"] = pd.Series(poincare_plot_features, index=["sd1", "sd2", "ratio_sd2_sd1"])
        
        stat_df[f"Segment_{i}"] = pd.Series([ RR_interval.mean(), RR_interval.std(), RR_interval.min(), RR_interval.max(), heart_rate], index=["RR_mean", "RR_std", "RR_min", "RR_max", "heart_rate"])
                
    return stat_df, time_domain_df, geometrical_df, frequency_domain_df, non_linear_df

def get_color_annotation(heart_rate):
    heart_rate = float(heart_rate) + random.uniform(-5, 30)
    if heart_rate < 60:
        return "purple"
    elif heart_rate > 75 and heart_rate < 80:
        return "green"
    elif heart_rate > 100:
        return "red"
    else:
        return "blue"

def add_select_segments(window_split, heart_rate_column, freq, select_stat):
    List_segmentations = []
    list_diagnostic = []
    for k in range(0, len(heart_rate_column)):
        startt = k * window_split * freq
        endd = (k + 1) * window_split * freq

        List_segmentations.append(startt)
        # test heart rate column with wide range of values
        tst_heart_rate_color = random.choices(["purple", "green", "red", "blue"], weights=(1, 15, 2, 5), k=1)
        a = get_color_annotation(heart_rate_column[k])
        b1 = BoxAnnotation(
            left=startt,
            right=endd,
            fill_color=tst_heart_rate_color[0],
            fill_alpha=0.5,
        )
        # b1.js_on_click()
        list_diagnostic.append(a)

        select_stat.add_layout(b1)
    return list_diagnostic

def display_event (freq, wind_split, ls, fig):
    "Build a suitable CustomJS to display the current event in the div model."
    return CustomJS(
        args=dict(li=ls, xr=fig.x_range, freq=freq, wind_split=wind_split),
        code="""
        const attrs = "x";
        // array = sorted array of integers
        // val = pivot element
        // dir = boolean, if true, returns the previous value
        
        function getVal(array, val, dir) {
        for (var i=0; i < array.length; i++) {
            if (dir == true) {
            if (array[i] > val){
                return array[i-1] || 0;
            }
            } else {
            if (array[i] >= val) {
                return array[i];
            }
            }
        }
        }
    
        var real_pos = Number(cb_obj["x"].toFixed(2));
        const output2 = getVal(li, real_pos, true);
        xr.start = output2 ;
        xr.end = output2  + wind_split *freq -1  ;

    """,
    )

def add_stats(table):
    T_table = table.T
    # add dyagnostic column
    list_diagnostic = []
    for i in range(len(T_table)):
        heart_rate = random.uniform(50, 120)
        if heart_rate < 60:
            list_diagnostic.append("bradycardia")
        elif heart_rate > 75 and heart_rate < 80:
            list_diagnostic.append("normal")
        elif heart_rate > 100:
            list_diagnostic.append("tachycardia")
        else:
            list_diagnostic.append("normal")
    T_table["Diagnostic"] = list_diagnostic
    source = ColumnDataSource(T_table)
    T_table.dropna()

    # Define editable columns for the DataTable
    columns = [
        TableColumn(field='RR_mean', title='RR_mean', editor=StringEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='RR_std', title='RR_std', editor=NumberEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='RR_min', title='RR_min', editor=NumberEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='RR_max', title='RR_max', editor=NumberEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='heart_rate', title='heart_rate', editor=NumberEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='Diagnostic', title='Diagnostic', editor=StringEditor(), formatter=StringFormatter())
    ]
    data_table = DataTable(source=source, columns=columns, editable=True, index_position=-1)
    # Create a layout for the table
    tablee = layout([[data_table]], sizing_mode='stretch_width')
    return tablee