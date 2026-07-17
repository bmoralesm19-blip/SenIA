"""SenIA — Traductor de lenguaje de señas a texto y voz (app de escritorio).

Una persona sorda hace señas frente a la cámara; SenIA las traduce a palabras,
arma la frase y puede decirla en voz alta para una persona oyente.

Ejecutar:  python app.py
"""

import math
import os
import threading
import time

import cv2
import customtkinter as ctk
import mediapipe as mp
import pyttsx3
from PIL import Image

from detector import features
from dictionary import CustomDictionary

HOLD_SECONDS = 1.2          # tiempo que hay que mantener la seña para confirmarla
CAM_SIZE = (860, 484)       # tamaño del video en la interfaz
RECORD_SAMPLES = 30         # muestras a grabar por palabra nueva
COUNTDOWN_SECONDS = 3
DICTIONARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "custom_words.json")

# Paleta celeste / negro
CELESTE = "#4dd0ff"
CELESTE_DIM = "#1a7fa8"
CELESTE_HOVER = "#7fdcff"
BG = "#0a0e12"
PANEL = "#10161d"
PANEL_2 = "#16202a"
TEXT = "#e8f6fd"
MUTED = "#7fa8bd"
DISABLED = "#2c3e4d"

CELESTE_BGR = (255, 208, 77)  # #4dd0ff en BGR para OpenCV


class SignWorker(threading.Thread):
    """Hilo que captura la cámara, detecta la mano y arma la frase."""

    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.frame = None        # último frame RGB (numpy)
        self.current = None      # seña detectada ahora mismo
        self.progress = 0.0      # 0..1 hacia la confirmación
        self.sentence = []
        self.running = True
        self._candidate = None
        self._candidate_since = 0.0
        self._committed = None   # evita repetir la palabra sin soltar la seña

        # Diccionario personalizado y grabación de palabras nuevas
        self.dictionary = CustomDictionary(DICTIONARY_PATH)
        self.mode = "translate"          # translate | countdown | record
        self.status_text = ""            # texto para la UI durante la grabación
        self.record_progress = 0.0
        self.word_just_added = None      # la UI lo consume para refrescar vocabulario
        self._record_word = None
        self._countdown_start = 0.0
        self._samples = []

    def start_recording(self, word):
        if self.mode != "translate" or not word:
            return
        self._record_word = word
        self._samples = []
        self._countdown_start = time.time()
        self.record_progress = 0.0
        self.mode = "countdown"

    def _handle_recording(self, feat):
        now = time.time()
        if self.mode == "countdown":
            remaining = COUNTDOWN_SECONDS - (now - self._countdown_start)
            if remaining > 0:
                self.status_text = f"Prepara la seña… {math.ceil(remaining)}"
            else:
                self.mode = "record"
        if self.mode == "record":
            if feat is not None:
                self._samples.append(feat)
            done = len(self._samples)
            self.record_progress = done / RECORD_SAMPLES
            self.status_text = (f"Grabando «{self._record_word}»  {done}/{RECORD_SAMPLES}"
                                if feat is not None else "Muestra tus manos a la cámara…")
            if done >= RECORD_SAMPLES:
                self.dictionary.add(self._record_word, self._samples)
                self.word_just_added = self._record_word
                self.mode = "translate"
                self.status_text = ""
                self._candidate = None
                self._committed = self._record_word  # no agregarla de inmediato a la frase

    def _update_gesture(self, word):
        now = time.time()
        if word != self._candidate:
            self._candidate = word
            self._candidate_since = now
            if word != self._committed:
                self._committed = None

        if self._candidate is None:
            self.progress = 0.0
        elif self._candidate == self._committed:
            self.progress = 1.0
        else:
            self.progress = min(1.0, (now - self._candidate_since) / HOLD_SECONDS)
            if self.progress >= 1.0:
                with self.lock:
                    self.sentence.append(self._candidate)
                self._committed = self._candidate
        self.current = self._candidate

    def run(self):
        mp_hands = mp.solutions.hands
        mp_face = mp.solutions.face_detection
        mp_draw = mp.solutions.drawing_utils
        lm_style = mp_draw.DrawingSpec(color=CELESTE_BGR, thickness=2, circle_radius=3)
        conn_style = mp_draw.DrawingSpec(color=(200, 160, 60), thickness=2)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
        hands = mp_hands.Hands(
            max_num_hands=2,
            model_complexity=0,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        face_detector = mp_face.FaceDetection(model_selection=0,
                                              min_detection_confidence=0.5)
        last_face, last_face_time = None, 0.0
        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.1)
                continue
            frame = cv2.flip(frame, 1)  # espejo, más natural para el usuario

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            # Rostro como referencia espacial (frente, mentón, etc.)
            now = time.time()
            face_result = face_detector.process(rgb)
            if face_result.detections:
                det = face_result.detections[0]
                box = det.location_data.relative_bounding_box
                nose = mp_face.get_key_point(det, mp_face.FaceKeyPoint.NOSE_TIP)
                last_face = (nose.x, nose.y, box.height or 1e-6)
                last_face_time = now
                h, w = frame.shape[:2]
                cv2.rectangle(frame,
                              (int(box.xmin * w), int(box.ymin * h)),
                              (int((box.xmin + box.width) * w),
                               int((box.ymin + box.height) * h)),
                              (120, 96, 40), 2)
            # Suavizado: reutiliza el último rostro visto hasta por 1 s
            face = last_face if now - last_face_time < 1.0 else None

            word, feat = None, None
            if result.multi_hand_landmarks:
                for hand in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(
                        frame, hand, mp_hands.HAND_CONNECTIONS, lm_style, conn_style)
                # Orden estable izquierda→derecha para que la seña bimanual
                # produzca siempre el mismo vector de features
                detected = sorted((h.landmark for h in result.multi_hand_landmarks),
                                  key=lambda lm: lm[0].x)
                feat = features(detected, face)
                word = self.dictionary.classify(feat)

            if self.mode == "translate":
                self._update_gesture(word)
            else:
                self._handle_recording(feat)
            self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cap.release()


def speak(text):
    """Dice la frase en voz alta (SAPI de Windows, offline)."""
    def _run():
        engine = pyttsx3.init()
        for voice in engine.getProperty("voices"):
            if "spanish" in voice.name.lower() or "sabina" in voice.name.lower() \
                    or "helena" in voice.name.lower():
                engine.setProperty("voice", voice.id)
                break
        engine.setProperty("rate", 155)
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=_run, daemon=True).start()


class SenIAApp(ctk.CTk):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.title("SenIA — Traductor de Lenguaje de Señas")
        self.geometry("1280x760")
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_header()
        self._build_body()
        self._tick()

    # ---------- construcción de la interfaz ----------

    def _card(self, parent):
        return ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=16,
                            border_width=1, border_color="#1d2a36")

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 6))

        logo = ctk.CTkLabel(header, text="🤟", font=("Segoe UI Emoji", 26),
                            fg_color=CELESTE_DIM, corner_radius=12, width=48, height=48)
        logo.pack(side="left")

        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.pack(side="left", padx=14)
        ctk.CTkLabel(titles, text="SenIA", font=("Segoe UI", 24, "bold"),
                     text_color=CELESTE).pack(anchor="w")
        ctk.CTkLabel(titles, text="Traductor de lenguaje de señas a texto y voz en tiempo real",
                     font=("Segoe UI", 13), text_color=MUTED).pack(anchor="w")

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(6, 20))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # --- Cámara (izquierda) ---
        cam_card = self._card(body)
        cam_card.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.cam_label = ctk.CTkLabel(cam_card, text="Encendiendo cámara…",
                                      font=("Segoe UI", 16), text_color=MUTED)
        self.cam_label.pack(expand=True, padx=12, pady=12)

        # --- Panel derecho ---
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        # Seña detectada
        sign_card = self._card(right)
        sign_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(sign_card, text="SEÑA DETECTADA", font=("Segoe UI", 11, "bold"),
                     text_color=MUTED).pack(anchor="w", padx=18, pady=(14, 0))
        self.word_label = ctk.CTkLabel(sign_card, text="Muestra una seña…",
                                       font=("Segoe UI", 34, "bold"), text_color=DISABLED)
        self.word_label.pack(pady=(4, 2))
        self.progress_bar = ctk.CTkProgressBar(sign_card, progress_color=CELESTE,
                                               fg_color=PANEL_2, height=8)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=18, pady=(2, 4))
        ctk.CTkLabel(sign_card, text="Mantén la seña ~1 segundo para agregarla a la frase",
                     font=("Segoe UI", 11), text_color=MUTED).pack(pady=(0, 12))

        # Frase
        phrase_card = self._card(right)
        phrase_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(phrase_card, text="FRASE", font=("Segoe UI", 11, "bold"),
                     text_color=MUTED).pack(anchor="w", padx=18, pady=(14, 4))
        self.sentence_label = ctk.CTkLabel(
            phrase_card, text="Aquí aparecerá la frase…", font=("Segoe UI", 20, "bold"),
            text_color=DISABLED, fg_color=PANEL_2, corner_radius=12,
            wraplength=400, justify="left", anchor="w", padx=14, pady=12)
        self.sentence_label.pack(fill="x", padx=18)

        buttons = ctk.CTkFrame(phrase_card, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=(10, 16))
        ctk.CTkButton(buttons, text="🔊  Hablar", command=self._speak,
                      fg_color=CELESTE, hover_color=CELESTE_HOVER, text_color="#05222e",
                      font=("Segoe UI", 13, "bold"), height=38,
                      corner_radius=10).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(buttons, text="⌫  Borrar palabra", command=self._backspace,
                      fg_color="transparent", hover_color=PANEL_2, text_color=CELESTE,
                      border_width=1, border_color=CELESTE_DIM,
                      font=("Segoe UI", 13, "bold"), height=38,
                      corner_radius=10).pack(side="left", expand=True, fill="x", padx=6)
        ctk.CTkButton(buttons, text="🗑  Limpiar", command=self._clear,
                      fg_color="transparent", hover_color=PANEL_2, text_color=CELESTE,
                      border_width=1, border_color=CELESTE_DIM,
                      font=("Segoe UI", 13, "bold"), height=38,
                      corner_radius=10).pack(side="left", expand=True, fill="x", padx=(6, 0))

        # Vocabulario
        vocab_card = self._card(right)
        vocab_card.pack(fill="both", expand=True)
        vocab_header = ctk.CTkFrame(vocab_card, fg_color="transparent")
        vocab_header.pack(fill="x", padx=18, pady=(14, 6))
        ctk.CTkLabel(vocab_header, text="VOCABULARIO", font=("Segoe UI", 11, "bold"),
                     text_color=MUTED).pack(side="left")
        ctk.CTkButton(vocab_header, text="➕  Agregar palabra", command=self._add_word,
                      fg_color="transparent", hover_color=PANEL_2, text_color=CELESTE,
                      border_width=1, border_color=CELESTE_DIM,
                      font=("Segoe UI", 12, "bold"), height=30, width=150,
                      corner_radius=8).pack(side="right")
        self.vocab_grid = ctk.CTkScrollableFrame(vocab_card, fg_color="transparent")
        self.vocab_grid.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        for col in range(3):
            self.vocab_grid.grid_columnconfigure(col, weight=1)
        self._rebuild_vocab()

    def _rebuild_vocab(self):
        for child in self.vocab_grid.winfo_children():
            child.destroy()

        words = sorted(self.worker.dictionary.words)
        if not words:
            ctk.CTkLabel(
                self.vocab_grid,
                text="Tu diccionario está vacío.\n"
                     "Pulsa «➕ Agregar palabra», escribe la palabra y muestra\n"
                     "tu seña a la cámara para entrenarla.",
                font=("Segoe UI", 13), text_color=MUTED, justify="center",
            ).grid(row=0, column=0, columnspan=3, pady=30)
            return

        for idx, word in enumerate(words):
            item = ctk.CTkFrame(self.vocab_grid, fg_color=PANEL_2, corner_radius=10,
                                border_width=1, border_color=CELESTE_DIM)
            item.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=4, pady=4)
            ctk.CTkLabel(item, text=word, font=("Segoe UI", 13, "bold"),
                         text_color=CELESTE).pack(pady=(10, 2))
            ctk.CTkButton(item, text="✕ eliminar", height=18, width=70,
                          fg_color="transparent", hover_color="#241a1a",
                          text_color="#c96a6a", font=("Segoe UI", 10),
                          command=lambda w=word: self._delete_word(w)).pack(pady=(0, 8))

    # ---------- acciones ----------

    def _add_word(self):
        if self.worker.mode != "translate":
            return
        dialog = ctk.CTkInputDialog(
            title="Agregar palabra",
            text="Escribe la palabra nueva.\nLuego tendrás 3 segundos para\n"
                 "preparar la seña (con una o dos manos)\n"
                 "y mantenerla frente a la cámara.")
        word = (dialog.get_input() or "").strip().upper()
        if word:
            self.worker.start_recording(word)

    def _delete_word(self, word):
        self.worker.dictionary.remove(word)
        self._rebuild_vocab()

    def _speak(self):
        with self.worker.lock:
            text = " ".join(self.worker.sentence)
        if text:
            speak(text.lower())

    def _backspace(self):
        with self.worker.lock:
            if self.worker.sentence:
                self.worker.sentence.pop()

    def _clear(self):
        with self.worker.lock:
            self.worker.sentence.clear()

    # ---------- refresco de la interfaz ----------

    def _tick(self):
        frame = self.worker.frame
        if frame is not None:
            image = ctk.CTkImage(light_image=Image.fromarray(frame), size=CAM_SIZE)
            self.cam_label.configure(image=image, text="")
            self.cam_label._image = image  # evita que el GC libere la imagen

        if self.worker.mode != "translate":
            # Grabando una palabra nueva: la tarjeta muestra el estado
            self.word_label.configure(text=self.worker.status_text, text_color=CELESTE,
                                      font=("Segoe UI", 20, "bold"))
            self.progress_bar.set(self.worker.record_progress)
        elif self.worker.current:
            self.word_label.configure(text=self.worker.current, text_color=CELESTE,
                                      font=("Segoe UI", 34, "bold"))
            self.progress_bar.set(self.worker.progress)
        else:
            self.word_label.configure(text="Muestra una seña…", text_color=DISABLED,
                                      font=("Segoe UI", 34, "bold"))
            self.progress_bar.set(self.worker.progress)

        if self.worker.word_just_added:
            self.worker.word_just_added = None
            self._rebuild_vocab()

        with self.worker.lock:
            text = " ".join(self.worker.sentence)
        if text:
            self.sentence_label.configure(text=text, text_color=TEXT)
        else:
            self.sentence_label.configure(text="Aquí aparecerá la frase…",
                                          text_color=DISABLED)

        self.after(33, self._tick)

    def _on_close(self):
        self.worker.running = False
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    worker = SignWorker()
    worker.start()
    SenIAApp(worker).mainloop()
