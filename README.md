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

La clasificación de señas es **geométrica por reglas** (qué dedos están
extendidos), sin modelos entrenados: rápida, local y sin datos externos.

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

## Entrena tus propias palabras

Pulsa **➕ Agregar palabra**, escribe la palabra y, tras una cuenta regresiva de
3 segundos, mantén tu seña frente a la cámara mientras SenIA graba 30 muestras.
La palabra queda guardada en `custom_words.json` (local) y se reconoce al
instante por vecino más cercano sobre los landmarks normalizados de la mano.
Las palabras personalizadas aparecen en el vocabulario con borde celeste y un
botón para eliminarlas, y tienen prioridad sobre las señas integradas.

Consejo: al grabar, mueve ligeramente la mano (ángulo y distancia) para que el
reconocimiento sea más robusto. Si una palabra se confunde, elimínala y vuelve
a grabarla.

## Vocabulario

| Seña | Palabra |
|------|---------|
| 🖐 Mano abierta | HOLA |
| 👍 Pulgar arriba | SÍ |
| 👎 Pulgar abajo | NO |
| ✌ Índice y medio | BIEN |
| ☝ Solo índice | YO |
| 🤟 Pulgar + índice + meñique | TE QUIERO |
| 🤙 Pulgar + meñique | AYUDA |
| Índice + medio + anular | GRACIAS |
| ✊ Puño cerrado | ALTO |

Además de estas señas integradas, puedes entrenar las tuyas con
**➕ Agregar palabra** (o añadir reglas geométricas en `detector.py`).
