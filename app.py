from pathlib import Path

from shiny import App, reactive, ui

from modules import soil_mapping, about

# Maps URL hash ↔ nav panel title
HASH_TO_NAV = {
    "#home":       "LDSF Soil Mapping",
    "#about_ldsf": "About the LDSF",
}
NAV_TO_HASH = {v: k for k, v in HASH_TO_NAV.items()}

# JS: sync window.location.hash with active tab (both directions)
_routing_js = ui.tags.script("""
const NAV_TO_HASH = """ + str(NAV_TO_HASH).replace("'", '"') + """;
const HASH_TO_NAV = """ + str(HASH_TO_NAV).replace("'", '"') + """;

// Tab → hash: update hash when user switches tabs
$(document).on('shiny:inputchanged', function(e) {
    if (e.name === 'nav') {
        const hash = NAV_TO_HASH[e.value];
        if (hash) history.replaceState(null, '', hash);
    }
});

// Hash → tab: wait for session to be fully running before sending input
$(document).on('shiny:connected', function() {
    const tab = HASH_TO_NAV[window.location.hash];
    if (tab) setTimeout(function() {
        Shiny.setInputValue('nav_from_hash', tab, {priority: 'event'});
    }, 300);
});
""")


app_ui = ui.page_navbar(
    ui.nav_panel("LDSF Soil Mapping", soil_mapping.ui("soil_mapping")),
    ui.nav_panel("About the LDSF", about.ui("about")),
    ui.nav_spacer(),
    ui.nav_control(
        ui.tags.a(
            ui.tags.img(
                src="cifor-icraf-logo-white.svg",
                alt="CIFOR-ICRAF",
                style="height: 36px; width: auto; display: block;",
            ),
            href="https://www.cifor-icraf.org",
            target="_blank",
            style="display: flex; align-items: center; padding: 0 1rem;",
        )
    ),
    id="nav",
    title=ui.tags.span(ui.HTML("🌍&nbsp;"), "Africa Soil Maps"),
    fillable="LDSF Soil Mapping",
    header=ui.tags.link(rel="stylesheet", href="style.css"),
    footer=ui.tags.div(
        _routing_js,
        ui.tags.footer(
            ui.tags.div(
                ui.tags.img(
                    src="spacial-logo.png",
                    alt="SPACIAL",
                    style="height: 28px; width: auto; display: block;",
                ),
                ui.tags.span(
                    ui.HTML(
                        "Developed by CIFOR-ICRAF SPACIAL&nbsp;&nbsp;·&nbsp;&nbsp;"
                        "&copy; CIFOR-ICRAF"
                    ),
                    style="font-size: 0.78rem; color: #a0b8a0;",
                ),
                style=(
                    "display: flex; align-items: center; gap: 0.85rem;"
                    " justify-content: center;"
                ),
            ),
            style=(
                "background: #0D1A0F; border-top: 1px solid rgba(255,255,255,0.08);"
                " padding: 0.5rem 1.5rem; text-align: center;"
            ),
        ),
    ),
    bg="#0D1A0F",
    inverse=True,
)


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.nav_from_hash)
    async def _hash_route():
        tab = input.nav_from_hash()
        if tab in NAV_TO_HASH:
            ui.update_navs("nav", selected=tab, session=session)

    soil_mapping.server("soil_mapping")
    about.server("about")


app = App(app_ui, server, static_assets=Path(__file__).parent / "www")
