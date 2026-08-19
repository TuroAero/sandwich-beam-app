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


def ibeam_inertia(b: float, h: float, tf: float, tw: float) -> float:
    """Second moment of area [m⁴] of a standard doubly-symmetric I-beam."""
    h_web = h - 2.0 * tf
    return (b * h**3 - (b - tw) * h_web**3) / 12.0


def ibeam_ei(
    b: float, h: float, tf: float, tw: float, E: float
) -> tuple[float, float]:
    """
    Flexural rigidity for a homogeneous I-beam.

    Returns (EI  [N·m²],  I  [m⁴]).
    """
    I = ibeam_inertia(b, h, tf, tw)
    return E * I, I


def ibeam_mass(
    b: float, h: float, tf: float, tw: float, L: float, rho: float
) -> float:
    """Mass [kg] of an I-beam of length L."""
    A = 2.0 * b * tf + (h - 2.0 * tf) * tw
    return A * rho * L
