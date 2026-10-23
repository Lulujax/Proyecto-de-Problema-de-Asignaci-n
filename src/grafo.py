"""Modulo de visualizacion del grafo bipartito (agentes vs tareas).

Usa networkx para el grafo y matplotlib para dibujar/guardar. Las aristas que
tocan nodos ficticios (problema desbalanceado) se dibujan en rojo y punteadas
para alertar a gerencia.
"""

from __future__ import annotations

import os
from typing import List, Tuple

import matplotlib
import matplotlib.pyplot as plt
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

    # ------------------------------------------------------------------ #
    # Construccion
    # ------------------------------------------------------------------ #
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
        total_agentes = len(self.agentes)
        total_tareas = len(self.tareas)
        for indice, agente in enumerate(self.agentes):
            # y decreciente para que el primero quede arriba.
            posiciones[agente] = (0.0, total_agentes - 1 - indice)
        for indice, tarea in enumerate(self.tareas):
            posiciones[tarea] = (1.0, total_tareas - 1 - indice)
        self.posiciones = posiciones

    # ------------------------------------------------------------------ #
    # Figura (reutilizable por GUI)
    # ------------------------------------------------------------------ #
    def crear_figura(self, figsize=(8, 6)):
        if self.grafo is None:
            self.construir()

        agentes_ficticios = set(self.resultado.agentes_ficticios)
        tareas_ficticias = set(self.resultado.tareas_ficticias)

        aristas_normales: List[Tuple[str, str]] = []
        aristas_ficticias: List[Tuple[str, str]] = []
        for agente, tarea, _ in self.resultado.asignaciones:
            if agente in agentes_ficticios or tarea in tareas_ficticias:
                aristas_ficticias.append((agente, tarea))
            else:
                aristas_normales.append((agente, tarea))

        figura, eje = plt.subplots(figsize=figsize)
        nx.draw_networkx_nodes(
            self.grafo, self.posiciones, nodelist=self.agentes,
            node_color="#9ecae9", node_size=1400, ax=eje,
        )
        nx.draw_networkx_nodes(
            self.grafo, self.posiciones, nodelist=self.tareas,
            node_color="#a1d99b", node_size=1400, ax=eje,
        )
        nx.draw_networkx_labels(self.grafo, self.posiciones, font_size=9, ax=eje)

        if aristas_normales:
            nx.draw_networkx_edges(
                self.grafo, self.posiciones, edgelist=aristas_normales,
                edge_color="#1f77b4", width=2.5, ax=eje,
            )
        if aristas_ficticias:
            nx.draw_networkx_edges(
                self.grafo, self.posiciones, edgelist=aristas_ficticias,
                edge_color="#d62728", width=2.5, style="dashed", ax=eje,
            )

        # Etiquetas de valor sobre las aristas.
        etiquetas_aristas = {
            (a, t): f"{v:g}" for (a, t, v) in self.resultado.asignaciones
        }
        nx.draw_networkx_edge_labels(
            self.grafo, self.posiciones, edge_labels=etiquetas_aristas, font_size=8, ax=eje
        )

        eje.set_title("Grafo bipartito de asignacion optima")
        eje.text(0.0, -0.08, "Agentes", transform=eje.transAxes, ha="center")
        eje.text(1.0, -0.08, "Tareas", transform=eje.transAxes, ha="center")
        eje.axis("off")

        # Leyenda manual.
        from matplotlib.lines import Line2D

        leyenda = [
            Line2D([0], [0], color="#1f77b4", lw=2, label="Asignacion normal"),
            Line2D([0], [0], color="#d62728", lw=2, linestyle="--",
                   label="Toca nodo ficticio (alerta)"),
        ]
        eje.legend(handles=leyenda, loc="lower center", bbox_to_anchor=(0.5, -0.18))

        figura.tight_layout()
        return figura

    # ------------------------------------------------------------------ #
    # Dibujar + guardar + mostrar
    # ------------------------------------------------------------------ #
    def dibujar(self, ruta_salida: str, mostrar: bool = True):
        figura = self.crear_figura()
        os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)
        figura.savefig(ruta_salida, dpi=120, bbox_inches="tight")
        if mostrar:
            plt.show()
        return ruta_salida