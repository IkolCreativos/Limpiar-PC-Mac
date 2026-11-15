#!/usr/bin/env python3
"""Verifica que un destino contenga integramente un origen.
Comprueba cobertura por ruta y una muestra aleatoria de hashes MD5.
Uso: verificar_copia.py ORIGEN DESTINO [n_muestra]
"""
import os, sys, hashlib, random
S,D = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv)>3 else 50
def ht(p):
    h=hashlib.md5()
    with open(p,'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''): h.update(b)
    return h.hexdigest()
pares=[]; faltan=[]
for r,_,fs in os.walk(S):
    for nm in fs:
        if nm.startswith('._') or nm=='.DS_Store': continue
        a=os.path.join(r,nm); rel=os.path.relpath(a,S); b=os.path.join(D,rel)
        (pares.append((a,b)) if os.path.exists(b) else faltan.append(rel))
print("=== COBERTURA ===")
print(f"  archivos en origen : {len(pares)+len(faltan):,}")
print(f"  presentes destino  : {len(pares):,}")
print(f"  FALTAN             : {len(faltan)}")
for f in faltan[:10]: print("    ", f)
if pares:
    random.seed(1); m=random.sample(pares, min(N,len(pares)))
    ok=bad=0
    for a,b in m:
        try:
            if ht(a)==ht(b): ok+=1
            else: bad+=1; print("  DIFIERE:", os.path.relpath(a,S))
        except Exception as e: bad+=1; print("  ERROR:", e)
    print(f"\n=== HASH (muestra de {len(m)}) ===")
    print(f"  identicos: {ok}   distintos: {bad}")
print(f"\n  >> {'VERIFICADO' if not faltan and not bad else 'REVISAR'}")
