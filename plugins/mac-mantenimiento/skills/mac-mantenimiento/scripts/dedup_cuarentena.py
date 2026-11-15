#!/usr/bin/env python3
"""Deduplica una carpeta MOVIENDO las copias sobrantes a una cuarentena
que conserva la estructura original. NUNCA borra nada.

De cada grupo de duplicados conserva UNA copia, eligiendo por este orden:
  1. la que tenga EXIF de camara (mas probable que sea el original)
  2. la de ruta mas corta
  3. orden alfabetico (determinista)

Uso: dedup_cuarentena.py <carpeta> <cuarentena> [--ejecutar]
Sin --ejecutar hace simulacion y no mueve nada."""
import os, sys, shutil, struct, hashlib, csv
from collections import defaultdict

MIN = int(os.environ.get('DEDUP_MIN', 8*1024))

def tiene_exif(ruta):
    try:
        with open(ruta, 'rb') as f: cab = f.read(65536)
    except OSError: return False
    i = cab.find(b'Exif\x00\x00')
    if i < 0: return False
    tiff = i + 6
    if len(cab) < tiff + 8: return False
    e = '<' if cab[tiff:tiff+2] == b'II' else '>' if cab[tiff:tiff+2] == b'MM' else None
    if not e: return False
    try:
        off = struct.unpack(e+'I', cab[tiff+4:tiff+8])[0]
        p = tiff + off
        n = struct.unpack(e+'H', cab[p:p+2])[0]; p += 2
        for _ in range(min(n, 80)):
            if p + 12 > len(cab): break
            tag = struct.unpack(e+'H', cab[p:p+2])[0]
            if tag in (0x010F, 0x0110): return True
            p += 12
    except Exception: pass
    return False

def h_parcial(r):
    try:
        with open(r,'rb') as f: return hashlib.md5(f.read(65536)).hexdigest()
    except OSError: return None

def h_total(r):
    h = hashlib.md5()
    try:
        with open(r,'rb') as f:
            for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    except OSError: return None
    return h.hexdigest()

def humano(n):
    for u in ('B','KB','MB','GB'):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

raiz, cuarentena = sys.argv[1], sys.argv[2]
ejecutar = '--ejecutar' in sys.argv

por_tam = defaultdict(list)
for r, _, fs in os.walk(raiz):
    if os.path.abspath(r).startswith(os.path.abspath(cuarentena)): continue
    for nm in fs:
        if nm.startswith('._') or nm == '.DS_Store': continue
        p = os.path.join(r, nm)
        try: sz = os.path.getsize(p)
        except OSError: continue
        if sz < MIN: continue
        por_tam[sz].append(p)

pre = defaultdict(list)
for t, ps in por_tam.items():
    if len(ps) < 2: continue
    for p in ps:
        hh = h_parcial(p)
        if hh: pre[(t, hh)].append(p)

grupos = defaultdict(list)
for k, ps in pre.items():
    if len(ps) < 2: continue
    for p in ps:
        hh = h_total(p)
        if hh: grupos[(k[0], hh)].append(p)

dups = {k: v for k, v in grupos.items() if len(v) > 1}

movidos = 0; liberado = 0
manifiesto = os.path.join(os.path.dirname(cuarentena), "MANIFIESTO-duplicados.csv")
filas = []
for (tam, hh), ps in sorted(dups.items()):
    ordenados = sorted(ps, key=lambda p: (not tiene_exif(p), len(p), p))
    conservar, sobrantes = ordenados[0], ordenados[1:]
    for s in sobrantes:
        rel = os.path.relpath(s, raiz)
        dest = os.path.join(cuarentena, rel)
        filas.append([rel, os.path.relpath(conservar, raiz), tam, hh[:12]])
        if ejecutar:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try: shutil.move(s, dest)
            except Exception as ex: print(f"  ERROR moviendo {rel}: {ex}"); continue
        movidos += 1; liberado += tam

modo = "EJECUTADO" if ejecutar else "SIMULACION (no se movio nada)"
print(f"=== {modo} ===")
print(f"  grupos de duplicados : {len(dups):,}")
print(f"  copias a cuarentena  : {movidos:,}")
print(f"  espacio a liberar    : {humano(liberado)}")
print(f"  se conservan          : {len(dups):,} originales (uno por grupo)")

if ejecutar or filas:
    with open(manifiesto, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(["archivo_movido", "copia_conservada", "bytes", "md5"])
        w.writerows(filas)
    print(f"\n  Manifiesto: {manifiesto}")
