"""Austrija: broj izlaza = kilometar. Iz izlaza sa brojem pravi "kal" ([naš km, km, smer]) za svaku sekciju
koja još nema kal sa tabli. Upotreba: python at_kal.py <assets/autoputevi> [--pisi]"""
import json, glob, os, sys, re, statistics

d0 = sys.argv[1]
pisi = '--pisi' in sys.argv
for f in sorted(glob.glob(os.path.join(d0, 'at-*.json'))):
    raw = open(f, encoding='utf-8').read()
    d = json.loads(raw)
    izm = []
    for si, sek in enumerate(d['sekcije']):
        if sek.get('kal'):
            izm.append(f's{si}:ima')
            continue
        tacke = []
        for s in d['stavke']:
            if s.get('si', 0) != si or s.get('t') != 'A':
                continue
            r = str(s.get('ref', ''))
            if not re.fullmatch(r'\d{1,3}', r):
                continue
            tacke.append((s['km'], int(r)))
        tacke.sort()
        if len(tacke) < 3:
            izm.append(f's{si}:malo({len(tacke)})')
            continue
        # smer: raste li broj izlaza sa našim km
        rast = sum(1 for a, b in zip(tacke, tacke[1:]) if b[1] > a[1])
        pad = sum(1 for a, b in zip(tacke, tacke[1:]) if b[1] < a[1])
        smer = 1 if rast >= pad else -1
        off = [b - smer * a for a, b in tacke]
        # zadrži tačke čiji se pomeraj slaže sa lokalnom medijanom (do 3 km)
        dobre = []
        for i, (a, b) in enumerate(tacke):
            okolina = off[max(0, i - 3):i + 4]
            if abs(off[i] - statistics.median(okolina)) <= 3:
                dobre.append([round(a, 2), b, smer])
        if len(dobre) < 3:
            izm.append(f's{si}:neslaganje')
            continue
        sek['kal'] = dobre
        izm.append(f's{si}:{len(dobre)}/{len(tacke)} smer{smer:+d} pomeraj~{statistics.median(off):.0f}')
    print(os.path.basename(f), ' '.join(izm))
    if pisi:
        open(f, 'w', encoding='utf-8', newline='').write(json.dumps(d, ensure_ascii=False, separators=(',', ':')))
