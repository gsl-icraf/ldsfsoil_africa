from pathlib import Path

from shiny import App, reactive, ui

from modules import soil_mapping, about

# Maps URL ?page= value ↔ nav panel title
PAGE_TO_NAV = {
    "soil_mapping": "LDSF Soil Mapping",
    "about": "About",
}
NAV_TO_PAGE = {v: k for k, v in PAGE_TO_NAV.items()}

# JS: keep ?page= query param in sync when the user switches tabs
_routing_js = ui.tags.script("""
$(document).on('shiny:inputchanged', function(e) {
    if (e.name === 'nav') {
        const pageMap = """ + str(NAV_TO_PAGE).replace("'", '"') + """;
        const page = pageMap[e.value] || e.value;
        const url = new URL(window.location);
        url.searchParams.set('page', page);
        window.history.pushState({}, '', url);
    }
});
""")


app_ui = ui.page_navbar(
    ui.nav_panel("LDSF Soil Mapping", soil_mapping.ui("soil_mapping")),
    ui.nav_panel("About", about.ui("about")),
    id="nav",
    title=ui.tags.span(ui.HTML("🌍&nbsp;"), "Africa Soil Maps"),
    fillable="LDSF Soil Mapping",
    header=ui.tags.link(rel="stylesheet", href="style.css"),
    footer=ui.tags.div(_routing_js),
    bg="#0D1A0F",   # deep dark green — Pan-African base
    inverse=True,  # light text/links on the dark background
)


def server(input, output, session):
    # On session start: read ?page= from URL and jump to the correct panel
    @reactive.effect
    async def _init_route():
        page = session.http_conn.query_params.get("page")
        if page and page in PAGE_TO_NAV:
            ui.update_navs("nav", selected=PAGE_TO_NAV[page], session=session)

    soil_mapping.server("soil_mapping")
    about.server("about")


app = App(app_ui, server, static_assets=Path(__file__).parent / "www")
