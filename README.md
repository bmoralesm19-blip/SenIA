# SenIA 🤟

**Traductor de lenguaje de señas a texto y voz en tiempo real.**

App de escritorio para Windows que permite a una persona oyente entender a una
persona sorda que no puede hablar ni escribir: la persona sorda hace señas
frente a la cámara, SenIA las traduce a palabras, arma la frase y puede decirla
en voz alta.

## Tecnología

- **Python 3.12**
- **MediaPipe Hands** — detección de 21 puntos por mano (hasta 2 manos).
- **MediaPipe Face Detection** — el rostro como referencia espacial: señas
  hechas en la frente y en el mentón se distinguen entre sí.
- **OpenCV** — captura de cámara y dibujo del esqueleto de la mano.
- **CustomTkinter** — interfaz de escritorio moderna (celeste / negro).
- **pyttsx3** — voz en español, 100 % offline (SAPI de Windows).

El vocabulario lo entrenas tú mismo: cada palabra se graba como una
**secuencia de ~2.5 s** (forma de la mano, posición respecto al rostro,
profundidad y movimiento) y se reconoce comparando el movimiento reciente
contra tus tomas, con remuestreo temporal y umbral de tolerancia para que no
haga falta repetir el gesto de forma perfecta. Sin modelos preentrenados,
rápido, local y sin datos externos.

## Instalación y uso

```bash
pip install -r requirements.txt
python app.py
```

## Cómo funciona

1. Haz tu seña frente a la cámara — quieta o **con movimiento** (subir la
   mano, acercarla a la cámara, trazar un arco…). Al reconocerla, la palabra
   se agrega a la frase (con 2.5 s de gracia antes de poder repetirla).
2. La persona oyente lee la frase o pulsa **🔊 Hablar** para oírla.
3. **⌫ Borrar palabra** quita la última; **🗑 Limpiar** reinicia la frase.

## Entrena tu vocabulario

El diccionario empieza vacío: tú decides qué palabras existen y qué seña usa
cada una.

1. Pulsa **➕ Agregar palabra** y escribe la palabra.
2. Tras una cuenta regresiva de 3 segundos, SenIA graba tu seña durante
   **2.5 segundos**: haz el movimiento completo (o mantén la postura si la
   seña es estática). Puedes usar **una o dos manos**; cuentan la posición
   relativa entre manos, la **posición respecto a tu rostro** (frente vs
   mentón) y la **distancia a la cámara** (acercar/alejar la mano). Mantén el
   rostro visible al grabar y al traducir.
3. La palabra queda guardada en `custom_words.json` (local). **Grabar la misma
   palabra otra vez agrega otra toma** y hace el reconocimiento más robusto.
4. Cada palabra tiene un botón **✕ eliminar** para regrabarla desde cero.

Consejo: agrega 2-3 tomas por palabra, variando ligeramente la velocidad y el
ángulo. Si dos palabras se confunden, usa gestos más distintos entre sí.
