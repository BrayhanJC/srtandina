"""Verifica que el computador tenga todo lo que el curso necesita (Reto P – Preparación del entorno).

  uv run python -m scripts.verificar_entorno                 → tabla en pantalla
  uv run python -m scripts.verificar_entorno --out entorno.txt   → además, guarda el reporte

Niveles:
  ✅ listo · ⚠️ falta, pero se necesita más adelante (FDS 3 o FDS 4) · ❌ falta y se necesita en el FDS 1
Código de salida: 0 si no hay ❌; 1 si hay al menos uno.
"""

import argparse
import importlib
import os
import platform
import shutil
import subprocess
import sys
import warnings
from datetime import datetime

PLANTILLA = "https://github.com/christiancandela/gpad-srt-template.git"
MODELO_OLLAMA = "qwen3:4b"
GB = 1024**3


def correr(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    """Ejecuta un comando y devuelve (código, salida). Código 127 si el programa no existe."""
    if shutil.which(cmd[0]) is None:
        return 127, ""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or r.stderr).strip()
    except (subprocess.TimeoutExpired, OSError) as exc:
        return 1, str(exc)


def ram_total_gb() -> float | None:
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / GB
    except (ValueError, OSError, AttributeError):
        return None  # Windows: no disponible sin dependencias adicionales


def silenciar_avisos():
    """Evita que los avisos internos de MLflow y Evidently al importarse confundan el reporte."""
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    warnings.filterwarnings("ignore")


def verificaciones() -> list[tuple[str, str, str, str]]:
    """Lista de (cuándo se necesita, elemento, estado, detalle)."""
    filas = []

    def fila(cuando, elemento, ok, detalle, nivel_si_falla):
        filas.append((cuando, elemento, "✅" if ok else nivel_si_falla, detalle))

    v = sys.version_info
    fila(
        "FDS 1",
        "Python 3.11–3.12 (lo instala uv)",
        (3, 11) <= v[:2] <= (3, 12),
        platform.python_version(),
        "❌",
    )

    c, out = correr(["uv", "--version"])
    fila("FDS 1", "uv", c == 0, out or "no instalado (ver Reto P, bloque 3)", "❌")

    c, out = correr(["git", "--version"])
    fila("FDS 1", "Git", c == 0, out or "no instalado (ver Reto P, bloque 2)", "❌")
    _, nombre = correr(["git", "config", "--global", "user.name"])
    _, correo = correr(["git", "config", "--global", "user.email"])
    fila(
        "FDS 1",
        "Git: nombre y correo configurados",
        bool(nombre and correo),
        f"{nombre or '—'} <{correo or '—'}>",
        "❌",
    )

    c, _ = correr(["git", "ls-remote", PLANTILLA, "HEAD"], timeout=30)
    fila(
        "FDS 1",
        "Acceso a GitHub (plantilla del curso)",
        c == 0,
        "OK" if c == 0 else "sin acceso: revise la red o el proxy",
        "❌",
    )

    faltan = []
    for paquete in ["dvc", "mlflow", "pandera", "sklearn", "fastapi", "evidently", "pytest"]:
        try:
            importlib.import_module(paquete)
        except Exception:  # noqa: BLE001 - cualquier fallo de importación cuenta como faltante
            faltan.append(paquete)
    fila(
        "FDS 1",
        "Librerías del curso (uv sync)",
        not faltan,
        "todas importan" if not faltan else f"faltan: {', '.join(faltan)}",
        "❌",
    )

    libre = shutil.disk_usage(".").free / GB
    fila("FDS 1", "Disco libre ≥ 15 GB", libre >= 15, f"{libre:.0f} GB libres", "⚠️")

    ram = ram_total_gb()
    fila(
        "FDS 1",
        "RAM ≥ 8 GB (16 GB recomendado)",
        ram is None or ram >= 7.5,
        "no se pudo medir (Windows)" if ram is None else f"{ram:.0f} GB",
        "⚠️",
    )

    c, out = correr(["docker", "--version"])
    fila("FDS 3", "Docker instalado", c == 0, out or "no instalado (ver Reto P, bloque 5)", "⚠️")
    c, mem = correr(["docker", "info", "--format", "{{.MemTotal}}"], timeout=30)
    if c == 0 and mem.isdigit():
        gb = int(mem) / GB
        fila("FDS 3", "Docker corriendo con ≥ 4 GB de RAM", gb >= 3.8, f"{gb:.1f} GB asignados", "⚠️")
    else:
        fila(
            "FDS 3", "Docker corriendo con ≥ 4 GB de RAM", False, "Docker no está abierto o no responde", "⚠️"
        )

    c, out = correr(["ollama", "list"], timeout=30)
    if c == 127:
        fila("FDS 4", f"Ollama con {MODELO_OLLAMA}", False, "Ollama no instalado (ver Reto P, bloque 6)", "⚠️")
    else:
        fila(
            "FDS 4",
            f"Ollama con {MODELO_OLLAMA}",
            MODELO_OLLAMA in out,
            "modelo descargado" if MODELO_OLLAMA in out else f"falta: ollama pull {MODELO_OLLAMA}",
            "⚠️",
        )
    return filas


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificación del entorno del curso")
    parser.add_argument("--out", help="archivo donde guardar el reporte (para entregarlo)")
    args = parser.parse_args()

    silenciar_avisos()
    filas = verificaciones()
    lineas = [
        f"Verificación del entorno · {datetime.now():%Y-%m-%d %H:%M} · "
        f"{platform.system()} {platform.release()} ({platform.machine()})",
        "",
        f"{'Para':<6} {'':2} {'Elemento':<44} Detalle",
        "-" * 100,
    ]
    lineas += [
        f"{cuando:<6} {estado:<2} {elemento:<44} {detalle}" for cuando, elemento, estado, detalle in filas
    ]
    bloqueantes = [f for f in filas if f[2] == "❌"]
    pendientes = [f for f in filas if f[2] == "⚠️"]
    lineas.append("-" * 100)
    if bloqueantes:
        lineas.append(f"❌ NO LISTO para el FDS 1: {len(bloqueantes)} elemento(s) por resolver.")
    else:
        lineas.append("✅ LISTO para el FDS 1.")
    if pendientes:
        lineas.append(f"⚠️  {len(pendientes)} elemento(s) para más adelante (revise la columna 'Para').")
    texto = "\n".join(lineas)
    print(texto)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(texto + "\n")
    return 1 if bloqueantes else 0


if __name__ == "__main__":
    sys.exit(main())
