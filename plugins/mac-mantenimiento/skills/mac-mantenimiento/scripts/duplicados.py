#!/usr/bin/env python3
"""Detecta archivos idénticos por CONTENIDO, sin importar el nombre.
Estrategia en 3 pasadas para no leer el disco entero:
  1. agrupa por tamaño  -> descarta todo lo que es único
  2. hash de los primeros 64 KB -> descarta casi todos los falsos positivos
  3. hash completo      -> confirmación
Uso: duplicados.py <carpeta> [carpeta2 ...]"""
import os, sys, hashlib
from collections import defaultdict

IGNORAR = {'.DS_Store', 'Icon\r', 'Thumbs.db'}
MIN = int(os.environ.get('DEDUP_MIN', 64*1024))  # umbral; DEDUP_MIN=0 para barrido exhaustivo

def hash_parcial(ruta, n=65536):
    try:
        with open(ruta, 'rb') as f: return hashlib.md5(f.read(n)).hexdigest()
    except OSError: return None

def hash_total(ruta):
    h = hashlib.md5()
    try:
        with open(ruta, 'rb') as f:
            for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    except OSError: return None
    return h.hexdigest()

def humano(n):
    for u in ('B','KB','MB','GB','TB'):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"

def main(dirs):
    por_tam = defaultdict(list); total = 0
    for d in dirs:
        for raiz, _, files in os.walk(d):
            for nm in files:
                if nm in IGNORAR or nm.startswith('._'): continue
                p = os.path.join(raiz, nm)
                try:
                    st = os.lstat(p)
                    if not os.path.isfile(p) or os.path.islink(p): continue
                    if st.st_size < MIN: continue
                    por_tam[st.st_size].append(p); total += 1
                except OSError: continue
    cand = {t: ps for t, ps in por_tam.items() if len(ps) > 1}
    print(f"Archivos escaneados: {total:,}", file=sys.stderr)
    print(f"Con tamaño repetido: {sum(len(v) for v in cand.values()):,}", file=sys.stderr)

    por_parcial = defaultdict(list)
    for t, ps in cand.items():
        for p in ps:
            h = hash_parcial(p)
            if h: por_parcial[(t, h)].append(p)
    cand2 = {k: v for k, v in por_parcial.items() if len(v) > 1}
    print(f"Tras hash parcial:   {sum(len(v) for v in cand2.values()):,}", file=sys.stderr)

    grupos = defaultdict(list)
    for (t, _), ps in cand2.items():
        for p in ps:
            h = hash_total(p)
            if h: grupos[(t, h)].append(p)

    dups = {k: v for k, v in grupos.items() if len(v) > 1}
    desperdicio = sum(t * (len(v) - 1) for (t, _), v in dups.items())
    print(f"\n{'='*70}")
    print(f"GRUPOS DE DUPLICADOS: {len(dups)}   |   ESPACIO RECUPERABLE: {humano(desperdicio)}")
    print('='*70)
    for (t, _), v in sorted(dups.items(), key=lambda x: -x[0][0]*(len(x[1])-1)):
        print(f"\n[{humano(t)} x {len(v)} copias  -> sobran {humano(t*(len(v)-1))}]")
        for p in sorted(v): print(f"   {p}")

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit("Uso: duplicados.py <carpeta> [...]")
    main(sys.argv[1:])
