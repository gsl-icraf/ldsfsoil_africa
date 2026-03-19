from shiny import module
from shiny import ui as sui

from utils import T

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
def ui(lang="en"):
    t = lambda *keys: T(lang, "about", *keys)

    return sui.div(
        # ── Page title ────────────────────────────────────────────────────────
        sui.h2(
            t("page_title"),
            style="color: #f0e8c0; margin-bottom: 0.25rem;",
        ),
        sui.p(
            t("page_subtitle_pre"),
            sui.tags.a(t("page_subtitle_link"), href=_LDSF_URL, target="_blank", style=_A),
            t("page_subtitle_post"),
            style=_P + " margin-bottom: 1.25rem;",
        ),

        # ── Two-card row ──────────────────────────────────────────────────────
        sui.div(

            # LEFT card — About the LDSF
            sui.div(
                sui.h3(t("what_title"), style=_H3),
                sui.p(t("what_p1"), style=_P),
                sui.p(
                    t("what_p2_pre"),
                    sui.tags.b(t("what_p2_countries")),
                    t("what_p2_mid"),
                    sui.tags.b(t("what_p2_sites")),
                    t("what_p2_post"),
                    style=_P,
                ),
                sui.hr(style=_HR),
                sui.h4(t("applications_title"), style=_H4),
                sui.tags.ul(
                    sui.tags.li(sui.tags.b(t("app_baseline_b")),   t("app_baseline"),   style=_LI),
                    sui.tags.li(sui.tags.b(t("app_restoration_b")),t("app_restoration"),style=_LI),
                    sui.tags.li(sui.tags.b(t("app_degradation_b")),t("app_degradation"),style=_LI),
                    sui.tags.li(sui.tags.b(t("app_capacity_b")),   t("app_capacity"),   style=_LI),
                    sui.tags.li(sui.tags.b(t("app_policy_b")),     t("app_policy"),     style=_LI),
                    class_="ps-3 mb-0",
                ),
                style=_CARD_STYLE,
            ),

            # RIGHT card — Soil layers & methods
            sui.div(
                sui.h3(t("soil_title"), style=_H3),
                sui.p(t("soil_intro"), style=_P),
                sui.tags.ul(
                    sui.tags.li(sui.tags.b(t("soc_b")),      t("soc"),      style=_LI),
                    sui.tags.li(sui.tags.b(t("ph_b")),       t("ph"),       style=_LI),
                    sui.tags.li(sui.tags.b(t("clay_b")),     t("clay"),     style=_LI),
                    sui.tags.li(sui.tags.b(t("sand_b")),     t("sand"),     style=_LI),
                    sui.tags.li(sui.tags.b(t("nitrogen_b")), t("nitrogen"), style=_LI),
                    sui.tags.li(sui.tags.b(t("cec_b")),      t("cec"),      style=_LI),
                    class_="ps-3 mb-0",
                ),
                sui.hr(style=_HR),
                sui.h4(t("methods_title"), style=_H4),
                sui.p(t("methods_p"), style=_P),
                sui.hr(style=_HR),
                sui.h4(t("info_title"), style=_H4),
                sui.tags.ul(
                    sui.tags.li(
                        sui.tags.a("ldsf.thegrit.earth", href=_LDSF_URL, target="_blank", style=_A),
                        t("info_ldsf"),
                        style=_LI,
                    ),
                    sui.tags.li(
                        t("info_contact"),
                        sui.tags.a("t.vagen@cifor-icraf.org",
                                   href="mailto:t.vagen@cifor-icraf.org", style=_A),
                        " · ",
                        sui.tags.a("l.a.winowiecki@cifor-icraf.org",
                                   href="mailto:l.a.winowiecki@cifor-icraf.org", style=_A),
                        style=_LI,
                    ),
                    class_="ps-3 mb-0",
                ),
                style=_CARD_STYLE,
            ),

            # INFOGRAPHIC card
            sui.div(
                sui.h3(t("indicator_title"), style=_H3 + " margin-bottom: 1rem;"),
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
