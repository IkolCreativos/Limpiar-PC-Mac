#!/usr/bin/env python3
"""Organiza fotos y videos en AÑO/MES[/CAMARA] leyendo metadatos reales.
Soporta JPEG, HEIC, PNG (via sips) y MOV/MP4 (via ffprobe).
NUNCA borra: solo mueve. Sin --ejecutar hace simulacion.

Uso:  organizar_multimedia.py ORIGEN [ORIGEN2 ...] DESTINO [--ejecutar] [--sin-camara]

Notas:
  - Un parser EXIF de JPEG NO lee HEIC: por eso se usa sips.
  - mdls devuelve fecha de sistema de archivos en video: por eso ffprobe.
  - Las carpetas tematicas (por persona o evento) NO deben pasarse aqui sin
    preguntar: reorganizarlas por fecha destruye esa agrupacion.
"""
import os, sys, re, subprocess, shutil, csv
from collections import Counter

MESES={1:"01-enero",2:"02-febrero",3:"03-marzo",4:"04-abril",5:"05-mayo",6:"06-junio",
       7:"07-julio",8:"08-agosto",9:"09-septiembre",10:"10-octubre",11:"11-noviembre",
       12:"12-diciembre"}
VIDEO={'.mov','.mp4','.m4v','.avi','.3gp','.mpg','.mpeg','.mkv','.mts','.m2ts'}
NULOS={"<nil>","nil",""}
UMBRAL_CAMARA=int(os.environ.get('UMBRAL_CAMARA','15'))

def meta_imagen(p):
    try:
        out=subprocess.run(["sips","-g","creation","-g","make","-g","model",p],
                           capture_output=True,text=True,timeout=20).stdout
    except Exception: return (None,None)
    f=re.search(r'creation:\s*(\d{4}):(\d{2})',out)
    mk=re.search(r'make:\s*(.+)',out); md=re.search(r'model:\s*(.+)',out)
    cam=(md.group(1).strip() if md else None) or (mk.group(1).strip() if mk else None)
    if cam in NULOS: cam=None
    return ((int(f.group(1)),int(f.group(2))) if f else None, cam)

def meta_video(p):
    try:
        out=subprocess.run(["ffprobe","-v","quiet","-show_entries",
            "format_tags=creation_time,com.apple.quicktime.model","-of","default=nw=1",p],
            capture_output=True,text=True,timeout=25).stdout
    except Exception: return (None,None)
    f=re.search(r'creation_time=(\d{4})-(\d{2})',out)
    md=re.search(r'quicktime\.model=(.+)',out)
    cam=md.group(1).strip() if md else None
    if cam in NULOS: cam=None
    return ((int(f.group(1)),int(f.group(2))) if f else None, cam)

RX_NOMBRE=re.compile(r'(19|20)\d{2}[-_](\d{2})[-_]\d{2}')

def limpio(s):
    s=re.sub(r'[<>:"/\\|?*]',' ',s or ''); s=re.sub(r'\s+',' ',s).strip()
    return s[:40] or "desconocida"

args=[a for a in sys.argv[1:] if not a.startswith('--')]
if len(args)<2: sys.exit(__doc__)
ORIGENES=args[:-1]; DEST=args[-1]
EJEC='--ejecutar' in sys.argv
USAR_CAM='--sin-camara' not in sys.argv

arch=[]
for O in ORIGENES:
    if not os.path.isdir(O): print(f"AVISO: no existe {O}",file=sys.stderr); continue
    for r,_,fs in os.walk(O):
        if os.path.abspath(r).startswith(os.path.abspath(DEST)): continue
        for nm in fs:
            if nm.startswith('._') or nm=='.DS_Store' or nm.endswith('.icloud'): continue
            arch.append(os.path.join(r,nm))
print(f"archivos a procesar: {len(arch):,}", file=sys.stderr)

plan=[]; cams=Counter(); anios=Counter(); sinf=0
for i,p in enumerate(arch):
    ext=os.path.splitext(p)[1].lower()
    fecha,cam = meta_video(p) if ext in VIDEO else meta_imagen(p)
    if not fecha:
        g=RX_NOMBRE.search(os.path.basename(p))
        if g: fecha=(int(g.group(0)[:4]), int(g.group(2)))
    if not fecha or not (1990<=fecha[0]<=2035): sinf+=1; fecha=None
    else: anios[fecha[0]]+=1
    cams[cam or "sin-camara"]+=1
    plan.append((p,fecha,cam))
    if (i+1)%300==0: print(f"  ...{i+1:,}", file=sys.stderr)

grupo={c:(limpio(c) if n>=UMBRAL_CAMARA else "otras-camaras") for c,n in cams.items()}
grupo["sin-camara"]="sin-camara"
ruidosas=sum(1 for c,n in cams.items() if n<UMBRAL_CAMARA)

print(f"\n=== {'EJECUTADO' if EJEC else 'SIMULACION (no se movio nada)'} ===")
print(f"  archivos        : {len(arch):,}")
print(f"  sin fecha       : {sinf:,}")
print(f"  camaras          : {len(cams)}  ({ruidosas} agrupadas en 'otras-camaras')")
print("\n  por año:")
for a,n in sorted(anios.items()): print(f"    {a}: {n:,}")
print("\n  camaras principales:")
for c,n in cams.most_common(10): print(f"    {n:6,}  {c}")

if EJEC:
    filas=[]; mov=0
    for p,f,c in plan:
        sub = os.path.join(str(f[0]), MESES[f[1]]) if f else "sin-fecha"
        if USAR_CAM: sub=os.path.join(sub, grupo[c or "sin-camara"])
        dd=os.path.join(DEST,sub); os.makedirs(dd,exist_ok=True)
        nm=os.path.basename(p); fin=os.path.join(dd,nm); k=1
        while os.path.exists(fin):
            b,e=os.path.splitext(nm); fin=os.path.join(dd,f"{b}__{k}{e}"); k+=1
        if os.path.abspath(p)==os.path.abspath(fin): continue
        try:
            shutil.move(p,fin); mov+=1
            filas.append([p, os.path.relpath(fin,DEST)])
        except Exception as ex: print("ERR",nm,ex,file=sys.stderr)
    man=os.path.join(os.path.dirname(DEST.rstrip('/')) or '.', "MANIFIESTO-organizacion.csv")
    with open(man,'w',newline='',encoding='utf-8') as fh:
        w=csv.writer(fh); w.writerow(["origen","destino"]); w.writerows(filas)
    print(f"\n  movidos: {mov:,}\n  manifiesto: {man}")
