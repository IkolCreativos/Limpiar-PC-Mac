#!/usr/bin/env python3
"""Reescribe archivos de ilustracion soltando los datos nativos y conservando
los vectores. Conserva nombre y extension para no romper vinculos de maquetacion
(un .ai que por dentro es PDF limpio se sigue colocando igual).

Usa la utilidad airewrite (CoreGraphics), que NO necesita Ghostscript.
Para archivos cuyo peso sean fotos incrustadas, usar reducir_incrustadas.py.

Compilar antes:  swiftc -O -o airewrite airewrite.swift

Uso:
  aplanar_ilustracion.py CARPETA CUARENTENA MANIFIESTO.csv
                         [--ext .ai] [--ganancia 0.80] [--dif 1.0]

Salvaguarda que da nombre a este script: si el ORIGINAL renderiza en blanco, no
se toca. Un .ai guardado sin compatibilidad PDF tiene la capa PDF vacia; al
reescribirlo se pierde todo su contenido, y compararlo antes y despues no lo
detecta porque ambos renders salen en blanco. Comparar dos vacios da identico.
"""
import os, sys, csv, shutil, subprocess, argparse

try:
    from PIL import Image
    import numpy as np
except ImportError:
    sys.exit("Falta PIL/numpy. Invoca con /usr/bin/python3, no con el de Homebrew.")

ap = argparse.ArgumentParser()
ap.add_argument("carpeta"); ap.add_argument("cuarentena"); ap.add_argument("manifiesto")
ap.add_argument("--ext", default=".ai")
ap.add_argument("--ganancia", type=float, default=0.80)
ap.add_argument("--dif", type=float, default=1.0)
ap.add_argument("--bin", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "airewrite"))
a = ap.parse_args()

if not os.path.exists(a.bin):
    sys.exit(f"Falta la utilidad {a.bin}. Compilala:\n"
             f"  swiftc -O -o {a.bin} {a.bin}.swift")

EXT = tuple(e.strip().lower() for e in a.ext.split(","))
TMP = os.path.join(a.cuarentena, "_tmp")
os.makedirs(TMP, exist_ok=True)

def render(p, out, px=600):
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
        if not n.startswith("._") and n.lower().endswith(EXT):
            files.append(os.path.join(r, n))
files.sort(key=os.path.getsize, reverse=True)
print(f"archivos a procesar: {len(files)}", flush=True)

filas = []; ok = blanco = sin = rech = err = 0; ganado = 0
for i, p in enumerate(files, 1):
    rel = os.path.relpath(p, a.carpeta); so = os.path.getsize(p)
    tmp = os.path.join(TMP, f"w{i}.pdf")
    ro = os.path.join(TMP, "o.png"); rn = os.path.join(TMP, "n.png")
    accion = "?"; sn = 0; dif = ""; pg = ""
    try:
        if not render(p, ro):
            accion = "rechazado_sin_render"; rech += 1
        elif arr(ro).std() < 1.0:
            accion = "origen_en_blanco_no_tocar"; blanco += 1
        else:
            r = subprocess.run([a.bin, p, tmp], capture_output=True, text=True, timeout=900)
            if r.returncode != 0 or not os.path.exists(tmp):
                accion = "error_reescritura"; err += 1
            else:
                pg = r.stdout.strip()
                t = pg.split()
                pin, pout = t[0].split("=")[1], t[1].split("=")[1]
                w1, w2 = t[2].split("=")[1].split("/"); h1, h2 = t[3].split("=")[1].split("/")
                sn = os.path.getsize(tmp)
                if pin != pout or w1 != w2 or h1 != h2:
                    accion = "rechazado_estructura"; rech += 1
                elif sn > so * a.ganancia:
                    accion = "sin_ganancia"; sin += 1
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
                        os.makedirs(os.path.join(a.cuarentena, os.path.dirname(rel)), exist_ok=True)
                        st = os.stat(p)
                        shutil.move(p, os.path.join(a.cuarentena, rel))
                        shutil.move(tmp, p)
                        os.utime(p, (st.st_atime, st.st_mtime))
                        accion = "aplanado"; ok += 1; ganado += so - sn
    except subprocess.TimeoutExpired:
        accion = "error_timeout"; err += 1
    except Exception as e:
        accion = f"error:{type(e).__name__}"; err += 1
    for x in (tmp, ro, rn):
        if os.path.exists(x) and not (x == tmp and accion == "aplanado"):
            try: os.remove(x)
            except OSError: pass
    filas.append([rel, so, sn, pg, dif, accion])
    if i % 25 == 0 or i == len(files):
        print(f"  {i}/{len(files)}  aplanados={ok} sin_ganancia={sin} "
              f"en_blanco_saltados={blanco} rechazados={rech} errores={err}  "
              f"liberado={ganado/2**30:.2f} GB", flush=True)

with open(a.manifiesto, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ruta_relativa", "bytes_antes", "bytes_despues", "paginas", "dif_media", "accion"])
    w.writerows(filas)
try: os.rmdir(TMP)
except OSError: pass
print(f"\nFIN  aplanados={ok}  sin_ganancia={sin}  en_blanco_saltados={blanco}  "
      f"rechazados={rech}  errores={err}")
print(f"espacio a liberar al vaciar la cuarentena: {ganado/2**30:.2f} GB")
