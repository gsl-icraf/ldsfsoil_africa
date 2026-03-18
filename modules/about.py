from shiny import module
from shiny import ui as sui


@module.ui
def ui():
    return sui.div(
        sui.h2("Africa Soil Maps"),
        sui.p(
            "This application provides interactive visualizations of soil data across the African continent. "
            "The maps are intended to support research, land use planning, and agricultural decision-making."
        ),
        sui.hr(),
        sui.h4("Available Maps"),
        sui.tags.ul(
            sui.tags.li(
                sui.tags.b("Soil Mapping: "),
                "Explore baseline soil property layers across Africa. "
                "Use the basemap selector to switch between dark, street, and satellite backgrounds.",
            ),
        ),
        sui.hr(),
        sui.h4("Basemaps"),
        sui.tags.ul(
            sui.tags.li(sui.tags.b("Dark: "), "CartoDB Dark Matter — a clean dark basemap suited for data overlays."),
            sui.tags.li(sui.tags.b("Streets: "), "CartoDB Voyager — a light street map showing roads and place names."),
            sui.tags.li(
                sui.tags.b("Satellite: "),
                "ESRI World Imagery — high-resolution satellite imagery sourced from Esri and partners.",
            ),
        ),
        sui.hr(),
        sui.h4("Data Sources"),
        sui.tags.ul(
            sui.tags.li("World Agroforestry (ICRAF) — Africa-wide soil property predictions at 250m resolution based on the Land Degradation Surveillance Framework (LDSF) soil data and machine learning.")
        ),
        sui.hr(),
        sui.h4("Notes"),
        sui.p(
            "This app is under active development. Soil layers and analytical tools will be added progressively. "
            "For questions or contributions, please get in touch with the development team."
        ),
        class_="p-4 about-content",
        style="max-width: 800px;",
    )


@module.server
def server(input, output, session):
    pass
