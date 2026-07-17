"""Extracción de features a partir de los landmarks de MediaPipe Hands.

Soporta señas de una o dos manos. El vector resultante es invariante a la
posición y al tamaño, pero conserva la posición relativa entre las manos,
lo que permite reconocer letras/señas bimanuales.
"""

import math

WRIST = 0

# Peso de la posición respecto al rostro frente a la forma de la mano
FACE_WEIGHT = 0.5


def features(hands, face=None):
    """Vector de features para 1 o 2 manos (42/84 valores, +2 por mano si hay rostro).

    `hands` es una lista de listas de landmarks, ordenada de izquierda a
    derecha por la muñeca. Todos los puntos se expresan relativos al punto
    medio de las muñecas y se normalizan por la distancia máxima, de modo
    que la separación y orientación entre ambas manos forma parte de la seña.

    `face` es (nariz_x, nariz_y, alto_del_rostro). Si está presente, se añade
    por cada mano el offset muñeca→nariz en unidades de rostro: así señas
    hechas en la frente y en el mentón producen vectores distintos.
    """
    wrists = [(lm[WRIST].x, lm[WRIST].y) for lm in hands]
    ax = sum(x for x, _ in wrists) / len(wrists)
    ay = sum(y for _, y in wrists) / len(wrists)

    rel = [(p.x - ax, p.y - ay) for lm in hands for p in lm]
    scale = max(math.hypot(x, y) for x, y in rel) or 1.0
    feat = [c / scale for xy in rel for c in xy]

    if face is not None:
        nose_x, nose_y, face_size = face
        for wx, wy in wrists:
            feat.append((wx - nose_x) / face_size * FACE_WEIGHT)
            feat.append((wy - nose_y) / face_size * FACE_WEIGHT)
    return feat
