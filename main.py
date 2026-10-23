"""Punto de entrada de la aplicacion."""
import os
import sys

# Permite ejecutar `python main.py` desde la raiz del proyecto.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui import iniciar_aplicacion


if __name__ == "__main__":
    iniciar_aplicacion()