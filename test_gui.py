import os
os.environ.setdefault("GEMINI_API_KEY", input("Gemini key (enter para omitir): ").strip())
os.environ.setdefault("NVIDIA_API_KEY", input("Nvidia key (enter para omitir): ").strip())
import sys
sys.path.insert(0, ".")
from src.cliente_ia import ProveedorGemini, ProveedorNvidia
from src.matriz import Matriz
from src.hungaro import Hungaro
m = Matriz(["A1"],["T1"],[[5]])
r = Hungaro(m, "min").resolver()
# Gemini
if os.getenv("GEMINI_API_KEY"):
    ok, txt = ProveedorGemini(modelo="gemini-2.5-flash").consultar("Di hola en una frase.")
    print("Gemini:", ok, txt[:200])
# Nvidia
if os.getenv("NVIDIA_API_KEY"):
    ok, txt = ProveedorNvidia().consultar("Di hola en una frase.")
    print("Nvidia:", ok, txt[:200])