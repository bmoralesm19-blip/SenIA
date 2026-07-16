# SenIA 🤟

**Traductor de lenguaje de señas a texto y voz en tiempo real.**

App de escritorio para Windows que permite a una persona oyente entender a una
persona sorda que no puede hablar ni escribir: la persona sorda hace señas
frente a la cámara, SenIA las traduce a palabras, arma la frase y puede decirla
en voz alta.

## Tecnología

- **Python 3.12**
- **MediaPipe Hands** — detección de 21 puntos de la mano por webcam.
- **OpenCV** — captura de cámara y dibujo del esqueleto de la mano.
- **CustomTkinter** — interfaz de escritorio moderna (celeste / negro).
- **pyttsx3** — voz en español, 100 % offline (SAPI de Windows).

El vocabulario lo entrenas tú mismo: cada palabra se graba con tu propia seña
y se reconoce por **vecino más cercano** sobre los landmarks normalizados de
la mano. Sin modelos preentrenados, rápido, local y sin datos externos.

## Instalación y uso

```bash
pip install -r requirements.txt
python app.py
```

## Cómo funciona

1. Haz una seña frente a la cámara y **mantenla ~1 segundo** (la barra celeste
   se llena) → la palabra se agrega a la frase.
2. La persona oyente lee la frase o pulsa **🔊 Hablar** para oírla.
3. **⌫ Borrar palabra** quita la última; **🗑 Limpiar** reinicia la frase.

## Entrena tu vocabulario

El diccionario empieza vacío: tú decides qué palabras existen y qué seña usa
cada una.

1. Pulsa **➕ Agregar palabra** y escribe la palabra.
2. Tras una cuenta regresiva de 3 segundos, mantén tu seña frente a la cámara
   mientras SenIA graba 30 muestras.
3. La palabra queda guardada en `custom_words.json` (local) y se reconoce al
   instante. Cada palabra tiene un botón **✕ eliminar** para regrabarla.

Consejo: al grabar, mueve ligeramente la mano (ángulo y distancia) para que el
reconocimiento sea más robusto. Si dos palabras se confunden, usa posturas de
mano bien distintas o elimina y vuelve a grabar.
