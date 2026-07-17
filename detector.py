"""Extracción de features a partir de los landmarks de MediaPipe Hands.

Soporta señas de una o dos manos. El vector resultante es invariante a la
posición y al tamaño, pero conserva la posición relativa entre las manos,
lo que permite reconocer letras/señas bimanuales.
"""

import math

WRIST = 0

# Peso de la posición respecto al rostro frente a la forma de la mano
FACE_WEIGHT = 0.5
# Peso del tamaño aparente de la mano (profundidad: acercar/alejar a la cámara)
DEPTH_WEIGHT_FACE = 0.5   # relativo al alto del rostro
DEPTH_WEIGHT_RAW = 2.0    # absoluto (fracción de imagen) cuando no hay rostro


def features(hands, face=None):
    """Vector de features para 1 o 2 manos.

    `hands` es una lista de listas de landmarks, ordenada de izquierda a
    derecha por la muñeca. Todos los puntos se expresan relativos al punto
    medio de las muñecas y se normalizan por la distancia máxima, de modo
    que la separación y orientación entre ambas manos forma parte de la seña.

    Por cada mano se añade además:
    - su posición respecto a la nariz (si `face` = (x, y, alto) está presente),
      para distinguir señas hechas en la frente, el mentón, etc.
    - su tamaño aparente en la imagen, que crece al acercar la mano a la
      cámara: la profundidad forma parte de la seña.
    """
    wrists = [(lm[WRIST].x, lm[WRIST].y) for lm in hands]
    ax = sum(x for x, _ in wrists) / len(wrists)
    ay = sum(y for _, y in wrists) / len(wrists)

    rel = [(p.x - ax, p.y - ay) for lm in hands for p in lm]
    scale = max(math.hypot(x, y) for x, y in rel) or 1.0
    feat = [c / scale for xy in rel for c in xy]

    for lm in hands:
        wx, wy = lm[WRIST].x, lm[WRIST].y
        hand_size = max(math.hypot(p.x - wx, p.y - wy) for p in lm) or 1e-6
        if face is not None:
            nose_x, nose_y, face_size = face
            feat.append((wx - nose_x) / face_size * FACE_WEIGHT)
            feat.append((wy - nose_y) / face_size * FACE_WEIGHT)
            feat.append(hand_size / face_size * DEPTH_WEIGHT_FACE)
        else:
            feat.append(hand_size * DEPTH_WEIGHT_RAW)
    return feat
