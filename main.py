"""Punto de entrada de la aplicacion."""

import os
import sys

# Permite ejecutar `python main.py` desde la raiz del proyecto.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Habilitar soporte para pantallas de alta resolucion (High-DPI) en Windows
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from src.gui import iniciar_aplicacion


if __name__ == "__main__":
    iniciar_aplicacion()
