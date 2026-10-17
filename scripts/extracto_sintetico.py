"""Extracto CRM sintético SIN defectos, con el esquema de la ficha técnica (Reto 02).

Lo usa la CI cuando no tiene acceso al extracto real (decisión del Reto 04, opción b): los datos
personales nunca salen del remoto del equipo y aun así la CI ejecuta el pipeline completo
(clean → validate → prepare → train → evaluate) con el mismo esquema. Las métricas de la CI son
entonces las de datos sintéticos: verifican que el pipeline funcione, no la calidad del modelo real.

  python -m scripts.extracto_sintetico                  → data/raw/crm_extracto.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.common import ROOT
from src.synthetic import generate_customers

FECHA_CORTE = pd.Timestamp("2026-09-30")


def extracto(n: int = 7000, seed: int = 42) -> pd.DataFrame:
    df = generate_customers(n=n, seed=seed)
    rng = np.random.default_rng(seed)
    df["region"] = rng.choice(["Quindío", "Risaralda", "Caldas", "Norte del Valle"], size=n)
    df["fecha_alta"] = [
        (FECHA_CORTE - pd.DateOffset(months=int(m))).date().isoformat() for m in df["tenure_months"]
    ]
    df["fecha_corte"] = FECHA_CORTE.date().isoformat()
    df["oferta_retencion_aceptada"] = 0  # sin información (y sin fuga) en el extracto sintético
    return df


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, default=ROOT / "data" / "raw" / "crm_extracto.csv")
    p.add_argument("--rows", type=int, default=7000)
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    extracto(args.rows).to_csv(args.out, index=False)
    print(f"[extracto_sintetico] {args.rows} filas → {args.out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
