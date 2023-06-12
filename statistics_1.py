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
import random
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

    datafr= get_stats(window_split, freq, peak_index)

    table = DataTable( columns=[TableColumn(field=Ci, title=Ci) for Ci in datafr.columns], source=ColumnDataSource(datafr), width=400, height=280, selectable=True, editable=True, reorderable=True, index_position=None, sizing_mode="stretch_width",)
    
    

    layout = grid([[p], [select]], sizing_mode="stretch_width")

    return layout

def get_stats(window_split, freq, peak_index):
    peak_index = peak_index[peak_index > 0].index.to_frame()
    stat_df = pd.DataFrame(columns=[f"RR_interval_{i}" for i in range(0, len(peak_index), window_split)], index=["mean", "std", "min", "max", "heart_rate"])
    for i in range(0, len(peak_index), window_split):
        window_peak_index = peak_index[i:i + window_split]
        RR_interval = window_peak_index.diff()
        RR_time_intervale = RR_interval / freq
        heart_rate = round(60 / RR_time_intervale.mean(), 2)
        
        stat_df[f"Segment_{i}"] = pd.Series([ RR_interval.mean(), RR_interval.std(), RR_interval.min(), RR_interval.max(), heart_rate], index=["mean", "std", "min", "max", "heart_rate"])
                
    return stat_df

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
    source = ColumnDataSource(T_table)
    T_table.dropna()

    # Define editable columns for the DataTable
    columns = [
        TableColumn(field='mean', title='mean', editor=StringEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='std', title='std', editor=NumberEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='min', title='min', editor=NumberEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='max', title='max', editor=NumberEditor(), formatter=NumberFormatter(format='0,00')),
        TableColumn(field='heart_rate', title='heart_rate', editor=NumberEditor(), formatter=NumberFormatter(format='0,00')),
    ]
    data_table = DataTable(source=source, columns=columns, editable=True, index_position=-1)
    # Create a layout for the table
    tablee = layout([[data_table]])
    return tablee