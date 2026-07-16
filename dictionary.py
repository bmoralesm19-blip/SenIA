"""Diccionario personalizado de señas entrenable por el usuario.

Guarda muestras (vectores de 42 features) por palabra en un JSON local y
clasifica por vecino más cercano (distancia euclidiana con umbral).
"""

import json
import math
import os

MATCH_THRESHOLD = 0.38   # distancia máxima para aceptar una coincidencia


class CustomDictionary:
    def __init__(self, path):
        self.path = path
        self.words = {}   # palabra -> lista de muestras (listas de 42 floats)
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as fh:
                    self.words = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self.words = {}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.words, fh, ensure_ascii=False)

    def add(self, word, samples):
        self.words.setdefault(word, []).extend(samples)
        self.save()

    def remove(self, word):
        self.words.pop(word, None)
        self.save()

    def classify(self, feat):
        """Devuelve la palabra personalizada más cercana o None."""
        best_word, best_dist = None, MATCH_THRESHOLD
        for word, samples in self.words.items():
            for sample in samples:
                # Solo comparar muestras con el mismo número de manos
                if len(sample) != len(feat):
                    continue
                dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(feat, sample)))
                if dist < best_dist:
                    best_word, best_dist = word, dist
        return best_word
