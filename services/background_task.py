# =============================================================================
# VESP Organizations - Background Task Runner
# =============================================================================

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
from typing import Any, Callable


class TaskSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)


class BackgroundTask(QRunnable):
    """Ejecutor de tareas en hilo de fondo con señales para UI."""

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = TaskSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            resultado = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(resultado)
        except Exception as e:
            self.signals.error.emit(str(e))


def run_background_task(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> BackgroundTask:
    """Lanza una tarea en el pool de hilos global."""
    tarea = BackgroundTask(fn, *args, **kwargs)
    QThreadPool.globalInstance().start(tarea)
    return tarea
