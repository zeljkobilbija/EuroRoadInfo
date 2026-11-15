"""
Ikona EuroRoadInfo: zastava EU (12 zlatnih zvezda u krugu na plavom polju).
Pravi vektorske ikone (adaptivna ikona, splash), PNG ikone za Android < 8 i ikonu za Google Play (512 px).
    python alati/ikona_eu.py
Proporcije kao na zastavi: krug zvezda = 1/3 visine, poluprečnik zvezde = 1/18 visine.
"""
import math
import os
from PIL import Image, ImageDraw

KOREN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RES = os.path.join(KOREN, 'app', 'src', 'main', 'res')
PLAVA, ZLATNA = '#003399', '#FFCC00'


def zvezda(cx, cy, r):
    """Petokraka zvezda (vrh gore) kao lista tačaka."""
    t = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.382
        t.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return t


def zvezde(c, krug, r):
    return [zvezda(c + krug * math.sin(k * math.pi / 6), c - krug * math.cos(k * math.pi / 6), r) for k in range(12)]


def putanja(zv):
    return ' '.join('M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in z) + ' Z' for z in zv)


def vektor(ime, opis, boja, krug, r, velicina='108dp'):
    p = putanja(zvezde(54, krug, r))
    with open(os.path.join(RES, 'drawable', ime), 'w', encoding='utf-8') as f:
        f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<!-- {opis} (generiše alati/ikona_eu.py) -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="{velicina}"
    android:height="{velicina}"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="{boja}" android:pathData="{p}" />
</vector>
''')


# adaptivna ikona: bezbedna zona je krug prečnika 66 od 108 → krug zvezda 21, zvezda 3.9
vektor('ic_launcher_foreground.xml', 'Ikona: 12 zvezda zastave EU', ZLATNA, 21, 3.9)
vektor('ic_splash.xml', 'Splash: 12 zvezda zastave EU', ZLATNA, 21, 3.9, '288dp')
with open(os.path.join(RES, 'drawable', 'ic_launcher_background.xml'), 'w', encoding='utf-8') as f:
    f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Pozadina ikone: plava zastave EU -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="{PLAVA}" android:pathData="M0,0h108v108h-108z" />
</vector>
''')


def slika(px, okrugla=False, ugao=0.0):
    """Ikona u PNG-u (crta se 4× veća pa se smanjuje, zbog glatkih ivica)."""
    s = px * 4
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if okrugla:
        d.ellipse((0, 0, s - 1, s - 1), fill=PLAVA)
    else:
        d.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * ugao), fill=PLAVA)
    for z in zvezde(s / 2, s * 0.30, s * 0.056):
        d.polygon(z, fill=ZLATNA)
    return im.resize((px, px), Image.LANCZOS)


for gustina, px in {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}.items():
    d = os.path.join(RES, 'mipmap-' + gustina)
    slika(px, ugao=0.18).save(os.path.join(d, 'ic_launcher.png'))
    slika(px, okrugla=True).save(os.path.join(d, 'ic_launcher_round.png'))
# Google Play: pun kvadrat bez providnosti (Play sam zaobljuje uglove)
slika(512).convert('RGB').save(os.path.join(KOREN, 'alati', 'ikona_play_512.png'))
print('ikone gotove')
