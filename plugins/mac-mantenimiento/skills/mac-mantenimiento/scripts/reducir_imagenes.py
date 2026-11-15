#!/usr/bin/env python3
"""Aplana PSD y reduce imagenes al tamano que la impresion puede usar, con sips.
Conserva nombre y extension para no romper vinculos de maquetacion.
Originales a cuarentena, todo al manifiesto.

Uso:
  reducir_imagenes.py CARPETA CUARENTENA MANIFIESTO.csv
                      [--tope 3508] [--calidad 90] [--ganancia 0.80] [--dif 6.0]

--tope es el lado mayor en pixeles. Referencias utiles:
    3508  A4 a sangre a 300 dpi
    4961  A3 a sangre a 300 dpi
    2480  A4 a 210 dpi (archivo de registro, no reimprimible)

Salvaguarda importante: sips PREMULTIPLICA el RGB por el alfa al escribir PSD.
Un PSD con canal alfa sale con el fondo en negro y, colocado sobre claro, se ve
oscurecido. La comparacion visual lo detecta y esos archivos se quedan intactos:
aparecen como 'rechazado_visual'. Para reducirlos habria que escribir el PSD
conservando alfa recto, que sips no sabe hacer.
"""
import os, sys, csv, shutil, subprocess, argparse

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit("Falta PIL/numpy. Invoca con /usr/bin/python3, no con el de Homebrew.")

ap = argparse.ArgumentParser()
ap.add_argument("carpeta"); ap.add_argument("cuarentena"); ap.add_argument("manifiesto")
ap.add_argument("--tope", type=int, default=3508)
ap.add_argument("--calidad", type=int, default=90)
ap.add_argument("--ganancia", type=float, default=0.80)
ap.add_argument("--dif", type=float, default=6.0)
a = ap.parse_args()

FMT = {".psd": "psd", ".psb": "psd", ".jpg": "jpeg", ".jpeg": "jpeg",
       ".png": "png", ".tif": "tiff", ".tiff": "tiff"}
TMP = os.path.join(a.cuarentena, "_tmp")
os.makedirs(TMP, exist_ok=True)

def dims(p):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", p],
                         capture_output=True, text=True, timeout=120).stdout
    d = {}
    for ln in out.splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1); d[k.strip()] = v.strip()
    return int(float(d.get("pixelWidth", 0))), int(float(d.get("pixelHeight", 0)))

def render(p, out, px=500):
    r = subprocess.run(["sips", "-s", "format", "png", "-Z", str(px), p, "--out", out],
                       capture_output=True)
    return r.returncode == 0 and os.path.exists(out)

def arr(p):
    return np.asarray(Image.open(p).convert("RGB"), float)

files = []
for r, _, fs in os.walk(a.carpeta):
    if os.sep + "_tmp" in r:
        continue
    for n in fs:
        if not n.startswith("._") and os.path.splitext(n)[1].lower() in FMT:
            files.append(os.path.join(r, n))
files.sort(key=os.path.getsize, reverse=True)
print(f"imagenes a procesar: {len(files)}  ·  tope {a.tope} px", flush=True)

filas = []; ok = sin = rech = err = 0; ganado = 0
for i, p in enumerate(files, 1):
    rel = os.path.relpath(p, a.carpeta); so = os.path.getsize(p)
    e = os.path.splitext(p)[1].lower(); fmt = FMT[e]
    tmp = os.path.join(TMP, f"w{i}{e}")
    ro = os.path.join(TMP, "o.png"); rn = os.path.join(TMP, "n.png")
    accion = "?"; sn = 0; dif = ""; wh = ""
    try:
        w, h = dims(p); wh = f"{w}x{h}"
        if max(w, h) == 0:
            raise ValueError("sin dimensiones")
        cmd = ["sips", "-s", "format", fmt]
        if fmt == "jpeg":
            cmd += ["-s", "formatOptions", str(a.calidad)]
        if max(w, h) > a.tope:
            cmd += ["-Z", str(a.tope)]
        cmd += [p, "--out", tmp]
        r = subprocess.run(cmd, capture_output=True, timeout=900)
        if r.returncode != 0 or not os.path.exists(tmp):
            accion = "error_conversion"; err += 1
        else:
            sn = os.path.getsize(tmp)
            if sn > so * a.ganancia:
                accion = "sin_ganancia"; sin += 1
            elif not (render(p, ro) and render(tmp, rn)):
                accion = "rechazado_sin_render"; rech += 1
            else:
                A, B = arr(ro), arr(rn)
                if A.shape != B.shape:
                    B = np.asarray(Image.open(rn).convert("RGB")
                                   .resize(Image.open(ro).size), float)
                dif = round(float(np.abs(A - B).mean()), 3)
                if dif > a.dif:
                    accion = "rechazado_visual"; rech += 1
                else:
                    os.makedirs(os.path.join(a.cuarentena, os.path.dirname(rel)), exist_ok=True)
                    st = os.stat(p)
                    shutil.move(p, os.path.join(a.cuarentena, rel))
                    shutil.move(tmp, p)
                    os.utime(p, (st.st_atime, st.st_mtime))
                    accion = "reducido"; ok += 1; ganado += so - sn
    except subprocess.TimeoutExpired:
        accion = "error_timeout"; err += 1
    except Exception as ex:
        accion = f"error:{type(ex).__name__}"; err += 1
    for x in (tmp, ro, rn):
        if os.path.exists(x) and not (x == tmp and accion == "reducido"):
            try: os.remove(x)
            except OSError: pass
    filas.append([rel, so, sn, wh, dif, accion])
    if i % 50 == 0 or i == len(files):
        print(f"  {i}/{len(files)}  reducidos={ok} sin_ganancia={sin} "
              f"rechazados={rech} errores={err}  liberado={ganado/2**30:.2f} GB", flush=True)

with open(a.manifiesto, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ruta_relativa", "bytes_antes", "bytes_despues", "dimensiones_antes",
                "dif_media", "accion"])
    w.writerows(filas)
try: os.rmdir(TMP)
except OSError: pass
print(f"\nFIN  reducidos={ok}  sin_ganancia={sin}  rechazados={rech}  errores={err}")
print(f"espacio a liberar al vaciar la cuarentena: {ganado/2**30:.2f} GB")
