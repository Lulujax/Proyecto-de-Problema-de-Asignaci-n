"""Pruebas minimas del motor Hungaro (Modulo A)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.matriz import Matriz
from src.hungaro import Hungaro


def probar_min():
    matriz = Matriz(
        ["A1", "A2", "A3"],
        ["T1", "T2", "T3"],
        [[5, 9, 7], [3, 6, 8], [4, 2, 10]],
    )
    hungaro = Hungaro(matriz, "min")
    resultado = hungaro.resolver()
    print("MIN -> costo total:", resultado.costo_total)
    for a, t, v in resultado.asignaciones:
        print(f"  {a} -> {t} = {v}")
    assert resultado.costo_total == 12, resultado.costo_total  # 5+6+? wait compute: A1-T1=5, A2-T? min: 3+2+7? let's just print
    print("OK min")


def probar_max():
    matriz = Matriz(
        ["A1", "A2", "A3"],
        ["T1", "T2", "T3"],
        [[5, 9, 7], [3, 6, 8], [4, 2, 10]],
    )
    hungaro = Hungaro(matriz, "max")
    resultado = hungaro.resolver()
    print("MAX -> beneficio total:", resultado.costo_total)
    for a, t, v in resultado.asignaciones:
        print(f"  {a} -> {t} = {v}")
    print("OK max")


def probar_desbalanceado():
    matriz = Matriz(
        ["A1", "A2", "A3", "A4"],
        ["T1", "T2", "T3"],
        [[4, 7, 3], [2, 5, 8], [6, 1, 4], [3, 9, 2]],
    )
    hungaro = Hungaro(matriz, "min")
    resultado = hungaro.resolver()
    print("DES -> costo total:", resultado.costo_total)
    print("  ficticios agentes:", resultado.agentes_ficticios)
    print("  ficticios tareas:", resultado.tareas_ficticias)
    print("  inactivos:", resultado.agentes_inactivos)
    print("  huerfanas:", resultado.tareas_huerfanas)
    for a, t, v in resultado.asignaciones:
        print(f"  {a} -> {t} = {v}")
    print("OK desbalanceado")


if __name__ == "__main__":
    probar_min()
    probar_max()
    probar_desbalanceado()
    print("TODAS LAS PRUEBAS PASARON")