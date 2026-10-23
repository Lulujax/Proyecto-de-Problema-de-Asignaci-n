"""Clase Matriz: representa la matriz de costos/beneficios del problema de asignacion.

Encapsula agentes (filas), tareas (columnas) y valores numericos, ademas de
validaciones basicas. Es el objeto que circula entre los modulos de ingesta,
el motor hungaro, el grafo y la interfaz.
"""

from __future__ import annotations

from typing import List


class Matriz:
    """Matriz de costos/beneficios para un problema de asignacion 1 a 1."""

    def __init__(self, agentes: List[str], tareas: List[str], valores: List[List[float]]):
        # Se copian las listas para evitar mutaciones externas compartidas.
        self.agentes: List[str] = list(agentes)
        self.tareas: List[str] = list(tareas)
        self.valores: List[List[float]] = [list(fila) for fila in valores]

    # ------------------------------------------------------------------ #
    # Validacion
    # ------------------------------------------------------------------ #
    def validar(self) -> None:
        """Valida la coherencia de la matriz. Lanza ValueError si hay problemas."""
        if not self.agentes:
            raise ValueError("La lista de agentes esta vacia.")
        if not self.tareas:
            raise ValueError("La lista de tareas esta vacia.")
        if len(self.valores) != len(self.agentes):
            raise ValueError(
                f"Numero de filas ({len(self.valores)}) no coincide con "
                f"numero de agentes ({len(self.agentes)})."
            )
        for indice_fila, fila in enumerate(self.valores):
            if len(fila) != len(self.tareas):
                raise ValueError(
                    f"La fila {indice_fila} tiene {len(fila)} columnas, "
                    f"pero se esperaban {len(self.tareas)}."
                )
            for indice_columna, valor in enumerate(fila):
                if not isinstance(valor, (int, float)):
                    raise ValueError(
                        f"Valor no numerico en [{indice_fila}][{indice_columna}]: {valor!r}"
                    )
                # Descartar NaN e infinitos que romperian el algoritmo.
                if valor != valor:  # NaN
                    raise ValueError(f"Valor NaN en [{indice_fila}][{indice_columna}].")
                if valor == float("inf") or valor == float("-inf"):
                    raise ValueError(f"Valor infinito en [{indice_fila}][{indice_columna}].")

    def es_cuadrada(self) -> bool:
        """Indica si el numero de agentes es igual al numero de tareas."""
        return len(self.agentes) == len(self.tareas)

    def dimensiones(self) -> tuple[int, int]:
        """Devuelve (numero_agentes, numero_tareas)."""
        return (len(self.agentes), len(self.tareas))

    def clonar(self) -> "Matriz":
        """Devuelve una copia profunda de la matriz."""
        return Matriz(self.agentes, self.tareas, self.valores)

    def a_texto(self) -> str:
        """Representacion legible de la matriz (para consola / logs)."""
        ancho = max([len(nombre) for nombre in self.agentes] + [6])
        encabezado = " " * ancho + " | " + " | ".join(f"{t:>8}" for t in self.tareas)
        lineas = [encabezado, "-" * len(encabezado)]
        for agente, fila in zip(self.agentes, self.valores):
            celdas = " | ".join(f"{v:>8}" for v in fila)
            lineas.append(f"{agente:>{ancho}} | {celdas}")
        return "\n".join(lineas)

    def obtener_valor(self, agente: str, tarea: str) -> float:
        """Devuelve el valor de la celda (agente, tarea)."""
        indice_fila = self.agentes.index(agente)
        indice_columna = self.tareas.index(tarea)
        return self.valores[indice_fila][indice_columna]

    def __repr__(self) -> str:
        return f"Matriz(agentes={len(self.agentes)}, tareas={len(self.tareas)})"