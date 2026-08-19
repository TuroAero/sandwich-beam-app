"""
app.py — Streamlit UI for the Sandwich Beam vs. I-Beam educational app.

Run with:  streamlit run app.py
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import streamlit as st

from calculations import ibeam_ei, ibeam_mass, sandwich_ei, sandwich_mass

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sandwich vs I-Beam",
    page_icon="🏗️",
    layout="wide",
)

# ── Material preset libraries ─────────────────────────────────────────────────
FACE_MATS: dict[str, dict] = {
    "Aviation Aluminum (2024-T3)":      {"E": 73.1,  "rho": 2780},
    "Carbon Fiber Composite (CFRP UD)": {"E": 135.0, "rho": 1550},
    "Structural Steel (A36)":           {"E": 200.0, "rho": 7850},
}
CORE_MATS: dict[str, dict] = {
    "Structural Foam (ROHACELL 110 WF)": {"E": 0.18, "rho": 110},
    "Nomex Honeycomb Core":              {"E": 1.0,  "rho": 48},
    "Balsa Wood Core":                   {"E": 4.0,  "rho": 150},
}

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔧 Configuration")

    L_mm = st.slider("Beam Length (mm)", 100, 5000, 1000, step=50)
    L = L_mm / 1000.0
    b_mm = st.slider("Shared width  b  (mm)", 10, 500, 100, step=5, key="b_shared")

    st.divider()

    # ── Sandwich beam ────────────────────────────────────────────────────────────────────────────────
    with st.expander("🥪 Sandwich Beam", expanded=True):
        tf_mm  = st.slider("Facesheet thickness  tᶠ  (mm)", 1, 30, 3, step=1, key="s_tf")
        hc_mm  = st.slider("Core thickness  hc  (mm)", 5, 200, 50, step=5, key="s_hc")

        st.markdown("**Facesheet material**")
        face_sel = st.selectbox(
            "Facesheet preset", list(FACE_MATS), index=0, key="face_sel"
        )
        fp = FACE_MATS[face_sel]
        E_face_GPa = st.number_input(
            "E_face  (GPa)", min_value=0.1, max_value=300.0,
            value=float(fp["E"]), step=0.1, format="%.1f",
            key=f"Ef_{face_sel}",
        )
        rho_face = st.number_input(
            "ρ_face  (kg/m³)", min_value=100, max_value=9000,
            value=fp["rho"], step=10,
            key=f"rf_{face_sel}",
        )

        st.markdown("**Core material**")
        core_sel = st.selectbox(
            "Core preset", list(CORE_MATS), index=0, key="core_sel"
        )
        cp = CORE_MATS[core_sel]
        E_core_GPa = st.number_input(
            "E_core  (GPa)", min_value=0.01, max_value=20.0,
            value=float(cp["E"]), step=0.01, format="%.2f",
            key=f"Ec_{core_sel}",
        )
        rho_core = st.number_input(
            "ρ_core  (kg/m³)", min_value=10, max_value=1000,
            value=cp["rho"], step=5,
            key=f"rc_{core_sel}",
        )

    st.divider()

    # ── I-Beam ────────────────────────────────────────────────────────────────
    with st.expander("⟪ I-Beam", expanded=True):
        b_bot_mm = st.slider(
            "Bottom flange width  b_bot  (mm)", 10, b_mm, b_mm, step=5,
            key=f"i_b_bot_{b_mm}",
        )
        h_i_mm  = st.slider("Total height  h_I  (mm)", 20, 500, 100, step=5, key="i_h")
        tf_i_mm = st.slider("Flange thickness  tᶠ_I  (mm)", 1, 50, 8, step=1, key="i_tf")
        tw_i_mm = st.slider("Web thickness  t_w  (mm)", 1, 50, 5, step=1, key="i_tw")

        st.markdown("**I-Beam material**")
        beam_sel = st.selectbox(
            "I-Beam preset", list(FACE_MATS), index=2, key="beam_sel"
        )
        ip = FACE_MATS[beam_sel]
        E_i_GPa = st.number_input(
            "E_I-beam  (GPa)", min_value=0.1, max_value=300.0,
            value=float(ip["E"]), step=0.1, format="%.1f",
            key=f"Ei_{beam_sel}",
        )
        rho_i = st.number_input(
            "ρ_I-beam  (kg/m³)", min_value=100, max_value=9000,
            value=ip["rho"], step=10,
            key=f"ri_{beam_sel}",
        )

# ── SI unit conversions ───────────────────────────────────────────────────────
b     = b_mm     / 1000.0  # shared width for both beams
b_bot = b_bot_mm / 1000.0
tf    = tf_mm    / 1000.0
hc    = hc_mm    / 1000.0
h_i   = h_i_mm   / 1000.0
tf_i = tf_i_mm / 1000.0
tw_i = tw_i_mm / 1000.0
E_face = E_face_GPa * 1e9
E_core = E_core_GPa * 1e9
E_i_Pa = E_i_GPa   * 1e9

# ── Input validation ──────────────────────────────────────────────────────────
errors: list[str] = []
if 2 * tf_i_mm >= h_i_mm:
    errors.append(
        "I-Beam: 2·tᶠ_I ≥ h_I — reduce flange thickness or increase total height."
    )
if tw_i_mm >= b_bot_mm:
    errors.append(
        "I-Beam: t_w ≥ b_bot — reduce web thickness or increase bottom flange width."
    )

# ── Page title and mechanics background ──────────────────────────────────────
st.title("🏗️ Sandwich Beam vs. I-Beam — Stiffness Efficiency")
st.caption(
    f"Euler–Bernoulli bending theory · Beam length  L = **{L_mm} mm** · "
    "Adjust parameters in the sidebar"
)

with st.expander("ℹ️ Mechanics background", expanded=False):
    st.markdown(
        r"""
**Sandwich beam** — transformed-section method:

$$EI_{\text{sandwich}} = E_{\text{face}}\,I_{\text{face}} + E_{\text{core}}\,I_{\text{core}}$$

$$I_{\text{face}} = 2\!\left(\frac{b\,t_f^3}{12} + b\,t_f\!\left(\frac{h_c+t_f}{2}\right)^{\!2}\right),
\qquad I_{\text{core}} = \frac{b\,h_c^3}{12}$$

**I-beam** — homogeneous material, parallel-axis theorem (supports asymmetric flanges):

$$EI_{\text{I-beam}} = E \sum_i \!\left(\frac{b_i\,t_f^3}{12} + b_i t_f d_i^2\right) + E\,\frac{t_w h_{\text{web}}^3}{12}$$

where $d_i$ is the distance from each flange centroid to the neutral axis.

**Structural efficiency**:  $\eta = EI \,/\, \text{Mass}$  — higher is better.
        """
    )

# ── Block rendering on invalid geometry ───────────────────────────────────────
if errors:
    for msg in errors:
        st.error(f"⚠️  {msg}")
    st.stop()

# ── Calculations ──────────────────────────────────────────────────────────────
EI_s, I_face_val, I_core_val = sandwich_ei(b, tf, hc, E_face, E_core)
I_s    = I_face_val + I_core_val
mass_s = sandwich_mass(b, tf, hc, L, rho_face, rho_core)
eff_s  = EI_s / mass_s if mass_s > 0 else 0.0

EI_i, I_i, y_c_i = ibeam_ei(b, b_bot, h_i, tf_i, tw_i, E_i_Pa)
mass_i = ibeam_mass(b, b_bot, h_i, tf_i, tw_i, L, rho_i)
eff_i  = EI_i / mass_i if mass_i > 0 else 0.0


def _pct(a: float, b: float) -> float:
    """Percentage difference of a relative to b."""
    return (a - b) / b * 100.0 if b != 0 else 0.0


# ── Metric comparison cards ───────────────────────────────────────────────────
st.subheader("📊 Performance Comparison")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("**Moment of Inertia  I  (m⁴)**")
    st.metric("🥪 Sandwich", f"{I_s:.3e}", f"{_pct(I_s, I_i):+.1f}% vs I-Beam")
    st.metric("⟪ I-Beam",   f"{I_i:.3e}")

with c2:
    st.markdown("**Flexural Rigidity  EI  (N·m²)**")
    st.metric("🥪 Sandwich", f"{EI_s:.3e}", f"{_pct(EI_s, EI_i):+.1f}% vs I-Beam")
    st.metric("⟪ I-Beam",   f"{EI_i:.3e}")

with c3:
    st.markdown("**Mass  (kg)**")
    # delta_color='inverse': green = lighter = better
    st.metric("🥪 Sandwich", f"{mass_s:.3f}", f"{_pct(mass_s, mass_i):+.1f}% vs I-Beam",
              delta_color="inverse")
    st.metric("⟪ I-Beam",   f"{mass_i:.3f}")

with c4:
    st.markdown("**Efficiency  EI/Mass  (N·m²/kg)**")
    st.metric("🥪 Sandwich", f"{eff_s:.3e}", f"{_pct(eff_s, eff_i):+.1f}% vs I-Beam")
    st.metric("⟪ I-Beam",   f"{eff_i:.3e}")

st.divider()

# ── Visualization helpers ─────────────────────────────────────────────────────

def _draw_cross_sections() -> plt.Figure:
    """Matplotlib figure with both beam cross-sections drawn to the same height scale."""
    h_s_mm   = 2 * tf_mm + hc_mm
    max_h    = max(h_s_mm, h_i_mm)
    margin_h = max_h * 0.15
    margin_w = b_mm * 0.15  # both beams share the same width

    # Shared Y limits so both beams are on the same height scale
    y_lo = -margin_h
    y_hi = max_h + margin_h

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 5.0), facecolor="#f8f8f8")

    C_FACE   = "#1565C0"
    C_FACE_E = "#0D47A1"
    C_CORE   = "#90CAF9"
    C_CORE_E = "#1976D2"
    C_FLANGE = "#BF360C"
    C_FLANGE_E = "#7F0000"
    C_WEB    = "#FFAB40"
    C_WEB_E  = "#E65100"
    C_NA     = "crimson"

    # ── Sandwich ──────────────────────────────────────────────────────────────
    hw = b_s_mm / 2
    # Bottom facesheet
    ax1.add_patch(patches.Rectangle(
        (-hw, 0), b_s_mm, tf_mm,
        fc=C_FACE, ec=C_FACE_E, lw=1.5, label="Facesheet", zorder=3,
    ))
    # Core
    ax1.add_patch(patches.Rectangle(
        (-hw, tf_mm), b_s_mm, hc_mm,
        fc=C_CORE, ec=C_CORE_E, lw=1.0, hatch="////", label="Core", zorder=3,
    ))
    # Top facesheet
    ax1.add_patch(patches.Rectangle(
        (-hw, tf_mm + hc_mm), b_s_mm, tf_mm,
        fc=C_FACE, ec=C_FACE_E, lw=1.5, zorder=3,
    ))
    ax1.axhline(h_s_mm / 2, color=C_NA, ls="--", lw=1.2, alpha=0.8, label="Neutral axis")

    ax1.set_xlim(-hw - margin_w, hw + margin_w)
    ax1.set_ylim(y_lo, y_hi)
    ax1.set_aspect("equal", adjustable="box")
    ax1.set_title(
        f"Sandwich Beam  (h = {h_s_mm} mm)\n"
        f"b = {b_mm} mm · tᴿ = {tf_mm} mm · hc = {hc_mm} mm",
        fontsize=8, fontweight="bold",
    )
    ax1.set_xlabel("Width (mm)", fontsize=7)
    ax1.set_ylabel("Height (mm)", fontsize=7)
    ax1.tick_params(labelsize=6)
    ax1.legend(fontsize=6.5, loc="upper right")
    ax1.set_facecolor("#f8f8f8")

    # ── I-Beam ────────────────────────────────────────────────────────────────
    hw2      = b_i_mm / 2
    h_web_mm = h_i_mm - 2 * tf_i_mm
    # Bottom flange
    ax2.add_patch(patches.Rectangle(
        (-hw2, 0), b_i_mm, tf_i_mm,
        fc=C_FLANGE, ec=C_FLANGE_E, lw=1.5, label="Flange", zorder=3,
    ))
    # Web
    ax2.add_patch(patches.Rectangle(
        (-tw_i_mm / 2, tf_i_mm), tw_i_mm, h_web_mm,
        fc=C_WEB, ec=C_WEB_E, lw=1.0, label="Web", zorder=3,
    ))
    # Top flange
    ax2.add_patch(patches.Rectangle(
        (-hw2, h_i_mm - tf_i_mm), b_i_mm, tf_i_mm,
        fc=C_FLANGE, ec=C_FLANGE_E, lw=1.5, zorder=3,
    ))
    ax2.axhline(h_i_mm / 2, color=C_NA, ls="--", lw=1.2, alpha=0.8, label="Neutral axis")

    ax2.set_xlim(-hw2 - margin_w, hw2 + margin_w)
    ax2.set_ylim(y_lo, y_hi)
    ax2.set_aspect("equal", adjustable="box")
    ax2.set_title(
        f"I-Beam  (h = {h_i_mm} mm)\n"
        f"b = {b_i_mm} mm · tᶠ = {tf_i_mm} mm · t_w = {tw_i_mm} mm",
        fontsize=8, fontweight="bold",
    )
    ax2.set_xlabel("Width (mm)", fontsize=7)
    ax2.tick_params(labelsize=6)
    ax2.legend(fontsize=6.5, loc="upper right")
    ax2.set_facecolor("#f8f8f8")

    fig.tight_layout(pad=1.5)
    return fig


def _draw_bar_chart() -> plt.Figure:
    """2×2 log-scale bar chart comparing the four structural metrics."""
    metric_data = [
        ("I  (m⁴)",             I_s,    I_i),
        ("EI  (N·m²)",          EI_s,   EI_i),
        ("Mass  (kg)",          mass_s, mass_i),
        ("EI/Mass  (N·m²/kg)",  eff_s,  eff_i),
    ]
    LABELS = ["Sandwich", "I-Beam"]
    COLORS = ["#1565C0", "#BF360C"]

    fig, axes = plt.subplots(2, 2, figsize=(6, 5.0), facecolor="#f8f8f8",
                             constrained_layout=True)
    for ax, (title, v_s, v_i) in zip(axes.flat, metric_data):
        # Guard against log(0)
        vals = [max(v_s, 1e-30), max(v_i, 1e-30)]
        bars = ax.bar(LABELS, vals, color=COLORS, edgecolor="white", lw=0.5, width=0.55)
        ax.set_yscale("log")
        ax.set_title(title, fontsize=8, fontweight="bold", pad=4)
        ax.tick_params(labelsize=6.5)
        ax.set_facecolor("#f8f8f8")
        for bar, val in zip(bars, [v_s, v_i]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.6,
                f"{val:.2e}",
                ha="center", va="bottom", fontsize=5.5, color="#222",
            )

    fig.suptitle("Metric comparison  (log scale)", fontsize=9, fontweight="bold")
    return fig


# ── Render visualizations ─────────────────────────────────────────────────────
vis_col, bar_col = st.columns([3, 2])

with vis_col:
    st.subheader("Cross-Section Geometry")
    fig_cs = _draw_cross_sections()
    st.pyplot(fig_cs)
    plt.close(fig_cs)

with bar_col:
    st.subheader("Metric Comparison")
    fig_bc = _draw_bar_chart()
    st.pyplot(fig_bc)
    plt.close(fig_bc)
