"""Interfaz grafica (Tkinter) que integra todos los modulos del proyecto.

Diseno con pestanas (Notebook) para un flujo claro: Datos -> Resolver -> Grafo -> IA.
Incluye barra de estado, barra de herramientas del grafo y feedback visual.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .matriz import Matriz
from .hungaro import Hungaro, ResultadoAsignacion
from .ingesta import IngestaDatos, IngestaError
from .grafo import GrafoBipartito
from .cliente_ia import ClienteIA, ProveedorGemini, ProveedorNvidia
from .pdf import GeneradorPDF


# Paleta y estilos compartidos.
COLOR_PRIMARIO = "#1f6feb"
COLOR_EXITO = "#2ea043"
COLOR_ALERTA = "#d29922"
COLOR_ERROR = "#f85149"


class AplicacionGUI:
    """Ventana principal de la aplicacion."""

    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        self.raiz.title("Optimizacion de Asignacion - Metodo Hungaro (Fase II)")
        self.raiz.geometry("1120x780")
        self.raiz.minsize(960, 680)

        self.matriz_actual: Optional[Matriz] = None
        self.resultado_actual: Optional[ResultadoAsignacion] = None
        self.texto_ia_resultado: Optional[str] = None
        self.objetivo_var = tk.StringVar(value="min")
        self.clave_api_var = tk.StringVar(value=os.getenv("GEMINI_API_KEY", ""))
        self.proveedor_var = tk.StringVar(value="Gemini")
        self.modelo_var = tk.StringVar(value="gemini-3.8-flash")
        self.pensamiento_var = tk.StringVar(value="LOW")
        self.clave_nvidia_var = tk.StringVar(value=os.getenv("NVIDIA_API_KEY", ""))
        self.archivo_actual_var = tk.StringVar(value="Ningun archivo cargado.")
        self.estado_var = tk.StringVar(value="Listo. Cargue una matriz para comenzar.")

        self._configurar_estilos()
        self._construir_interfaz()

    # ------------------------------------------------------------------ #
    # Estilos
    # ------------------------------------------------------------------ #
    def _configurar_estilos(self) -> None:
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("TButton", padding=6, font=("Segoe UI", 10))
        estilo.configure("Primario.TButton", background=COLOR_PRIMARIO, foreground="white",
                        padding=8, font=("Segoe UI", 10, "bold"))
        estilo.map("Primario.TButton", background=[("active", "#388bfd")])
        estilo.configure("TLabel", font=("Segoe UI", 10))
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 12, "bold"))
        estilo.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        estilo.configure("TNotebook.Tab", padding=(12, 6), font=("Segoe UI", 10, "bold"))

    # ------------------------------------------------------------------ #
    # Interfaz
    # ------------------------------------------------------------------ #
    def _construir_interfaz(self) -> None:
        contenedor = ttk.Frame(self.raiz, padding=10)
        contenedor.pack(fill="both", expand=True)

        # Cabecera
        cabecera = ttk.Frame(contenedor)
        cabecera.pack(fill="x", pady=(0, 8))
        ttk.Label(cabecera, text="Optimizacion de Asignacion de Recursos", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(cabecera, text="Metodo Hungaro con soporte dinamico y analisis de IA - Rutas y Suministros C.A.",
                 foreground="#57606a").pack(anchor="w")

        # Notebook principal
        self.notebook = ttk.Notebook(contenedor)
        self.notebook.pack(fill="both", expand=True)

        self.pestana_datos = ttk.Frame(self.notebook, padding=10)
        self.pestana_resolver = ttk.Frame(self.notebook, padding=10)
        self.pestana_grafo = ttk.Frame(self.notebook, padding=10)
        self.pestana_ia = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.pestana_datos, text="1. Datos")
        self.notebook.add(self.pestana_resolver, text="2. Resolver")
        self.notebook.add(self.pestana_grafo, text="3. Grafo")
        self.notebook.add(self.pestana_ia, text="4. IA")

        self._construir_pestana_datos()
        self._construir_pestana_resolver()
        self._construir_pestana_grafo()
        self._construir_pestana_ia()

        # Barra de estado
        barra_estado = ttk.Frame(contenedor, relief="sunken")
        barra_estado.pack(fill="x", pady=(8, 0))
        ttk.Label(barra_estado, textvariable=self.estado_var, anchor="w").pack(fill="x", padx=6, pady=2)

    # ------------------------------------------------------------------ #
    # Pestana: Datos
    # ------------------------------------------------------------------ #
    def _construir_pestana_datos(self) -> None:
        marco = ttk.LabelFrame(self.pestana_datos, text="Carga de datos", padding=10)
        marco.pack(fill="x", pady=5)

        fila_botones = ttk.Frame(marco)
        fila_botones.pack(fill="x")
        ttk.Button(fila_botones, text="Cargar CSV", command=self._cargar_csv).pack(side="left", padx=4)
        ttk.Button(fila_botones, text="Cargar JSON", command=self._cargar_json).pack(side="left", padx=4)
        ttk.Button(fila_botones, text="Matriz por defecto", command=self._cargar_por_defecto,
                   style="Primario.TButton").pack(side="left", padx=4)

        ttk.Label(marco, textvariable=self.archivo_actual_var, foreground="#57606a").pack(anchor="w", pady=(6, 2))

        marco_tabla = ttk.LabelFrame(self.pestana_datos, text="Matriz actual", padding=8)
        marco_tabla.pack(fill="both", expand=True, pady=8)

        self.tabla_matriz = ttk.Treeview(marco_tabla, show="headings", height=10)
        scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tabla_matriz.yview)
        scroll_x = ttk.Scrollbar(marco_tabla, orient="horizontal", command=self.tabla_matriz.xview)
        self.tabla_matriz.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tabla_matriz.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        marco_tabla.rowconfigure(0, weight=1)
        marco_tabla.columnconfigure(0, weight=1)

        marco_objetivo = ttk.LabelFrame(self.pestana_datos, text="Objetivo del problema", padding=10)
        marco_objetivo.pack(fill="x", pady=5)
        ttk.Radiobutton(marco_objetivo, text="Minimizar costo", variable=self.objetivo_var, value="min").pack(side="left", padx=12)
        ttk.Radiobutton(marco_objetivo, text="Maximizar beneficio / eficiencia", variable=self.objetivo_var, value="max").pack(side="left", padx=12)

        ttk.Button(self.pestana_datos, text="Ir a Resolver ->", command=lambda: self.notebook.select(1),
                   style="Primario.TButton").pack(anchor="e", pady=4)

    # ------------------------------------------------------------------ #
    # Pestana: Resolver
    # ------------------------------------------------------------------ #
    def _construir_pestana_resolver(self) -> None:
        marco_accion = ttk.Frame(self.pestana_resolver)
        marco_accion.pack(fill="x", pady=4)
        ttk.Button(marco_accion, text="Resolver con Metodo Hungaro", command=self._resolver,
                   style="Primario.TButton").pack(side="left")
        self.etiqueta_costo = ttk.Label(marco_accion, text="Costo/beneficio optimo: -", style="Titulo.TLabel")
        self.etiqueta_costo.pack(side="left", padx=16)

        marco_asignacion = ttk.LabelFrame(self.pestana_resolver, text="Matriz de asignacion final", padding=8)
        marco_asignacion.pack(fill="both", expand=True, pady=6)
        self.tabla_asignacion = ttk.Treeview(marco_asignacion, columns=("agente", "tarea", "valor"), show="headings", height=8)
        for col, txt, ancho in (("agente", "Agente", 260), ("tarea", "Tarea", 260), ("valor", "Valor", 120)):
            self.tabla_asignacion.heading(col, text=txt)
            self.tabla_asignacion.column(col, width=ancho, anchor="center")
        scroll = ttk.Scrollbar(marco_asignacion, orient="vertical", command=self.tabla_asignacion.yview)
        self.tabla_asignacion.configure(yscrollcommand=scroll.set)
        self.tabla_asignacion.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        marco_pasos = ttk.LabelFrame(self.pestana_resolver, text="Pasos del Metodo Hungaro (didactico)", padding=8)
        marco_pasos.pack(fill="both", expand=True, pady=6)
        self.texto_pasos = tk.Text(marco_pasos, height=10, wrap="word", font=("Consolas", 9))
        barra = ttk.Scrollbar(marco_pasos, command=self.texto_pasos.yview)
        self.texto_pasos.configure(yscrollcommand=barra.set)
        self.texto_pasos.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        ttk.Button(self.pestana_resolver, text="Ir a Grafo ->", command=lambda: self.notebook.select(2)).pack(anchor="e", pady=4)

    # ------------------------------------------------------------------ #
    # Pestana: Grafo
    # ------------------------------------------------------------------ #
    def _construir_pestana_grafo(self) -> None:
        marco = ttk.Frame(self.pestana_grafo)
        marco.pack(fill="x", pady=4)
        ttk.Button(marco, text="Generar y mostrar grafo", command=self._mostrar_grafo,
                   style="Primario.TButton").pack(side="left")
        self.etiqueta_grafo = ttk.Label(marco, text="Sin grafo generado.", foreground="#57606a")
        self.etiqueta_grafo.pack(side="left", padx=12)
        ttk.Button(marco, text="Exportar reporte a PDF", command=self._exportar_pdf).pack(side="right", padx=4)

        self.marco_canvas = ttk.LabelFrame(self.pestana_grafo, text="Grafo bipartito de asignacion", padding=6)
        self.marco_canvas.pack(fill="both", expand=True, pady=6)
        self.canvas_grafo = None
        self.toolbar_grafo = None
        self.figura_actual = None

        ttk.Button(self.pestana_grafo, text="Ir a IA ->", command=lambda: self.notebook.select(3)).pack(anchor="e", pady=4)

    # ------------------------------------------------------------------ #
    # Pestana: IA
    # ------------------------------------------------------------------ #
    def _construir_pestana_ia(self) -> None:
        marco_proveedor = ttk.Frame(self.pestana_ia)
        marco_proveedor.pack(fill="x", pady=4)
        ttk.Label(marco_proveedor, text="Proveedor de IA:").pack(side="left")
        combo_proveedor = ttk.Combobox(
            marco_proveedor, textvariable=self.proveedor_var, width=12, state="readonly",
            values=["Gemini", "Nvidia"],
        )
        combo_proveedor.pack(side="left", padx=6)
        combo_proveedor.bind("<<ComboboxSelected>>", lambda e: self._actualizar_modelos_por_proveedor())

        marco_clave = ttk.Frame(self.pestana_ia)
        marco_clave.pack(fill="x", pady=4)
        ttk.Label(marco_clave, text="Clave Gemini (opcional):").pack(anchor="w")
        fila_g = ttk.Frame(marco_clave)
        fila_g.pack(fill="x", pady=2)
        self.entrada_clave = ttk.Entry(fila_g, textvariable=self.clave_api_var, show="*", width=52)
        self.entrada_clave.pack(side="left")
        ttk.Button(fila_g, text="Mostrar", width=9, command=self._alternar_visibilidad_clave).pack(side="left", padx=6)

        ttk.Label(marco_clave, text="Clave NVIDIA (opcional):").pack(anchor="w", pady=(6, 0))
        fila_n = ttk.Frame(marco_clave)
        fila_n.pack(fill="x", pady=2)
        self.entrada_clave_nvidia = ttk.Entry(fila_n, textvariable=self.clave_nvidia_var, show="*", width=52)
        self.entrada_clave_nvidia.pack(side="left")

        marco_modelo = ttk.Frame(self.pestana_ia)
        marco_modelo.pack(fill="x", pady=4)
        ttk.Label(marco_modelo, text="Modelo:").pack(side="left")
        self.combo_modelo = ttk.Combobox(
            marco_modelo, textvariable=self.modelo_var, width=26, state="readonly",
            values=[
                "gemini-3.8-flash",
                "gemini-3.6-flash",
                "gemini-3.5-flash",
                "gemini-3.1-flash-lite",
                "gemini-2.5-flash",
            ],
        )
        self.combo_modelo.pack(side="left", padx=6)
        ttk.Label(marco_modelo, text="Nivel de pensamiento:").pack(side="left", padx=(12, 0))
        combo_pensamiento = ttk.Combobox(
            marco_modelo, textvariable=self.pensamiento_var, width=10, state="readonly",
            values=["LOW", "MEDIUM", "HIGH"],
        )
        combo_pensamiento.pack(side="left", padx=6)

        ttk.Button(self.pestana_ia, text="Consultar IA", command=self._consultar_ia,
                   style="Primario.TButton").pack(anchor="w", pady=6)

        self.barra_progreso = ttk.Progressbar(self.pestana_ia, mode="indeterminate")
        self.barra_progreso.pack(fill="x", pady=2)

        marco_resultado = ttk.LabelFrame(self.pestana_ia, text="Analisis ejecutivo (IA)", padding=8)
        marco_resultado.pack(fill="both", expand=True, pady=6)
        self.texto_ia = tk.Text(marco_resultado, height=14, wrap="word", font=("Segoe UI", 10))
        scroll = ttk.Scrollbar(marco_resultado, command=self.texto_ia.yview)
        self.texto_ia.configure(yscrollcommand=scroll.set)
        self.texto_ia.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # ------------------------------------------------------------------ #
    # Carga de datos
    # ------------------------------------------------------------------ #
    def _cargar_csv(self) -> None:
        ruta = filedialog.askopenfilename(title="Seleccionar archivo CSV",
                                         filetypes=[("Archivos CSV", "*.csv"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            matriz = IngestaDatos.cargar_csv(ruta)
        except IngestaError as error:
            messagebox.showerror("Error de ingesta", str(error))
            self._set_estado(f"Error CSV: {error}", COLOR_ERROR)
            return
        except Exception as error:
            messagebox.showerror("Error inesperado", str(error))
            return
        self._establecer_matriz(matriz, f"CSV: {os.path.basename(ruta)}")

    def _cargar_json(self) -> None:
        ruta = filedialog.askopenfilename(title="Seleccionar archivo JSON",
                                         filetypes=[("Archivos JSON", "*.json"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            matriz = IngestaDatos.cargar_json(ruta)
        except IngestaError as error:
            messagebox.showerror("Error de ingesta", str(error))
            self._set_estado(f"Error JSON: {error}", COLOR_ERROR)
            return
        except Exception as error:
            messagebox.showerror("Error inesperado", str(error))
            return
        self._establecer_matriz(matriz, f"JSON: {os.path.basename(ruta)}")

    def _cargar_por_defecto(self) -> None:
        try:
            matriz = IngestaDatos.matriz_por_defecto()
        except Exception as error:
            messagebox.showerror("Error", str(error))
            return
        self._establecer_matriz(matriz, "Matriz por defecto en memoria")

    def _establecer_matriz(self, matriz: Matriz, mensaje: str) -> None:
        self.matriz_actual = matriz
        self.resultado_actual = None
        self.texto_ia_resultado = None
        self._mostrar_matriz(matriz)
        self.archivo_actual_var.set(f"{mensaje}  |  Dimensiones: {matriz.dimensiones()[0]} agentes x {matriz.dimensiones()[1]} tareas")
        self.etiqueta_costo.config(text="Costo/beneficio optimo: -")
        self._limpiar_treeview(self.tabla_asignacion)
        self.texto_pasos.delete("1.0", "end")
        self.texto_ia.delete("1.0", "end")
        self._limpiar_grafo()
        self._set_estado("Matriz cargada correctamente. Elija el objetivo y resuelva.", COLOR_EXITO)

    def _mostrar_matriz(self, matriz: Matriz) -> None:
        self._limpiar_treeview(self.tabla_matriz)
        columnas = ["Agente"] + matriz.tareas
        self.tabla_matriz["columns"] = columnas
        for col in columnas:
            self.tabla_matriz.heading(col, text=col)
            self.tabla_matriz.column(col, width=120, anchor="center")
        for agente, fila in zip(matriz.agentes, matriz.valores):
            self.tabla_matriz.insert("", "end", values=[agente] + [self._formatear(v) for v in fila])

    # ------------------------------------------------------------------ #
    # Resolver
    # ------------------------------------------------------------------ #
    def _resolver(self) -> None:
        if self.matriz_actual is None:
            messagebox.showwarning("Sin datos", "Cargue una matriz antes de resolver.")
            self._set_estado("Debe cargar una matriz primero.", COLOR_ALERTA)
            return
        objetivo = self.objetivo_var.get()
        try:
            hungaro = Hungaro(self.matriz_actual, objetivo)
            resultado = hungaro.resolver()
        except Exception as error:
            messagebox.showerror("Error al resolver", str(error))
            self._set_estado(f"Error al resolver: {error}", COLOR_ERROR)
            return
        self.resultado_actual = resultado

        self._limpiar_treeview(self.tabla_asignacion)
        for agente, tarea, valor in resultado.asignaciones:
            self.tabla_asignacion.insert("", "end", values=(agente, tarea, self._formatear(valor)))

        etiqueta = "Costo" if objetivo == "min" else "Beneficio"
        self.etiqueta_costo.config(text=f"{etiqueta} total optimo: {self._formatear(resultado.costo_total)}")

        self.texto_pasos.delete("1.0", "end")
        for paso in resultado.pasos:
            self.texto_pasos.insert("end", paso + "\n")

        if resultado.hubo_ficticios:
            detalle = []
            if resultado.agentes_inactivos:
                detalle.append("Agentes inactivos: " + ", ".join(resultado.agentes_inactivos))
            if resultado.tareas_huerfanas:
                detalle.append("Tareas huerfanas: " + ", ".join(resultado.tareas_huerfanas))
            messagebox.showinfo("Nodos ficticios detectados", "\n".join(detalle) if detalle else "Se usaron nodos ficticios.")
            self._set_estado("Resuelto. Se detectaron nodos ficticios (ver detalles).", COLOR_ALERTA)
        else:
            self._set_estado("Problema resuelto correctamente (balanceado).", COLOR_EXITO)

    # ------------------------------------------------------------------ #
    # Grafo
    # ------------------------------------------------------------------ #
    def _mostrar_grafo(self) -> None:
        if self.resultado_actual is None:
            messagebox.showwarning("Sin resultado", "Resuelva el problema antes de generar el grafo.")
            self._set_estado("Debe resolver primero.", COLOR_ALERTA)
            return
        try:
            grafo = GrafoBipartito(self.resultado_actual)
            grafo.construir()
            figura = grafo.crear_figura()
        except Exception as error:
            messagebox.showerror("Error al generar grafo", str(error))
            self._set_estado(f"Error en grafo: {error}", COLOR_ERROR)
            return

        self.figura_actual = figura
        ruta_salida = os.path.join("output", "grafo_asignacion.png")
        os.makedirs("output", exist_ok=True)
        try:
            figura.savefig(ruta_salida, dpi=120, bbox_inches="tight")
        except Exception as error:
            messagebox.showerror("Error al guardar grafo", str(error))
            self._set_estado(f"Error al guardar: {error}", COLOR_ERROR)
            return

        self._dibujar_canvas(figura)
        self.etiqueta_grafo.config(text=f"Grafo guardado en {ruta_salida}.", foreground=COLOR_EXITO)
        self._set_estado("Grafo generado y guardado en disco.", COLOR_EXITO)

    def _dibujar_canvas(self, figura) -> None:
        # Limpia canvas anterior.
        if self.canvas_grafo is not None:
            self.canvas_grafo.get_tk_widget().destroy()
            self.canvas_grafo = None
        if self.toolbar_grafo is not None:
            self.toolbar_grafo.destroy()
            self.toolbar_grafo = None
        self.canvas_grafo = FigureCanvasTkAgg(figura, master=self.marco_canvas)
        self.canvas_grafo.draw()
        self.canvas_grafo.get_tk_widget().pack(fill="both", expand=True)
        self.toolbar_grafo = NavigationToolbar2Tk(self.canvas_grafo, self.marco_canvas, pack_toolbar=False)
        self.toolbar_grafo.update()
        self.toolbar_grafo.pack(fill="x")

    def _exportar_pdf(self) -> None:
        if self.resultado_actual is None or self.matriz_actual is None:
            messagebox.showwarning("Sin resultado", "Resuelva el problema antes de exportar a PDF.")
            return
        if not self.texto_ia_resultado:
            messagebox.showwarning(
                "Falta analisis de IA",
                "Debe consultar la IA (pestana IA) antes de generar el reporte, "
                "ya que el reporte requiere la conclusion textual exacta de la API.",
            )
            return
        ruta = os.path.join("output", "reporte_asignacion.pdf")
        os.makedirs("output", exist_ok=True)
        capturas = []
        try:
            from PIL import ImageGrab
            tab_actual = self.notebook.index(self.notebook.select())
            for indice in range(self.notebook.index("end")):
                self.notebook.select(indice)
                self.raiz.update()
                self.raiz.update_idletasks()
                x = self.raiz.winfo_x()
                y = self.raiz.winfo_y()
                w = self.raiz.winfo_width()
                h = self.raiz.winfo_height()
                capturas.append(ImageGrab.grab(bbox=(x, y, x + w, y + h)))
            self.notebook.select(tab_actual)
            self.raiz.update()
        except Exception as error:
            self._set_estado(f"Captura no disponible: {error}", COLOR_ALERTA)
        try:
            generador = GeneradorPDF(ruta)
            generador.generar(
                self.matriz_actual,
                self.resultado_actual,
                self.figura_actual,
                self.texto_ia_resultado,
                capturas,
            )
        except Exception as error:
            messagebox.showerror("Error al generar PDF", str(error))
            self._set_estado(f"Error PDF: {error}", COLOR_ERROR)
            return
        messagebox.showinfo("PDF generado", f"Reporte guardado en:\n{ruta}")
        self._set_estado(f"PDF exportado: {ruta}", COLOR_EXITO)

    def _limpiar_grafo(self) -> None:
        if self.canvas_grafo is not None:
            self.canvas_grafo.get_tk_widget().destroy()
            self.canvas_grafo = None
        if self.toolbar_grafo is not None:
            self.toolbar_grafo.destroy()
            self.toolbar_grafo = None
        self.etiqueta_grafo.config(text="Sin grafo generado.", foreground="#57606a")

    # ------------------------------------------------------------------ #
    # IA
    # ------------------------------------------------------------------ #
    def _alternar_visibilidad_clave(self) -> None:
        # Alterna visibilidad para ambos campos de clave (Gemini y NVIDIA)
        actual = self.entrada_clave.cget("show")
        self.entrada_clave.config(show="" if actual == "*" else "*")
        actual_nv = self.entrada_clave_nvidia.cget("show")
        self.entrada_clave_nvidia.config(show="" if actual_nv == "*" else "*")

    def _actualizar_modelos_por_proveedor(self) -> None:
        proveedor = self.proveedor_var.get()
        if proveedor == "Nvidia":
            modelos = ["nvidia/nemotron-3-ultra-550b-a55b", "nvidia/nemotron-3.5-lightning-30b-a3b"]
            self.modelo_var.set(modelos[0])
        else:
            modelos = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
            if self.modelo_var.get() not in modelos:
                self.modelo_var.set(modelos[0])
        self.combo_modelo["values"] = modelos

    def _consultar_ia(self) -> None:
        if self.resultado_actual is None or self.matriz_actual is None:
            messagebox.showwarning("Sin resultado", "Resuelva el problema antes de consultar la IA.")
            self._set_estado("Debe resolver primero.", COLOR_ALERTA)
            return
        proveedor_nombre = self.proveedor_var.get()
        modelo = self.modelo_var.get().strip()
        if proveedor_nombre == "Nvidia":
            clave = self.clave_nvidia_var.get().strip()
            if clave and ("\n" in clave or "\r" in clave or len(clave) > 200 or not clave.startswith("nvapi-")):
                messagebox.showerror("Clave invalida", "La clave de NVIDIA parece incorrecta. Debe comenzar con 'nvapi-' y no contener saltos de linea. Limpie el campo y vuelva a pegarla.")
                self._set_estado("Clave NVIDIA invalida.", COLOR_ERROR)
                return
            proveedor = ProveedorNvidia(api_key=clave if clave else None, modelo=modelo or "nvidia/nemotron-3-ultra-550b-a55b")
        else:
            clave = self.clave_api_var.get().strip()
            if clave and ("\n" in clave or "\r" in clave or len(clave) > 200):
                messagebox.showerror("Clave invalida", "La clave de Gemini parece incorrecta. No debe contener saltos de linea.")
                self._set_estado("Clave Gemini invalida.", COLOR_ERROR)
                return
            proveedor = ProveedorGemini(
                api_key=clave if clave else None,
                modelo=modelo or "gemini-3.8-flash",
                nivel_pensamiento=self.pensamiento_var.get().strip() or "LOW",
            )
        cliente = ClienteIA(proveedor=proveedor)
        objetivo = self.objetivo_var.get()

        self.texto_ia.delete("1.0", "end")
        self.texto_ia.insert("end", "Consultando a la IA, por favor espere...\n")
        self.barra_progreso.start(10)
        self.raiz.update()

        ok, texto = cliente.consultar(self.matriz_actual, objetivo, self.resultado_actual)
        self.barra_progreso.stop()
        self.texto_ia.delete("1.0", "end")
        if ok:
            self.texto_ia.insert("end", texto)
            self.texto_ia_resultado = texto
            self._set_estado("Analisis de IA recibido correctamente.", COLOR_EXITO)
        else:
            self.texto_ia.insert("end", f"[Error] {texto}")
            self._set_estado(f"Error IA: {texto}", COLOR_ERROR)

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

    def _set_estado(self, mensaje: str, color: str = "#24292f") -> None:
        self.estado_var.set(mensaje)


def iniciar_aplicacion() -> None:
    raiz = tk.Tk()
    AplicacionGUI(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    iniciar_aplicacion()