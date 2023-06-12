from bokeh.plotting import figure
from bokeh.models import (
    DatetimeTickFormatter,
    RangeTool,
    Button,
    CustomJS,
    Spinner,
    Toggle,
    BoxSelectTool,
)
from bokeh.models.tools import BoxZoomTool
from bokeh.layouts import row, grid
from bokeh.events import SelectionGeometry
import streamlit as st

@st.cache_resource
def get_figure(x, y, start, end, y_peaks, window_split, freq, segmentation, peak_index):
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

    callbackk = CustomJS(
        args=dict(p=p),
        code="""
        p.x_range.start = 0;
        """,
    )

    box_select = BoxSelectTool(dimensions="width")
    p.add_tools(box_select)
    p.js_on_event(SelectionGeometry, callbackk)

    select = figure(
        title="selected range",
        height=100,
        sizing_mode="stretch_width",
        x_range=(0, len(x)),
        x_axis_type="datetime",
        y_axis_type=None,
        tools="",
        toolbar_location=None,
        background_fill_color="#efefef",
        align="center",
        output_backend="webgl",
    )
    select.line(x=x, y=y, line_color="#428bca")

    select.xaxis.formatter = DatetimeTickFormatter(
        seconds="%M:%S",
        minutes="%M:%S",
        milliseconds="%M:%S",
        minsec="%M:%S",
        years="%M:%S",
    )

    range_tool = RangeTool(x_range=p.x_range)
    select.add_tools(range_tool)

    peaks_figure = p.scatter(
        x=peak_index,
        y=y_peaks,
        size=5,
        line_color=None,
        fill_color="red",
        name="peaks",
        muted_alpha=0.2,
        visible=False,
    )

    spinner = Spinner(title="Step size", low=0, high=duration, step=window_split, value=window_split, width=70, align="center")

    callback_spinner = CustomJS(
        args=dict(spinner=spinner, p=p, freq=freq),
        code="""
        var value = spinner.value;
        p.x_range.end = p.x_range.start + value*freq;
        """,
    )
    spinner.js_on_change("value", callback_spinner)

    toggle_show_peaks = Toggle(label="Show Peaks", button_type="success", width=100, align="center")

    callback_toggle_peaks = CustomJS(
        args=dict(toggle=toggle_show_peaks, peaks=peaks_figure),
        code="""
        if (toggle.active) {
            toggle.label = "Hide Peaks";
            peaks.visible = true;
        } else {
            toggle.label = "Show Peaks";
            peaks.visible = false;
        }
        """,
    )
    toggle_show_peaks.js_on_change("active", callback_toggle_peaks)

    button_previous = Button(label="Previous", button_type="primary", max_width=50, align="start")
    button_next = Button(label="Next", button_type="primary", max_width=50, align="end")

    callback_previous = CustomJS(
        args=dict(button=button_previous, other_button = button_next , freq=freq , spinner=spinner, segmentation=segmentation, end=len(x), x_range = p.x_range, peak_index=peak_index),
                code="""
                var step = spinner.value;
                
                
                var segmentation = segmentation;
                var peak = peak_index;

                const output2 = peak.reduce((prev, curr) => Math.abs(curr - x_range.end) < Math.abs(prev - x_range.end) ? curr : prev);
                const output1 = peak.reduce((prev, curr) => Math.abs(curr - x_range.start) < Math.abs(prev - x_range.start) ? curr : prev);
                const index_1 = peak.indexOf(output1);
                const index_2 = peak.indexOf(output2);
                
                if (x_range.start == 0) {
                    button.disabled = true;
                }
                else if (x_range.end < end) {
                    other_button.disabled = false;
                }
                if (segmentation == 'seconds') {
                    if (x_range.start - step*freq < 0) {
                        x_range.start = 0;
                        x_range.end = step*freq;
                        }
                    else {
                        x_range.start = x_range.start - step*freq;
                        x_range.end = x_range.end - step*freq;
                    }
                }
                else {
                    if (index_1 - step < 0) {
                        x_range.start = peak[0];
                        x_range.start = peak[step];
                        }
                    else { 
                        x_range.start = peak[index_1 - step];
                        x_range.end = peak[index_2 - step];
                    }
                }
                if (x_range.start == 0) {
                    button.disabled = true;
                }
                else if (x_range.end < end) {
                    other_button.disabled = false;
                }
                """,
            )

    callback_next = CustomJS(
        args=dict(button=button_next, other_button = button_previous, freq=freq , spinner=spinner, segmentation=segmentation, end=len(x), x_range = p.x_range, peak_index=peak_index),
        code="""
        var step = spinner.value;
        var end = end;
        var segmentation = segmentation;
        var peak = peak_index;

        if (x_range.end == end) {
            button.disabled = true;
        }
        else if (x_range.start > 0) {
            other_button.disabled = false;
        }

        const output2 = peak.reduce((prev, curr) => Math.abs(curr - x_range.end) < Math.abs(prev - x_range.end) ? curr : prev);
        const output1 = peak.reduce((prev, curr) => Math.abs(curr - x_range.start) < Math.abs(prev - x_range.start) ? curr : prev);
        const index_1 = peak.indexOf(output1);
        const index_2 = peak.indexOf(output2);
        
        if (segmentation == 'seconds') {
            if (x_range.end + step*freq > end) {
                x_range.end = end;
                x_range.start = end - step*freq;
                }
            else {
                x_range.start += step*freq;
                x_range.end += step*freq;
            }
        }
        else {
            if (index_1 + step > peak.length) {
                x_range.end = peak[-1];
                x_range.start = peak[-step];
                }
            else { 
                x_range.start = peak[index_1 + step];
                x_range.end = peak[index_2 + step];
            }
        }
        if (x_range.end == end) {
            button.disabled = true;
        }
        else if (x_range.start > 0) {
            other_button.disabled = false;
        }
        """,
    )
    button_next.js_on_click(callback_next)
    button_previous.js_on_click(callback_previous)
    

    layout = grid(
        [
            [toggle_show_peaks, spinner],
            [p],
            [select],
            [button_previous, button_next],
        ],
        sizing_mode="stretch_width",
    )

    return layout
