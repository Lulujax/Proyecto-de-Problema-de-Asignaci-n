# Optimizacion de Asignacion de Recursos mediante el Metodo Hungaro

Proyecto academico - Fase II  
Universidad Jose Antonio Paez - Ingenieria en Computacion  
Empresa ficticia: "Rutas y Suministros C.A."

## Descripcion

Sistema que asigna conductores (agentes) a rutas/vehiculos (tareas) de forma
optima, exactamente 1 a 1, minimizando costos o maximizando beneficio/eficiencia,
usando el **Metodo Hungaro implementado desde cero** (sin librerias de optimizacion).
Incluye auto-balanceo de matrices no cuadradas, visualizacion de grafo bipartito
y analisis ejecutivo generado por IA (Gemini).

## Requisitos

- Python 3.11 o superior (probado en 3.12).
- Dependencias listadas en `requirements.txt`.

## Instalacion

```bash
git clone <url-del-repositorio>
cd Proyecto-de-Problema-de-Asignacion
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

Configurar la clave de IA (opcional, solo para el modulo D):

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="tu_clave_aqui"
# o cree un archivo .env a partir de .env.example
```

## Ejecucion

```bash
python main.py
```

## Flujo de uso

1. **Cargar datos**: botones "Cargar CSV", "Cargar JSON" o "Matriz por defecto".
2. **Elegir objetivo**: Minimizar costo o Maximizar beneficio/eficiencia.
3. **Resolver**: ejecuta el Metodo Hungaro y muestra la matriz de asignacion + costo/beneficio total + pasos.
4. **Grafo**: genera y muestra el grafo bipartito (se guarda en `output/grafo_asignacion.png`).
5. **IA**: consulta a Gemini y muestra el analisis ejecutivo en pantalla.

## Formato de archivos de entrada

### CSV (con encabezados)

```
,Tarea_A,Tarea_B,Tarea_C
Agente_1,5,9,7
Agente_2,3,6,8
Agente_3,4,2,10
```

- Primera fila: celda vacia + nombres de tareas.
- Filas siguientes: nombre del agente + valores numericos.

### JSON

```json
{
  "agentes": ["Conductor A", "Conductor B", "Conductor C", "Conductor D"],
  "tareas": ["Ruta Norte", "Ruta Sur", "Ruta Este"],
  "matriz": [
    [4, 7, 3],
    [2, 5, 8],
    [6, 1, 4],
    [3, 9, 2]
  ],
  "objetivo_sugerido": "min"
}
```

Se incluyen archivos de ejemplo en `data/matriz_ejemplo.csv` y `data/matriz_ejemplo.json`.

## Estructura del proyecto

```
src/
  matriz.py        # Clase Matriz
  hungaro.py       # Clase Hungaro (algoritmo desde cero)
  ingesta.py       # Clase IngestaDatos
  grafo.py         # Clase GrafoBipartito
  cliente_ia.py    # Clases ProveedorIA / ProveedorGemini / ClienteIA
  gui.py           # Clase AplicacionGUI (Tkinter)
main.py
data/
tests/
output/
```

## Pruebas

```bash
python tests/test_hungaro.py
```

## Notas tecnicas

- El Metodo Hungaro se implementa con listas nativas de Python; no se usa
  `scipy`, `pulp` ni `ortools`.
- Las matrices no cuadradas se auto-balancean con filas/columnas ficticias de
  costo 0; los nodos ficticios se registran y se resaltan en el grafo.
- La maximizacion se transforma a minimizacion mediante `max_global - valor`
  y el resultado final reporta el beneficio real.
- La clave API nunca se hardcodea: se lee de `GEMINI_API_KEY` o del campo de la GUI.