# Bitácoras de los retos

Una por reto: `reto-00.md` … `reto-07.md` (contrato §6.1). Cada bitácora responde las preguntas del
reto, enlaza las evidencias (commits, corridas de MLflow, capturas, reportes) y cierra con una
reflexión gerencial de 5–8 líneas. Parta de [`plantilla.md`](plantilla.md).


## 11. Reproducir desde cero

### Isntalación Windows
1. `git clone https://github.com/BrayhanJC/srtandina && cd strandina`
2. `uv sync --frozen`
3. Si el remoto es una carpeta sincronizada: `uv run dvc remote modify --local almacen url "<su-ruta>"`
4. `uv run dvc pull`
5. `uv run dvc repro`

### Instalación Macosx

1. `git clone https://github.com/BrayhanJC/srtandina && cd strandina`
2. `uv sync --frozen --python 3.12 --managed-python`
3. Si el remoto es una carpeta sincronizada: 
    `uv run dvc remote add -d almacen "<su-ruta>"`
    `uv run dvc remote modify --local almacen url "<su-ruta>"`
4. `uv run dvc pull`
5. `uv run dvc repro --force`
