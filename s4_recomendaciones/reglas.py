"""Reglas IF-THEN derivadas de guías clínicas (SOGC 467, Informes_teoricos)."""

from config import LC_CORTO_MM, LC_MODERADO_MM


def recomendacion_if_then(fila: dict) -> str:
    """
    Evalúa reglas de arriba hacia abajo (mayor prioridad primero).
    fila: dict con las 9 entradas de FEATURES_ENTRADA.
    """
    prob = float(fila["prob_prematuro"])
    urg = str(fila["nivel_urgencia"]).upper()
    pp = int(fila["parto_previo"])
    lc = float(fila["cl_sim_mm"])
    gh = int(fila["hipertension_gestacional"])
    inf = int(fila["infeccion_activa"])
    mult = int(fila["embarazo_multiple"])
    cronicas = int(fila["num_condiciones_cronicas"])

    if urg == "ROJO" or prob >= 0.60:
        return "derivacion_alto_riesgo"

    if inf == 1:
        return "tratar_infeccion"

    if pp == 1 and lc <= LC_CORTO_MM:
        return "progesterona_vaginal"

    if lc <= LC_CORTO_MM or (lc <= LC_MODERADO_MM and prob >= 0.30):
        return "seguimiento_estrecho_lc"

    if gh == 1 or mult == 1 or urg == "NARANJA" or cronicas >= 3:
        return "vigilancia_hta_multiple"

    if urg == "AMARILLO" or prob >= 0.25:
        return "seguimiento_estrecho_lc"

    return "control_prenatal_rutinario"
