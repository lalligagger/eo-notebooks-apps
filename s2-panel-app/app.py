import holoviews as hv
import panel as pn
import xarray as xr
import json
from odc.stac import stac_load
import pystac
from pystac_client.client import Client
# import rasterio as rio
# from rasterio.session import AWSSession

from modules.constants import S2_BAND_COMB, S2_SPINDICES
from modules.image_plots import (
    # plot_s2_band_comb,
    plot_s2_spindex,
    plot_true_color_image,
)
from modules.image_statistics import HIST_PLACEHOLDER, plot_s2_spindex_hist

# Load the floatpanel extension
pn.extension("floatpanel")

# Disable webgl: https://github.com/holoviz/panel/issues/4855
hv.renderer("bokeh").webgl = False

client = Client.open('https://earth-search.aws.element84.com/v1/')

def get_band_comb_text(band_comb):
    """
    A function that return a StaticText showing
    the selected band combination.
    """

    band_comb_text = pn.widgets.StaticText(
        name="Band Combination", value=", ".join(str(band_comb))
    )

    return band_comb_text


def create_s2_dashboard():
    """
    This function creates the main dashboard
    """
    print("loading STAC items")
    with open('./tmp/items.json', "r") as f:
        payload = json.loads(f.read())
        query = payload["features"]
        items = pystac.ItemCollection(query)

    # Read the data TODO: move this to plot functions, so we only load the needed band(s)
    # s2_data = xr.open_dataarray("data/s2_data.nc", decode_coords="all")
    # aws_session = AWSSession(requester_pays=True)
    # with rio.Env(aws_session):
    #     print("loading items/ delayed data")
    #     s2_data = stac_load(
    #         items,
    #         bands=["red", "green", "blue", "nir", "nir08", "swir16", "swir22"],
    #         resolution=500,
    #         chunks={'time':1, 'x': 2048, 'y': 2048},
    #         # crs='EPSG:4326',
    #         ).to_stacked_array(new_dim='band', sample_dims=('time', 'x', 'y'))
    
    # s2_data = s2_data.astype("int16")

    # Time variable
    time_var = [i.datetime for i in items]
    time_date = [t.date() for t in time_var]

    # Time Select
    time_opts = dict(zip(time_date, time_date))
    time_select = pn.widgets.Select(name="Time", options=time_opts)

    # Sentinel-2 spectral indices ToogleGroup 
    # TODO: Switch to AutocompleteInput validated by spyndex names
    tg_title = pn.widgets.StaticText(name="", value="Sentinel-2 spectral indices")
    s2_spindices_tg = pn.widgets.ToggleGroup(
        name="Sentinel-2 indices",
        widget_type="button",
        behavior="radio",
        options=S2_SPINDICES,
    )

    # Create histogram button
    # TODO: Fix hist functionality
    show_hist_bt = pn.widgets.Button(name="Create Histogram", icon="chart-histogram")
    show_hist_bt.on_click(plot_s2_spindex_hist)

    # Resolution slider
    res_select = pn.widgets.IntSlider(name="Slider", start=50, end=2500, step=50, value=250)

    # Mask clouds Switch
    clm_title = pn.widgets.StaticText(name="", value="Mask clouds?")
    clm_switch = pn.widgets.Switch(name="Switch")

    # TODO: could these be merged into a single function that returns the slider plot?
    # Or returns 2 hv plots that are bound w/ Swipe below?
    # (Would solve current lag of spindex showing after RGB)
    s2_true_color_bind = pn.bind(
        plot_true_color_image,
        items=items,
        time=time_select,
        mask_clouds=clm_switch,
        resolution=res_select
    )

    s2_spindex_bind = pn.bind(
        plot_s2_spindex,
        items=items,
        time=time_select,
        s2_spindex=s2_spindices_tg,
        mask_clouds=clm_switch,
        resolution=res_select
    )

    # Use the Swipe tool to compare the spectral index with the true color image
    spindex_truecolor_swipe = pn.Swipe(s2_true_color_bind, s2_spindex_bind)

    # Create the main layout
    main_layout = pn.Row(
        # pn.Column(s2_band_comb_bind, s2_band_comb_text_bind),
        pn.Column(HIST_PLACEHOLDER, spindex_truecolor_swipe, show_hist_bt),
    )

    # Create the dashboard and turn into a deployable application
    s2_dash = pn.template.FastListTemplate(
        site="",
        title="EO DEMO: Sentinel-2 STAC explorer",
        theme="default",
        main=[main_layout],
        sidebar=[
            time_select,
            tg_title,
            s2_spindices_tg,
            res_select,
            clm_title,
            clm_switch,
        ],
    )

    return s2_dash


if __name__.startswith("bokeh"):
    # Create the dashboard and turn into a deployable application
    s2_dash = create_s2_dashboard()
    s2_dash.servable()
