"""
calculations.py — Pure structural mechanics functions.

All inputs/outputs use SI base units:
  lengths  → metres (m)
  moduli   → Pascals (Pa)
  density  → kg/m³
  mass     → kg
  inertia  → m⁴
  EI       → N·m²
"""


def sandwich_face_inertia(b: float, tf: float, hc: float) -> float:
    """Combined second moment of area of both facesheets about the neutral axis (m⁴)."""
    d = (hc + tf) / 2.0  # centroidal distance of each facesheet from NA
    return 2.0 * (b * tf**3 / 12.0 + b * tf * d**2)


def sandwich_core_inertia(b: float, hc: float) -> float:
    """Second moment of area of the core about the neutral axis (m⁴)."""
    return b * hc**3 / 12.0


def sandwich_ei(
    b: float, tf: float, hc: float, E_face: float, E_core: float
) -> tuple[float, float, float]:
    """
    Equivalent flexural rigidity for a sandwich beam.

    Returns (EI  [N·m²],  I_face  [m⁴],  I_core  [m⁴]).
    Uses the transformed-section method:  EI = E_face·I_face + E_core·I_core
    """
    I_face = sandwich_face_inertia(b, tf, hc)
    I_core = sandwich_core_inertia(b, hc)
    EI = E_face * I_face + E_core * I_core
    return EI, I_face, I_core


def sandwich_mass(
    b: float, tf: float, hc: float, L: float,
    rho_face: float, rho_core: float,
) -> float:
    """Mass [kg] of a sandwich beam of length L."""
    A_face = 2.0 * b * tf
    A_core = b * hc
    return (A_face * rho_face + A_core * rho_core) * L


def ibeam_inertia(
    b_top: float, b_bot: float, h: float, tf: float, tw: float
) -> tuple[float, float]:
    """Returns (I [m⁴], y_c [m]) via the parallel-axis theorem.
    y_c is the neutral-axis height measured from the bottom face.
    b_top == b_bot recovers the standard symmetric case."""
    h_web = h - 2.0 * tf
    A_top, A_web, A_bot = b_top * tf, tw * h_web, b_bot * tf
    y_top = h - tf / 2.0
    y_web = tf + h_web / 2.0
    y_bot = tf / 2.0
    y_c = (A_top * y_top + A_web * y_web + A_bot * y_bot) / (A_top + A_web + A_bot)
    I = (b_top * tf**3 / 12.0 + A_top * (y_top - y_c)**2
       + tw * h_web**3 / 12.0 + A_web * (y_web - y_c)**2
       + b_bot * tf**3 / 12.0 + A_bot * (y_bot - y_c)**2)
    return I, y_c


def ibeam_ei(
    b_top: float, b_bot: float, h: float, tf: float, tw: float, E: float
) -> tuple[float, float, float]:
    """
    Flexural rigidity for a homogeneous (possibly mono-symmetric) I-beam.

    Returns (EI  [N·m²],  I  [m⁴],  y_c  [m]).
    """
    I, y_c = ibeam_inertia(b_top, b_bot, h, tf, tw)
    return E * I, I, y_c


def ibeam_mass(
    b_top: float, b_bot: float, h: float, tf: float, tw: float, L: float, rho: float
) -> float:
    """Mass [kg] of a (possibly mono-symmetric) I-beam of length L."""
    h_web = h - 2.0 * tf
    A = (b_top + b_bot) * tf + tw * h_web
    return A * rho * L
