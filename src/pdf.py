"""Generador de reporte en PDF usando matplotlib (sin dependencias extra)."""

from __future__ import annotations

import textwrap
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .matriz import Matriz
from .hungaro import ResultadoAsignacion


class GeneradorPDF:
    """Genera un PDF con el resumen de la asignacion, grafo y analisis de IA."""

    def __init__(self, ruta_salida: str):
        self.ruta_salida = ruta_salida

    def generar(
        self,
        matriz: Matriz,
        resultado: ResultadoAsignacion,
        figura_grafo=None,
        texto_ia: Optional[str] = None,
    ) -> str:
        with PdfPages(self.ruta_salida) as pdf:
            # Pagina 1: resumen + matriz + asignacion.
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis("off")
            y = 0.96
            ax.text(0.5, y, "Reporte de Asignacion - Metodo Hungaro", ha="center",
                    fontsize=16, weight="bold")
            y -= 0.04
            ax.text(0.5, y, "Rutas y Suministros C.A. - Fase II", ha="center",
                    fontsize=11, color="#57606a")
            y -= 0.06
            objetivo_txt = "Minimizar costo" if resultado.objetivo == "min" else "Maximizar beneficio/eficiencia"
            ax.text(0.1, y, f"Objetivo: {objetivo_txt}", fontsize=12)
            y -= 0.03
            etiqueta = "Costo" if resultado.objetivo == "min" else "Beneficio"
            ax.text(0.1, y, f"{etiqueta} total optimo: {resultado.costo_total}", fontsize=13, weight="bold")
            y -= 0.06
            ax.text(0.1, y, "Matriz original (costos/beneficios):", fontsize=12, weight="bold")
            y -= 0.03
            for line in matriz.a_texto().split("\n"):
                ax.text(0.1, y, line, fontsize=9, family="monospace")
                y -= 0.022
            y -= 0.03
            ax.text(0.1, y, "Asignacion final:", fontsize=12, weight="bold")
            y -= 0.03
            for agente, tarea, valor in resultado.asignaciones:
                ax.text(0.1, y, f"  {agente} -> {tarea} = {valor}", fontsize=10)
                y -= 0.025
            if resultado.hubo_ficticios:
                y -= 0.02
                if resultado.agentes_inactivos:
                    ax.text(0.1, y, "Agentes inactivos: " + ", ".join(resultado.agentes_inactivos), fontsize=10)
                    y -= 0.025
                if resultado.tareas_huerfanas:
                    ax.text(0.1, y, "Tareas huerfanas: " + ", ".join(resultado.tareas_huerfanas), fontsize=10)
                    y -= 0.025
            pdf.savefig(fig)
            plt.close(fig)

            # Pagina 2: grafo (si existe).
            if figura_grafo is not None:
                pdf.savefig(figura_grafo)

            # Pagina 3: analisis de IA (si existe).
            if texto_ia:
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.axis("off")
                ax.text(0.5, 0.96, "Analisis de IA (Gerente de Operaciones y RRHH)", ha="center",
                        fontsize=14, weight="bold")
                y = 0.9
                for parrafo in texto_ia.split("\n"):
                    if parrafo.strip() == "":
                        y -= 0.02
                        continue
                    for linea in textwrap.wrap(parrafo, width=95):
                        ax.text(0.1, y, linea, fontsize=10, va="top")
                        y -= 0.022
                    y -= 0.02
                pdf.savefig(fig)
                plt.close(fig)

        return self.ruta_salida