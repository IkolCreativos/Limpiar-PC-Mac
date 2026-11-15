#!/usr/bin/env python3
"""Cruza N carpetas y devuelve la matriz de solapamiento por contenido.
Solo lee: no mueve ni borra nada.

Uso:  cruce_ubicaciones.py ETIQUETA=/ruta [ETIQUETA=/ruta ...] [--json salida.json]

Salida: cuántos grupos de archivos idénticos comparte cada combinación de
ubicaciones, cuánto espacio sobra, y qué porcentaje de cada carpeta es exclusivo.
"""
import os, sys, hashlib, json
from collections import defaultdict

MIN = int(os.environ.get('CRUCE_MIN', 8*1024))

def hp(p, n=65536):
    try:
        with open(p,'rb') as f: return hashlib.md5(f.read(n)).hexdigest()
    except OSError: return None

def ht(p):
    h=hashlib.md5()
    try:
        with open(p,'rb') as f:
            for b in iter(lambda: f.read(1<<20), b''): h.update(b)
    except OSError: return None
    return h.hexdigest()

def hum(n):
    for u in ('B','KB','MB','GB','TB'):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"

salida=None
_av=sys.argv[1:]
if '--json' in _av:
    i=_av.index('--json')
    salida=_av[i+1] if i+1<len(_av) else None
    del _av[i:i+2]
args=[a for a in _av if not a.startswith('--')]
if not args:
    sys.exit(__doc__)
UB={}
for a in args:
    if '=' not in a: sys.exit(f"formato: ETIQUETA=/ruta  (recibido: {a})")
    k,v=a.split('=',1); UB[k]=v

por_tam=defaultdict(list); cuenta=defaultdict(int); peso=defaultdict(int)
for k,base in UB.items():
    if not os.path.isdir(base):
        print(f"AVISO: no existe {base}", file=sys.stderr); continue
    for r,_,fs in os.walk(base):
        for nm in fs:
            if nm.startswith('._') or nm=='.DS_Store' or nm.endswith('.icloud'): continue
            p=os.path.join(r,nm)
            try: sz=os.path.getsize(p)
            except OSError: continue
            cuenta[k]+=1; peso[k]+=sz
            if sz<MIN or sz==0: continue
            por_tam[sz].append((k,p))
print("Indexado:", {k:f"{cuenta[k]:,}" for k in UB}, file=sys.stderr)

pre=defaultdict(list)
for sz,items in por_tam.items():
    if len(items)<2: continue
    for k,p in items:
        h=hp(p)
        if h: pre[(sz,h)].append((k,p))
print(f"Candidatos tras hash parcial: {sum(len(v) for v in pre.values() if len(v)>1):,}", file=sys.stderr)

grupos=defaultdict(list)
for key,items in pre.items():
    if len(items)<2: continue
    for k,p in items:
        h=ht(p)
        if h: grupos[(key[0],h)].append((k,p))
dups={k:v for k,v in grupos.items() if len(v)>1}

comb=defaultdict(lambda:[0,0])
fuera=defaultdict(set)
for (sz,_),items in dups.items():
    ks=sorted(set(k for k,_ in items))
    comb[tuple(ks)][0]+=1
    comb[tuple(ks)][1]+=sz*(len(items)-1)
    for k,p in items:
        if set(ks)-{k}: fuera[k].add(p)

print("\n=== INVENTARIO ===")
for k in UB: print(f"  {k:<12} {cuenta[k]:8,} archivos  {hum(peso[k]):>10}")

print("\n=== SOLAPAMIENTOS ===")
for locs,(n,w) in sorted(comb.items(), key=lambda x:-x[1][1]):
    et=" + ".join(locs) if len(locs)>1 else f"{locs[0]} (interno)"
    print(f"  {et:<34} {n:6,} grupos   sobran {hum(w)}")

print("\n=== EXCLUSIVIDAD ===")
for k in UB:
    n=len(fuera[k]); tot=max(cuenta[k],1)
    pf=sum(os.path.getsize(p) for p in fuera[k] if os.path.exists(p))
    print(f"  {k:<12} con gemelo en otra ubicacion: {n:7,} de {cuenta[k]:,} ({n*100//tot}%)"
          f"   exclusivo: {hum(peso[k]-pf)}")

if salida:
    json.dump({f"{k[0]}|{k[1]}":v for k,v in dups.items()}, open(salida,"w"))
    print(f"\n  detalle: {salida}")
