from shiny import module, render, reactive
from shiny import ui as sui
from maplibre import Map, MapOptions, MapContext, output_maplibregl, render_maplibregl
from load_data import SOIL_LAYERS

# Africa center (lng, lat) and zoom
AFRICA_CENTER = (20.0, 2.0)
AFRICA_ZOOM   = 3

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

def build_map_style(active_basemap="topo", active_soil="none"):
    """Build a complete MapLibre style with all basemaps + soil layers.
    Basemap and soil visibility are toggled via set_layout_property — no setStyle needed."""
    sources, layers = {}, []
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
    for key, tile_url in _SOIL_TILE_URLS.items():
        sources[f"soil-{key}"] = {"type": "raster", "tiles": [tile_url], "tileSize": 256}
        layers.append({
            "id": f"soil-{key}", "type": "raster", "source": f"soil-{key}",
            "paint": {"raster-opacity": 0.8},
            "layout": {"visibility": "visible" if key == active_soil else "none"},
        })
    return {"version": 8, "sources": sources, "layers": layers}


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
        cap = info.get("cap", False)
        cap_low = info.get("cap_low", False)
        unit = info.get("unit", "")

        # Gradient bar: top = high value, bottom = low value
        stops = ", ".join(reversed(colors))
        gradient = f"linear-gradient(to bottom, {stops})"
        bar_h = 220

        # Label positions for each bin value
        n = len(bins)
        label_divs = []
        for i, val in enumerate(reversed(bins)):
            pct = i / (n - 1) * 100
            if cap and i == 0:
                label = f"\u2265{val}"
            elif cap_low and i == n - 1:
                label = f"\u2264{val}"
            else:
                label = str(val)
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
                # Unit label — rotated vertically, left of the bar
                sui.div(
                    unit,
                    style=(
                        f"writing-mode: vertical-rl; transform: rotate(180deg);"
                        " font-size: 0.85rem; color: #1a1a1a; white-space: nowrap;"
                        f" height: {bar_h}px; display: flex; align-items: center;"
                        " justify-content: center; padding-right: 12px; flex-shrink: 0;"
                    ),
                ),
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
    @reactive.event(input.reset_view)
    async def _reset_view():
        sui.update_radio_buttons("basemap", selected="topo")
        sui.update_select("property", selected="none")
        try:
            async with MapContext("map") as mc:
                mc.add_call("flyTo", {"center": list(AFRICA_CENTER), "zoom": AFRICA_ZOOM})
        except Exception as e:
            print(f"[reset] {e}")
