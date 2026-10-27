"""Modulo de visualizacion del grafo bipartito (agentes vs tareas).

Usa networkx para la estructura del grafo y matplotlib para renderizar.
Evita el solapamiento central de etiquetas distribuyendo las posiciones de costo
a lo largo de las trayectorias de forma escalonada. Soporta temas oscuro y claro.
"""

from __future__ import annotations

import os
from typing import List, Tuple

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

from .hungaro import ResultadoAsignacion


class GrafoBipartito:
    """Construye y dibuja el grafo bipartito de una asignacion optima."""

    def __init__(self, resultado: ResultadoAsignacion):
        self.resultado = resultado
        self.grafo: nx.Graph = None
        self.posiciones: dict = None
        self.agentes: List[str] = list(resultado.matriz_original.agentes) + list(
            resultado.agentes_ficticios
        )
        self.tareas: List[str] = list(resultado.matriz_original.tareas) + list(
            resultado.tareas_ficticias
        )

    def construir(self) -> nx.Graph:
        grafo = nx.Graph()
        for agente in self.agentes:
            grafo.add_node(agente, bipartition=0, tipo="agente")
        for tarea in self.tareas:
            grafo.add_node(tarea, bipartition=1, tipo="tarea")

        for agente, tarea, _ in self.resultado.asignaciones:
            grafo.add_edge(agente, tarea)

        self.grafo = grafo
        self._calcular_posiciones()
        return grafo

    def _calcular_posiciones(self) -> None:
        posiciones = {}
        total_agentes = max(len(self.agentes), 1)
        total_tareas = max(len(self.tareas), 1)
        max_items = max(total_agentes, total_tareas)

        # Distribuir uniformemente en el eje vertical
        for indice, agente in enumerate(self.agentes):
            posiciones[agente] = (0.0, total_agentes - 1 - indice)
        for indice, tarea in enumerate(self.tareas):
            posiciones[tarea] = (1.0, total_tareas - 1 - indice)
        self.posiciones = posiciones

    def crear_figura(self, figsize=(9.2, 6.0), tema: str = "dark"):
        if self.grafo is None:
            self.construir()

        agentes_ficticios = set(self.resultado.agentes_ficticios)
        tareas_ficticias = set(self.resultado.tareas_ficticias)

        aristas_normales: List[Tuple[str, str, float]] = []
        aristas_ficticias: List[Tuple[str, str, float]] = []
        for agente, tarea, valor in self.resultado.asignaciones:
            if agente in agentes_ficticios or tarea in tareas_ficticias:
                aristas_ficticias.append((agente, tarea, valor))
            else:
                aristas_normales.append((agente, tarea, valor))

        # Configuracion de paleta segun tema
        if tema == "dark":
            bg_color = "#161f2e"
            text_color = "#f8fafc"
            subtext_color = "#94a3b8"
            edge_norm = "#60a5fa"
            edge_fict = "#f43f5e"
            box_bg = "#1e293b"
            legend_bg = "#1e293b"
            legend_edge = "#334155"
        else:
            bg_color = "#ffffff"
            text_color = "#0f172a"
            subtext_color = "#475569"
            edge_norm = "#1d4ed8"
            edge_fict = "#dc2626"
            box_bg = "#f8fafc"
            legend_bg = "#f8fafc"
            legend_edge = "#cbd5e1"

        figura, eje = plt.subplots(figsize=figsize, facecolor=bg_color)
        eje.set_facecolor(bg_color)

        total_a = len(self.agentes)
        total_t = len(self.tareas)
        max_y = max(total_a, total_t) - 1

        # 1. Dibujar Aristas (Lineas)
        for agente, tarea, valor in aristas_normales:
            xa, ya = self.posiciones[agente]
            xt, yt = self.posiciones[tarea]
            eje.plot([xa, xt], [ya, yt], color=edge_norm, linewidth=2.8, zorder=2, alpha=0.95)

        for agente, tarea, valor in aristas_ficticias:
            xa, ya = self.posiciones[agente]
            xt, yt = self.posiciones[tarea]
            eje.plot([xa, xt], [ya, yt], color=edge_fict, linewidth=2.5, linestyle="--", zorder=2, alpha=0.95)

        # 2. Dibujar Etiquetas de Valor SIN SOLAPAMIENTO CENTRAL
        # Colocamos las etiquetas en posiciones escalonadas cerca del agente (t entre 0.22 y 0.36)
        # Esto asegura que NUNCA coincidan en el punto medio (t=0.5) donde se cruzan las lineas
        for idx, (agente, tarea, valor) in enumerate(self.resultado.asignaciones):
            xa, ya = self.posiciones[agente]
            xt, yt = self.posiciones[tarea]
            es_fict = (agente in agentes_ficticios or tarea in tareas_ficticias)
            c_arista = edge_fict if es_fict else edge_norm

            # Escalonamiento inteligente: alterna 0.22 y 0.34 segun el indice del agente
            t_ratio = 0.22 if idx % 2 == 0 else 0.34
            lx = xa + t_ratio * (xt - xa)
            ly = ya + t_ratio * (yt - ya)

            simbolo = "" if self.resultado.objetivo == "max" else ""
            txt_valor = f" {valor:g} "

            eje.text(
                lx, ly, txt_valor,
                color=text_color,
                fontsize=9.5,
                fontweight="bold",
                ha="center",
                va="center",
                bbox=dict(
                    boxstyle="round,pad=0.35",
                    facecolor=box_bg,
                    edgecolor=c_arista,
                    linewidth=1.6,
                ),
                zorder=10,
            )

        # 3. Dibujar Nodos Agentes (Izquierda)
        for idx, agente in enumerate(self.agentes):
            x, y = self.posiciones[agente]
            es_fict = agente in agentes_ficticios
            color_nodo = "#f43f5e" if es_fict else "#3b82f6"
            borde_nodo = "#be123c" if es_fict else "#1d4ed8"

            # Circulo del nodo
            eje.scatter(x, y, s=1400, color=color_nodo, edgecolors=borde_nodo, linewidths=2.2, zorder=5)

            # Letra/Identificador dentro del circulo (ej. C1, C2...)
            tag_interior = f"C{idx + 1}" if not es_fict else "CF"
            eje.text(x, y, tag_interior, color="#ffffff", fontweight="bold", fontsize=10,
                     ha="center", va="center", zorder=6)

            # Nombre descriptivo completo a la izquierda del circulo (sin desbordamiento)
            nombre_label = f"{agente}" + (" (Ficticio)" if es_fict else "")
            color_lbl = "#f87171" if es_fict else text_color
            eje.text(x - 0.08, y, nombre_label, color=color_lbl, fontweight="bold", fontsize=9.5,
                     ha="right", va="center", zorder=6)

        # 4. Dibujar Nodos Tareas (Derecha)
        for idx, tarea in enumerate(self.tareas):
            x, y = self.posiciones[tarea]
            es_fict = tarea in tareas_ficticias
            color_nodo = "#f43f5e" if es_fict else "#10b981"
            borde_nodo = "#be123c" if es_fict else "#047857"

            # Circulo del nodo
            eje.scatter(x, y, s=1400, color=color_nodo, edgecolors=borde_nodo, linewidths=2.2, zorder=5)

            # Letra/Identificador dentro del circulo (ej. R1, R2...)
            tag_interior = f"R{idx + 1}" if not es_fict else "RF"
            eje.text(x, y, tag_interior, color="#ffffff", fontweight="bold", fontsize=10,
                     ha="center", va="center", zorder=6)

            # Nombre descriptivo completo a la derecha del circulo (sin desbordamiento)
            nombre_label = f"{tarea}" + (" (Ficticia)" if es_fict else "")
            color_lbl = "#f87171" if es_fict else text_color
            eje.text(x + 0.08, y, nombre_label, color=color_lbl, fontweight="bold", fontsize=9.5,
                     ha="left", va="center", zorder=6)

        # Encabezados de columnas superiores
        eje.text(0.0, max_y + 0.55, "CONDUCTORES (AGENTES)", ha="center",
                 fontsize=10.5, fontweight="bold", color=subtext_color)
        eje.text(1.0, max_y + 0.55, "RUTAS (TAREAS)", ha="center",
                 fontsize=10.5, fontweight="bold", color=subtext_color)

        # Limites de visualizacion amplios para evitar recortes laterales
        eje.set_xlim(-0.55, 1.55)
        eje.set_ylim(-0.8, max_y + 0.8)
        eje.axis("off")

        # Titulo
        eje.set_title("Grafo Bipartito de Asignación Óptima", fontsize=13, fontweight="bold", color=text_color, pad=16)

        # Leyenda inferior
        leyenda = [
            Line2D([0], [0], color=edge_norm, lw=2.8, label="Asignación Óptima"),
        ]
        if aristas_ficticias:
            leyenda.append(
                Line2D([0], [0], color=edge_fict, lw=2.5, linestyle="--", label="Asignación Ficticia (Alerta)")
            )

        legend = eje.legend(
            handles=leyenda, loc="lower center", bbox_to_anchor=(0.5, -0.10),
            ncol=len(leyenda), frameon=True, facecolor=legend_bg, edgecolor=legend_edge
        )
        for text in legend.get_texts():
            text.set_color(text_color)
            text.set_fontsize(9)

        figura.tight_layout()
        return figura

    def dibujar(self, ruta_salida: str, mostrar: bool = True, tema: str = "dark"):
        figura = self.crear_figura(tema=tema)
        os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)
        figura.savefig(ruta_salida, dpi=140, bbox_inches="tight", facecolor=figura.get_facecolor())
        if mostrar:
            plt.show()
        return ruta_salida
