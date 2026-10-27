"""Interfaz grafica moderna (Tkinter / Dark Mode) para la asignacion de recursos.

Diseno tipo dashboard con pestanas (Notebook) optimizado para presentacion:
  1. Datos: Carga de archivos, presets de demostracion rapida y matriz interactiva.
  2. Resolver: Tarjetas de metricas KPI, asignacion optima y pasos didacticos resaltados.
  3. Grafo: Visualizacion vectorial del grafo bipartito con paleta de alto contraste.
  4. IA: Analisis ejecutivo asincrono (multihilo) sin bloqueo de interfaz.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, List

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .matriz import Matriz
from .hungaro import Hungaro, ResultadoAsignacion
from .ingesta import IngestaDatos, IngestaError
from .grafo import GrafoBipartito
from .cliente_ia import ClienteIA, ProveedorGemini, ProveedorNvidia
from .pdf import GeneradorPDF


# ------------------------------------------------------------------ #
# Paleta de Colores - Dark Mode Dashboard
# ------------------------------------------------------------------ #
BG_APP = "#0f172a"          # Slate 900 (Fondo principal de la ventana)
BG_CARD = "#1e293b"         # Slate 800 (Fondo de tarjetas y paneles)
BG_CARD_LIGHT = "#334155"   # Slate 700 (Bordes y elementos secundarios)
TEXT_MAIN = "#f8fafc"       # Slate 50  (Texto primario)
TEXT_MUTED = "#94a3b8"      # Slate 400 (Texto secundario)
ACCENT_BLUE = "#3b82f6"     # Blue 500  (Accion principal)
ACCENT_BLUE_HOVER = "#2563eb"
ACCENT_GREEN = "#10b981"    # Emerald 500 (Exito / Optimo)
ACCENT_AMBER = "#f59e0b"    # Amber 500 (Advertencias / Ficticios)
ACCENT_RED = "#ef4444"      # Red 500   (Errores / Alertas)


class AplicacionGUI:
    """Ventana principal moderna de la aplicacion."""

    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        self.raiz.title("Sistema de Asignación de Recursos - Método Húngaro")
        self.raiz.geometry("1180x820")
        self.raiz.minsize(1020, 720)
        self.raiz.configure(bg=BG_APP)

        # Estado del modelo
        self.matriz_actual: Optional[Matriz] = None
        self.resultado_actual: Optional[ResultadoAsignacion] = None
        self.texto_ia_resultado: Optional[str] = None
        self.consultando_ia: bool = False

        # Variables reactivas
        self.objetivo_var = tk.StringVar(value="min")
        self.clave_api_var = tk.StringVar(value=os.getenv("GEMINI_API_KEY", ""))
        self.proveedor_var = tk.StringVar(value="Gemini")
        self.modelo_var = tk.StringVar(value="gemini-3.8-flash")
        self.pensamiento_var = tk.StringVar(value="LOW")
        self.clave_nvidia_var = tk.StringVar(value=os.getenv("NVIDIA_API_KEY", ""))
        self.archivo_actual_var = tk.StringVar(value="Ningún archivo cargado.")
        self.estado_var = tk.StringVar(value="Listo. Seleccione un caso de prueba o cargue un archivo.")

        # Variables de KPIs
        self.kpi_costo_var = tk.StringVar(value="--")
        self.kpi_estado_var = tk.StringVar(value="Sin Calcular")
        self.kpi_asignaciones_var = tk.StringVar(value="0 / 0")
        self.kpi_objetivo_var = tk.StringVar(value="Minimización de Costo")

        self._configurar_estilos()
        self._construir_interfaz()

        # Cargar preset por defecto de inicio
        self._cargar_preset(0)

    # ------------------------------------------------------------------ #
    # Configuracion de Estilos
    # ------------------------------------------------------------------ #
    def _configurar_estilos(self) -> None:
        self.estilo = ttk.Style()
        try:
            self.estilo.theme_use("clam")
        except tk.TclError:
            pass

        # Generales
        self.estilo.configure(".", background=BG_APP, foreground=TEXT_MAIN)
        self.estilo.configure("TFrame", background=BG_APP)
        self.estilo.configure("Card.TFrame", background=BG_CARD)
        self.estilo.configure("TLabel", background=BG_APP, foreground=TEXT_MAIN, font=("Segoe UI", 10))

        # Encabezados
        self.estilo.configure("HeroTitle.TLabel", background=BG_APP, foreground=TEXT_MAIN, font=("Segoe UI", 16, "bold"))
        self.estilo.configure("HeroSub.TLabel", background=BG_APP, foreground=TEXT_MUTED, font=("Segoe UI", 10))
        self.estilo.configure("CardTitle.TLabel", background=BG_CARD, foreground=TEXT_MAIN, font=("Segoe UI", 11, "bold"))
        self.estilo.configure("CardDesc.TLabel", background=BG_CARD, foreground=TEXT_MUTED, font=("Segoe UI", 9))

        # Tarjetas KPI
        self.estilo.configure("KPIValue.TLabel", background=BG_CARD, foreground=ACCENT_BLUE, font=("Segoe UI", 18, "bold"))
        self.estilo.configure("KPILabel.TLabel", background=BG_CARD, foreground=TEXT_MUTED, font=("Segoe UI", 9, "bold"))

        # Botones
        self.estilo.configure(
            "TButton",
            background=BG_CARD_LIGHT,
            foreground=TEXT_MAIN,
            borderwidth=0,
            focusthickness=0,
            padding=(12, 7),
            font=("Segoe UI", 9, "bold"),
        )
        self.estilo.map("TButton", background=[("active", "#475569"), ("disabled", "#1e293b")])

        self.estilo.configure(
            "Primary.TButton",
            background=ACCENT_BLUE,
            foreground="#ffffff",
            padding=(14, 8),
            font=("Segoe UI", 10, "bold"),
        )
        self.estilo.map("Primary.TButton", background=[("active", ACCENT_BLUE_HOVER), ("disabled", "#475569")])

        self.estilo.configure(
            "Success.TButton",
            background=ACCENT_GREEN,
            foreground="#ffffff",
            padding=(12, 7),
            font=("Segoe UI", 9, "bold"),
        )
        self.estilo.map("Success.TButton", background=[("active", "#059669")])

        # Radiobuttons & Checkbuttons
        self.estilo.configure("TRadiobutton", background=BG_CARD, foreground=TEXT_MAIN, font=("Segoe UI", 10))
        self.estilo.map("TRadiobutton", background=[("active", BG_CARD)])

        # LabelFrame
        self.estilo.configure(
            "TLabelframe",
            background=BG_CARD,
            bordercolor=BG_CARD_LIGHT,
            relief="solid",
            borderwidth=1,
            padding=10,
        )
        self.estilo.configure(
            "TLabelframe.Label",
            background=BG_CARD,
            foreground=TEXT_MAIN,
            font=("Segoe UI", 10, "bold"),
        )

        # Notebook (Pestanas)
        self.estilo.configure("TNotebook", background=BG_APP, borderwidth=0)
        self.estilo.configure(
            "TNotebook.Tab",
            background=BG_CARD,
            foreground=TEXT_MUTED,
            padding=(16, 8),
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        self.estilo.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT_BLUE), ("active", BG_CARD_LIGHT)],
            foreground=[("selected", "#ffffff"), ("active", TEXT_MAIN)],
        )

        # Treeview (Tablas)
        self.estilo.configure(
            "Treeview",
            background=BG_CARD,
            foreground=TEXT_MAIN,
            fieldbackground=BG_CARD,
            rowheight=28,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        self.estilo.configure(
            "Treeview.Heading",
            background="#0f172a",
            foreground=TEXT_MAIN,
            font=("Segoe UI", 9, "bold"),
            padding=(6, 6),
            borderwidth=1,
            relief="flat",
        )
        self.estilo.map("Treeview", background=[("selected", ACCENT_BLUE_HOVER)], foreground=[("selected", "#ffffff")])
        self.estilo.map("Treeview.Heading", background=[("active", "#1e293b")])

        # Comboboxes en Dark Mode (evita fondo blanco / gris desentonado)
        self.estilo.configure(
            "TCombobox",
            fieldbackground="#1e293b",
            background="#334155",
            foreground="#f8fafc",
            arrowcolor="#f8fafc",
            bordercolor="#475569",
            darkcolor="#1e293b",
            lightcolor="#334155",
            padding=5,
            font=("Segoe UI", 9),
        )
        self.estilo.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", "#1e293b"),
                ("active", "#223049"),
                ("focus", "#223049"),
                ("disabled", "#0f172a"),
            ],
            foreground=[
                ("readonly", "#f8fafc"),
                ("active", "#ffffff"),
                ("focus", "#ffffff"),
                ("disabled", "#64748b"),
            ],
            background=[
                ("active", ACCENT_BLUE),
                ("focus", ACCENT_BLUE),
            ],
            arrowcolor=[
                ("active", "#ffffff"),
            ],
        )

        # Campos de texto (Entry) en Dark Mode
        self.estilo.configure(
            "TEntry",
            fieldbackground="#0f172a",
            foreground="#f8fafc",
            insertcolor="#38bdf8",
            bordercolor="#475569",
            lightcolor="#334155",
            darkcolor="#0f172a",
            padding=6,
            font=("Segoe UI", 9),
        )
        self.estilo.map(
            "TEntry",
            fieldbackground=[
                ("focus", "#162032"),
                ("disabled", "#1e293b"),
            ],
            bordercolor=[
                ("focus", ACCENT_BLUE),
            ],
            foreground=[
                ("disabled", "#64748b"),
            ],
        )

        # Estilo para el menu desplegable de los Comboboxes
        self.raiz.option_add("*TCombobox*Listbox.background", "#1e293b")
        self.raiz.option_add("*TCombobox*Listbox.foreground", "#f8fafc")
        self.raiz.option_add("*TCombobox*Listbox.selectBackground", ACCENT_BLUE)
        self.raiz.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.raiz.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))

        # Scrollbars
        self.estilo.configure("Vertical.TScrollbar", background=BG_CARD_LIGHT, troughcolor=BG_CARD, borderwidth=0)
        self.estilo.configure("Horizontal.TScrollbar", background=BG_CARD_LIGHT, troughcolor=BG_CARD, borderwidth=0)

    # ------------------------------------------------------------------ #
    # Construccion Principal
    # ------------------------------------------------------------------ #
    def _construir_interfaz(self) -> None:
        contenedor = ttk.Frame(self.raiz, padding=(16, 12))
        contenedor.pack(fill="both", expand=True)

        # Cabecera Hero
        self._construir_cabecera(contenedor)

        # Notebook
        self.notebook = ttk.Notebook(contenedor)
        self.notebook.pack(fill="both", expand=True, pady=(6, 8))

        self.pestana_datos = ttk.Frame(self.notebook, padding=12)
        self.pestana_resolver = ttk.Frame(self.notebook, padding=12)
        self.pestana_grafo = ttk.Frame(self.notebook, padding=12)
        self.pestana_ia = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.pestana_datos, text="  1. Entrada de Datos  ")
        self.notebook.add(self.pestana_resolver, text="  2. Optimización y Pasos  ")
        self.notebook.add(self.pestana_grafo, text="  3. Grafo Bipartito  ")
        self.notebook.add(self.pestana_ia, text="  4. Análisis Ejecutivo (IA)  ")

        self._construir_pestana_datos()
        self._construir_pestana_resolver()
        self._construir_pestana_grafo()
        self._construir_pestana_ia()

        # Barra de estado inferior
        barra_estado = tk.Frame(contenedor, bg=BG_CARD, height=28, relief="flat", padx=10)
        barra_estado.pack(fill="x", pady=(4, 0))
        self.lbl_estado = tk.Label(
            barra_estado,
            textvariable=self.estado_var,
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_estado.pack(side="left", fill="x", expand=True, pady=4)

        # Indicador de modo
        tk.Label(
            barra_estado,
            text="Modo Presentación Activo  ●",
            bg=BG_CARD,
            fg=ACCENT_GREEN,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right", padx=6)

    def _construir_cabecera(self, padre: ttk.Frame) -> None:
        cabecera = tk.Frame(padre, bg=BG_APP)
        cabecera.pack(fill="x", pady=(0, 10))

        izq = tk.Frame(cabecera, bg=BG_APP)
        izq.pack(side="left", fill="y")
        ttk.Label(izq, text="SISTEMA DE ASIGNACIÓN DE RECURSOS", style="HeroTitle.TLabel").pack(anchor="w")
        ttk.Label(
            izq,
            text="Optimización de Rutas y Operaciones Logísticas mediante el Método Húngaro",
            style="HeroSub.TLabel",
        ).pack(anchor="w")

        der = tk.Frame(cabecera, bg=BG_APP)
        der.pack(side="right", fill="y")
        badge = tk.Frame(der, bg=BG_CARD, padx=12, pady=6, highlightbackground=BG_CARD_LIGHT, highlightthickness=1)
        badge.pack(side="top", anchor="e")
        tk.Label(badge, text="Caso de Estudio:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(anchor="e")
        tk.Label(badge, text="Rutas y Suministros C.A.", bg=BG_CARD, fg="#60a5fa", font=("Segoe UI", 10, "bold")).pack(anchor="e")

    # ------------------------------------------------------------------ #
    # Pestana 1: Datos y Presets
    # ------------------------------------------------------------------ #
    def _construir_pestana_datos(self) -> None:
        # Fila superior: Acciones y Casos de Demostracion
        panel_acciones = ttk.LabelFrame(self.pestana_datos, text="Carga de Datos y Casos Preconfigurados")
        panel_acciones.pack(fill="x", pady=(0, 10))

        fila_carga = tk.Frame(panel_acciones, bg=BG_CARD)
        fila_carga.pack(fill="x", pady=4)

        ttk.Button(fila_carga, text="Cargar archivo CSV", command=self._cargar_csv).pack(side="left", padx=(0, 6))
        ttk.Button(fila_carga, text="Cargar archivo JSON", command=self._cargar_json).pack(side="left", padx=6)

        # Separador visual
        tk.Frame(fila_carga, bg=BG_CARD_LIGHT, width=2, height=26).pack(side="left", padx=12)

        tk.Label(fila_carga, text="Cargar Ejemplo Rápido:", bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        self.combo_presets = ttk.Combobox(
            fila_carga,
            width=36,
            state="readonly",
            values=[
                "1. Distribución Valencia (4x4 Balanceado)",
                "2. Flota con Conductor Excedente (4x3 Desbalanceado)",
                "3. Rutas sin Cobertura (3x4 Desbalanceado)",
                "4. Maximización de Beneficios por Ruta (5x5)",
            ],
        )
        self.combo_presets.current(0)
        self.combo_presets.pack(side="left", padx=6)
        ttk.Button(fila_carga, text="Cargar Caso", style="Primary.TButton", command=self._aplicar_preset_seleccionado).pack(side="left", padx=6)

        # Info del archivo cargado
        fila_info = tk.Frame(panel_acciones, bg=BG_CARD)
        fila_info.pack(fill="x", pady=(8, 0))
        tk.Label(fila_info, text="Fuente actual:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(fila_info, textvariable=self.archivo_actual_var, bg=BG_CARD, fg="#38bdf8", font=("Segoe UI", 9)).pack(side="left", padx=6)

        # Matriz visualizada
        panel_matriz = ttk.LabelFrame(self.pestana_datos, text="Matriz de Costos / Beneficios Operativos")
        panel_matriz.pack(fill="both", expand=True, pady=6)

        contenedor_tabla = tk.Frame(panel_matriz, bg=BG_CARD)
        contenedor_tabla.pack(fill="both", expand=True, padx=4, pady=4)

        self.tabla_matriz = ttk.Treeview(contenedor_tabla, show="headings", height=9)
        self.tabla_matriz.tag_configure("par", background="#1e293b")
        self.tabla_matriz.tag_configure("impar", background="#162032")

        scroll_y = ttk.Scrollbar(contenedor_tabla, orient="vertical", command=self.tabla_matriz.yview)
        scroll_x = ttk.Scrollbar(contenedor_tabla, orient="horizontal", command=self.tabla_matriz.xview)
        self.tabla_matriz.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabla_matriz.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        contenedor_tabla.rowconfigure(0, weight=1)
        contenedor_tabla.columnconfigure(0, weight=1)

        # Objetivo del problema y boton resolver
        panel_inferior = tk.Frame(self.pestana_datos, bg=BG_APP)
        panel_inferior.pack(fill="x", pady=(8, 0))

        marco_objetivo = ttk.LabelFrame(panel_inferior, text="Objetivo de Optimización")
        marco_objetivo.pack(side="left", fill="x", expand=True, padx=(0, 8))

        r_min = ttk.Radiobutton(
            marco_objetivo,
            text="Minimizar Costo Operativo (Combustible / Distancia / Horas)",
            variable=self.objetivo_var,
            value="min",
            command=self._actualizar_objetivo_kpi,
        )
        r_min.pack(side="left", padx=14, pady=6)

        r_max = ttk.Radiobutton(
            marco_objetivo,
            text="Maximizar Beneficio / Eficiencia de Entregas",
            variable=self.objetivo_var,
            value="max",
            command=self._actualizar_objetivo_kpi,
        )
        r_max.pack(side="left", padx=14, pady=6)

        ttk.Button(
            panel_inferior,
            text="Resolver y Ver Asignación  →",
            style="Primary.TButton",
            command=lambda: [self._resolver(), self.notebook.select(1)],
        ).pack(side="right", padx=(8, 0), pady=12)

    # ------------------------------------------------------------------ #
    # Pestana 2: Resolver y Pasos
    # ------------------------------------------------------------------ #
    def _construir_pestana_resolver(self) -> None:
        # Tarjetas KPI superiores
        panel_kpis = tk.Frame(self.pestana_resolver, bg=BG_APP)
        panel_kpis.pack(fill="x", pady=(0, 10))

        self._crear_tarjeta_kpi(panel_kpis, "RESULTADO ÓPTIMO", self.kpi_costo_var, ACCENT_BLUE, 0)
        self._crear_tarjeta_kpi(panel_kpis, "BALANCE DE RECURSOS", self.kpi_estado_var, ACCENT_GREEN, 1)
        self._crear_tarjeta_kpi(panel_kpis, "ASIGNACIÓN EFECTIVA", self.kpi_asignaciones_var, "#38bdf8", 2)
        self._crear_tarjeta_kpi(panel_kpis, "FUNCIÓN OBJETIVO", self.kpi_objetivo_var, "#a855f7", 3)

        # Botonera de acciones
        barra_acciones = tk.Frame(self.pestana_resolver, bg=BG_APP)
        barra_acciones.pack(fill="x", pady=(0, 8))

        ttk.Button(barra_acciones, text="⚡ Re-ejecutar Método Húngaro", style="Primary.TButton", command=self._resolver).pack(side="left")
        ttk.Button(
            barra_acciones,
            text="Ver Grafo Bipartito  →",
            command=lambda: [self._mostrar_grafo(), self.notebook.select(2)],
        ).pack(side="right")

        # Contenedor dividido: Asignacion final (izq) y Pasos didacticos (der)
        contenedor_detalles = tk.Frame(self.pestana_resolver, bg=BG_APP)
        contenedor_detalles.pack(fill="both", expand=True)

        # Columna Izquierda: Tabla Asignacion
        marco_asig = ttk.LabelFrame(contenedor_detalles, text="Plan Óptimo de Asignación (1 a 1)")
        marco_asig.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.tabla_asignacion = ttk.Treeview(marco_asig, columns=("agente", "tarea", "valor"), show="headings", height=10)
        for col, txt, ancho in (("agente", "Conductor / Agente", 170), ("tarea", "Ruta / Tarea Asignada", 170), ("valor", "Costo/Beneficio", 110)):
            self.tabla_asignacion.heading(col, text=txt)
            self.tabla_asignacion.column(col, width=ancho, anchor="center")

        self.tabla_asignacion.tag_configure("normal", background="#1e293b", foreground=TEXT_MAIN)
        self.tabla_asignacion.tag_configure("ficticio", background="#2a1b24", foreground="#f43f5e")

        scroll_asig = ttk.Scrollbar(marco_asig, orient="vertical", command=self.tabla_asignacion.yview)
        self.tabla_asignacion.configure(yscrollcommand=scroll_asig.set)
        self.tabla_asignacion.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll_asig.pack(side="right", fill="y", pady=4)

        # Columna Derecha: Pasos Didacticos
        marco_pasos = ttk.LabelFrame(contenedor_detalles, text="Traza Didáctica del Algoritmo (Paso a Paso)")
        marco_pasos.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self.texto_pasos = tk.Text(
            marco_pasos,
            height=10,
            wrap="word",
            bg="#0f172a",
            fg=TEXT_MAIN,
            insertbackground="#38bdf8",
            relief="flat",
            font=("Consolas", 9),
            padx=8,
            pady=8,
        )
        self.texto_pasos.tag_configure("titulo", foreground="#38bdf8", font=("Consolas", 9, "bold"))
        self.texto_pasos.tag_configure("iteracion", foreground="#c084fc", font=("Consolas", 9, "bold"))
        self.texto_pasos.tag_configure("exito", foreground="#34d399", font=("Consolas", 9, "bold"))
        self.texto_pasos.tag_configure("alerta", foreground="#fbbf24", font=("Consolas", 9, "bold"))
        self.texto_pasos.tag_configure("normal", foreground="#e2e8f0")

        scroll_pasos = ttk.Scrollbar(marco_pasos, orient="vertical", command=self.texto_pasos.yview)
        self.texto_pasos.configure(yscrollcommand=scroll_pasos.set)
        self.texto_pasos.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll_pasos.pack(side="right", fill="y", pady=4)

    def _crear_tarjeta_kpi(self, padre: tk.Frame, etiqueta: str, variable: tk.StringVar, color_acento: str, columna: int) -> None:
        tarjeta = tk.Frame(padre, bg=BG_CARD, padx=14, pady=10, highlightbackground=BG_CARD_LIGHT, highlightthickness=1)
        tarjeta.pack(side="left", fill="both", expand=True, padx=4)

        tk.Label(tarjeta, text=etiqueta, bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        lbl_valor = tk.Label(tarjeta, textvariable=variable, bg=BG_CARD, fg=color_acento, font=("Segoe UI", 16, "bold"))
        lbl_valor.pack(anchor="w", pady=(2, 0))

    # ------------------------------------------------------------------ #
    # Pestana 3: Grafo Bipartito
    # ------------------------------------------------------------------ #
    def _construir_pestana_grafo(self) -> None:
        barra_grafo = tk.Frame(self.pestana_grafo, bg=BG_APP)
        barra_grafo.pack(fill="x", pady=(0, 8))

        ttk.Button(barra_grafo, text="🔄 Actualizar Grafo", style="Primary.TButton", command=self._mostrar_grafo).pack(side="left")
        self.etiqueta_grafo = tk.Label(barra_grafo, text="Grafo pendiente por generar.", bg=BG_APP, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.etiqueta_grafo.pack(side="left", padx=14)

        ttk.Button(barra_grafo, text="📄 Exportar Reporte Ejecutivo a PDF", style="Success.TButton", command=self._exportar_pdf).pack(side="right")
        ttk.Button(barra_grafo, text="Ir a IA  →", command=lambda: self.notebook.select(3)).pack(side="right", padx=6)

        self.marco_canvas = ttk.LabelFrame(self.pestana_grafo, text="Visualización Gráfica Bipartita (Conductores vs Rutas)")
        self.marco_canvas.pack(fill="both", expand=True, pady=4)

        self.canvas_grafo = None
        self.toolbar_grafo = None
        self.figura_actual = None

    # ------------------------------------------------------------------ #
    # Pestana 4: Inteligencia Artificial
    # ------------------------------------------------------------------ #
    def _construir_pestana_ia(self) -> None:
        panel_config = ttk.LabelFrame(self.pestana_ia, text="Configuración del Asistente Ejecutivo")
        panel_config.pack(fill="x", pady=(0, 8))

        fila1 = tk.Frame(panel_config, bg=BG_CARD)
        fila1.pack(fill="x", pady=4)

        tk.Label(fila1, text="Proveedor:", bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.combo_proveedor = ttk.Combobox(
            fila1, textvariable=self.proveedor_var, width=12, state="readonly", values=["Gemini", "Nvidia"]
        )
        self.combo_proveedor.pack(side="left", padx=6)
        self.combo_proveedor.bind("<<ComboboxSelected>>", lambda e: self._actualizar_vista_proveedor())

        tk.Label(fila1, text="Modelo:", bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(14, 0))
        self.combo_modelo = ttk.Combobox(
            fila1,
            textvariable=self.modelo_var,
            width=28,
            state="readonly",
            values=["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"],
        )
        self.combo_modelo.pack(side="left", padx=6)

        # Marco para Nivel de Pensamiento (relevante para modelos Gemini)
        self.marco_pensamiento = tk.Frame(fila1, bg=BG_CARD)
        self.marco_pensamiento.pack(side="left", padx=(14, 0))
        tk.Label(self.marco_pensamiento, text="Nivel de Pensamiento:", bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.combo_pensamiento = ttk.Combobox(
            self.marco_pensamiento, textvariable=self.pensamiento_var, width=10, state="readonly", values=["LOW", "MEDIUM", "HIGH"]
        )
        self.combo_pensamiento.pack(side="left", padx=6)

        # Claves API Dinamicas (Muestra unicamente la clave del proveedor seleccionado)
        self.marco_clave_dinamica = tk.Frame(panel_config, bg=BG_CARD)
        self.marco_clave_dinamica.pack(fill="x", pady=(8, 4))

        # Fila exclusiva Gemini
        self.fila_clave_gemini = tk.Frame(self.marco_clave_dinamica, bg=BG_CARD)
        tk.Label(self.fila_clave_gemini, text="API Key Gemini:", bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.entrada_clave = ttk.Entry(self.fila_clave_gemini, textvariable=self.clave_api_var, show="*", width=38)
        self.entrada_clave.pack(side="left", padx=8)
        ttk.Button(self.fila_clave_gemini, text="Mostrar/Ocultar", command=self._alternar_visibilidad_clave).pack(side="left", padx=4)
        tk.Label(
            self.fila_clave_gemini,
            text="💡 Opcional: Se lee de la variable GEMINI_API_KEY o del archivo .env",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        ).pack(side="left", padx=10)

        # Fila exclusiva NVIDIA
        self.fila_clave_nvidia = tk.Frame(self.marco_clave_dinamica, bg=BG_CARD)
        tk.Label(self.fila_clave_nvidia, text="API Key NVIDIA NIM:", bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.entrada_clave_nvidia = ttk.Entry(self.fila_clave_nvidia, textvariable=self.clave_nvidia_var, show="*", width=38)
        self.entrada_clave_nvidia.pack(side="left", padx=8)
        ttk.Button(self.fila_clave_nvidia, text="Mostrar/Ocultar", command=self._alternar_visibilidad_clave).pack(side="left", padx=4)
        tk.Label(
            self.fila_clave_nvidia,
            text="💡 Opcional: Inicia con 'nvapi-...'. Se lee de la variable NVIDIA_API_KEY",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        ).pack(side="left", padx=10)

        # Inicializar el proveedor activo
        self._actualizar_vista_proveedor()

        # Boton y barra de progreso
        fila_ejecutar = tk.Frame(self.pestana_ia, bg=BG_APP)
        fila_ejecutar.pack(fill="x", pady=(4, 6))

        self.btn_consultar_ia = ttk.Button(
            fila_ejecutar,
            text="✨ Generar Dictamen Estratégico con IA",
            style="Primary.TButton",
            command=self._consultar_ia,
        )
        self.btn_consultar_ia.pack(side="left")

        self.lbl_ia_status = tk.Label(
            fila_ejecutar,
            text="Listo para analizar la solución óptima.",
            bg=BG_APP,
            fg=TEXT_MUTED,
            font=("Segoe UI", 9),
        )
        self.lbl_ia_status.pack(side="left", padx=14)

        self.barra_progreso = ttk.Progressbar(self.pestana_ia, mode="indeterminate")
        self.barra_progreso.pack(fill="x", pady=(0, 6))

        # Cuadro de resultado de IA
        marco_resultado = ttk.LabelFrame(self.pestana_ia, text="Dictamen Ejecutivo y Recomendaciones de Operación")
        marco_resultado.pack(fill="both", expand=True, pady=4)

        self.texto_ia = tk.Text(
            marco_resultado,
            height=12,
            wrap="word",
            bg="#0f172a",
            fg=TEXT_MAIN,
            insertbackground="#38bdf8",
            relief="flat",
            font=("Segoe UI", 11),
            padx=12,
            pady=12,
        )
        scroll_ia = ttk.Scrollbar(marco_resultado, command=self.texto_ia.yview)
        self.texto_ia.configure(yscrollcommand=scroll_ia.set)
        self.texto_ia.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll_ia.pack(side="right", fill="y", pady=4)

    # ------------------------------------------------------------------ #
    # Presets para la Feria
    # ------------------------------------------------------------------ #
    def _obtener_presets(self) -> List[tuple[str, Matriz, str]]:
        """Retorna casos de prueba listos para demostracion en vivo."""
        casos = [
            (
                "Distribución Valencia (4x4 Balanceado)",
                Matriz(
                    agentes=["Conductor 1", "Conductor 2", "Conductor 3", "Conductor 4"],
                    tareas=["Ruta Norte", "Ruta Sur", "Ruta Este", "Ruta Oeste"],
                    valores=[
                        [12.0, 9.0, 15.0, 8.0],
                        [10.0, 14.0, 7.0, 11.0],
                        [8.0, 6.0, 12.0, 9.0],
                        [13.0, 11.0, 10.0, 14.0],
                    ],
                ),
                "min",
            ),
            (
                "Flota con Conductor Excedente (4x3 Desbalanceado)",
                Matriz(
                    agentes=["Conductor A", "Conductor B", "Conductor C", "Conductor D"],
                    tareas=["Ruta Expresa 1", "Ruta Expresa 2", "Ruta Expresa 3"],
                    valores=[
                        [4.0, 7.0, 3.0],
                        [2.0, 5.0, 8.0],
                        [6.0, 1.0, 4.0],
                        [3.0, 9.0, 2.0],
                    ],
                ),
                "min",
            ),
            (
                "Rutas sin Cobertura (3x4 Desbalanceado)",
                Matriz(
                    agentes=["Conductor Alfa", "Conductor Beta", "Conductor Gamma"],
                    tareas=["Zona Industrial", "Zona Norte", "Centro Urbano", "Eje Costero"],
                    valores=[
                        [15.0, 20.0, 18.0, 25.0],
                        [22.0, 16.0, 14.0, 19.0],
                        [18.0, 24.0, 20.0, 15.0],
                    ],
                ),
                "min",
            ),
            (
                "Maximización de Beneficios por Ruta (5x5)",
                Matriz(
                    agentes=["Unidad 101", "Unidad 102", "Unidad 103", "Unidad 104", "Unidad 105"],
                    tareas=["Contrato A", "Contrato B", "Contrato C", "Contrato D", "Contrato E"],
                    valores=[
                        [45.0, 60.0, 50.0, 70.0, 55.0],
                        [50.0, 65.0, 75.0, 60.0, 80.0],
                        [70.0, 55.0, 60.0, 85.0, 65.0],
                        [60.0, 70.0, 80.0, 75.0, 90.0],
                        [55.0, 80.0, 65.0, 70.0, 75.0],
                    ],
                ),
                "max",
            ),
        ]
        return casos

    def _cargar_preset(self, indice: int) -> None:
        casos = self._obtener_presets()
        if 0 <= indice < len(casos):
            nombre, matriz, obj = casos[indice]
            self.objetivo_var.set(obj)
            self._actualizar_objetivo_kpi()
            self._establecer_matriz(matriz, f"Caso Demo: {nombre}")

    def _aplicar_preset_seleccionado(self) -> None:
        indice = self.combo_presets.current()
        self._cargar_preset(indice)

    def _actualizar_objetivo_kpi(self) -> None:
        if self.objetivo_var.get() == "min":
            self.kpi_objetivo_var.set("Minimización de Costo")
        else:
            self.kpi_objetivo_var.set("Maximización de Beneficio")

    # ------------------------------------------------------------------ #
    # Carga de Datos Externa
    # ------------------------------------------------------------------ #
    def _cargar_csv(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo CSV", filetypes=[("Archivos CSV", "*.csv"), ("Todos", "*.*")]
        )
        if not ruta:
            return
        try:
            matriz = IngestaDatos.cargar_csv(ruta)
        except IngestaError as error:
            messagebox.showerror("Error de Ingesta", str(error))
            self._set_estado(f"Error CSV: {error}", ACCENT_RED)
            return
        except Exception as error:
            messagebox.showerror("Error Inesperado", str(error))
            return
        self._establecer_matriz(matriz, f"CSV: {os.path.basename(ruta)}")

    def _cargar_json(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo JSON", filetypes=[("Archivos JSON", "*.json"), ("Todos", "*.*")]
        )
        if not ruta:
            return
        try:
            matriz = IngestaDatos.cargar_json(ruta)
        except IngestaError as error:
            messagebox.showerror("Error de Ingesta", str(error))
            self._set_estado(f"Error JSON: {error}", ACCENT_RED)
            return
        except Exception as error:
            messagebox.showerror("Error Inesperado", str(error))
            return
        self._establecer_matriz(matriz, f"JSON: {os.path.basename(ruta)}")

    def _establecer_matriz(self, matriz: Matriz, mensaje: str) -> None:
        self.matriz_actual = matriz
        self.resultado_actual = None
        self.texto_ia_resultado = None

        self._mostrar_matriz(matriz)
        n_filas, n_cols = matriz.dimensiones()
        self.archivo_actual_var.set(f"{mensaje}  |  Dimensiones: {n_filas} conductores × {n_cols} rutas")

        # Reset KPIs
        self.kpi_costo_var.set("--")
        self.kpi_estado_var.set("Listo p/ Resolver")
        self.kpi_asignaciones_var.set(f"0 / {max(n_filas, n_cols)}")

        self._limpiar_treeview(self.tabla_asignacion)
        self.texto_pasos.delete("1.0", "end")
        self.texto_ia.delete("1.0", "end")
        self._limpiar_grafo()
        self._set_estado("Datos cargados correctamente. Presione 'Resolver' para calcular la asignación óptima.", ACCENT_GREEN)

    def _mostrar_matriz(self, matriz: Matriz) -> None:
        self._limpiar_treeview(self.tabla_matriz)
        columnas = ["Conductor"] + matriz.tareas
        self.tabla_matriz["columns"] = columnas
        for col in columnas:
            self.tabla_matriz.heading(col, text=col)
            ancho = 140 if col == "Conductor" else 115
            self.tabla_matriz.column(col, width=ancho, anchor="center")

        for idx, (agente, fila) in enumerate(zip(matriz.agentes, matriz.valores)):
            tag = "par" if idx % 2 == 0 else "impar"
            valores_formateados = [agente] + [self._formatear(v) for v in fila]
            self.tabla_matriz.insert("", "end", values=valores_formateados, tags=(tag,))

    # ------------------------------------------------------------------ #
    # Logica de Resolucion (Metodo Hungaro)
    # ------------------------------------------------------------------ #
    def _resolver(self) -> None:
        if self.matriz_actual is None:
            messagebox.showwarning("Sin Datos", "Cargue una matriz o seleccione un caso de prueba antes de resolver.")
            self._set_estado("Debe cargar una matriz primero.", ACCENT_AMBER)
            return

        objetivo = self.objetivo_var.get()
        try:
            hungaro = Hungaro(self.matriz_actual, objetivo)
            resultado = hungaro.resolver()
        except Exception as error:
            messagebox.showerror("Error al Resolver", str(error))
            self._set_estado(f"Error al resolver: {error}", ACCENT_RED)
            return

        self.resultado_actual = resultado

        # Llenar tabla de asignacion
        self._limpiar_treeview(self.tabla_asignacion)
        ficticios_set = set(resultado.agentes_ficticios) | set(resultado.tareas_ficticias)

        for agente, tarea, valor in resultado.asignaciones:
            es_ficticio = (agente in ficticios_set or tarea in ficticios_set)
            tag = "ficticio" if es_ficticio else "normal"
            tarea_label = f"{tarea} (Ficticio)" if es_ficticio else tarea
            self.tabla_asignacion.insert("", "end", values=(agente, tarea_label, self._formatear(valor)), tags=(tag,))

        # Actualizar KPIs
        simbolo = "$" if objetivo == "min" else "Pts "
        self.kpi_costo_var.set(f"{simbolo}{self._formatear(resultado.costo_total)}")
        total_asignaciones = len(resultado.asignaciones)
        self.kpi_asignaciones_var.set(f"{total_asignaciones} / {total_asignaciones}")

        if resultado.hubo_ficticios:
            self.kpi_estado_var.set("⚠ Nodos Ficticios")
        else:
            self.kpi_estado_var.set("✔ Balanceado 100%")

        # Rellenar pasos didacticos con colores
        self.texto_pasos.delete("1.0", "end")
        for paso in resultado.pasos:
            if paso.startswith("==="):
                self.texto_pasos.insert("end", paso + "\n", "titulo")
            elif paso.startswith("---"):
                self.texto_pasos.insert("end", paso + "\n", "iteracion")
            elif "optima" in paso.lower() or "costo total" in paso.lower():
                self.texto_pasos.insert("end", paso + "\n", "exito")
            elif "ficticio" in paso.lower():
                self.texto_pasos.insert("end", paso + "\n", "alerta")
            else:
                self.texto_pasos.insert("end", paso + "\n", "normal")

        # Auto-generar grafo en segundo plano para que ya este listo al abrir pestaña 3
        try:
            grafo = GrafoBipartito(self.resultado_actual)
            self.figura_actual = grafo.crear_figura(tema="dark")
        except Exception:
            pass

        self._set_estado("Problema resuelto exitosamente mediante el Método Húngaro.", ACCENT_GREEN)

    # ------------------------------------------------------------------ #
    # Visualizacion de Grafo
    # ------------------------------------------------------------------ #
    def _mostrar_grafo(self) -> None:
        if self.resultado_actual is None:
            messagebox.showwarning("Sin Resultado", "Ejecute la resolución del problema antes de generar el grafo.")
            self._set_estado("Debe resolver primero.", ACCENT_AMBER)
            return

        try:
            grafo = GrafoBipartito(self.resultado_actual)
            figura = grafo.crear_figura(tema="dark")
        except Exception as error:
            messagebox.showerror("Error al Generar Grafo", str(error))
            self._set_estado(f"Error en grafo: {error}", ACCENT_RED)
            return

        self.figura_actual = figura
        ruta_salida = os.path.join("output", "grafo_asignacion.png")
        os.makedirs("output", exist_ok=True)
        try:
            figura.savefig(ruta_salida, dpi=130, bbox_inches="tight", facecolor=figura.get_facecolor())
        except Exception as error:
            self._set_estado(f"Aviso: No se pudo escribir png en disco: {error}", ACCENT_AMBER)

        self._dibujar_canvas(figura)
        self.etiqueta_grafo.config(text="✔ Grafo bipartito sincronizado con la solución óptima.", fg=ACCENT_GREEN)
        self._set_estado("Grafo bipartito renderizado correctamente.", ACCENT_GREEN)

    def _dibujar_canvas(self, figura) -> None:
        if self.canvas_grafo is not None:
            self.canvas_grafo.get_tk_widget().destroy()
            self.canvas_grafo = None
        if self.toolbar_grafo is not None:
            self.toolbar_grafo.destroy()
            self.toolbar_grafo = None

        self.canvas_grafo = FigureCanvasTkAgg(figura, master=self.marco_canvas)
        self.canvas_grafo.draw()
        widget = self.canvas_grafo.get_tk_widget()
        widget.configure(bg=BG_CARD)
        widget.pack(fill="both", expand=True)

        self.toolbar_grafo = NavigationToolbar2Tk(self.canvas_grafo, self.marco_canvas, pack_toolbar=False)
        self.toolbar_grafo.configure(bg=BG_CARD)
        for item in self.toolbar_grafo.winfo_children():
            try:
                item.configure(bg=BG_CARD)
            except Exception:
                pass
        self.toolbar_grafo.update()
        self.toolbar_grafo.pack(fill="x")

    def _limpiar_grafo(self) -> None:
        if self.canvas_grafo is not None:
            self.canvas_grafo.get_tk_widget().destroy()
            self.canvas_grafo = None
        if self.toolbar_grafo is not None:
            self.toolbar_grafo.destroy()
            self.toolbar_grafo = None
        self.etiqueta_grafo.config(text="Grafo pendiente por generar.", fg=TEXT_MUTED)

    # ------------------------------------------------------------------ #
    # Exportacion de Reporte en PDF (100% Vectorial, Sin Parpadeo)
    # ------------------------------------------------------------------ #
    def _exportar_pdf(self) -> None:
        if self.resultado_actual is None or self.matriz_actual is None:
            messagebox.showwarning("Sin Resultado", "Resuelva el problema antes de exportar el reporte a PDF.")
            return

        ruta = os.path.join("output", "reporte_asignacion.pdf")
        os.makedirs("output", exist_ok=True)

        # Generar figura en tema claro para que en PDF / impresion quede impecable
        try:
            grafo_pdf = GrafoBipartito(self.resultado_actual)
            figura_pdf = grafo_pdf.crear_figura(tema="light")
        except Exception:
            figura_pdf = self.figura_actual

        try:
            generador = GeneradorPDF(ruta)
            generador.generar(
                matriz=self.matriz_actual,
                resultado=self.resultado_actual,
                figura_grafo=figura_pdf,
                texto_ia=self.texto_ia_resultado,
            )
        except Exception as error:
            messagebox.showerror("Error al Generar PDF", str(error))
            self._set_estado(f"Error PDF: {error}", ACCENT_RED)
            return

        self._set_estado(f"PDF exportado con éxito: {ruta}", ACCENT_GREEN)
        
        # Abrir el PDF automaticamente en Windows si el usuario lo desea
        respuesta = messagebox.askyesno(
            "Reporte PDF Generado",
            f"El reporte técnico se generó exitosamente en:\n{ruta}\n\n¿Desea abrir el archivo ahora?",
        )
        if respuesta:
            try:
                os.startfile(ruta)
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    # Inteligencia Artificial Asincrona (Multihilo)
    # ------------------------------------------------------------------ #
    def _alternar_visibilidad_clave(self) -> None:
        proveedor = self.proveedor_var.get()
        entrada = self.entrada_clave_nvidia if proveedor == "Nvidia" else self.entrada_clave
        actual = entrada.cget("show")
        nuevo = "" if actual == "*" else "*"
        entrada.config(show=nuevo)

    def _actualizar_vista_proveedor(self) -> None:
        proveedor = self.proveedor_var.get()
        if proveedor == "Nvidia":
            modelos = ["nvidia/nemotron-3-ultra-550b-a55b", "nvidia/nemotron-3.5-lightning-30b-a3b"]
            if self.modelo_var.get() not in modelos:
                self.modelo_var.set(modelos[0])
            self.combo_modelo["values"] = modelos

            # Ocultar Gemini, mostrar solo NVIDIA
            self.fila_clave_gemini.pack_forget()
            self.fila_clave_nvidia.pack(fill="x")

            # Ocultar selector de pensamiento (no aplica a Nvidia)
            self.marco_pensamiento.pack_forget()
        else:
            modelos = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
            if self.modelo_var.get() not in modelos:
                self.modelo_var.set(modelos[0])
            self.combo_modelo["values"] = modelos

            # Ocultar NVIDIA, mostrar solo Gemini
            self.fila_clave_nvidia.pack_forget()
            self.fila_clave_gemini.pack(fill="x")

            # Mostrar selector de pensamiento
            self.marco_pensamiento.pack(side="left", padx=(14, 0))

    def _actualizar_modelos_por_proveedor(self) -> None:
        self._actualizar_vista_proveedor()

    def _consultar_ia(self) -> None:
        if self.consultando_ia:
            return

        if self.resultado_actual is None or self.matriz_actual is None:
            messagebox.showwarning("Sin Resultado", "Debe resolver el problema antes de solicitar el análisis de IA.")
            self._set_estado("Debe resolver primero.", ACCENT_AMBER)
            return

        proveedor_nombre = self.proveedor_var.get()
        modelo = self.modelo_var.get().strip()

        if proveedor_nombre == "Nvidia":
            clave = self.clave_nvidia_var.get().strip()
            if clave and ("\n" in clave or "\r" in clave or len(clave) > 200 or not clave.startswith("nvapi-")):
                messagebox.showerror("Clave Inválida", "La clave de NVIDIA parece incorrecta (debe iniciar con 'nvapi-').")
                self._set_estado("Clave NVIDIA inválida.", ACCENT_RED)
                return
            proveedor = ProveedorNvidia(api_key=clave if clave else None, modelo=modelo or "nvidia/nemotron-3-ultra-550b-a55b")
        else:
            clave = self.clave_api_var.get().strip()
            if clave and ("\n" in clave or "\r" in clave or len(clave) > 200):
                messagebox.showerror("Clave Inválida", "La clave de Gemini no debe contener saltos de línea.")
                self._set_estado("Clave Gemini inválida.", ACCENT_RED)
                return
            proveedor = ProveedorGemini(
                api_key=clave if clave else None,
                modelo=modelo or "gemini-3.8-flash",
                nivel_pensamiento=self.pensamiento_var.get().strip() or "LOW",
            )

        cliente = ClienteIA(proveedor=proveedor)
        objetivo = self.objetivo_var.get()

        # Activar estado de carga sin bloquear la interfaz
        self.consultando_ia = True
        self.btn_consultar_ia.configure(state="disabled")
        self.lbl_ia_status.config(text="Analizando solución con IA en segundo plano...", fg="#38bdf8")
        self.barra_progreso.start(10)
        self.texto_ia.delete("1.0", "end")
        self.texto_ia.insert("end", "Conectando con el asistente de Inteligencia Artificial...\nPor favor espere unos momentos.")
        self._set_estado("Consultando IA (asíncrono)...", "#38bdf8")

        def _hilo_consulta():
            try:
                ok, texto = cliente.consultar(self.matriz_actual, objetivo, self.resultado_actual)
            except Exception as exc:
                ok, texto = False, f"Excepción durante la consulta: {exc}"
            self.raiz.after(0, lambda: self._finalizar_consulta_ia(ok, texto))

        hilo = threading.Thread(target=_hilo_consulta, daemon=True)
        hilo.start()

    def _finalizar_consulta_ia(self, ok: bool, texto: str) -> None:
        self.consultando_ia = False
        self.barra_progreso.stop()
        self.btn_consultar_ia.configure(state="normal")
        self.texto_ia.delete("1.0", "end")

        if ok:
            self.texto_ia.insert("end", texto)
            self.texto_ia_resultado = texto
            self.lbl_ia_status.config(text="✔ Análisis ejecutivo generado con éxito.", fg=ACCENT_GREEN)
            self._set_estado("Dictamen de IA recibido correctamente.", ACCENT_GREEN)
        else:
            self.texto_ia.insert("end", f"[Error en Consulta de IA]\n\n{texto}\n\nNota: Puede revisar su conexión a internet o verificar la API Key ingresada.")
            self.lbl_ia_status.config(text="⚠ Ocurrió un error al contactar al proveedor de IA.", fg=ACCENT_RED)
            self._set_estado(f"Error IA: {texto[:60]}...", ACCENT_RED)

    # ------------------------------------------------------------------ #
    # Utilidades
    # ------------------------------------------------------------------ #
    @staticmethod
    def _formatear(valor) -> str:
        if isinstance(valor, float):
            if valor == int(valor) and abs(valor) < 1e15:
                return str(int(valor))
            return f"{valor:g}"
        return str(valor)

    @staticmethod
    def _limpiar_treeview(tabla: ttk.Treeview) -> None:
        for item in tabla.get_children():
            tabla.delete(item)

    def _set_estado(self, mensaje: str, color: str = TEXT_MAIN) -> None:
        self.estado_var.set(mensaje)
        try:
            self.lbl_estado.config(fg=color)
        except Exception:
            pass


def iniciar_aplicacion() -> None:
    raiz = tk.Tk()
    AplicacionGUI(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    iniciar_aplicacion()
