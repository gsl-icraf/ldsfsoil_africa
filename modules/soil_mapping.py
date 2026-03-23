import math
import urllib.parse

import httpx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from shiny import module, render, reactive
from shiny import ui as sui
from maplibre import Map, MapOptions, MapContext, output_maplibregl, render_maplibregl
from load_data import SOIL_LAYERS
from utils import T

# Africa center (lng, lat) and zoom
AFRICA_CENTER = (20.0, 2.0)
AFRICA_ZOOM   = 3

TITILER_BASE   = "https://titiler.thegrit.earth"
SCALE_FACTOR   = 100  # COGs store float * SCALE_FACTOR as int16
LEGEND_BAR_H   = 220  # px height of the legend colour bar

# Convenience dict: key → pre-computed tile URL
_SOIL_TILE_URLS = {key: info["tiles_url"] for key, info in SOIL_LAYERS.items()}

# All basemaps as raster tile sources — no setStyle() needed, just toggle visibility
BASEMAP_TILES = {
    "topo": {
        "tiles": [
            "https://a.tile.opentopomap.org/{z}/{x}/{y}.png",
            "https://b.tile.opentopomap.org/{z}/{x}/{y}.png",
            "https://c.tile.opentopomap.org/{z}/{x}/{y}.png",
        ],
        "attribution": "Map data: &copy; OpenStreetMap contributors, SRTM | Style: &copy; OpenTopoMap (CC-BY-SA)",
        "maxzoom": 17,
    },
    "dark": {
        "tiles": [
            "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        ],
        "attribution": "&copy; OpenStreetMap contributors &copy; CARTO",
    },
    "streets": {
        "tiles": [
            "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
            "https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
            "https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
        ],
        "attribution": "&copy; OpenStreetMap contributors &copy; CARTO",
    },
    "satellite": {
        "tiles": [
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ],
        "attribution": "Tiles &copy; Esri",
    },
}

_EMPTY_FC = {"type": "FeatureCollection", "features": []}

# African country bounding boxes: [[west, south], [east, north]]
AFRICA_COUNTRIES = {
    "Algeria":                  [[-8.67, 18.97],  [11.99, 37.09]],
    "Angola":                   [[11.64, -18.02], [24.08, -4.44]],
    "Benin":                    [[0.77,  6.14],   [3.85,  12.41]],
    "Botswana":                 [[19.99, -26.91], [29.37, -17.78]],
    "Burkina Faso":             [[-5.52, 9.40],   [2.40,  15.08]],
    "Burundi":                  [[28.99, -4.47],  [30.85, -2.31]],
    "Cameroon":                 [[8.50,  1.65],   [16.01, 13.08]],
    "Central African Republic": [[14.42, 2.22],   [27.46, 11.00]],
    "Chad":                     [[13.47, 7.44],   [24.00, 23.45]],
    "Comoros":                  [[43.22, -12.42], [44.54, -11.36]],
    "Congo (Brazzaville)":      [[11.21, -5.02],  [18.65,  3.71]],
    "DR Congo":                 [[12.18, -13.46], [31.31,  5.39]],
    "Djibouti":                 [[41.75, 10.93],  [43.42, 12.71]],
    "Egypt":                    [[24.70, 22.00],  [36.90, 31.67]],
    "Equatorial Guinea":        [[8.02,  0.86],   [11.34,  3.79]],
    "Eritrea":                  [[36.43, 12.36],  [43.13, 18.00]],
    "Eswatini":                 [[30.80, -27.32], [32.14, -25.72]],
    "Ethiopia":                 [[32.99, 3.40],   [47.99, 14.89]],
    "Gabon":                    [[8.70,  -3.98],  [14.52,  2.32]],
    "Gambia":                   [[-16.82, 13.06], [-13.80, 13.83]],
    "Ghana":                    [[-3.26, 4.74],   [1.20,  11.17]],
    "Guinea":                   [[-15.13, 7.19],  [-7.65, 12.67]],
    "Guinea-Bissau":            [[-16.71, 10.93], [-13.64, 12.68]],
    "Ivory Coast":              [[-8.60, 4.36],   [-2.49, 10.74]],
    "Kenya":                    [[33.90, -4.68],  [41.90,  5.03]],
    "Lesotho":                  [[27.01, -30.65], [29.46, -28.57]],
    "Liberia":                  [[-11.49, 4.36],  [-7.37,  8.55]],
    "Libya":                    [[9.31,  19.50],  [25.16, 33.17]],
    "Madagascar":               [[43.22, -25.60], [50.48, -11.95]],
    "Malawi":                   [[32.67, -16.80], [35.92,  -9.37]],
    "Mali":                     [[-4.24, 10.15],  [4.27,  25.00]],
    "Mauritania":               [[-17.07, 14.62], [-4.83, 27.40]],
    "Mauritius":                [[57.30, -20.52], [57.80, -19.98]],
    "Morocco":                  [[-13.17, 27.67], [-1.01, 35.92]],
    "Mozambique":               [[32.07, -26.87], [40.84, -10.47]],
    "Namibia":                  [[11.73, -28.97], [25.26, -16.97]],
    "Niger":                    [[0.17,  11.69],  [15.90, 23.52]],
    "Nigeria":                  [[2.69,   4.24],  [14.68, 13.87]],
    "Rwanda":                   [[28.86,  -2.84], [30.90,  -1.05]],
    "São Tomé and Príncipe":    [[6.45,   0.02],  [7.46,   1.70]],
    "Senegal":                  [[-17.54, 12.31], [-11.35, 16.69]],
    "Sierra Leone":             [[-13.30, 6.93],  [-10.28, 10.00]],
    "Somalia":                  [[40.99,  -1.68], [51.41, 12.02]],
    "South Africa":             [[16.34, -34.82], [32.89, -22.13]],
    "South Sudan":              [[23.89,   3.49], [35.95, 12.24]],
    "Sudan":                    [[21.83,   8.68], [38.60, 22.23]],
    "Tanzania":                 [[29.34, -11.75], [40.44,  -0.99]],
    "Togo":                     [[0.14,   6.10],  [1.81,  11.14]],
    "Tunisia":                  [[7.52,  30.24],  [11.58, 37.54]],
    "Uganda":                   [[29.58,  -1.48], [35.04,  4.23]],
    "Western Sahara":           [[-17.10, 20.77], [-8.67, 27.67]],
    "Zambia":                   [[21.97, -18.08], [33.49,  -8.22]],
    "Zimbabwe":                 [[25.24, -22.42], [33.07, -15.61]],
}


def build_map_style(active_basemap="topo", active_soil="none"):
    """Build a complete MapLibre style with all basemaps + soil layers + circle overlay."""
    sources, layers = {}, []

    # Basemaps
    for key, info in BASEMAP_TILES.items():
        sources[f"basemap-{key}"] = {
            "type": "raster", "tiles": info["tiles"], "tileSize": 256,
            "attribution": info.get("attribution", ""),
            **({} if "maxzoom" not in info else {"maxzoom": info["maxzoom"]}),
        }
        layers.append({
            "id": f"basemap-{key}", "type": "raster", "source": f"basemap-{key}",
            "layout": {"visibility": "visible" if key == active_basemap else "none"},
        })

    # Soil raster layers
    for key, tile_url in _SOIL_TILE_URLS.items():
        sources[f"soil-{key}"] = {"type": "raster", "tiles": [tile_url], "tileSize": 256}
        layers.append({
            "id": f"soil-{key}", "type": "raster", "source": f"soil-{key}",
            "paint": {"raster-opacity": 0.8},
            "layout": {"visibility": "visible" if key == active_soil else "none"},
        })

    # Country outline overlay — always present, initially empty
    sources["country-source"] = {"type": "geojson", "data": _EMPTY_FC}
    layers.append({
        "id": "country-line",
        "type": "line",
        "source": "country-source",
        "paint": {"line-color": "#000000", "line-width": 3},
        "layout": {"visibility": "none"},
    })

    # Circle overlay (marker mode) — always present, initially empty
    sources["circle-source"] = {"type": "geojson", "data": _EMPTY_FC}
    layers.append({
        "id": "circle-fill",
        "type": "fill",
        "source": "circle-source",
        "paint": {"fill-color": "rgba(255,255,255,0.12)"},
        "layout": {"visibility": "none"},
    })
    layers.append({
        "id": "circle-line",
        "type": "line",
        "source": "circle-source",
        "paint": {"line-color": "#FCD116", "line-width": 2, "line-dasharray": [4, 2]},
        "layout": {"visibility": "none"},
    })

    return {"version": 8, "sources": sources, "layers": layers}


def _circle_polygon(lng, lat, radius_km=2.0, n=64):
    """GeoJSON Polygon approximating a circle of radius_km around (lng, lat)."""
    R = 6371.0
    lat_r = math.radians(lat)
    coords = []
    for i in range(n + 1):
        angle = 2 * math.pi * i / n
        dlat = math.degrees(radius_km / R * math.cos(angle))
        dlng = math.degrees(radius_km / R * math.sin(angle) / math.cos(lat_r))
        coords.append([lng + dlng, lat + dlat])
    return {"type": "Polygon", "coordinates": [coords]}


async def _show_circle(lng, lat):
    """Update the circle overlay on the map to a 2 km circle at (lng, lat)."""
    polygon = _circle_polygon(lng, lat)
    geojson = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": polygon, "properties": {}}
    ]}
    try:
        async with MapContext("map") as mc:
            mc.add_call("removeLayer", "circle-line")
            mc.add_call("removeLayer", "circle-fill")
            mc.add_call("removeSource", "circle-source")
            mc.add_call("addSource", "circle-source", {"type": "geojson", "data": geojson})
            mc.add_call("addLayer", {
                "id": "circle-fill", "type": "fill", "source": "circle-source",
                "paint": {"fill-color": "rgba(255,255,255,0.10)"},
            })
            mc.add_call("addLayer", {
                "id": "circle-line", "type": "line", "source": "circle-source",
                "paint": {"line-color": "#FCD116", "line-width": 2,
                          "line-dasharray": [4, 2]},
            })
    except Exception as e:
        print(f"[circle] {e}")


async def _hide_circle():
    """Remove circle data from the map overlay."""
    try:
        async with MapContext("map") as mc:
            mc.add_call("removeLayer", "circle-line")
            mc.add_call("removeLayer", "circle-fill")
            mc.add_call("removeSource", "circle-source")
            mc.add_call("addSource", "circle-source", {"type": "geojson", "data": _EMPTY_FC})
            mc.add_call("addLayer", {
                "id": "circle-fill", "type": "fill", "source": "circle-source",
                "paint": {"fill-color": "rgba(255,255,255,0.0)"},
                "layout": {"visibility": "none"},
            })
            mc.add_call("addLayer", {
                "id": "circle-line", "type": "line", "source": "circle-source",
                "paint": {"line-color": "#000000", "line-width": 3},
                "layout": {"visibility": "none"},
            })
    except Exception as e:
        print(f"[circle-hide] {e}")


async def _hide_country_outline():
    try:
        async with MapContext("map") as mc:
            mc.add_call("removeLayer", "country-line")
            mc.add_call("removeSource", "country-source")
            mc.add_call("addSource", "country-source", {"type": "geojson", "data": _EMPTY_FC})
            mc.add_call("addLayer", {
                "id": "country-line", "type": "line", "source": "country-source",
                "paint": {"line-color": "#000000", "line-width": 3},
                "layout": {"visibility": "none"},
            })
    except Exception as e:
        print(f"[country-hide] {e}")


# Pan-African palette
_TITLE_CLASS   = "pan-african-title fw-bold mb-0"
_CARD_TEXT     = "#d8e8d4"
_ACCENT        = "#FCD116"
_SIDEBAR_BG    = "rgba(0, 80, 30, 0.45)"

def _make_marker_js(lang="en"):
    on_text  = T(lang, "soil_mapping", "marker_on").replace("'", "\\'")
    off_text = T(lang, "soil_mapping", "marker_off").replace("'", "\\'")
    return sui.tags.script(f"""
var _MARKER_ON_TEXT  = '{on_text}';
var _MARKER_OFF_TEXT = '{off_text}';
Shiny.addCustomMessageHandler('marker_mode_change', function(active) {{
    var canvases = document.querySelectorAll('.maplibregl-canvas');
    canvases.forEach(function(c) {{
        c.style.cursor = active ? 'crosshair' : '';
    }});
    var btn = document.getElementById('marker_toggle_btn');
    if (btn) {{
        btn.textContent = active ? _MARKER_ON_TEXT : _MARKER_OFF_TEXT;
        btn.style.borderColor = active ? 'rgba(252,209,22,0.7)' : 'rgba(196,137,90,0.45)';
        btn.style.color = active ? '#FCD116' : '#e8d5b0';
    }}
}});
""")

_MARKER_BTN_STYLE = (
    "background: rgba(196,137,90,0.18);"
    " border: 1px solid rgba(196,137,90,0.45);"
    " color: #e8d5b0;"
    " border-radius: 0.4rem;"
    " padding: 0.3rem 0.75rem;"
    " font-size: 0.85rem;"
    " cursor: pointer;"
    " width: 100%;"
    " margin-top: 0.5rem;"
)


@module.ui
def ui(lang="en"):
    t = lambda *keys: T(lang, "soil_mapping", *keys)

    collapse_text = t("right_panel_collapse").replace("'", "\\'")
    expand_text   = t("right_panel_expand").replace("'", "\\'")
    panel_js = sui.tags.script(f"""
function toggleRightPanel(btn) {{
    var card = btn.closest('.glass-card-instructions');
    if (!card) return;
    var collapsed = card.classList.toggle('panel-collapsed');
    btn.innerHTML = collapsed ? '&#8249;' : '&#8250;';
    btn.title = collapsed ? '{expand_text}' : '{collapse_text}';
}}
""")

    return sui.layout_sidebar(
        sui.sidebar(
            sui.output_ui("sidebar_heading_ui"),
            sui.output_ui("property_hint"),
            sui.output_ui("marker_btn_ui"),
            sui.output_ui("legend"),
            sui.output_ui("depth_note_ui"),
            sui.output_ui("density_section"),
            _make_marker_js(lang),
            width=323,
            open="desktop",
            fillable=True,
        ),
        sui.div(
            sui.card(
                sui.card_body(
                    sui.div(
                        sui.h2(
                            sui.HTML(t("welcome_title")),
                            class_=_TITLE_CLASS,
                        ),
                        sui.div(
                            sui.div(
                                sui.span(
                                    t("sidebar_title"),
                                    style=(
                                        "color: #f0e8c0; font-size: 0.8rem;"
                                        " margin-bottom: 0.2rem; display: block; font-size: 1rem;"
                                    ),
                                ),
                                sui.input_select(
                                    "property",
                                    None,
                                    choices=(
                                        {"none": t("none")}
                                        | {k: v["title"] for k, v in SOIL_LAYERS.items()}
                                    ),
                                    selected="none",
                                    width="200px",
                                ),
                                style=(
                                    "display: flex; flex-direction: column;"
                                    " align-items: flex-start;"
                                ),
                            ),
                            sui.div(
                                sui.span(
                                    t("select_country"),
                                    style=(
                                        "color: #f0e8c0; font-size: 0.8rem;"
                                        " margin-bottom: 0.2rem; display: block; font-size: 1rem;"
                                    ),
                                ),
                                sui.input_select(
                                    "country_zoom",
                                    None,
                                    choices=(
                                        {"none": t("select")}
                                        | {k: k for k in sorted(AFRICA_COUNTRIES)}
                                    ),
                                    selected="none",
                                    width="200px",
                                ),
                                style=(
                                    "display: flex; flex-direction: column;"
                                    " align-items: flex-start;"
                                ),
                            ),
                            style=(
                                "display: flex; gap: 1rem;"
                                " align-items: flex-end; flex-wrap: wrap;"
                            ),
                        ),
                        style=(
                            "display: flex; align-items: center;"
                            " justify-content: space-between;"
                            " width: 100%; flex-wrap: wrap; gap: 0.5rem;"
                        ),
                    ),
                    class_="d-flex align-items-center flex-wrap",
                ),
                class_="glass-card",
                style="border: none !important; box-shadow: none !important; background: transparent !important;",
            ),
            sui.div(
                sui.card(
                    output_maplibregl("map", height="100%"),
                    sui.card_footer(
                        sui.div(
                            sui.div(
                                sui.span(t("basemap"), style="font-weight: bold; margin-right: 0.75rem;"),
                                sui.input_radio_buttons(
                                    "basemap",
                                    None,
                                    choices={
                                        "topo":      t("basemap_topo"),
                                        "dark":      t("basemap_dark"),
                                        "streets":   t("basemap_streets"),
                                        "satellite": t("basemap_satellite"),
                                    },
                                    selected="topo",
                                    inline=True,
                                ),
                                style="display: flex; align-items: center;",
                            ),
                            sui.div(
                                sui.output_ui("layer_toggle_ui"),
                                sui.input_action_button(
                                    "reset_view",
                                    t("reset_view"),
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
                                style="display: flex; gap: 0.5rem; align-items: center;",
                            ),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%;",
                        ),
                        style="background: rgba(40,40,40,0.8); border-top: none; color: #f0e8c0; padding: 0.5rem 1rem;"
                    ),
                    class_="map-card",
                    full_screen=True,
                    style="flex: 1 1 0; min-height: 0; padding: 0; overflow: hidden; background: rgba(55, 32, 12, 0.50) !important;",
                ),
                sui.card(
                    sui.card_header(
                        sui.tags.div(
                            sui.tags.span(sui.tags.b(t("right_panel_title")), id="right_panel_title"),
                            sui.tags.button(
                                sui.HTML("&#8250;"),
                                id="right_panel_btn",
                                onclick="toggleRightPanel(this)",
                                title=t("right_panel_collapse"),
                                style=(
                                    "background: transparent; border: none; color: #f0e8c0;"
                                    " font-size: 1.4rem; line-height: 1; cursor: pointer;"
                                    " padding: 0; flex-shrink: 0;"
                                ),
                            ),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%;",
                        ),
                    ),
                    sui.card_body(
                        sui.p(
                            t("right_panel_desc"),
                            style=f"color: {_CARD_TEXT}; font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;",
                        ),
                        sui.hr(style="border-color: rgba(196,137,90,0.12); margin: 0 0 1rem 0;"),
                        sui.h6(
                            t("how_to_title"),
                            style=f"color: {_CARD_TEXT}; font-size: 0.85rem; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;",
                        ),
                        sui.tags.ul(
                            sui.tags.li(sui.tags.b(t("how_pan_b")),     t("how_pan")),
                            sui.tags.li(sui.tags.b(t("how_zoom_b")),    t("how_zoom")),
                            sui.tags.li(sui.tags.b(t("how_basemap_b")), t("how_basemap")),
                            sui.tags.li(sui.tags.b(t("how_layers_b")),  t("how_layers")),
                            sui.tags.li(sui.tags.b(t("how_click_b")),   t("how_click")),
                            class_="ps-3",
                            style="font-size: 1rem; line-height: 1.7;",
                        ),
                        sui.hr(style=(
                            "border-color: rgba(196,137,90,0.12);"
                            " margin: 1rem 0 0.75rem 0;"
                        )),
                        sui.p(
                            t("map_year_note"),
                            style="color: #a8c4a8; font-size: 1.2rem; font-style: italic; margin: 0;",
                        ),
                        sui.hr(style=(
                            "border-color: rgba(196,137,90,0.12);"
                            " margin: 0.75rem 0 0 0;"
                        )),
                        style=f"color: {_CARD_TEXT}; overflow-y: auto;",
                        id="right_panel_body",
                    ),
                    id="right_info_card",
                    class_="glass-card-instructions",
                    style="width: 450px; flex-shrink: 0; overflow: hidden; transition: width 0.3s ease;",
                ),
                panel_js,
                style="display: flex; flex-direction: row; flex: 1 1 0; min-height: 0; gap: 0.75rem;",
            ),
            style="display: flex; flex-direction: column; height: 100%; gap: 0.75rem;",
        ),
        fillable=True,
        fill=True,
    )


def _legend_ticks(bins, custom_ticks):
    """Return list of (value, pct_from_top) for legend tick marks.

    If custom_ticks is provided, each tick is positioned proportionally within
    [bins[0], bins[-1]].  Otherwise 5 evenly-spaced ticks are used.
    """
    v_min, v_max = bins[0], bins[-1]
    vals = sorted(custom_ticks, reverse=True) if custom_ticks else list(
        np.linspace(v_max, v_min, 5)
    )
    return [(v, (v_max - v) / (v_max - v_min) * 100) for v in vals]


@module.server
def server(input, output, session):

    _marker_active  = reactive.value(False)
    _last_click     = reactive.value(None)
    _layer_visible  = reactive.value(True)

    @reactive.calc
    def _lang():
        try:
            qs = session.input[".clientdata_url_search"]()
            params = urllib.parse.parse_qs(qs.lstrip("?"))
            return params.get("lang", ["en"])[0]
        except Exception:
            return "en"

    # ── Sidebar heading ───────────────────────────────────────────────────────
    @render.ui
    def sidebar_heading_ui():
        lang = _lang()
        prop = input.property()
        style = "color: #f0e8c0; letter-spacing: 0.05em; font-size: 1.15rem;"
        if prop == "none":
            return sui.h6(T(lang, "soil_mapping", "sidebar_heading"), style=style)
        title = SOIL_LAYERS[prop]["title"]
        text = T(lang, "soil_mapping", "sidebar_displaying").format(title=title)
        return sui.div(
            sui.h6(text, style=style),
            sui.p(
                T(lang, "soil_mapping", "sidebar_depth_note"),
                style=(
                    "color: #a8c4a8; font-size: 1rem;"
                    " font-style: italic; margin: 0.1rem 0 0.5rem 0;"
                ),
            ),
        )

    # ── Property hint (shown only when no property selected) ──────────────────
    @render.ui
    def property_hint():
        if input.property() != "none":
            return sui.div()
        lang = _lang()
        return sui.p(
            T(lang, "soil_mapping", "property_hint"),
            style="color: #d8e8d4; font-size: 1.05rem; margin-top: 0.5rem; font-style: italic; line-height: 1.6;",
        )

    # ── Depth note (shown when a property is selected) ────────────────────────
    @render.ui
    def depth_note_ui():
        if input.property() == "none":
            return sui.div()
        lang = _lang()
        return sui.div(
            sui.span(
                T(lang, "soil_mapping", "depth_note"),
                style="color: #d8e8d4; font-size: 0.85rem;",
            ),
            sui.tags.button(
                T(lang, "soil_mapping", "depth_more"),
                onclick="history.pushState(null,'','#about_ldsf'); Shiny.setInputValue('nav_from_hash', 'About the LDSF', {priority: 'event'});",
                style=(
                    "background: rgba(196,137,90,0.18);"
                    " border: 1px solid rgba(196,137,90,0.45);"
                    " color: #FCD116;"
                    " border-radius: 0.4rem;"
                    " padding: 0.2rem 0.75rem;"
                    " font-size: 0.85rem;"
                    " cursor: pointer;"
                    " width: 100%;"
                ),
            ),
            style=(
                "background: rgba(0,50,20,0.45);"
                " border: 1px solid rgba(196,137,90,0.2); border-radius: 0.5rem;"
                " padding: 0.6rem 0.75rem;"
                " display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem;"
            ),
        )

    # ── Marker mode button (hidden when no property selected) ─────────────────
    @render.ui
    def marker_btn_ui():
        if input.property() == "none":
            return sui.div()
        lang = _lang()
        return sui.tags.button(
            T(lang, "soil_mapping", "marker_off"),
            id="marker_toggle_btn",
            onclick="Shiny.setInputValue('soil_mapping-marker_toggle', Math.random());",
            style=_MARKER_BTN_STYLE,
        )

    # ── Layer visibility toggle button ────────────────────────────────────────
    @render.ui
    def layer_toggle_ui():
        if input.property() == "none":
            return sui.div()
        lang    = _lang()
        visible = _layer_visible.get()
        label   = T(lang, "soil_mapping", "layer_on" if visible else "layer_off")
        return sui.tags.button(
            label,
            id="layer_toggle_btn",
            onclick="Shiny.setInputValue('soil_mapping-layer_toggle', Math.random());",
            style=(
                "background: rgba(196,137,90,0.18);"
                " border: 1px solid rgba(196,137,90,0.45);"
                " color: #e8d5b0;"
                " border-radius: 0.4rem;"
                " padding: 0.2rem 0.75rem;"
                " font-size: 0.85rem;"
                " cursor: pointer;"
            ),
        )

    @reactive.effect
    @reactive.event(input.layer_toggle)
    async def _toggle_layer():
        prop = input.property()
        if prop == "none":
            return
        new_vis = not _layer_visible.get()
        _layer_visible.set(new_vis)
        vis_str = "visible" if new_vis else "none"
        try:
            async with MapContext("map") as mc:
                mc.set_layout_property(f"soil-{prop}", "visibility", vis_str)
        except Exception as e:
            print(f"[layer_toggle] {e}")

    # ── Handle property change ─────────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.property)
    async def _on_property_change():
        _layer_visible.set(True)
        if input.property() == "none":
            # Clearing the property: remove circle and turn off marker mode
            if _last_click.get() is not None:
                _last_click.set(None)
                await _hide_circle()
            if _marker_active.get():
                _marker_active.set(False)
                await session.send_custom_message("marker_mode_change", False)
        # If switching between properties, keep the circle — histogram rerenders automatically
        # Switch basemap to dark when a property is selected, topo when cleared
        if input.property() != "none":
            sui.update_radio_buttons("basemap", selected="dark")
            try:
                async with MapContext("map") as mc:
                    for key in BASEMAP_TILES:
                        mc.set_layout_property(f"basemap-{key}", "visibility",
                                               "visible" if key == "dark" else "none")
            except Exception as e:
                print(f"[auto-basemap] {e}")

    # ── Marker mode toggle ────────────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.marker_toggle)
    async def _toggle_marker():
        new_state = not _marker_active.get()
        _marker_active.set(new_state)
        if not new_state:
            _last_click.set(None)
            await _hide_circle()
        await session.send_custom_message("marker_mode_change", new_state)

    # ── Handle map click ──────────────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input["map_clicked"])
    async def _handle_click():
        if not _marker_active.get():
            return
        clicked = input["map_clicked"]()
        if not clicked or "coords" not in clicked:
            return
        _last_click.set(clicked)
        coords = clicked["coords"]
        await _show_circle(coords["lng"], coords["lat"])

    # ── Legend ────────────────────────────────────────────────────────────────
    @render.ui
    def legend():
        prop = input.property()
        if prop == "none":
            return sui.div()
        info = SOIL_LAYERS[prop]
        colors = info["colors"]
        bins = info["bins"]
        cap = info.get("cap", False)
        cap_low = info.get("cap_low", False)
        unit = info.get("unit", "")

        gradient   = f"linear-gradient(to bottom, {', '.join(reversed(colors))})"
        tick_items = _legend_ticks(bins, info.get("ticks"))
        label_divs = []
        for i, (val, pct) in enumerate(tick_items):
            rounded = format(round(val, 1), 'g')
            if cap and i == 0:
                label = f"\u2265{rounded}"
            elif cap_low and i == len(tick_items) - 1:
                label = f"\u2264{rounded}"
            else:
                label = rounded
            label_divs.append(
                sui.div(
                    label,
                    style=(
                        f"position: absolute; top: {pct}%; transform: translateY(-50%);"
                        " font-size: 0.75rem; color: #1a1a1a; white-space: nowrap;"
                    ),
                )
            )

        return sui.div(
            sui.div(
                sui.div(
                    unit,
                    style=(
                        "writing-mode: vertical-rl; transform: rotate(180deg);"
                        " font-size: 0.85rem; color: #1a1a1a; white-space: nowrap;"
                        f" height: {LEGEND_BAR_H}px; display: flex; align-items: center;"
                        " justify-content: center; padding-right: 12px; flex-shrink: 0;"
                    ),
                ),
                sui.div(
                    style=(
                        f"background: {gradient}; width: 28px; height: {LEGEND_BAR_H}px;"
                        " border-radius: 4px; border: 1px solid rgba(0,0,0,0.15);"
                        " flex-shrink: 0;"
                    ),
                ),
                sui.div(
                    *label_divs,
                    style=f"position: relative; height: {LEGEND_BAR_H}px; padding-left: 8px;",
                ),
                style="display: flex; flex-direction: row; align-items: flex-start;",
            ),
            style=(
                "margin-top: 1rem; padding: 0.75rem 0.5rem;"
                " background: rgba(255,255,255,0.92); border-radius: 0.5rem;"
                " display: flex; justify-content: center;"
            ),
        )

    # ── Density section ───────────────────────────────────────────────────────
    @render.ui
    def density_section():
        if not _marker_active.get():
            return sui.div()
        lang = _lang()
        click = _last_click.get()
        if click is None:
            return sui.div(
                sui.p(
                    T(lang, "soil_mapping", "click_hint"),
                    style="color: #d8e8d4; font-size: 0.8rem; margin-top: 0.75rem; font-style: italic;",
                )
            )
        prop = input.property()
        if prop == "none":
            return sui.div(
                sui.p(
                    T(lang, "soil_mapping", "select_hint"),
                    style="color: #d8e8d4; font-size: 0.8rem; margin-top: 0.75rem; font-style: italic;",
                )
            )
        coords = click["coords"]
        radius_label = T(lang, "soil_mapping", "radius_label")
        return sui.div(
            sui.hr(style="border-color: rgba(196,137,90,0.2); margin: 0.75rem 0 0.5rem 0;"),
            sui.p(
                f"📍 {coords['lat']:.4f}°, {coords['lng']:.4f}°  |  {radius_label}",
                style="color: #d8e8d4; font-size: 0.78rem; margin: 0 0 0.4rem 0;",
            ),
            sui.output_plot("density_plot", height="180px"),
        )

    # ── Density plot ──────────────────────────────────────────────────────────
    @render.plot
    async def density_plot():
        click = _last_click.get()
        prop  = input.property()
        lang  = _lang()
        no_data_label = T(lang, "soil_mapping", "no_data")
        pixels_label  = T(lang, "soil_mapping", "pixels")
        mean_label    = T(lang, "soil_mapping", "mean")

        if click is None or prop == "none":
            fig = plt.figure(figsize=(2.6, 1.8))
            fig.patch.set_alpha(0)
            return fig

        info    = SOIL_LAYERS[prop]
        cog_url = info["cog_url"]
        coords  = click["coords"]
        lng, lat = coords["lng"], coords["lat"]

        polygon = _circle_polygon(lng, lat, radius_km=2.0)
        geojson = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": polygon, "properties": {}}],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{TITILER_BASE}/cog/statistics",
                    params={"url": cog_url, "nodata": -9999},
                    json=geojson,
                )
            if resp.status_code != 200:
                raise ValueError(f"TiTiler {resp.status_code}: {resp.text[:200]}")
            data = resp.json()
            feat  = data["features"][0]
            props = feat["properties"]
            # Support both 'statistics' wrapper and flat layout
            b1 = props.get("statistics", props).get("b1") or props.get("b1")
            counts = np.array(b1["histogram"][0], dtype=float)
            edges  = np.array(b1["histogram"][1], dtype=float) / SCALE_FACTOR
        except Exception as e:
            print(f"[density_plot] {e}")
            fig, ax = plt.subplots(figsize=(2.6, 1.8))
            ax.text(0.5, 0.5, no_data_label, ha="center", va="center",
                    transform=ax.transAxes, color="#888", fontsize=9)
            ax.set_axis_off()
            fig.patch.set_facecolor("white")
            fig.patch.set_alpha(0.92)
            return fig

        bin_centers = (edges[:-1] + edges[1:]) / 2
        mask = (counts > 0) & (edges[:-1] > 0)
        if not mask.any():
            fig, ax = plt.subplots(figsize=(2.6, 1.8))
            ax.text(0.5, 0.5, no_data_label, ha="center", va="center",
                    transform=ax.transAxes, color="#888", fontsize=9)
            ax.set_axis_off()
            fig.patch.set_facecolor("white")
            fig.patch.set_alpha(0.92)
            return fig

        mean_val = np.average(bin_centers[mask], weights=counts[mask])
        bar_color   = info["colors"][len(info["colors"]) // 2]

        fig, ax = plt.subplots(figsize=(2.6, 1.8))
        fig.patch.set_facecolor("white")
        fig.patch.set_alpha(0.92)
        ax.set_facecolor("#f8f8f4")

        ax.bar(bin_centers, counts, width=(edges[1] - edges[0]) * 0.9,
               color=bar_color, edgecolor="none", alpha=0.85)
        ax.axvline(mean_val, color="#333", linewidth=1.2, linestyle="--",
                   label=f"{mean_label} {mean_val:.2f}")

        ax.set_xlabel(info.get("unit", ""), fontsize=7, color="#333")
        ax.set_ylabel(pixels_label, fontsize=7, color="#333")
        ax.tick_params(labelsize=6, colors="#444")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#aaa")
        ax.legend(fontsize=6, frameon=False, labelcolor="#333")

        fig.tight_layout(pad=0.4)
        return fig

    # ── Map ───────────────────────────────────────────────────────────────────
    @render_maplibregl
    def map():
        return Map(MapOptions(
            style=build_map_style("topo", "none"),
            center=AFRICA_CENTER,
            zoom=AFRICA_ZOOM,
        ))

    @reactive.effect
    @reactive.event(input.basemap)
    async def _update_basemap():
        new_basemap = input.basemap()
        try:
            async with MapContext("map") as mc:
                for key in BASEMAP_TILES:
                    vis = "visible" if key == new_basemap else "none"
                    mc.set_layout_property(f"basemap-{key}", "visibility", vis)
        except Exception as e:
            print(f"[basemap] {e}")

    @reactive.effect
    @reactive.event(input.property)
    async def _update_property():
        prop = input.property()
        try:
            async with MapContext("map") as mc:
                for key in SOIL_LAYERS:
                    vis = "visible" if key == prop else "none"
                    mc.set_layout_property(f"soil-{key}", "visibility", vis)
        except Exception as e:
            print(f"[property] {e}")

    @reactive.effect
    @reactive.event(input.country_zoom)
    async def _zoom_to_country():
        country = input.country_zoom()
        if country == "none":
            await _hide_country_outline()
            return
        bounds = AFRICA_COUNTRIES.get(country)
        if bounds is None:
            return

        # Fetch simplified country polygon from Nominatim
        country_geojson = _EMPTY_FC
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": country, "format": "geojson",
                            "polygon_geojson": 1, "limit": 1,
                            "addressdetails": 0},
                    headers={"User-Agent": "AfricaSoilMaps/1.0"},
                )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("features"):
                    country_geojson = data
        except Exception as e:
            print(f"[country boundary] {e}")

        try:
            async with MapContext("map") as mc:
                mc.add_call("removeLayer", "country-line")
                mc.add_call("removeSource", "country-source")
                mc.add_call("addSource", "country-source",
                            {"type": "geojson", "data": country_geojson})
                mc.add_call("addLayer", {
                    "id": "country-line", "type": "line",
                    "source": "country-source",
                    "paint": {"line-color": "#000000", "line-width": 3},
                })
                mc.add_call("fitBounds", bounds, {"padding": 30, "duration": 800})
        except Exception as e:
            print(f"[country_zoom] {e}")

    @reactive.effect
    @reactive.event(input.reset_view)
    async def _reset_view():
        sui.update_radio_buttons("basemap", selected="topo")
        sui.update_select("property", selected="none")
        sui.update_select("country_zoom", selected="none")
        _marker_active.set(False)
        _last_click.set(None)
        _layer_visible.set(True)
        await session.send_custom_message("marker_mode_change", False)
        await _hide_circle()
        await _hide_country_outline()
        try:
            async with MapContext("map") as mc:
                mc.add_call("flyTo", {"center": list(AFRICA_CENTER), "zoom": AFRICA_ZOOM})
        except Exception as e:
            print(f"[reset] {e}")
