"""Generador de reporte en PDF usando matplotlib (sin dependencias extra)."""

from __future__ import annotations

import textwrap
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .matriz import Matriz
from .hungaro import ResultadoAsignacion


class GeneradorPDF:
    """Genera un reporte PDF ejecutivo con el resumen de la asignacion, grafo y analisis."""

    def __init__(self, ruta_salida: str):
        self.ruta_salida = ruta_salida

    def generar(
        self,
        matriz: Matriz,
        resultado: ResultadoAsignacion,
        figura_grafo=None,
        texto_ia: Optional[str] = None,
        capturas=None,
    ) -> str:
        with PdfPages(self.ruta_salida) as pdf:
            # -------------------------------------------------------------
            # Pagina 1: Resumen Ejecutivo y Tablas de Asignacion
            # -------------------------------------------------------------
            fig, ax = plt.subplots(figsize=(8.5, 11), facecolor="#ffffff")
            ax.axis("off")
            
            # Encabezado institucional
            ax.text(0.5, 0.95, "SISTEMA DE ASIGNACIÓN DE RECURSOS", ha="center",
                    fontsize=16, weight="bold", color="#0f172a")
            ax.text(0.5, 0.92, "Optimización Operativa mediante Método Húngaro", ha="center",
                    fontsize=12, color="#2563eb", weight="semibold")
            ax.text(0.5, 0.895, "Caso de Estudio: Rutas y Suministros C.A.", ha="center",
                    fontsize=10, color="#64748b")
            
            # Linea divisoria superior
            ax.plot([0.08, 0.92], [0.88, 0.88], color="#e2e8f0", lw=1.5)
            
            y = 0.85
            objetivo_txt = "Minimizar costo operativo" if resultado.objetivo == "min" else "Maximizar beneficio / eficiencia"
            etiqueta = "Costo" if resultado.objetivo == "min" else "Beneficio"
            
            # Caja de Resumen Metrico (KPI)
            rect = plt.Rectangle((0.08, y - 0.08), 0.84, 0.09, facecolor="#f8fafc",
                                 edgecolor="#cbd5e1", transform=ax.transAxes)
            ax.add_patch(rect)
            
            ax.text(0.12, y - 0.03, f"Función Objetivo: {objetivo_txt}", fontsize=10.5, color="#334155")
            ax.text(0.12, y - 0.065, f"{etiqueta} Total Óptimo: {resultado.costo_total:g}", fontsize=12,
                    weight="bold", color="#1e40af")
            
            estado_txt = "Problema Balanceado (Asignación 100% efectiva)" if not resultado.hubo_ficticios else "Problema Desbalanceado (Se requirieron nodos ficticios)"
            estado_color = "#15803d" if not resultado.hubo_ficticios else "#b45309"
            ax.text(0.58, y - 0.065, f"Estado: {estado_txt}", fontsize=9.5, weight="bold", color=estado_color)
            
            y -= 0.12
            
            # Matriz Original
            ax.text(0.08, y, "1. Matriz Original de Evaluación:", fontsize=11, weight="bold", color="#0f172a")
            y -= 0.025
            
            lineas_matriz = matriz.a_texto().split("\n")
            for linea in lineas_matriz[:16]:  # Limite de seguridad visual
                ax.text(0.10, y, linea, fontsize=8.5, family="monospace", color="#334155")
                y -= 0.020
            
            if len(lineas_matriz) > 16:
                ax.text(0.10, y, f"... ({len(lineas_matriz) - 16} filas adicionales en matriz)", fontsize=8, color="#64748b")
                y -= 0.020
                
            y -= 0.02
            
            # Asignacion Optima
            ax.text(0.08, y, "2. Plan de Asignación Óptima (1 a 1):", fontsize=11, weight="bold", color="#0f172a")
            y -= 0.028
            
            # Encabezado de tabla de asignacion
            ax.text(0.12, y, "Conductor / Agente", fontsize=9.5, weight="bold", color="#475569")
            ax.text(0.45, y, "Ruta / Tarea Asignada", fontsize=9.5, weight="bold", color="#475569")
            ax.text(0.78, y, "Valor Unitario", fontsize=9.5, weight="bold", color="#475569")
            y -= 0.012
            ax.plot([0.10, 0.90], [y, y], color="#cbd5e1", lw=1.0)
            y -= 0.020
            
            for agente, tarea, valor in resultado.asignaciones:
                es_ficticio = (agente in resultado.agentes_ficticios or tarea in resultado.tareas_ficticias)
                col_txt = "#b91c1c" if es_ficticio else "#0f172a"
                tag = " (Ficticio)" if es_ficticio else ""
                
                ax.text(0.12, y, f"{agente}", fontsize=9, color=col_txt)
                ax.text(0.45, y, f"{tarea}{tag}", fontsize=9, color=col_txt)
                ax.text(0.78, y, f"{valor:g}", fontsize=9, weight="bold", color=col_txt)
                y -= 0.020
                
            if resultado.hubo_ficticios:
                y -= 0.015
                if resultado.agentes_inactivos:
                    ax.text(0.10, y, "● Conductores en reserva (sin ruta): " + ", ".join(resultado.agentes_inactivos),
                            fontsize=9, color="#b45309", weight="semibold")
                    y -= 0.020
                if resultado.tareas_huerfanas:
                    ax.text(0.10, y, "● Rutas no cubiertas (requieren atención): " + ", ".join(resultado.tareas_huerfanas),
                            fontsize=9, color="#b91c1c", weight="semibold")
                    y -= 0.020
                    
            # Pie de pagina
            ax.text(0.5, 0.03, "Página 1 de 3 - Reporte Generado Automáticamente", ha="center", fontsize=8, color="#94a3b8")
            
            pdf.savefig(fig)
            plt.close(fig)

            # -------------------------------------------------------------
            # Pagina 2: Grafo Bipartito de Asignacion
            # -------------------------------------------------------------
            if figura_grafo is not None:
                pdf.savefig(figura_grafo)

            # -------------------------------------------------------------
            # Pagina 3: Dictamen Ejecutivo y Analisis de IA
            # -------------------------------------------------------------
            fig_ia, ax_ia = plt.subplots(figsize=(8.5, 11), facecolor="#ffffff")
            ax_ia.axis("off")
            
            ax_ia.text(0.5, 0.95, "ANÁLISIS ESTRATÉGICO Y RECOMENDACIONES", ha="center",
                       fontsize=15, weight="bold", color="#0f172a")
            ax_ia.text(0.5, 0.92, "Evaluación Operativa y de Recursos Humanos", ha="center",
                       fontsize=11, color="#2563eb", weight="semibold")
            ax_ia.plot([0.08, 0.92], [0.90, 0.90], color="#e2e8f0", lw=1.5)
            
            y = 0.85
            contenido_analisis = texto_ia if texto_ia and texto_ia.strip() else (
                "No se ejecutó la consulta al asistente de Inteligencia Artificial para esta corrida.\n\n"
                "Conclusiones del Modelo Matemático:\n"
                "- La solución calculada representa el óptimo global del problema de asignación 1 a 1 mediante el Método Húngaro.\n"
                f"- El {etiqueta.lower()} total consolidado es de {resultado.costo_total:g} unidades.\n"
                "- Se recomienda verificar los recursos inactivos o tareas huérfanas en caso de desbalance operativo."
            )
            
            for parrafo in contenido_analisis.split("\n"):
                if parrafo.strip() == "":
                    y -= 0.02
                    continue
                for linea in textwrap.wrap(parrafo, width=90):
                    ax_ia.text(0.10, y, linea, fontsize=9.5, color="#1e293b", va="top")
                    y -= 0.022
                y -= 0.015
                
            ax_ia.text(0.5, 0.03, "Página 3 de 3 - Reporte Generado Automáticamente", ha="center", fontsize=8, color="#94a3b8")
            
            pdf.savefig(fig_ia)
            plt.close(fig_ia)

            # Paginas opcionales si se envian capturas explícitas (compatibilidad)
            if capturas:
                for indice, captura in enumerate(capturas, start=1):
                    fig_c, ax_c = plt.subplots(figsize=(8.5, 11), facecolor="#ffffff")
                    ax_c.axis("off")
                    import numpy as np
                    imagen = np.array(captura)
                    ax_c.imshow(imagen)
                    ax_c.axis("off")
                    pdf.savefig(fig_c)
                    plt.close(fig_c)

        return self.ruta_salida
