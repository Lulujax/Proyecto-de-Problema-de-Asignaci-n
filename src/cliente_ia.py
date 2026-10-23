"""Modulo de integracion con la API de IA (Gemini), con diseno extensible.

Se define una clase base `ProveedorIA` para que se puedan anadir otros
proveedores (OpenAI, Claude) sin modificar el resto del sistema. La clave API
se lee de la variable de entorno GEMINI_API_KEY (o se pasa por constructor).
"""

from __future__ import annotations

import os
from typing import Tuple

import requests

from .hungaro import ResultadoAsignacion
from .matriz import Matriz


class ProveedorIA:
    """Interfaz comun para proveedores de IA."""

    def consultar(self, prompt: str) -> Tuple[bool, str]:
        raise NotImplementedError("Subclase debe implementar consultar().")


class ProveedorGemini(ProveedorIA):
    """Proveedor concreto para la API de Google Gemini."""

    def __init__(
        self,
        api_key: str = None,
        modelo: str = "gemini-3.8-flash",
        timeout: int = 30,
        nivel_pensamiento: str = "LOW",
    ):
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        self.modelo = modelo
        self.timeout = timeout
        self.nivel_pensamiento = (nivel_pensamiento or "").upper()

    def consultar(self, prompt: str) -> Tuple[bool, str]:
        if not self.api_key or not self.api_key.strip():
            return (
                False,
                "No se encontro la clave API. Defina la variable de entorno "
                "GEMINI_API_KEY o ingresela en la aplicacion.",
            )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.modelo}:generateContent"
        )
        parametros = {"key": self.api_key.strip()}
        configuracion_generacion = {"maxOutputTokens": 512}
        # Los modelos Gemini 3.x usan niveles de pensamiento (LOW/MEDIUM/HIGH).
        if self.nivel_pensamiento in ("LOW", "MEDIUM", "HIGH"):
            configuracion_generacion["thinkingConfig"] = {
                "thinkingLevel": self.nivel_pensamiento
            }
        cuerpo = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": configuracion_generacion,
        }

        try:
            respuesta = requests.post(
                url, params=parametros, json=cuerpo, timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            return False, "Tiempo de espera agotado al consultar la IA (timeout)."
        except requests.exceptions.ConnectionError:
            return False, "Sin conexion a internet o no se pudo alcanzar el servicio de IA."
        except requests.exceptions.RequestException as error:
            return False, f"Error de red al consultar la IA: {error}"

        if respuesta.status_code in (401, 403):
            return False, "Clave API invalida o sin permisos para el servicio de IA."
        if respuesta.status_code == 429:
            return False, "Se excedio la cuota de la API de IA. Intente mas tarde."
        if not respuesta.ok:
            detalle = respuesta.text[:300] if respuesta.text else ""
            return False, f"Error HTTP {respuesta.status_code} de la IA: {detalle}"

        try:
            datos = respuesta.json()
            texto = datos["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            return False, f"Respuesta inesperada de la IA: {error}"

        texto = texto.strip()
        if not texto:
            return False, "La IA devolvio una respuesta vacia."
        return True, texto


class ClienteIA:
    """Orquesta la construccion del prompt y la consulta al proveedor."""

    def __init__(self, proveedor: ProveedorIA = None):
        self.proveedor = proveedor if proveedor is not None else ProveedorGemini()

    def construir_prompt(
        self, matriz_original: Matriz, objetivo: str, resultado: ResultadoAsignacion
    ) -> str:
        objetivo_texto = (
            "minimizar costos" if objetivo == "min" else "maximizar beneficio/eficiencia"
        )
        lineas = []
        lineas.append(
            "Actua como Gerente de Operaciones y Recursos Humanos de la empresa "
            "'Rutas y Suministros C.A.'."
        )
        lineas.append("")
        lineas.append(
            "Se resolvio un problema de asignacion 1 a 1 de conductores (agentes) "
            "a rutas (tareas) mediante el Metodo Hungaro."
        )
        lineas.append(f"Objetivo del problema: {objetivo_texto}.")
        lineas.append("")
        lineas.append("Matriz original (costos/beneficios):")
        lineas.append(matriz_original.a_texto())
        lineas.append("")
        lineas.append("Matriz de asignacion final (agente -> tarea = valor):")
        for agente, tarea, valor in resultado.asignaciones:
            lineas.append(f"  {agente} -> {tarea} = {valor}")
        lineas.append(
            f"{'Costo' if objetivo == 'min' else 'Beneficio'} total optimo: "
            f"{resultado.costo_total}"
        )
        lineas.append("")
        if resultado.agentes_inactivos:
            lineas.append(
                "Agentes inactivos (sin tarea asignada): "
                + ", ".join(resultado.agentes_inactivos)
            )
        if resultado.tareas_huerfanas:
            lineas.append(
                "Tareas huerfanas (sin agente asignado): "
                + ", ".join(resultado.tareas_huerfanas)
            )
        if not resultado.agentes_inactivos and not resultado.tareas_huerfanas:
            lineas.append(
                "No hubo agentes inactivos ni tareas huerfanas (problema balanceado)."
            )
        lineas.append("")
        lineas.append(
            "Responde SIEMPRE en espanol, con maximo 2 parrafos de analisis ejecutivo "
            "y una recomendacion de negocio concreta sobre que hacer con los recursos "
            "inactivos o tareas huerfanas si los hubo. No incluyas tu proceso de "
            "pensamiento ni texto en otro idioma."
        )
        return "\n".join(lineas)

    def consultar(
        self, matriz_original: Matriz, objetivo: str, resultado: ResultadoAsignacion
    ) -> Tuple[bool, str]:
        prompt = self.construir_prompt(matriz_original, objetivo, resultado)
        return self.proveedor.consultar(prompt)

class ProveedorNvidia(ProveedorIA):
    # Proveedor concreto para la API de NVIDIA NIM (compatible con OpenAI).

    def __init__(self, api_key=None, modelo="nvidia/nemotron-3-ultra-550b-a55b", timeout=60):
        self.api_key = api_key if api_key is not None else os.getenv("NVIDIA_API_KEY")
        self.modelo = modelo
        self.timeout = timeout

    def consultar(self, prompt):
        if not self.api_key or not self.api_key.strip():
            return False, "No se encontro la clave API de NVIDIA. Defina NVIDIA_API_KEY o ingresela en la aplicacion."
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        cabeceras = {"Authorization": "Bearer " + self.api_key.strip(), "Content-Type": "application/json"}
        cuerpo = {
            "model": self.modelo,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.4,
            "chat_template_kwargs": {"thinking": False},
        }
        try:
            respuesta = requests.post(url, headers=cabeceras, json=cuerpo, timeout=self.timeout)
            if not respuesta.ok and respuesta.status_code in (400, 422):
                cuerpo.pop("chat_template_kwargs", None)
                respuesta = requests.post(url, headers=cabeceras, json=cuerpo, timeout=self.timeout)
        except requests.exceptions.Timeout:
            return False, "Tiempo de espera agotado al consultar NVIDIA (timeout)."
        except requests.exceptions.ConnectionError:
            return False, "Sin conexion a internet o no se pudo alcanzar NVIDIA."
        except requests.exceptions.RequestException as error:
            return False, "Error de red al consultar NVIDIA: " + str(error)
        if respuesta.status_code in (401, 403):
            return False, "Clave API de NVIDIA invalida o sin permisos."
        if respuesta.status_code == 429:
            return False, "Se excedio la cuota de la API de NVIDIA. Intente mas tarde."
        if not respuesta.ok:
            detalle = respuesta.text[:300] if respuesta.text else ""
            return False, "Error HTTP " + str(respuesta.status_code) + " de NVIDIA: " + detalle
        try:
            datos = respuesta.json()
            mensaje = datos["choices"][0]["message"]
            texto = mensaje.get("content") or mensaje.get("reasoning_content") or ""
        except (KeyError, IndexError, TypeError, ValueError) as error:
            return False, "Respuesta inesperada de NVIDIA: " + str(error)
        texto = texto.strip()
        if not texto:
            return False, "NVIDIA devolvio una respuesta vacia."
        return True, texto

