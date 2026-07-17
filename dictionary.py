"""Diccionario personalizado de señas dinámicas entrenable por el usuario.

Cada palabra se guarda como una o más "tomas": secuencias de 12 keyframes de
features (forma de la mano, posición respecto al rostro y profundidad). El
reconocimiento compara el buffer en vivo contra las tomas con varias ventanas
de tiempo y remuestreo, lo que da tolerancia a la velocidad y a la
imprecisión natural del movimiento humano.
"""

import json
import os

import numpy as np

MATCH_THRESHOLD = 0.45   # distancia media máxima para aceptar una coincidencia
KEYFRAMES = 12           # frames a los que se remuestrea cada secuencia
MIN_FRAMES = 5           # mínimo de frames útiles para formar una secuencia
WINDOWS = (1.0, 1.6, 2.2, 2.8)   # ventanas de tiempo (s) probadas al reconocer


def _resample(frames, k=KEYFRAMES):
    """Remuestrea una lista de vectores a k keyframes (normaliza la velocidad)."""
    idx = np.linspace(0, len(frames) - 1, k).round().astype(int)
    return np.asarray([frames[i] for i in idx], dtype=np.float32)


def _majority_dim(frames):
    """Filtra los frames a la dimensión mayoritaria (nº de manos / rostro)."""
    dims = [len(f) for f in frames]
    dim = max(set(dims), key=dims.count)
    return [f for f in frames if len(f) == dim]


class CustomDictionary:
    def __init__(self, path):
        self.path = path
        self.words = {}   # palabra -> lista de tomas (arrays KEYFRAMES x D)
        self.load()

    def load(self):
        self.words = {}
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return
        for word, samples in raw.items():
            takes = []
            for sample in samples:
                arr = np.asarray(sample, dtype=np.float32)
                # Se descartan muestras del formato antiguo (vectores planos)
                if arr.ndim == 2 and arr.shape[0] == KEYFRAMES:
                    takes.append(arr)
            if takes:
                self.words[word] = takes

    def save(self):
        data = {word: [take.tolist() for take in takes]
                for word, takes in self.words.items()}
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)

    def add(self, word, frames):
        """Guarda una toma nueva a partir de los frames grabados. True si sirvió."""
        frames = _majority_dim(frames)
        if len(frames) < MIN_FRAMES:
            return False
        self.words.setdefault(word, []).append(_resample(frames))
        self.save()
        return True

    def remove(self, word):
        self.words.pop(word, None)
        self.save()

    def takes(self, word):
        return len(self.words.get(word, []))

    def classify(self, buffer, now):
        """Devuelve la palabra más cercana al movimiento reciente o None.

        `buffer` es una lista de (timestamp, feature_vector) de los últimos
        segundos. Se prueban varias ventanas de tiempo para que no importe
        cuánto dure el gesto.
        """
        if not self.words:
            return None
        best_word, best_dist = None, MATCH_THRESHOLD
        for window in WINDOWS:
            frames = [f for t, f in buffer if now - t <= window]
            if len(frames) < MIN_FRAMES:
                continue
            frames = _majority_dim(frames)
            if len(frames) < MIN_FRAMES:
                continue
            seq = _resample(frames)
            dim = seq.shape[1]
            for word, takes in self.words.items():
                for take in takes:
                    if take.shape[1] != dim:
                        continue
                    dist = float(np.mean(np.linalg.norm(seq - take, axis=1)))
                    if dist < best_dist:
                        best_word, best_dist = word, dist
        return best_word
