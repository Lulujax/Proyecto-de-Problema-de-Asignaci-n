"""Motor del Metodo Hungaro implementado desde cero (sin librerias de optimizacion externas).

Implementa el algoritmo clasico paso a paso:
  1. Auto-balanceo (filas/columnas ficticias con costo 0).
  2. Transformacion para maximizacion (max - valor).
  3. Reduccion de filas.
  4. Reduccion de columnas.
  5. Cobertura de ceros con el minimo numero de lineas (teorema de Konig).
  6. Ajuste de la matriz y repeticion.
  7. Extraccion de la asignacion optima 1 a 1.

Todos los pasos se registran en `self.pasos` para fines didacticos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .matriz import Matriz


@dataclass
class ResultadoAsignacion:
    """Resultado de resolver un problema de asignacion."""

    asignaciones: List[Tuple[str, str, float]] = field(default_factory=list)
    costo_total: float = 0.0
    objetivo: str = "min"  # "min" o "max"
    hubo_ficticios: bool = False
    agentes_ficticios: List[str] = field(default_factory=list)
    tareas_ficticias: List[str] = field(default_factory=list)
    agentes_inactivos: List[str] = field(default_factory=list)
    tareas_huerfanas: List[str] = field(default_factory=list)
    pasos: List[str] = field(default_factory=list)
    matriz_original: Matriz = None


class Hungaro:
    """Resuelve un problema de asignacion con el Metodo Hungaro."""

    def __init__(self, matriz: Matriz, objetivo: str = "min"):
        if objetivo not in ("min", "max"):
            raise ValueError("El objetivo debe ser 'min' o 'max'.")
        matriz.validar()
        self.matriz_original: Matriz = matriz.clonar()
        self.objetivo: str = objetivo
        self.pasos: List[str] = []

        # Se rellenan durante resolver()
        self.agentes_ficticios: List[str] = []
        self.tareas_ficticias: List[str] = []
        self.matriz_balanceada: Matriz = None  # balanceada, sin transformar
        self.matriz_trabajo: List[List[float]] = None  # balanceada + transformada (o no)
        self.factor_max: float = None  # max global usado en maximizacion

    # ------------------------------------------------------------------ #
    # API publica
    # ------------------------------------------------------------------ #
    def resolver(self) -> ResultadoAsignacion:
        """Ejecuta todo el flujo y devuelve el resultado."""
        self.pasos = []
        self.agentes_ficticios = []
        self.tareas_ficticias = []

        # 1. Auto-balanceo
        self._registrar_paso("=== INICIO DEL METODO HUNGARO ===")
        self._registrar_paso(f"Objetivo: {'minimizar costo' if self.objetivo == 'min' else 'maximizar beneficio'}.")
        self._registrar_paso(f"Matriz original {self.matriz_original.dimensiones()}:")
        self._registrar_paso(self.matriz_original.a_texto())

        self.auto_balancear()
        self._registrar_paso(f"Tras auto-balanceo: {self.matriz_balanceada.dimensiones()}.")
        if self.agentes_ficticios or self.tareas_ficticias:
            self._registrar_paso(f"Agentes ficticios: {self.agentes_ficticios}")
            self._registrar_paso(f"Tareas ficticias: {self.tareas_ficticias}")
        self._registrar_paso(self.matriz_balanceada.a_texto())

        # 2. Transformacion para maximizacion
        if self.objetivo == "max":
            self.transformar_para_maximizacion()

        # 3. Algoritmo clasico sobre matriz cuadrada
        n = len(self.matriz_trabajo)
        self._reducir_filas()
        self._reducir_columnas()

        iteracion = 0
        while True:
            iteracion += 1
            self._registrar_paso(f"--- Iteracion {iteracion}: cobertura de ceros ---")
            cubiertas_filas, cubiertas_columnas, num_lineas, emparejamiento = self._cubrir_ceros(self.matriz_trabajo)
            self._registrar_paso(
                f"Lineas: {num_lineas} (filas cubiertas: {sum(cubiertas_filas)}, "
                f"columnas cubiertas: {sum(cubiertas_columnas)})."
            )
            if num_lineas >= n:
                self._registrar_paso("Numero de lineas = n: existe asignacion optima.")
                break
            self._ajustar_matriz(cubiertas_filas, cubiertas_columnas)

        # 4. Extraer asignacion sobre la matriz final
        _, _, _, emparejamiento = self._cubrir_ceros(self.matriz_trabajo)
        asignaciones_trabajo = self._extraer_asignacion(emparejamiento)

        # 5. Revertir a valores originales y calcular totales reales
        resultado = self._construir_resultado(asignaciones_trabajo)
        self._registrar_paso("=== RESULTADO FINAL ===")
        for agente, tarea, valor in resultado.asignaciones:
            self._registrar_paso(f"  {agente} -> {tarea} = {valor}")
        self._registrar_paso(
            f"{'Costo' if self.objetivo == 'min' else 'Beneficio'} total optimo: "
            f"{resultado.costo_total}"
        )
        resultado.pasos = list(self.pasos)
        return resultado

    def auto_balancear(self) -> None:
        """Anade filas/columnas ficticias con costo 0 si la matriz no es cuadrada."""
        agentes = list(self.matriz_original.agentes)
        tareas = list(self.matriz_original.tareas)
        valores = [list(fila) for fila in self.matriz_original.valores]

        n_agentes = len(agentes)
        n_tareas = len(tareas)

        if n_agentes < n_tareas:
            # Faltan agentes: se agregan agentes ficticios (filas).
            cantidad = n_tareas - n_agentes
            for i in range(1, cantidad + 1):
                nombre = f"Agente_Ficticio_{i}"
                agentes.append(nombre)
                self.agentes_ficticios.append(nombre)
                valores.append([0] * n_tareas)
        elif n_agentes > n_tareas:
            # Sobran agentes: se agregan tareas ficticias (columnas).
            cantidad = n_agentes - n_tareas
            for i in range(1, cantidad + 1):
                nombre = f"Tarea_Ficticia_{i}"
                tareas.append(nombre)
                self.tareas_ficticias.append(nombre)
            for fila in valores:
                fila.extend([0] * cantidad)

        self.matriz_balanceada = Matriz(agentes, tareas, valores)
        self.matriz_balanceada.validar()
        # Copia de trabajo (se transformara si es maximizacion).
        self.matriz_trabajo = [list(fila) for fila in valores]

    def transformar_para_maximizacion(self) -> None:
        """Convierte un problema de maximizacion en minimizacion.

        Se usa la transformacion: nuevo = max_global - valor. Asi todos los
        valores quedan no negativos y el Metodo Hungaro (de minimos) aplica.
        """
        max_global = max(valor for fila in self.matriz_trabajo for valor in fila)
        # Si todos los valores son iguales, max_global puede ser 0; se evita division
        # por cero (no se divide, solo se resta, asi que es seguro).
        self.factor_max = max_global
        self.matriz_trabajo = [
            [self.factor_max - valor for valor in fila] for fila in self.matriz_trabajo
        ]
        self._registrar_paso(
            f"Maximizacion: transformacion aplicada (max_global = {self.factor_max}). "
            f"nuevo = max_global - valor."
        )

    # ------------------------------------------------------------------ #
    # Pasos didacticos
    # ------------------------------------------------------------------ #
    def _registrar_paso(self, texto: str) -> None:
        self.pasos.append(texto)

    def _reducir_filas(self) -> None:
        for i, fila in enumerate(self.matriz_trabajo):
            minimo_fila = min(fila)
            if minimo_fila != 0:
                self.matriz_trabajo[i] = [v - minimo_fila for v in fila]
        self._registrar_paso("Reduccion de filas: se resto el minimo de cada fila.")

    def _reducir_columnas(self) -> None:
        n = len(self.matriz_trabajo)
        m = len(self.matriz_trabajo[0])
        for j in range(m):
            minimo_columna = min(self.matriz_trabajo[i][j] for i in range(n))
            if minimo_columna != 0:
                for i in range(n):
                    self.matriz_trabajo[i][j] -= minimo_columna
        self._registrar_paso("Reduccion de columnas: se resto el minimo de cada columna.")

    def _cubrir_ceros(self, matriz: List[List[float]]):
        """Devuelve (filas_cubiertas, columnas_cubiertas, num_lineas, emparejamiento).

        Usa el teorema de Konig para cubrir todos los ceros con el minimo
        numero de lineas (filas o columnas).
        """
        n = len(matriz)
        # Emparejamiento maximo de ceros (Hungarian matching auxiliar).
        match_fila = [-1] * n  # match_fila[r] = c
        match_columna = [-1] * n  # match_columna[c] = r

        def intentar_emparejar(fila: int, visitadas_columnas: List[bool]) -> bool:
            for columna in range(n):
                if matriz[fila][columna] == 0 and not visitadas_columnas[columna]:
                    visitadas_columnas[columna] = True
                    if match_columna[columna] == -1 or intentar_emparejar(
                        match_columna[columna], visitadas_columnas
                    ):
                        match_fila[fila] = columna
                        match_columna[columna] = fila
                        return True
            return False

        for fila in range(n):
            visitadas = [False] * n
            intentar_emparejar(fila, visitadas)

        # Teorema de Konig: a partir del emparejamiento maximo.
        filas_sin_emparejar = [r for r in range(n) if match_fila[r] == -1]

        visitadas_filas = [False] * n
        visitadas_columnas = [False] * n
        pila = list(filas_sin_emparejar)
        for r in filas_sin_emparejar:
            visitadas_filas[r] = True

        while pila:
            fila_actual = pila.pop()
            for columna in range(n):
                if matriz[fila_actual][columna] == 0 and not visitadas_columnas[columna]:
                    visitadas_columnas[columna] = True
                    fila_emparejada = match_columna[columna]
                    if fila_emparejada != -1 and not visitadas_filas[fila_emparejada]:
                        visitadas_filas[fila_emparejada] = True
                        pila.append(fila_emparejada)

        # Lineas cubiertas: filas NO visitadas + columnas visitadas.
        filas_cubiertas = [not visitadas_filas[r] for r in range(n)]
        columnas_cubiertas = [visitadas_columnas[c] for c in range(n)]
        num_lineas = sum(filas_cubiertas) + sum(columnas_cubiertas)
        return filas_cubiertas, columnas_cubiertas, num_lineas, match_fila

    def _ajustar_matriz(self, filas_cubiertas: List[bool], columnas_cubiertas: List[bool]) -> None:
        n = len(self.matriz_trabajo)
        m = len(self.matriz_trabajo[0])
        # Minimo entre celdas no cubiertas.
        no_cubiertos = [
            self.matriz_trabajo[i][j]
            for i in range(n)
            for j in range(m)
            if not filas_cubiertas[i] and not columnas_cubiertas[j]
        ]
        if not no_cubiertos:
            return
        minimo = min(no_cubiertos)
        for i in range(n):
            for j in range(m):
                if not filas_cubiertas[i] and not columnas_cubiertas[j]:
                    self.matriz_trabajo[i][j] -= minimo
                elif filas_cubiertas[i] and columnas_cubiertas[j]:
                    self.matriz_trabajo[i][j] += minimo
        # Celdas con exactamente una linea no cambian.
        self._registrar_paso(
            f"Ajuste: minimo no cubierto = {minimo}; restado a filas no cubiertas, "
            f"sumado a columnas cubiertas."
        )

    def _extraer_asignacion(self, emparejamiento: List[int]) -> List[Tuple[int, int]]:
        """Devuelve lista de (indice_fila, indice_columna) asignados."""
        # Recalcular emparejamiento final por seguridad.
        n = len(self.matriz_trabajo)
        match_fila = [-1] * n
        match_columna = [-1] * n

        def intentar(fila, visitadas):
            for columna in range(n):
                if self.matriz_trabajo[fila][columna] == 0 and not visitadas[columna]:
                    visitadas[columna] = True
                    if match_columna[columna] == -1 or intentar(match_columna[columna], visitadas):
                        match_fila[fila] = columna
                        match_columna[columna] = fila
                        return True
            return False

        for fila in range(n):
            visitadas = [False] * n
            intentar(fila, visitadas)

        return [(f, match_fila[f]) for f in range(n) if match_fila[f] != -1]

    def _construir_resultado(self, asignaciones_indices: List[Tuple[int, int]]) -> ResultadoAsignacion:
        agentes = self.matriz_balanceada.agentes
        tareas = self.matriz_balanceada.tareas
        # Valores originales (balanceados, sin transformar) para reportar.
        valores_originales = self.matriz_balanceada.valores

        asignaciones: List[Tuple[str, str, float]] = []
        costo_total = 0.0
        for indice_fila, indice_columna in asignaciones_indices:
            agente = agentes[indice_fila]
            tarea = tareas[indice_columna]
            valor_original = valores_originales[indice_fila][indice_columna]
            asignaciones.append((agente, tarea, valor_original))
            costo_total += valor_original

        agentes_ficticios_set = set(self.agentes_ficticios)
        tareas_ficticias_set = set(self.tareas_ficticias)

        agentes_inactivos = [
            agente for (agente, tarea, _) in asignaciones
            if tarea in tareas_ficticias_set
        ]
        tareas_huerfanas = [
            tarea for (agente, tarea, _) in asignaciones
            if agente in agentes_ficticios_set
        ]

        hubo_ficticios = bool(self.agentes_ficticios or self.tareas_ficticias)

        return ResultadoAsignacion(
            asignaciones=asignaciones,
            costo_total=costo_total,
            objetivo=self.objetivo,
            hubo_ficticios=hubo_ficticios,
            agentes_ficticios=list(self.agentes_ficticios),
            tareas_ficticias=list(self.tareas_ficticias),
            agentes_inactivos=agentes_inactivos,
            tareas_huerfanas=tareas_huerfanas,
            pasos=list(self.pasos),
            matriz_original=self.matriz_original,
        )

    # ------------------------------------------------------------------ #
    # Utilidades
    # ------------------------------------------------------------------ #
    def obtener_pasos(self) -> List[str]:
        return list(self.pasos)