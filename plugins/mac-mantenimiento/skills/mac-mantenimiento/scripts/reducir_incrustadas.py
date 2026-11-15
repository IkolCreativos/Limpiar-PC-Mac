#!/usr/bin/env python3
"""Reduce las imagenes incrustadas dentro de PDF o .ai CONSERVANDO los vectores.

El texto y los trazos quedan identicos: Ghostscript solo toca los flujos de
imagen. Conserva nombre y extension para no romper vinculos de maquetacion.
Cada original se mueve a cuarentena y todo queda en un manifiesto.

Requiere: brew install ghostscript
          swiftc -O -o pdfpaginas pdfpaginas.swift   (recuento fiable de paginas)

Uso:
  reducir_incrustadas.py CARPETA CUARENTENA MANIFIESTO.csv [--dpi 300]
                         [--ext .ai,.pdf] [--ganancia 0.80] [--dif 12.0]
                         [--timeout 300]

Sobre --dif: recomprimir JPEG mueve mas pixeles que reducir resolucion sin que
haya degradacion. Medido sobre material real, esta transformacion da diferencias
de 4 a 8; el fallo grave de verdad (premultiplicacion de alfa) da de 21 a 42. Por
eso aqui el umbral es 12 y no el 6 que usa reducir_imagenes.py. El texto y los
trazos salen identicos pixel a pixel: la diferencia esta toda en las fotos.

Salvaguardas (cada una viene de un fallo real):
  - Si el ORIGINAL renderiza en blanco, no se toca: su contenido esta en datos
    nativos que Ghostscript descartaria. Comparar dos vacios siempre da identico.
  - Se exige que coincida el numero de paginas.
  - Se exige que el resultado renderice con contenido.
  - Lo que no pase cualquier comprobacion se queda intacto y se registra.
  - gs se invoca con la entrada estandar cerrada y con limite de tiempo: con
    ciertos archivos se queda bloqueado al 0% de CPU esperando entrada.
"""
import os, sys, csv, shutil, subprocess, argparse

def _np_pil():
    try:
        from PIL import Image
        import numpy as np
        return Image, np
    except ImportError:
        sys.exit("Falta PIL/numpy. Invoca este script con /usr/bin/python3, "
                 "no con el python3 de Homebrew.")
Image, np = _np_pil()

ap = argparse.ArgumentParser()
ap.add_argument("carpeta"); ap.add_argument("cuarentena"); ap.add_argument("manifiesto")
ap.add_argument("--dpi", type=int, default=300)
ap.add_argument("--ext", default=".ai")
ap.add_argument("--ganancia", type=float, default=0.80)
ap.add_argument("--dif", type=float, default=12.0)
ap.add_argument("--solo", default=None,
                help="fichero de texto con rutas relativas a procesar; el resto se ignora")
ap.add_argument("--timeout", type=int, default=300,
                help="segundos por archivo; gs puede colgarse con archivos malformados")
a = ap.parse_args()

EXT = tuple(e.strip().lower() for e in a.ext.split(","))
TMP = os.path.join(a.cuarentena, "_tmp")
os.makedirs(TMP, exist_ok=True)
if not shutil.which("gs"):
    sys.exit("No hay ghostscript. Instalalo con: brew install ghostscript")

def render(p, out, px=600):
    r = subprocess.run(["sips", "-s", "format", "png", "-Z", str(px), p, "--out", out],
                       capture_output=True)
    return r.returncode == 0 and os.path.exists(out)

def arr(p):
    return np.asarray(Image.open(p).convert("RGB"), float)

PAGBIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfpaginas")

def paginas(p):
    """Cuenta paginas via CoreGraphics. Devuelve -1 si no se puede determinar.

    NO contar la cadena "/Type/Page" en el binario: Ghostscript reescribe la
    estructura y comprime los objetos, asi que el recuento cambia sin que
    cambien las paginas. Eso produjo rechazos falsos sobre los archivos mas
    pesados (28 paginas contadas como 33 antes y 29 despues).
    """
    if not os.path.exists(PAGBIN):
        return -1          # sin el binario, no se comprueban paginas
    try:
        r = subprocess.run([PAGBIN, p], capture_output=True, text=True, timeout=120)
        return int(r.stdout.strip())
    except Exception:
        return -1

files = []
for r, _, fs in os.walk(a.carpeta):
    if os.sep + "_tmp" in r:
        continue
    for n in fs:
        if n.startswith("._"):
            continue
        if n.lower().endswith(EXT):
            files.append(os.path.join(r, n))
if a.solo:
    quiero = {l.strip() for l in open(a.solo, encoding="utf-8") if l.strip()}
    files = [f for f in files if os.path.relpath(f, a.carpeta) in quiero]
files.sort(key=os.path.getsize, reverse=True)
print(f"archivos a procesar: {len(files)}  ·  {a.dpi} dpi", flush=True)

filas = []
ok = blanco = sin = rech = err = 0
ganado = 0
for i, p in enumerate(files, 1):
    rel = os.path.relpath(p, a.carpeta)
    so = os.path.getsize(p)
    tmp = os.path.join(TMP, f"w{i}{os.path.splitext(p)[1]}")
    ro = os.path.join(TMP, "o.png")
    rn = os.path.join(TMP, "n.png")
    accion = "?"; sn = 0; dif = ""
    try:
        # 1. el original debe tener contenido visible
        if not render(p, ro):
            accion = "rechazado_sin_render"; rech += 1
        elif arr(ro).std() < 1.0:
            accion = "origen_en_blanco_no_tocar"; blanco += 1
        else:
            pin = paginas(p)
            r = subprocess.run(
                ["gs", "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dQUIET",
                 "-dDownsampleColorImages=true", f"-dColorImageResolution={a.dpi}",
                 "-dColorImageDownsampleType=/Bicubic",
                 "-dDownsampleGrayImages=true", f"-dGrayImageResolution={a.dpi}",
                 "-dGrayImageDownsampleType=/Bicubic",
                 "-dAutoFilterColorImages=false", "-dColorImageFilter=/DCTEncode",
                 f"-sOutputFile={tmp}", p],
                capture_output=True, timeout=a.timeout,
                stdin=subprocess.DEVNULL)   # sin esto gs puede quedarse
                                            # bloqueado esperando entrada
            if r.returncode != 0 or not os.path.exists(tmp):
                accion = "error_ghostscript"; err += 1
            else:
                sn = os.path.getsize(tmp)
                if sn > so * a.ganancia:
                    accion = "sin_ganancia"; sin += 1
                elif pin > 0 and paginas(tmp) != pin:
                    accion = "rechazado_paginas"; rech += 1
                elif not render(tmp, rn):
                    accion = "rechazado_sin_render"; rech += 1
                elif arr(rn).std() < 1.0:
                    accion = "rechazado_quedaba_en_blanco"; rech += 1
                else:
                    A, B = arr(ro), arr(rn)
                    if A.shape != B.shape:
                        B = np.asarray(Image.open(rn).convert("RGB")
                                       .resize(Image.open(ro).size), float)
                    dif = round(float(np.abs(A - B).mean()), 3)
                    if dif > a.dif:
                        accion = "rechazado_visual"; rech += 1
                    else:
                        os.makedirs(os.path.join(a.cuarentena, os.path.dirname(rel)),
                                    exist_ok=True)
                        st = os.stat(p)
                        shutil.move(p, os.path.join(a.cuarentena, rel))
                        shutil.move(tmp, p)
                        os.utime(p, (st.st_atime, st.st_mtime))
                        accion = "reducido"; ok += 1; ganado += so - sn
    except subprocess.TimeoutExpired:
        accion = "error_timeout"; err += 1
    except Exception as e:
        accion = f"error:{type(e).__name__}"; err += 1
    for x in (tmp, ro, rn):
        if os.path.exists(x) and accion != "reducido":
            try: os.remove(x)
            except OSError: pass
        elif x != tmp and os.path.exists(x):
            try: os.remove(x)
            except OSError: pass
    filas.append([rel, so, sn, dif, accion])
    if i % 10 == 0 or i == len(files):
        print(f"  {i}/{len(files)}  reducidos={ok} sin_ganancia={sin} "
              f"en_blanco_saltados={blanco} rechazados={rech} errores={err}  "
              f"liberado={ganado/2**30:.2f} GB", flush=True)

with open(a.manifiesto, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ruta_relativa", "bytes_antes", "bytes_despues", "dif_media", "accion"])
    w.writerows(filas)
try: os.rmdir(TMP)
except OSError: pass
print(f"\nFIN  reducidos={ok}  sin_ganancia={sin}  en_blanco_saltados={blanco}  "
      f"rechazados={rech}  errores={err}")
print(f"espacio a liberar al vaciar la cuarentena: {ganado/2**30:.2f} GB")
print(f"manifiesto: {a.manifiesto}")
