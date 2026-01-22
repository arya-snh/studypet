import sys
import cv2
import time
import threading
import signal
from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QCoreApplication
from PyQt6.QtGui import QMovie, QGuiApplication

from gaze_tracking import GazeTracking

gaze = GazeTracking()

def is_user_distracted(frame):
    gaze.refresh(frame)
    distracted = (
        gaze.is_left() or
        gaze.is_right() or
        gaze.pupil_left_coords() is None or
        gaze.pupil_right_coords() is None
    )
    return distracted

class PetWindow(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.movie = QMovie("pictures/cat.gif")
        if not self.movie.isValid():
            print("Warning: cat.gif not found or invalid — pet will use fallback size")

        self.setMovie(self.movie)
        self.movie.start()

        rect = self.movie.frameRect()
        if rect.isEmpty():
            self.setFixedSize(200, 200)   # fallback size
        else:
            self.setFixedSize(rect.size())

        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.right() - self.width() - 20
            y = geom.bottom() - self.height() - 60
            self.move(x, y)

        self.drag_pos = None
        self._locked_visible = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, event):
        self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.drag_pos:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.user_close()
            return
        super().keyPressEvent(event)

    def show(self):
        super().show()
        self._locked_visible = True
        self.setFocus()

    def hide(self):
        if self._locked_visible:
            print("DEBUG: hide() ignored because pet is locked (only user can close)")
            return
        super().hide()

    def user_close(self):
        self._locked_visible = False
        super().hide()

    def closeEvent(self, event):
        event.ignore()
        super().hide()


class AttentionThread(QThread):
    distracted_changed = pyqtSignal(bool)

    def __init__(self, parent=None, interval_s=2.0):
        super().__init__(parent)
        self._running = True
        self.interval_s = interval_s
        self.gaze = GazeTracking()

    def run(self):
        cap = cv2.VideoCapture(0)
        prev = None
        while self._running:
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                # small sleep to avoid busy loop; let camera warm up
                self.msleep(100)
                continue

            # analyze frame (use same logic as is_user_distracted)
            self.gaze.refresh(frame)
            distracted = (
                self.gaze.is_left() or
                self.gaze.is_right() or
                self.gaze.pupil_left_coords() is None or
                self.gaze.pupil_right_coords() is None
            )

            if prev is None or distracted != prev:
                self.distracted_changed.emit(distracted)
                prev = distracted

            # sleep interval (seconds)
            for _ in range(int(self.interval_s * 10)):
                if not self._running:
                    break
                self.msleep(100)
        cap.release()

    def stop(self):
        self._running = False

app = QApplication(sys.argv)
pet = PetWindow()

print("DEBUG: movie.isValid =", pet.movie.isValid())
print("DEBUG: movie.frameRect =", pet.movie.frameRect())
print("DEBUG: movie.frameCount =", pet.movie.frameCount())
pet.show()
pet.raise_()
pet.activateWindow()
print("DEBUG: pet.isVisible() after show() ->", pet.isVisible(), "geometry:", pet.geometry())
QCoreApplication.processEvents()

attention_thread = AttentionThread()

def on_distracted(distracted: bool):
    if distracted:
        print("DISTRACTED → Showing pet 🐶")
        pet.show()
    else:
        print("FOCUSED 😌")

attention_thread.distracted_changed.connect(on_distracted)
attention_thread.start()

def clean_shutdown():
    attention_thread.stop()
    attention_thread.wait(2000)

app.aboutToQuit.connect(clean_shutdown)

def handle_sigint(sig, frame):
    print("SIGINT received — quitting")
    QCoreApplication.quit()

signal.signal(signal.SIGINT, handle_sigint)

exit_code = app.exec()
clean_shutdown()
sys.exit(exit_code)
