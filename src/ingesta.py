"""Modulo de ingesta de datos: carga de matrices desde CSV/JSON y matriz por defecto.

Toda la logica de lectura y validacion vive aqui para mantener el resto del
sistema desacoplado del formato de archivo. Los errores se encapsulan en
`IngestaError` con mensajes claros para el usuario.
"""

from __future__ import annotations

import csv
import json
import os
from typing import List

from .matriz import Matriz


class IngestaError(Exception):
    """Error de ingesta de datos con mensaje amigable para el usuario."""


class IngestaDatos:
    """Carga matrices desde archivos externos o provee una matriz por defecto."""

    # ------------------------------------------------------------------ #
    # CSV
    # ------------------------------------------------------------------ #
    @staticmethod
    def cargar_csv(ruta: str) -> Matriz:
        """Carga una matriz desde un archivo CSV con encabezados.

        Formato esperado:
            (vacio),Tarea_1,Tarea_2,...
            Agente_1,5,9,...
            Agente_2,3,6,...
        """
        if not isinstance(ruta, str) or not ruta.strip():
            raise IngestaError("La ruta del archivo CSV no puede estar vacia.")
        if not os.path.isfile(ruta):
            raise IngestaError(f"El archivo no existe: {ruta}")
        if not ruta.lower().endswith(".csv"):
            raise IngestaError("El archivo debe tener extension .csv.")

        try:
            with open(ruta, "r", encoding="utf-8-sig", newline="") as archivo:
                lector = csv.reader(archivo)
                filas = [fila for fila in lector]
        except OSError as error:
            raise IngestaError(f"No se pudo leer el archivo CSV: {error}") from error
        except UnicodeDecodeError as error:
            raise IngestaError(f"El archivo CSV no es texto valido (UTF-8): {error}") from error

        # Eliminar filas completamente vacias al final.
        filas = [fila for fila in filas if any(celda.strip() != "" for celda in fila)]
        if not filas:
            raise IngestaError("El archivo CSV esta vacio.")

        if len(filas[0]) < 2:
            raise IngestaError(
                "La primera fila debe contener el encabezado con los nombres de las tareas."
            )

        tareas = [celda.strip() for celda in filas[0][1:]]
        if any(tarea == "" for tarea in tareas):
            raise IngestaError("Hay nombres de tarea vacios en el encabezado.")
        if len(set(tareas)) != len(tareas):
            raise IngestaError("Los nombres de tarea no pueden repetirse.")

        agentes: List[str] = []
        valores: List[List[float]] = []

        for indice, fila in enumerate(filas[1:], start=2):
            if len(fila) != len(filas[0]):
                raise IngestaError(
                    f"La fila {indice} tiene {len(fila)} columnas, "
                    f"se esperaban {len(filas[0])}."
                )
            nombre_agente = fila[0].strip()
            if nombre_agente == "":
                raise IngestaError(f"Nombre de agente vacio en la fila {indice}.")
            if nombre_agente in agentes:
                raise IngestaError(f"Agente duplicado: {nombre_agente}.")
            agentes.append(nombre_agente)

            fila_valores: List[float] = []
            for columna, celda in enumerate(fila[1:], start=1):
                texto = celda.strip()
                try:
                    valor = float(texto)
                except ValueError as error:
                    raise IngestaError(
                        f"Valor no numerico en fila {indice}, columna {columna}: {celda!r}."
                    ) from error
                fila_valores.append(valor)
            valores.append(fila_valores)

        if not agentes:
            raise IngestaError("No se encontraron filas de agentes en el CSV.")

        matriz = Matriz(agentes, tareas, valores)
        try:
            matriz.validar()
        except ValueError as error:
            raise IngestaError(str(error)) from error
        return matriz

    # ------------------------------------------------------------------ #
    # JSON
    # ------------------------------------------------------------------ #
    @staticmethod
    def cargar_json(ruta: str) -> Matriz:
        """Carga una matriz desde un archivo JSON.

        Formato esperado:
            {
                "agentes": ["A1", "A2"],
                "tareas": ["T1", "T2"],
                "matriz": [[5, 9], [3, 6]],
                "objetivo_sugerido": "min"   (opcional)
            }
        """
        if not isinstance(ruta, str) or not ruta.strip():
            raise IngestaError("La ruta del archivo JSON no puede estar vacia.")
        if not os.path.isfile(ruta):
            raise IngestaError(f"El archivo no existe: {ruta}")
        if not ruta.lower().endswith(".json"):
            raise IngestaError("El archivo debe tener extension .json.")

        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except OSError as error:
            raise IngestaError(f"No se pudo leer el archivo JSON: {error}") from error
        except json.JSONDecodeError as error:
            raise IngestaError(f"JSON invalido: {error}") from error

        if not isinstance(datos, dict):
            raise IngestaError("El JSON debe contener un objeto (diccionario).")

        for clave in ("agentes", "tareas", "matriz"):
            if clave not in datos:
                raise IngestaError(f"Falta la clave obligatoria '{clave}' en el JSON.")

        agentes = datos["agentes"]
        tareas = datos["tareas"]
        matriz_valores = datos["matriz"]

        if not isinstance(agentes, list) or not all(isinstance(a, str) for a in agentes):
            raise IngestaError("'agentes' debe ser una lista de strings.")
        if not isinstance(tareas, list) or not all(isinstance(t, str) for t in tareas):
            raise IngestaError("'tareas' debe ser una lista de strings.")
        if not agentes:
            raise IngestaError("La lista 'agentes' no puede estar vacia.")
        if not tareas:
            raise IngestaError("La lista 'tareas' no puede estar vacia.")
        if len(set(agentes)) != len(agentes):
            raise IngestaError("Los nombres de agentes no pueden repetirse.")
        if len(set(tareas)) != len(tareas):
            raise IngestaError("Los nombres de tareas no pueden repetirse.")
        if not isinstance(matriz_valores, list):
            raise IngestaError("'matriz' debe ser una lista de filas.")

        valores: List[List[float]] = []
        for indice_fila, fila in enumerate(matriz_valores):
            if not isinstance(fila, list):
                raise IngestaError(f"La fila {indice_fila} de 'matriz' no es una lista.")
            fila_convertida: List[float] = []
            for indice_columna, valor in enumerate(fila):
                if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                    raise IngestaError(
                        f"Valor no numerico en matriz[{indice_fila}][{indice_columna}]: {valor!r}."
                    )
                fila_convertida.append(float(valor))
            valores.append(fila_convertida)

        matriz = Matriz(agentes, tareas, valores)
        try:
            matriz.validar()
        except ValueError as error:
            raise IngestaError(str(error)) from error
        return matriz

    # ------------------------------------------------------------------ #
    # Fallback
    # ------------------------------------------------------------------ #
    @staticmethod
    def matriz_por_defecto() -> Matriz:
        """Devuelve una matriz en memoria usada como fallback."""
        agentes = ["Conductor Norte", "Conductor Sur", "Conductor Este"]
        tareas = ["Ruta A", "Ruta B", "Ruta C"]
        valores = [
            [5, 9, 7],
            [3, 6, 8],
            [4, 2, 10],
        ]
        matriz = Matriz(agentes, tareas, valores)
        matriz.validar()
        return matriz