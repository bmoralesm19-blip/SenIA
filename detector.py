"""Clasificador geométrico de señas sobre los 21 landmarks de MediaPipe Hands.

No requiere entrenamiento: decide qué dedos están extendidos midiendo
distancias entre landmarks y aplica reglas para mapear posturas a palabras.
"""

import math

# Índices de landmarks de MediaPipe Hands
WRIST = 0
THUMB_TIP, THUMB_IP, THUMB_MCP = 4, 3, 2
FINGER_TIPS = [8, 12, 16, 20]   # índice, medio, anular, meñique
FINGER_PIPS = [6, 10, 14, 18]
PINKY_MCP = 17


def _dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def fingers_extended(lm):
    """Devuelve [pulgar, índice, medio, anular, meñique] como booleanos."""
    wrist = lm[WRIST]

    # Pulgar: su punta queda lejos de la base del meñique cuando está extendido
    thumb = _dist(lm[THUMB_TIP], lm[PINKY_MCP]) > _dist(lm[THUMB_IP], lm[PINKY_MCP]) * 1.08

    others = [
        _dist(lm[tip], wrist) > _dist(lm[pip], wrist) * 1.15
        for tip, pip in zip(FINGER_TIPS, FINGER_PIPS)
    ]
    return [thumb] + others


def features(lm):
    """Vector de 42 features: landmarks (x, y) relativos a la muñeca,
    normalizados por el tamaño de la mano (invariante a posición y escala)."""
    wx, wy = lm[WRIST].x, lm[WRIST].y
    rel = [(p.x - wx, p.y - wy) for p in lm]
    scale = max(math.hypot(x, y) for x, y in rel) or 1.0
    return [c / scale for xy in rel for c in xy]


def classify(lm):
    """Mapea la postura de la mano a una palabra. Devuelve None si no reconoce."""
    t, i, m, a, p = fingers_extended(lm)

    if t and i and m and a and p:
        return "HOLA"
    if not any([t, i, m, a, p]):
        return "ALTO"
    if t and i and p and not m and not a:
        return "TE QUIERO"
    if t and p and not i and not m and not a:
        return "AYUDA"
    if i and m and a and not t and not p:
        return "GRACIAS"
    if i and m and not t and not a and not p:
        return "BIEN"
    if i and not t and not m and not a and not p:
        return "YO"
    if t and not i and not m and not a and not p:
        # Pulgar solo: arriba = SÍ, abajo = NO (eje Y crece hacia abajo)
        if lm[THUMB_TIP].y < lm[WRIST].y - 0.05:
            return "SÍ"
        if lm[THUMB_TIP].y > lm[WRIST].y + 0.05:
            return "NO"
    return None
