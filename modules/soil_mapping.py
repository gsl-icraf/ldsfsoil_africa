from shiny import module, render, reactive
from shiny import ui as sui
from maplibre import Map, MapOptions, MapContext, Layer, LayerType, output_maplibregl, render_maplibregl
from maplibre.sources import RasterTileSource
from maplibre.basemaps import Basemap, Carto
import urllib.parse
import json
import numpy as np

# Africa center (lng, lat) and zoom
AFRICA_CENTER = (20.0, 2.0)
AFRICA_ZOOM = 3

# Topo + OSM hybrid using OpenTopoMap (renders OSM data with contours & hillshading)
TOPO_STYLE = {
    "version": 8,
    "sources": {
        "opentopomap": {
            "type": "raster",
            "tiles": [
                "https://a.tile.opentopomap.org/{z}/{x}/{y}.png",
                "https://b.tile.opentopomap.org/{z}/{x}/{y}.png",
                "https://c.tile.opentopomap.org/{z}/{x}/{y}.png",
            ],
            "tileSize": 256,
            "attribution": "Map data: &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors, <a href='http://viewfinderpanoramas.org'>SRTM</a> | Map style: &copy; <a href='https://opentopomap.org'>OpenTopoMap</a> (CC-BY-SA)",
            "maxzoom": 17,
        }
    },
    "layers": [{"id": "topo", "type": "raster", "source": "opentopomap"}],
}

# Satellite style using ESRI World Imagery (free, no API key needed)
SATELLITE_STYLE = {
    "version": 8,
    "sources": {
        "esri-satellite": {
            "type": "raster",
            "tiles": [
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ],
            "tileSize": 256,
            "attribution": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
        }
    },
    "layers": [{"id": "satellite", "type": "raster", "source": "esri-satellite"}],
}

BASEMAP_STYLES = {
    "topo": TOPO_STYLE,
    "dark": Basemap.carto_url(Carto.DARK_MATTER),
    "streets": Basemap.carto_url(Carto.VOYAGER),
    "satellite": SATELLITE_STYLE,
}

TITILER_ENDPOINT = "https://titiler.thegrit.earth/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png"

# Soil Layer Definitions
SOIL_LAYERS = {
    "soc": {
        "title": "Soil Organic Carbon",
        "url": "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m/Africa_predsoc_2024-2025_250m.tif",
        "bins": [0, 2.5, 12, 21.5, 31, 40.5, 100],
        "colors": ["#FFFECB", "#F2C95D", "#E69352", "#D85F4D", "#8E3F3D", "#442817", "#191900"],
    },
    "ph": {
        "title": "pH",
        "url": "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m/Africa_predpH_2024-2025_250m.tif",
        "bins": [4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        "colors": ["#d7191c", "#fdae61", "#ffffbf", "#a6d96a", "#1a9641", "#0571b0"],
    },
    "clay": {
        "title": "Clay",
        "url": "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m/Africa_predclay_2024-2025_250m.tif",
        "bins": [0, 15, 30, 45, 60, 100],
        "colors": ["#f7fcfd", "#e0ecf4", "#bfd3e6", "#9ebcda", "#8c96c6", "#8c6bb1"],
    },
    "sand": {
        "title": "Sand",
        "url": "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m/Africa_predsand_2024-2025_250m.tif",
        "bins": [0, 20, 40, 60, 80, 100],
        "colors": ["#ffffd4", "#fee391", "#fec44f", "#fe9929", "#d95f0e", "#993404"],
    },
    "tn": {
        "title": "Total Nitrogen",
        "url": "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m/Africa_predtn_2024-2025_250m.tif",
        "bins": [0, 5, 10, 20, 30, 50],
        "colors": ["#f7fcf0", "#e0f3db", "#ccebc5", "#a8ddb5", "#7bccc4", "#4eb3d3"],
    },
    "cec": {
        "title": "CEC",
        "url": "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m/Africa_predcec_2024-2025_250m.tif",
        "bins": [0, 50, 100, 200, 300, 500],
        "colors": ["#fff7bc", "#fee391", "#fec44f", "#fe9929", "#ec7014", "#cc4c02"],
    },
    "exca": {
        "title": "Exchangeable Calcium",
        "url": "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m/Africa_predexca_2024-2025_250m.tif",
        "bins": [0, 20, 50, 100, 200, 400],
        "colors": ["#f7f4f9", "#e7e1ef", "#d4b9da", "#c994c7", "#df65b0", "#980043"],
    },
    "exmg": {
        "title": "Exchangeable Magnesium",
        "url": "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m/Africa_predexmg_2024-2025_250m.tif",
        "bins": [0, 10, 25, 50, 100, 200],
        "colors": ["#f0f9e8", "#ccebc5", "#a8ddb5", "#7bccc4", "#43a2ca", "#0868ac"],
    },
}

def build_tile_url(cog_url, bins, colors, n_bins=100, nodata=-9999):
    """Build a TiTiler tile URL with an interval colormap."""
    bin_arr = np.array(bins, dtype=float)
    linear_values = np.linspace(bin_arr[0], bin_arr[-1], n_bins)
    
    def hex_to_rgb(hex_color):
        h = hex_color.lstrip("#")
        return [int(h[i:i+2], 16) for i in (0, 2, 4)]

    rgb_colors = [hex_to_rgb(c) for c in colors]
    norm_bins = (bin_arr - bin_arr[0]) / (bin_arr[-1] - bin_arr[0])
    norm_linear = (linear_values - bin_arr[0]) / (bin_arr[-1] - bin_arr[0])

    def interpolate_color(t):
        for j in range(len(norm_bins) - 1):
            if norm_bins[j] <= t <= norm_bins[j + 1]:
                denom = norm_bins[j + 1] - norm_bins[j]
                seg_t = (t - norm_bins[j]) / denom if denom else 0
                return [
                    int(rgb_colors[j][k] + seg_t * (rgb_colors[j + 1][k] - rgb_colors[j][k]))
                    for k in range(3)
                ] + [255]
        return rgb_colors[-1] + [255]

    gradient = [interpolate_color(t) for t in norm_linear]
    # Prepend a fully transparent interval to mask nodata (-9999) and zero
    colormap = [
        [[-10000.0, float(linear_values[0])], [0, 0, 0, 0]],
    ] + [
        [[float(linear_values[i]), float(linear_values[i + 1])], gradient[i]]
        for i in range(n_bins - 1)
    ]

    encoded_cog = urllib.parse.quote(cog_url, safe="")
    encoded_colormap = urllib.parse.quote(json.dumps(colormap), safe="")
    return (
        f"{TITILER_ENDPOINT}?url={encoded_cog}"
        f"&colormap={encoded_colormap}"
        f"&return_mask=true"
    )


# Pan-African palette
_TITLE_CLASS   = "pan-african-title fw-bold mb-0"
_CARD_TEXT     = "#d8e8d4"   # soft green-white — readable on dark glass bg
_ACCENT        = "#FCD116"   # Pan-African gold
_SIDEBAR_BG    = "rgba(0, 80, 30, 0.45)"   # glass green (also set via CSS)


@module.ui
def ui():
    return sui.layout_sidebar(
        sui.sidebar(
            sui.h6("Soil Property", style="color: #f0e8c0; letter-spacing: 0.05em;"),
            sui.input_select(
                "property",
                None,
                choices={"none": "None"} | {k: v["title"] for k, v in SOIL_LAYERS.items()},
                selected="none",
            ),
            sui.output_ui("legend"),
            width=280,
            open="desktop",
            fillable=True,
        ),
        sui.div(
            sui.card(
                sui.card_body(
                    sui.h2(
                        sui.HTML("Welcome to the LDSF Africa<br>Soil Mapping Dashboard!"),
                        class_=_TITLE_CLASS,
                    ),
                    class_="d-flex align-items-center justify-content-center",
                ),
                class_="glass-card",
                style="border: none !important; box-shadow: none !important; background: transparent !important;",
            ),
            sui.div(
                # Map fills remaining horizontal space
                sui.card(
                    output_maplibregl("map", height="100%"),
                    sui.card_footer(
                        sui.div(
                            sui.div(
                                sui.span("Basemap:", style="font-weight: bold; margin-right: 0.75rem;"),
                                sui.input_radio_buttons(
                                    "basemap",
                                    None,
                                    choices={"topo": "Topo", "dark": "Dark", "streets": "Streets", "satellite": "Satellite"},
                                    selected="topo",
                                    inline=True,
                                ),
                                style="display: flex; align-items: center;",
                            ),
                            sui.input_action_button(
                                "reset_view",
                                "⟳ Reset view",
                                style=(
                                    "background: rgba(196,137,90,0.18);"
                                    " border: 1px solid rgba(196,137,90,0.45);"
                                    " color: #e8d5b0;"
                                    " border-radius: 0.4rem;"
                                    " padding: 0.2rem 0.75rem;"
                                    " font-size: 0.85rem;"
                                    " cursor: pointer;"
                                ),
                            ),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%;",
                        ),
                        style="background: rgba(40,40,40,0.8); border-top: none; color: #f0e8c0; padding: 0.5rem 1rem;"
                    ),
                    class_="map-card",
                    full_screen=True,
                    style="flex: 1 1 0; min-height: 0; padding: 0; overflow: hidden; background: rgba(55, 32, 12, 0.50) !important;",
                ),
                # Instructions card docked to the right
                sui.card(
                    sui.card_header(
                        sui.tags.div(
                            sui.tags.span(
                                sui.tags.b("About this dashboard"),
                                id="right_panel_title",
                            ),
                            sui.tags.button(
                                sui.HTML("&#8250;"),
                                id="right_panel_btn",
                                onclick="toggleRightPanel(this)",
                                title="Collapse panel",
                                style=(
                                    "background: transparent;"
                                    " border: none;"
                                    " color: #f0e8c0;"
                                    " font-size: 1.4rem;"
                                    " line-height: 1;"
                                    " cursor: pointer;"
                                    " padding: 0;"
                                    " flex-shrink: 0;"
                                ),
                            ),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%;",
                        ),
                    ),
                    sui.card_body(
                        sui.p(
                            "This dashboard presents soil property maps for the African continent "
                            "derived from the Land Degradation Surveillance Framework (LDSF). "
                            "The LDSF is a multi-scale sampling and monitoring framework developed "
                            "by World Agroforestry (ICRAF) to assess and monitor the health of "
                            "terrestrial ecosystems. Use the map to explore spatial patterns in "
                            "soil properties including organic carbon, pH, texture, and nutrient "
                            "availability at 250 m resolution.",
                            style=f"color: {_CARD_TEXT}; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;",
                        ),
                        sui.hr(style="border-color: rgba(196,137,90,0.25); margin: 0 0 1rem 0;"),
                        sui.h6(
                            "How to use this dashboard",
                            style=f"color: {_CARD_TEXT}; font-size: 0.85rem; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;",
                        ),
                        sui.tags.ul(
                            sui.tags.li(
                                sui.tags.b("Pan: "),
                                "Click and drag to move the map.",
                            ),
                            sui.tags.li(
                                sui.tags.b("Zoom: "),
                                "Scroll wheel, pinch, or use the +/− buttons.",
                            ),
                            sui.tags.li(
                                sui.tags.b("Basemap: "),
                                "Switch between Dark, Streets and Satellite using the controls on the left.",
                            ),
                            sui.tags.li(
                                sui.tags.b("Layers: "),
                                "Soil property layers will appear here as they are added to the dashboard.",
                            ),
                            sui.tags.li(
                                sui.tags.b("Click features: "),
                                "Click on mapped areas to see soil property values and site metadata.",
                            ),
                            class_="ps-3",
                            style="font-size: 1rem; line-height: 1.7;",
                        ),
                        style=f"color: {_CARD_TEXT}; overflow-y: auto;",
                        id="right_panel_body",
                    ),
                    id="right_info_card",
                    class_="glass-card-instructions",
                    style="width: 450px; flex-shrink: 0; overflow: hidden; transition: width 0.3s ease;",
                ),
                sui.tags.script("""
function toggleRightPanel(btn) {
    var card = btn.closest('.glass-card-instructions');
    if (!card) return;
    var collapsed = card.classList.toggle('panel-collapsed');
    btn.innerHTML = collapsed ? '&#8249;' : '&#8250;';
    btn.title = collapsed ? 'Expand panel' : 'Collapse panel';
}
"""),
                style="display: flex; flex-direction: row; flex: 1 1 0; min-height: 0; gap: 0.75rem;",
            ),
            style="display: flex; flex-direction: column; height: 100%; gap: 0.75rem;",
        ),
        fillable=True,
        fill=True,
    )


@module.server
def server(input, output, session):

    @render.ui
    def legend():
        prop = input.property()
        if prop == "none":
            return sui.div()
        info = SOIL_LAYERS[prop]
        colors = info["colors"]
        bins = info["bins"]

        # Gradient bar: top = high value, bottom = low value
        stops = ", ".join(reversed(colors))
        gradient = f"linear-gradient(to bottom, {stops})"
        bar_h = 220

        # Label positions for each bin value
        n = len(bins)
        label_divs = []
        for i, val in enumerate(reversed(bins)):
            pct = i / (n - 1) * 100
            label_divs.append(
                sui.div(
                    str(val),
                    style=(
                        f"position: absolute; top: {pct}%; transform: translateY(-50%);"
                        " font-size: 0.75rem; color: #1a1a1a; white-space: nowrap;"
                    ),
                )
            )

        return sui.div(
            sui.div(
                sui.div(
                    style=(
                        f"background: {gradient}; width: 28px; height: {bar_h}px;"
                        " border-radius: 4px; border: 1px solid rgba(0,0,0,0.15);"
                        " flex-shrink: 0;"
                    ),
                ),
                sui.div(
                    *label_divs,
                    style=f"position: relative; height: {bar_h}px; padding-left: 8px;",
                ),
                style="display: flex; flex-direction: row; align-items: flex-start;",
            ),
            style=(
                "margin-top: 1rem; padding: 0.75rem 0.5rem;"
                " background: rgba(255,255,255,0.92); border-radius: 0.5rem;"
                " display: flex; justify-content: center;"
            ),
        )

    @render_maplibregl
    def map():
        m = Map(
            MapOptions(
                style=BASEMAP_STYLES["topo"],
                center=AFRICA_CENTER,
                zoom=AFRICA_ZOOM,
            )
        )
        for key, info in SOIL_LAYERS.items():
            tile_url = build_tile_url(info["url"], info["bins"], info["colors"])
            m.add_layer(
                Layer(
                    id=f"soil-{key}",
                    type=LayerType.RASTER,
                    source=RasterTileSource(tiles=[tile_url], tile_size=256),
                    paint={"raster-opacity": 0.8},
                    layout={"visibility": "none"},
                )
            )
        return m

    @reactive.effect
    @reactive.event(input.basemap)
    async def _update_basemap():
        style = BASEMAP_STYLES[input.basemap()]
        async with MapContext("map") as mc:
            mc.add_call("setStyle", style)

    @reactive.effect
    @reactive.event(input.property)
    async def _update_property():
        prop = input.property()
        async with MapContext("map") as mc:
            for key in SOIL_LAYERS:
                vis = "visible" if key == prop else "none"
                mc.set_layout_property(f"soil-{key}", "visibility", vis)

    @reactive.effect
    @reactive.event(input.reset_view)
    async def _reset_view():
        sui.update_radio_buttons("basemap", selected="topo")
        sui.update_radio_buttons("property", selected="none")
        async with MapContext("map") as mc:
            mc.add_call("flyTo", {"center": list(AFRICA_CENTER), "zoom": AFRICA_ZOOM})
