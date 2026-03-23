import json
import urllib.parse
import urllib.request
import numpy as np

# ── TiTiler endpoint ────────────────────────────────────────────────────────
TITILER_ENDPOINT = "https://titiler.thegrit.earth/cog/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
STAC_BASE        = "https://stacapi100.thegrit.earth/eodata/cogeo/africa_soil_maps_250m"

# ── COG URLs ────────────────────────────────────────────────────────────────
soc_cog_url  = f"{STAC_BASE}/ldsfsoil_africa_predsoc_2024-2025_250m_cog.tif"
ph_cog_url   = f"{STAC_BASE}/ldsfsoil_africa_predpH_2024-2025_250m_cog.tif"
clay_cog_url = f"{STAC_BASE}/ldsfsoil_africa_predclay_2024-2025_250m_cog.tif"
sand_cog_url = f"{STAC_BASE}/ldsfsoil_africa_predsand_2024-2025_250m_cog.tif"
tn_cog_url   = f"{STAC_BASE}/ldsfsoil_africa_predtn_2024-2025_250m_cog.tif"
cec_cog_url  = f"{STAC_BASE}/ldsfsoil_africa_predcec_2024-2025_250m_cog.tif"

# ── Colormaps ───────────────────────────────────────────────────────────────
soc_bins   = [1, 2.5, 12, 21.5, 31, 40.5, 120]
soc_colors = ["#FFFECB", "#F2C95D", "#E69352", "#D85F4D", "#8E3F3D", "#442817", "#191900"]

ph_bins = [4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5]
ph_colors = ["#fde725", "#5dc863", "#27ad81", "#21908c", "#2c728e", "#3b528b", "#472d7b", "#3b0f70","#440154"]

clay_bins   = [0, 15, 30, 50, 70, 85, 100]
clay_colors = ["#440154", "#3b528b", "#21918c", "#27ad81", "#5dc963", "#aadc32", "#fde725"]

sand_bins   = [0, 15, 30, 50, 70, 85, 100]
sand_colors = ["#440154", "#3b528b", "#21918c", "#27ad81", "#5dc963", "#aadc32", "#fde725"]

tn_bins   = [0.1, 2, 4, 6, 8, 10]
tn_colors = ["#FFFECB", "#F2C95D", "#E69352", "#D85F4D", "#8E3F3D", "#442817"]

cec_bins   = [0, 20, 40, 60, 80, 100]
cec_colors = ["#440154", "#3b528b", "#21918c", "#5dc963", "#aadc32", "#fde725"]

# ── Histogram stretch ────────────────────────────────────────────────────────
TITILER_BASE = "https://titiler.thegrit.earth"

def stretch_range(cog_url, scale_factor=100):
    """2nd–98th percentile stretch range from valid raster pixels (>0)."""
    url = (f"{TITILER_BASE}/cog/statistics"
           f"?url={urllib.parse.quote(cog_url, safe='')}"
           f"&nodata=-32768&histogram_bins=100")
    with urllib.request.urlopen(url, timeout=30) as resp:
        band = json.loads(resp.read())["b1"]
    counts = np.array(band["histogram"][0], dtype=float)
    edges  = np.array(band["histogram"][1], dtype=float) / scale_factor
    mids   = (edges[:-1] + edges[1:]) / 2
    valid  = mids > 0
    cdf    = np.cumsum(counts[valid]) / counts[valid].sum()
    mids   = mids[valid]
    return float(np.interp(0.0, cdf, mids)), float(np.interp(1.0, cdf, mids))


def stretched_bins(cog_url, bins, low=None, high=None):
    """Replace bin range with stretch range, keeping the same number of stops.

    low/high: optional overrides for the lower/upper bound.
    """
    try:
        p_low, p_high = stretch_range(cog_url)
        return list(np.linspace(
            low  if low  is not None else p_low,
            high if high is not None else p_high,
            len(bins),
        ))
    except (OSError, ValueError, KeyError):
        return bins


# ── Tile URL builder ────────────────────────────────────────────────────────
def build_tile_url(cog_url, bins, colors, n_bins=100, scale_factor=100):
    """Build a TiTiler tile URL with an interpolated interval colormap.

    Matches the R create_custom_colormap approach: interpolates n_bins colours
    between the bin breakpoints, encodes as TiTiler interval format:
      [[val_lo, val_hi], [r, g, b, 255]]
    A fully-transparent leading interval masks nodata and sub-range values.

    scale_factor: COGs store values as float * scale_factor (integer).
      All bin values are multiplied by scale_factor before encoding.
    """
    bin_arr    = np.array(bins, dtype=float) * scale_factor
    norm_bins  = (bin_arr - bin_arr[0]) / (bin_arr[-1] - bin_arr[0])
    lin_vals   = np.linspace(bin_arr[0], bin_arr[-1], n_bins)
    def hex_to_rgb(h):
        h = h.lstrip("#")
        return [int(h[i:i+2], 16) for i in (0, 2, 4)]

    rgb = [hex_to_rgb(c) for c in colors]

    def interp(t):
        for j in range(len(norm_bins) - 1):
            if norm_bins[j] <= t <= norm_bins[j + 1]:
                denom = norm_bins[j + 1] - norm_bins[j]
                s = (t - norm_bins[j]) / denom if denom else 0
                return [int(rgb[j][k] + s * (rgb[j+1][k] - rgb[j][k])) for k in range(3)] + [255]
        return rgb[-1] + [255]

    gradient = [interp((v - bin_arr[0]) / (bin_arr[-1] - bin_arr[0])) for v in lin_vals]
    colormap  = [
        [[-40000.0, float(lin_vals[0])], [0, 0, 0, 0]],  # transparent nodata/sub-range mask
    ] + [
        [[float(lin_vals[i]), float(lin_vals[i+1])], gradient[i]]
        for i in range(n_bins - 1)
    ]

    encoded_cog = urllib.parse.quote(cog_url, safe="")
    encoded_cm  = urllib.parse.quote(json.dumps(colormap), safe="")
    return (
        f"{TITILER_ENDPOINT}?url={encoded_cog}"
        f"&colormap={encoded_cm}"
        f"&return_mask=true"
    )

# ── Histogram-stretched bins ─────────────────────────────────────────────────
soc_bins_s  = stretched_bins(soc_cog_url,  soc_bins, high=120)
ph_bins_s   = stretched_bins(ph_cog_url,   ph_bins, low=3.5)
clay_bins_s = stretched_bins(clay_cog_url, clay_bins)
sand_bins_s = stretched_bins(sand_cog_url, sand_bins)
tn_bins_s   = stretched_bins(tn_cog_url,   tn_bins)
cec_bins_s  = stretched_bins(cec_cog_url,  cec_bins, high=100)

# ── Pre-computed tile URLs ───────────────────────────────────────────────────
soc_tiles_url  = build_tile_url(soc_cog_url,  soc_bins_s,  soc_colors)
ph_tiles_url   = build_tile_url(ph_cog_url,   ph_bins_s,   ph_colors)
clay_tiles_url = build_tile_url(clay_cog_url, clay_bins_s, clay_colors)
sand_tiles_url = build_tile_url(sand_cog_url, sand_bins_s, sand_colors)
tn_tiles_url   = build_tile_url(tn_cog_url,   tn_bins_s,   tn_colors)
cec_tiles_url  = build_tile_url(cec_cog_url,  cec_bins_s,  cec_colors)

# ── Layer catalogue (consumed by soil_mapping.py) ───────────────────────────
SOIL_LAYERS = {
    "soc":  {"title": "Soil Organic Carbon", "unit": "g/kg",    "cog_url": soc_cog_url,
             "tiles_url": soc_tiles_url,  "bins": soc_bins_s,  "colors": soc_colors,
             "cap": True, "cap_low": True},
    "ph":   {"title": "pH",                  "unit": "pH",      "cog_url": ph_cog_url,
             "tiles_url": ph_tiles_url,   "bins": ph_bins_s,   "colors": ph_colors,
             "cap": True, "cap_low": True},
    "clay": {"title": "Clay",                "unit": "%",       "cog_url": clay_cog_url,
             "tiles_url": clay_tiles_url, "bins": clay_bins_s, "colors": clay_colors,
             "cap": True, "cap_low": True},
    "sand": {"title": "Sand",                "unit": "%",       "cog_url": sand_cog_url,
             "tiles_url": sand_tiles_url, "bins": sand_bins_s, "colors": sand_colors,
             "cap": True, "cap_low": True},
    "tn":   {"title": "Total Nitrogen",      "unit": "g/kg",    "cog_url": tn_cog_url,
             "tiles_url": tn_tiles_url,   "bins": tn_bins_s,   "colors": tn_colors,
             "cap": True, "cap_low": True},
    "cec":  {"title": "CEC",                 "unit": "cmol/kg", "cog_url": cec_cog_url,
             "tiles_url": cec_tiles_url,  "bins": cec_bins_s,  "colors": cec_colors,
             "cap": True, "cap_low": True},
}
