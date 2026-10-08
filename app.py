"""Panelboard enclosure recommendation: the 3-size and 4-size options on the field data.

Run with:  streamlit run app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data" / "panels.csv"

# Size C/D is the largest Siemens P5 box in the submittals (90" x 38" x 14.5"), so every panel fits a standard size.
THREE = {"A": (50, 20, 5.75), "B": (74, 20, 5.75), "C": (90, 38, 14.5)}
FOUR = {"A": (50, 20, 5.75), "B": (74, 20, 5.75), "C": (80, 24, 7.75), "D": (90, 38, 14.5)}
COLORS_3 = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
COLORS_4 = {"A": "#2a78d6", "B": "#eb6834", "C": "#eda100", "D": "#1baf7a"}
LAYOUT = dict(margin=dict(l=10, r=10, t=10, b=10), font=dict(size=14), plot_bgcolor="rgba(0,0,0,0)",
              paper_bgcolor="rgba(0,0,0,0)", hoverlabel=dict(font_size=13), showlegend=False)
GRID = dict(gridcolor="rgba(128,128,128,0.18)", zeroline=False)


def fmt(v):
    return f"{v:g}"


def hex_rgba(h, a):
    h = h.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


@st.cache_data
def load():
    """One row per panelboard (anonymized). need_* is the box its Siemens interior needs; submitted_* is as submitted."""
    return pd.read_csv(DATA).rename(columns={
        "need_H": "H", "need_W": "W", "need_D": "D",
        "submitted_H": "sub_H", "submitted_W": "sub_W", "submitted_D": "sub_D"})


@st.cache_data
def assign(dims):
    """Put each panel in the smallest (by volume) standard box that holds its Siemens box."""
    x = load().copy()
    sizes = pd.DataFrame(list(dims.values()), columns=["H", "W", "D"], index=list(dims))
    x["size"] = "Custom"
    for name in (sizes["H"] * sizes["W"] * sizes["D"]).sort_values().index[::-1]:
        s = sizes.loc[name]
        x.loc[(x["H"] <= s.H) & (x["W"] <= s.W) & (x["D"] <= s.D), "size"] = name
    for dim in ("H", "W", "D"):
        x[f"std_{dim}"] = x["size"].map(sizes[dim])
    w = x["enclosures"]
    stats = {
        "n": int(w.sum()),
        "counts": x.groupby("size")["enclosures"].sum().to_dict(),
        "wider": w[x["std_W"] > x["sub_W"]].sum() / w.sum(),
        "extra": float(((x["std_H"] * x["std_W"] - x["sub_H"] * x["sub_W"]) / 144 * w).sum() / w.sum()),
    }
    return sizes, x, stats


def footprint(sizes, x, colors):
    """Every submitted panel by width x height, with the standard boxes drawn as outlines."""
    fig = go.Figure()
    for name, s in sizes.iloc[::-1].iterrows():
        c = colors[name]
        fig.add_shape(type="rect", x0=0, y0=0, x1=s.W, y1=s.H, layer="below",
                      line=dict(color=c, width=3, dash="dot"), fillcolor=hex_rgba(c, 0.07))
        label = f"<b>Size {name}</b>  {fmt(s.H)}\" × {fmt(s.W)}\" × {fmt(s.D)}\""
        if s.W >= sizes["W"].max():
            # Left end of the top edge, clear of the P5 star at the top-right corner.
            x_lbl = sizes.loc[sizes["W"] < s.W, "W"].max() + 0.6
            fig.add_annotation(x=x_lbl, y=s.H + 1, text=label, showarrow=False, xanchor="left", yanchor="bottom",
                               font=dict(color=c, size=14))
        else:
            fig.add_annotation(x=s.W + 0.6, y=s.H - 1, text=label, showarrow=False, xanchor="left", yanchor="top",
                               font=dict(color=c, size=14), bgcolor="rgba(14,17,23,0.75)")
    fp = x.groupby(["sub_W", "sub_H", "size"], as_index=False).agg(
        n=("enclosures", "sum"), mfrs=("mfr", lambda v: ", ".join(sorted(set(v)))))
    for name in sizes.index:
        g = fp[fp["size"] == name]
        fig.add_trace(go.Scatter(
            x=g["sub_W"], y=g["sub_H"], mode="markers",
            marker=dict(size=np.sqrt(g["n"]) * 3 + 6, color=colors[name], opacity=0.85, line=dict(color="white", width=1)),
            customdata=np.stack([g["n"], g["mfrs"]], axis=-1),
            hovertemplate="<b>%{y}\" tall × %{x}\" wide</b><br>%{customdata[0]} panels (%{customdata[1]})"
                          f"<br>Goes in Size {name}<extra></extra>"))
    # The largest Siemens P5 in the data sets the power box.
    p5 = x[(x["mfr"] == "Siemens") & (x["siemens_family"] == "P4/P5")]
    top = p5.sort_values(["sub_H", "sub_W"], ascending=False).iloc[0]
    same = p5[(p5["sub_H"] == top.sub_H) & (p5["sub_W"] == top.sub_W)]
    amps = f"{fmt(same['amps'].min())}–{fmt(same['amps'].max())}A"
    fig.add_trace(go.Scatter(
        x=[top.sub_W], y=[top.sub_H], mode="markers", hoverinfo="skip",
        marker=dict(symbol="star", size=26, color="#ffd400", line=dict(color="black", width=1.5))))
    fig.add_annotation(
        x=top.sub_W, y=top.sub_H, ax=0, ay=-62, showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor="#ffd400",
        text=f"<b>Largest Siemens P5 submitted</b><br>{fmt(top.sub_H)}\" × {fmt(top.sub_W)}\" "
             f"({len(same)} panels, {amps})", font=dict(size=14, color="#ffd400"),
        bgcolor="rgba(14,17,23,0.85)", bordercolor="#ffd400", borderpad=4, align="left")
    fig.update_layout(**LAYOUT, height=620, xaxis_title="Width as submitted (in)", yaxis_title="Height as submitted (in)")
    fig.update_xaxes(range=[0, 48], dtick=4, **GRID)
    fig.update_yaxes(range=[0, 112], dtick=10, **GRID)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def depth_view(sizes, x, colors):
    """Side view: each size drawn to scale as depth x height, with how many panels need its depth."""
    fig = go.Figure()
    gap, x0 = 6, 0
    for name, s in sizes.iterrows():
        c = colors[name]
        fig.add_shape(type="rect", x0=x0, y0=0, x1=x0 + s.D, y1=s.H, line=dict(color=c, width=3),
                      fillcolor=hex_rgba(c, 0.25))
        fig.add_annotation(x=x0 + s.D / 2, y=s.H + 2, yanchor="bottom", showarrow=False,
                           text=f"<b>{name}</b><br><b>{fmt(s.D)}\"</b>", font=dict(size=15, color=c))
        x0 += s.D + gap
    fig.add_shape(type="line", x0=-2, x1=x0 - gap + 2, y0=0, y1=0, line=dict(color="#8a8984", width=2))
    fig.update_layout(**LAYOUT, height=620)
    fig.update_xaxes(visible=False, range=[-3, x0 - gap + 3], scaleanchor="y")
    fig.update_yaxes(visible=False, range=[-3, 112])
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("Side view, to scale: how deep each box sticks out from the wall.")


def chart_row(sizes, x, colors):
    c1, c2 = st.columns([5, 1], gap="medium")
    with c1:
        footprint(sizes, x, colors)
    with c2:
        depth_view(sizes, x, colors)


def deep_count(x, box):
    """Panels in the power box that need more than Siemens' standard 12.75" P5 depth."""
    g = x[(x["size"] == box) & (x["D"] > 12.75)]
    return int(g["enclosures"].sum()), sorted(g["amps"].dropna().unique())


st.set_page_config(page_title="Panelboard Enclosure Sizes", page_icon="📐", layout="wide")

s3, x3, st3 = assign(THREE)
s4, x4, st4 = assign(FOUR)
n = st3["n"]

st.title("Panelboard Enclosure Sizes")

# ---------------------------------------------------------------- 3 sizes
st.header("Recommended: 3 sizes")
chart_row(s3, x3, COLORS_3)
c3 = st3["counts"]
st.markdown(
    f"Each dot is a panelboard from our 30 submittals ({n:,} total, all manufacturers), placed at the width and height "
    f"it was submitted at. Its color is the standard box it goes in. **Sizes A and B** are Siemens' own 20\"-wide P1/P2 "
    f"boxes (50\" and 74\"), and **Size C** is the largest Siemens P5 box in the data (★). So every Siemens interior "
    f"fits one of the three: A holds {c3['A']:,} panels, B holds {c3['B']:,}, C holds {c3['C']:,}. Dots above or right "
    f"of an outline are other brands' oversized boxes; the Siemens interior for that rating fits the standard size.")
n_deep, deep_amps = deep_count(x3, "C")
st.info(
    f"**Depth.** A and B are **5.75\"** deep, Siemens' standard for every P1/P2 interior. The power box is **14.5\"** "
    f"deep so every panel fits, but only **{n_deep} panels** (all {', '.join(f'{fmt(a)}A' for a in deep_amps)}) need more "
    f"than Siemens' standard P5 depth of **12.75\"**. Our main product is switchboards, so we may build those biggest boards as "
    f"switchboards instead. If we do, the power box can drop to **12.75\"**. That's the shallowest it can "
    f"go and still take a Siemens P5 interior.")

# ---------------------------------------------------------------- 4 sizes
st.divider()
st.header("Alternative: add a 4th size for Siemens P3")
chart_row(s4, x4, COLORS_4)
c4 = st4["counts"]
st.markdown(
    f"This adds Siemens' P3 box (**80\" × 24\" × 7.75\"**) as its own size, so the {c4['C']:,} P3 distribution panels "
    f"no longer go into the 38\"-wide power box. Average extra wall space per panel drops from "
    f"**{st3['extra']:.1f} to {st4['extra']:.1f} ft²**, and panels wider than the superintendent planned for drop from "
    f"**{st3['wider']:.0%} to {st4['wider']:.0%}**. Sizes A and B, which hold {(c4['A'] + c4['B']) / n:.0%} of all panels, "
    f"don't change. The P3 box is 7.75\" deep, Siemens' standard P3 depth. The power box (D) is still built to the "
    f"largest Siemens P5 (★), with the same 14.5\" vs. 12.75\" depth choice. The trade-off is one more box to "
    f"stock, draw and build, for about {c4['C'] / n:.0%} of panels.")
