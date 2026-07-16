"""Extracción de features de la mano a partir de los 21 landmarks de MediaPipe.

El vector resultante es invariante a la posición y al tamaño de la mano,
lo que permite comparar señas grabadas por el usuario sin entrenamiento previo.
"""

import math

WRIST = 0


def features(lm):
    """Vector de 42 features: landmarks (x, y) relativos a la muñeca,
    normalizados por el tamaño de la mano (invariante a posición y escala)."""
    wx, wy = lm[WRIST].x, lm[WRIST].y
    rel = [(p.x - wx, p.y - wy) for p in lm]
    scale = max(math.hypot(x, y) for x, y in rel) or 1.0
    return [c / scale for xy in rel for c in xy]
