from shiny import module
from shiny import ui as sui

_LDSF_URL = "https://ldsf.thegrit.earth"

_CARD_STYLE = (
    "background: rgba(0,50,20,0.45); backdrop-filter: blur(8px);"
    " border: 1px solid rgba(196,137,90,0.2); border-radius: 0.6rem;"
    " padding: 1.5rem; flex: 1 1 0; min-width: 0;"
)
_H3  = "color: #f0e8c0; margin-top: 0; margin-bottom: 0.75rem; font-size: 1.15rem;"
_H4  = "color: #f0e8c0; margin-top: 1.25rem; margin-bottom: 0.4rem; font-size: 1rem;"
_P   = "color: #d8e8d4; font-size: 0.92rem; line-height: 1.7; margin-bottom: 0.75rem;"
_LI  = "color: #d8e8d4; font-size: 0.92rem; line-height: 1.7;"
_HR  = "border-color: rgba(196,137,90,0.2); margin: 1rem 0;"
_A   = "color: #FCD116; text-decoration: none;"


@module.ui
def ui():
    return sui.div(
        # ── Page title ────────────────────────────────────────────────────────
        sui.h2(
            "About the LDSF Africa Soil Mapping Dashboard",
            style="color: #f0e8c0; margin-bottom: 0.25rem;",
        ),
        sui.p(
            "Continent-wide soil property predictions at 250 m resolution, derived from the ",
            sui.tags.a("Land Degradation Surveillance Framework (LDSF)", href=_LDSF_URL, target="_blank", style=_A),
            " — a globally deployed field monitoring system for soil and land health.",
            style=_P + " margin-bottom: 1.25rem;",
        ),

        # ── Two-card row ──────────────────────────────────────────────────────
        sui.div(

            # LEFT card — About the LDSF
            sui.div(
                sui.h3("What is the LDSF?", style=_H3),
                sui.p(
                    "The Land Degradation Surveillance Framework (LDSF) is a comprehensive field methodology "
                    "and capacity development platform developed by CIFOR-ICRAF (World Agroforestry). "
                    "It provides a consistent, robust framework to assess and monitor soil and land health, "
                    "combining simple field tools with advanced analysis — soil laboratory testing, "
                    "remote sensing, and machine learning — built on a rigorous hierarchical sampling design.",
                    style=_P,
                ),
                sui.p(
                    "Since its inception the LDSF has been deployed across ",
                    sui.tags.b("40+ countries"),
                    " and ",
                    sui.tags.b("500+ sites"),
                    " spanning sub-Saharan Africa, Central America, and South and South-East Asia.",
                    style=_P,
                ),
                sui.hr(style=_HR),
                sui.h4("Applications", style=_H4),
                sui.tags.ul(
                    sui.tags.li(sui.tags.b("Baseline assessments: "), "Establish soil health benchmarks before interventions.", style=_LI),
                    sui.tags.li(sui.tags.b("Restoration monitoring: "), "Track effectiveness of land restoration over time.", style=_LI),
                    sui.tags.li(sui.tags.b("Degradation research: "), "Understand drivers and spatial patterns of land degradation.", style=_LI),
                    sui.tags.li(sui.tags.b("Capacity building: "), "Train local stakeholders in evidence-based land management.", style=_LI),
                    sui.tags.li(sui.tags.b("Policy support: "), "Spatially explicit soil data for land-use planning and decision-making.", style=_LI),
                    class_="ps-3 mb-0",
                ),
                style=_CARD_STYLE,
            ),

            # RIGHT card — Soil layers & methods
            sui.div(
                sui.h3("Soil Properties in this Dashboard", style=_H3),
                sui.p(
                    "All layers are predictions for the 0–20 cm topsoil interval, modelled at 250 m resolution "
                    "using LDSF field and laboratory data combined with satellite-derived covariates.",
                    style=_P,
                ),
                sui.tags.ul(
                    sui.tags.li(sui.tags.b("Soil Organic Carbon (g/kg): "), "Key indicator of soil fertility and carbon sequestration potential.", style=_LI),
                    sui.tags.li(sui.tags.b("pH: "), "Acidity/alkalinity, controlling nutrient availability and microbial activity.", style=_LI),
                    sui.tags.li(sui.tags.b("Clay (%): "), "Clay fraction — influences water retention and structural stability.", style=_LI),
                    sui.tags.li(sui.tags.b("Sand (%): "), "Sand fraction — linked to drainage and erosion risk.", style=_LI),
                    sui.tags.li(sui.tags.b("Total Nitrogen (g/kg): "), "Primary macronutrient, tightly coupled with organic carbon.", style=_LI),
                    sui.tags.li(sui.tags.b("CEC (cmol/kg): "), "Cation Exchange Capacity — the soil's ability to retain nutrients.", style=_LI),
                    class_="ps-3 mb-0",
                ),
                sui.hr(style=_HR),
                sui.h4("Data & Methods", style=_H4),
                sui.p(
                    "Predictions generated by CIFOR-ICRAF using ensemble machine learning models trained on "
                    "LDSF observations. Covariates include terrain indices and multi-temporal satellite imagery. "
                    "Maps are served as Cloud-Optimised GeoTIFFs (COGs) via a TiTiler tile server for fast on-demand rendering.",
                    style=_P,
                ),
                sui.hr(style=_HR),
                sui.h4("Further Information", style=_H4),
                sui.tags.ul(
                    sui.tags.li(
                        sui.tags.a("ldsf.thegrit.earth", href=_LDSF_URL, target="_blank", style=_A),
                        " — field manual, publications, and global site map.",
                        style=_LI,
                    ),
                    sui.tags.li(
                        "Contact: ",
                        sui.tags.a("t.vagen@cifor-icraf.org", href="mailto:t.vagen@cifor-icraf.org", style=_A),
                        " · ",
                        sui.tags.a("l.a.winowiecki@cifor-icraf.org", href="mailto:l.a.winowiecki@cifor-icraf.org", style=_A),
                        style=_LI,
                    ),
                    class_="ps-3 mb-0",
                ),
                style=_CARD_STYLE,
            ),

            # INFOGRAPHIC card
            sui.div(
                sui.h3("LDSF Indicator Framework", style=_H3 + " margin-bottom: 1rem;"),
                sui.tags.img(
                    src="https://ldsf.thegrit.earth/assets/LDSF%20indicators.png",
                    style="width: 100%; height: auto; display: block; border-radius: 0.4rem;",
                    alt="LDSF Indicator Framework",
                ),
                style=_CARD_STYLE,
            ),

            style="display: flex; flex-direction: row; gap: 1.25rem; align-items: flex-start;",
        ),

        class_="p-4",
        style="width: 100%;",
    )


@module.server
def server(input, output, session):
    pass
