"""
Ugrađuje glasovne poruke u Vožnju jedne aplikacije (EuroRoadInfo je izvor Glas.java).
  python alati/glas_ugradi.py <putanja do projekta>     npr. ../AustriaRoadInfo
Radi: kopira Glas.java (sa paketom aplikacije), dodaje tekstove na 18 jezika, dugme 🔊 na karticu Vožnja
(svi layout-i sa voznjaDugme), poziva Glas iz VoznjaService (start, autoput/km/pravac, odmorište ispred,
upozorenje o saobraćaju, stop) i VoznjaKartica (dugme). Ponovno pokretanje ne pravi duplikate.
"""
import os, re, sys

KOREN = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
IZVOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'src', 'main', 'java',
                     'com', 'zeljkobilbija001', 'euroroadinfo', 'Glas.java')
MAIN = os.path.join(KOREN, 'app', 'src', 'main')
JAVA = None
for d, _, f in os.walk(os.path.join(MAIN, 'java')):
    if 'VoznjaService.java' in f:
        JAVA = d
assert JAVA, 'nema VoznjaService.java'
PAKET = open(os.path.join(JAVA, 'VoznjaService.java'), encoding='utf-8').read().split(';')[0].replace('package ', '').strip()

# ---------- tekstovi ----------
T = {  # start, stop, polozaj, odmoriste, gorivo, saobracaj, km_jed, mi_jed, km_naz, mi_naz, dugme
 '':   ["Driving mode started. You will soon hear which motorway you are on.", "Driving mode stopped.",
        "You are on the %1$s, %3$s %2$s, towards %4$s.", "In %1$d %2$s, service area: %3$s.", "Fuel: %s.",
        "Traffic warning: in %1$d %2$s, %3$s.", "kilometres", "miles", "kilometre", "mile", "Voice messages"],
 'sr': ["Vožnja je pokrenuta. Uskoro ćete čuti na kom ste autoputu.", "Vožnja je zaustavljena.",
        "Nalazite se na autoputu %1$s, %3$s %2$s, pravac %4$s.", "Za %1$d %2$s, odmorište: %3$s.", "Gorivo: %s.",
        "Upozorenje: za %1$d %2$s, %3$s.", "kilometara", "milja", "kilometar", "milja", "Glasovne poruke"],
 'hr': ["Vožnja je pokrenuta. Uskoro ćete čuti na kojoj ste autocesti.", "Vožnja je zaustavljena.",
        "Nalazite se na autocesti %1$s, %3$s %2$s, smjer %4$s.", "Za %1$d %2$s, odmorište: %3$s.", "Gorivo: %s.",
        "Upozorenje: za %1$d %2$s, %3$s.", "kilometara", "milja", "kilometar", "milja", "Glasovne poruke"],
 'sl': ["Vožnja je zagnana. Kmalu boste slišali, na kateri avtocesti ste.", "Vožnja je ustavljena.",
        "Ste na avtocesti %1$s, %3$s %2$s, smer %4$s.", "Čez %1$d %2$s, počivališče: %3$s.", "Gorivo: %s.",
        "Opozorilo: čez %1$d %2$s, %3$s.", "kilometrov", "milj", "kilometer", "milja", "Glasovna sporočila"],
 'de': ["Fahrmodus gestartet. Gleich hören Sie, auf welcher Autobahn Sie sind.", "Fahrmodus beendet.",
        "Sie sind auf der %1$s, %3$s %2$s, Richtung %4$s.", "In %1$d %2$s, Raststätte: %3$s.", "Kraftstoff: %s.",
        "Verkehrswarnung: in %1$d %2$s, %3$s.", "Kilometern", "Meilen", "Kilometer", "Meile", "Sprachansagen"],
 'it': ["Modalità guida avviata. Tra poco saprai su quale autostrada ti trovi.", "Modalità guida fermata.",
        "Sei sulla %1$s, %3$s %2$s, direzione %4$s.", "Tra %1$d %2$s, area di servizio: %3$s.", "Carburante: %s.",
        "Attenzione traffico: tra %1$d %2$s, %3$s.", "chilometri", "miglia", "chilometro", "miglio", "Messaggi vocali"],
 'fr': ["Mode conduite démarré. Vous saurez bientôt sur quelle autoroute vous êtes.", "Mode conduite arrêté.",
        "Vous êtes sur l'autoroute %1$s, %3$s %2$s, direction %4$s.", "Dans %1$d %2$s, aire de service : %3$s.",
        "Carburant : %s.", "Alerte trafic : dans %1$d %2$s, %3$s.", "kilomètres", "miles", "kilomètre", "mile",
        "Messages vocaux"],
 'es': ["Modo conducción iniciado. Pronto sabrá en qué autopista está.", "Modo conducción detenido.",
        "Está en la autopista %1$s, %3$s %2$s, dirección %4$s.", "En %1$d %2$s, área de servicio: %3$s.",
        "Combustible: %s.", "Aviso de tráfico: en %1$d %2$s, %3$s.", "kilómetros", "millas", "kilómetro", "milla",
        "Mensajes de voz"],
 'pt': ["Modo condução iniciado. Em breve saberá em que autoestrada está.", "Modo condução parado.",
        "Está na autoestrada %1$s, %3$s %2$s, direção %4$s.", "Daqui a %1$d %2$s, área de serviço: %3$s.",
        "Combustível: %s.", "Aviso de trânsito: daqui a %1$d %2$s, %3$s.", "quilómetros", "milhas", "quilómetro",
        "milha", "Mensagens de voz"],
 'nl': ["Rijmodus gestart. U hoort zo op welke snelweg u bent.", "Rijmodus gestopt.",
        "U bent op de %1$s, %3$s %2$s, richting %4$s.", "Over %1$d %2$s, verzorgingsplaats: %3$s.", "Brandstof: %s.",
        "Verkeerswaarschuwing: over %1$d %2$s, %3$s.", "kilometer", "mijl", "kilometer", "mijl", "Spraakberichten"],
 'pl': ["Tryb jazdy uruchomiony. Wkrótce usłyszysz, na której autostradzie jesteś.", "Tryb jazdy zatrzymany.",
        "Jesteś na autostradzie %1$s, %3$s %2$s, kierunek %4$s.", "Za %1$d %2$s, MOP: %3$s.", "Paliwo: %s.",
        "Ostrzeżenie: za %1$d %2$s, %3$s.", "kilometrów", "mil", "kilometr", "mila", "Komunikaty głosowe"],
 'cs': ["Režim jízdy spuštěn. Brzy uslyšíte, na které dálnici jste.", "Režim jízdy zastaven.",
        "Jste na dálnici %1$s, %3$s %2$s, směr %4$s.", "Za %1$d %2$s, odpočívka: %3$s.", "Palivo: %s.",
        "Dopravní varování: za %1$d %2$s, %3$s.", "kilometrů", "mil", "kilometr", "míle", "Hlasové zprávy"],
 'sk': ["Režim jazdy spustený. Čoskoro budete počuť, na ktorej diaľnici ste.", "Režim jazdy zastavený.",
        "Ste na diaľnici %1$s, %3$s %2$s, smer %4$s.", "O %1$d %2$s, odpočívadlo: %3$s.", "Palivo: %s.",
        "Dopravné varovanie: o %1$d %2$s, %3$s.", "kilometrov", "míľ", "kilometer", "míľa", "Hlasové správy"],
 'hu': ["Vezetés mód elindítva. Hamarosan hallja, melyik autópályán van.", "Vezetés mód leállítva.",
        "Ön a(z) %1$s autópályán van, %3$s: %2$s, irány: %4$s.", "%1$d %2$s múlva pihenőhely: %3$s.",
        "Üzemanyag: %s.", "Forgalmi figyelmeztetés: %1$d %2$s múlva %3$s.", "kilométer", "mérföld", "kilométer",
        "mérföld", "Hangüzenetek"],
 'ro': ["Modul de conducere pornit. În curând veți afla pe ce autostradă sunteți.", "Modul de conducere oprit.",
        "Sunteți pe autostrada %1$s, %3$s %2$s, direcția %4$s.", "Peste %1$d %2$s, zonă de servicii: %3$s.",
        "Carburant: %s.", "Avertizare trafic: peste %1$d %2$s, %3$s.", "kilometri", "mile", "kilometrul", "mila",
        "Mesaje vocale"],
 'el': ["Η λειτουργία οδήγησης ξεκίνησε. Σύντομα θα ακούσετε σε ποιον αυτοκινητόδρομο βρίσκεστε.",
        "Η λειτουργία οδήγησης σταμάτησε.", "Βρίσκεστε στον αυτοκινητόδρομο %1$s, %3$s %2$s, κατεύθυνση %4$s.",
        "Σε %1$d %2$s, σταθμός εξυπηρέτησης: %3$s.", "Καύσιμα: %s.", "Προειδοποίηση κυκλοφορίας: σε %1$d %2$s, %3$s.",
        "χιλιόμετρα", "μίλια", "χιλιόμετρο", "μίλι", "Φωνητικά μηνύματα"],
 'ru': ["Режим вождения запущен. Скоро вы услышите, на какой автомагистрали находитесь.",
        "Режим вождения остановлен.", "Вы на автомагистрали %1$s, %3$s %2$s, направление %4$s.",
        "Через %1$d %2$s, зона отдыха: %3$s.", "Топливо: %s.", "Внимание: через %1$d %2$s, %3$s.", "километров",
        "миль", "километр", "миля", "Голосовые сообщения"],
 'tr': ["Sürüş modu başlatıldı. Yakında hangi otoyolda olduğunuzu duyacaksınız.", "Sürüş modu durduruldu.",
        "%1$s otoyolundasınız, %3$s %2$s, yön %4$s.", "%1$d %2$s sonra dinlenme tesisi: %3$s.", "Yakıt: %s.",
        "Trafik uyarısı: %1$d %2$s sonra %3$s.", "kilometre", "mil", "kilometre", "mil", "Sesli mesajlar"],
}
IMENA = ['glas_start', 'glas_stop', 'glas_polozaj', 'glas_odmoriste', 'glas_gorivo', 'glas_saobracaj',
         'glas_km_jed', 'glas_mi_jed', 'glas_km_naziv', 'glas_mi_naziv', 'glas_dugme']
res = os.path.join(MAIN, 'res')
n = 0
for d in sorted(os.listdir(res)):
    if not re.fullmatch(r'values(-[a-z]{2})?', d): continue
    p = os.path.join(res, d, 'strings.xml')
    if not os.path.exists(p): continue
    jez = d[7:] if d != 'values' else ''
    if jez not in T: continue
    s = open(p, encoding='utf-8').read()
    if 'name="glas_start"' in s: continue
    red = '    <!-- Glasovne poruke u Vožnji -->\n' + ''.join(
        '    <string name="%s"%s>%s</string>\n' % (k, ' formatted="false"' if False else '',
                                                    v.replace("'", "\\'"))
        for k, v in zip(IMENA, T[jez]))
    s = s.replace('</resources>', red + '</resources>')
    open(p, 'w', encoding='utf-8').write(s); n += 1
print('tekstovi:', n, 'jezika')

# ---------- Glas.java ----------
g = open(IZVOR, encoding='utf-8').read().replace('package com.zeljkobilbija001.euroroadinfo;', 'package %s;' % PAKET)
open(os.path.join(JAVA, 'Glas.java'), 'w', encoding='utf-8').write(g)

# ---------- layout: dugme 🔊 ispred kružića ----------
DUGME = '''        <TextView
            android:id="@+id/voznjaGlas"
            android:layout_width="40dp"
            android:layout_height="40dp"
            android:layout_marginStart="6dp"
            android:background="?attr/selectableItemBackgroundBorderless"
            android:contentDescription="@string/glas_dugme"
            android:gravity="center"
            android:text="🔊"
            android:textSize="20sp" />

'''
nl = 0
for f in os.listdir(os.path.join(res, 'layout')):
    p = os.path.join(res, 'layout', f)
    s = open(p, encoding='utf-8').read()
    if 'voznjaDugme' not in s or 'voznjaGlas' in s: continue
    m = re.search(r'\n(\s*)<ProgressBar\s+android:id="@\+id/voznjaTrazi"', s)
    assert m, f
    s = s[:m.start() + 1] + DUGME + s[m.start() + 1:]
    open(p, 'w', encoding='utf-8').write(s); nl += 1
print('layout-i:', nl)

# ---------- VoznjaKartica: dugme ----------
p = os.path.join(JAVA, 'VoznjaKartica.java')
if not os.path.exists(p): p = os.path.join(JAVA, 'MainActivity.java')
s = open(p, encoding='utf-8').read()
if 'voznjaGlas' not in s:
    old = '        dugme.setOnClickListener(v -> {' if 'VoznjaKartica' in p else '        voznjaDugme.setOnClickListener(v -> {'
    new = '''        // 🔊/🔇: glasovne poruke u Vožnji (podrazumevano uključene)
        android.widget.TextView glas = KONT.findViewById(R.id.voznjaGlas);
        if (glas != null) {
            glas.setText(Glas.ukljucen(KONT) ? "🔊" : "🔇");
            glas.setOnClickListener(v -> {
                boolean da = !Glas.ukljucen(KONT);
                Glas.postavi(KONT, da);
                glas.setText(da ? "🔊" : "🔇");
            });
        }
''' + old
    assert old in s, p; s = s.replace(old, new, 1).replace('KONT', 'a' if 'VoznjaKartica' in p else 'this')
    if 'import android.widget.TextView;' not in s:
        s = s.replace('import android.view.View;', 'import android.view.View;\nimport android.widget.TextView;', 1)
    open(p, 'w', encoding='utf-8').write(s)

# ---------- VoznjaService ----------
p = os.path.join(JAVA, 'VoznjaService.java'); s = open(p, encoding='utf-8').read()
if 'Glas glas' not in s:
    def zameni(old, new, cnt=1):
        global s
        assert old in s, old[:60]
        s = s.replace(old, new, cnt)
    red_p = re.search(r'    private long pocetak, poslednjiPutNaAutoputu[^;]*;', s).group(0)
    zameni(red_p,
           red_p + '''
    /** Glasovne poruke (start, autoput/km/pravac, odmorište ispred, saobraćaj, stop). */
    private Glas glas;
    private String najavljenAutoput;
    private final java.util.Set<String> najavljeno = new java.util.HashSet<>();''')
    zameni('''        radi = true;
        instanca = this;''', '''        radi = true;
        instanca = this;
        glas = new Glas(this);
        glas.reci(getString(R.string.glas_start));''')
    zameni('''    public void onDestroy() {
        glavna.removeCallbacksAndMessages(null);''', '''    public void onDestroy() {
        glavna.removeCallbacksAndMessages(null);
        if (glas != null) {
            glas.reci(getString(R.string.glas_stop));
            glas.ugasi();
            glas = null;
        }''')
    i0 = s.index('private void obradiLokaciju'); i1 = s.index('private float brzina', i0)
    j = s.rindex('        osveziObavestenje();', i0, i1)
    s = s[:j] + '        osveziObavestenje();\n        najave();' + s[j + len('        osveziObavestenje();'):]
    zameni('''    /** Brzina u m/s:''', '''    // ---------- Glasovne poruke ----------

    private boolean milje() {
        Podaci p = autoput != null ? Podaci.za(this, Autoputevi.poId(autoput)) : null;
        return p != null && MILJE_POLJE;
    }

    /** Autoput, km i pravac kad se sazna (i pri prelasku na drugi autoput); odmorište ispred (do 5 km/mi). */
    private void najave() {
        Glas g = glas;
        if (g == null) return;
        if (autoput == null) { najavljenAutoput = null; return; }
        String kuda = kuda();
        if (kuda == null) return;
        Podaci p = Podaci.za(this, Autoputevi.poId(autoput));
        if (p == null || deonica >= p.deonice.size()) return;
        if (!autoput.equals(najavljenAutoput)) {
            najavljenAutoput = autoput;
            Autoput a = Autoputevi.poId(autoput);
            String oznaka = a != null ? a.oznaka() : autoput;
            String kmT = String.valueOf(Math.round(p.deonice.get(deonica).kmZaPrikaz(km)));
            g.reci(getString(R.string.glas_polozaj, oznaka, kmT,
                    getString(milje() ? R.string.glas_mi_naziv : R.string.glas_km_naziv), kuda));
        }
        double znak = smer == '+' ? 1 : -1;
        for (Stavka st : p.stavke) {
            if (st.deonica != deonica || (st.tip != Stavka.ODMORISTE && st.tip != Stavka.AUTOHOF) || !st.uSmeru(smer)) continue;
            double d = (st.km - km) * znak;
            if (d < 0.3 || d > 5) continue;
            if (!najavljeno.add("R" + autoput + ":" + st.deonica + ":" + st.km)) continue;
            String ime = st.naziv.isEmpty() ? "" : st.naziv;
            String t = getString(R.string.glas_odmoriste, (int) Math.max(1, Math.round(d)),
                    getString(milje() ? R.string.glas_mi_jed : R.string.glas_km_jed), ime);
            if (!st.gorivo.isEmpty()) t += " " + getString(R.string.glas_gorivo, String.join(", ", st.gorivo));
            g.reci(t);
        }
    }

    /** Brzina u m/s:''')
    if '        Obavestenja.obradi(this, id, svi, ispred, udaljenosti);' in s: zameni('''        Obavestenja.obradi(this, id, svi, ispred, udaljenosti);''', '''        Obavestenja.obradi(this, id, svi, ispred, udaljenosti);
        Glas g = glas;
        if (g != null) {
            for (Dogadjaj d : ispred) {
                if (!najavljeno.add("D" + d.id)) continue;
                Integer u = udaljenosti.get(d.id);
                String sta = getString(DogadjajAdapter.naziv(d.vrsta)) + (d.deonica.isEmpty() ? "" : ", " + d.deonica);
                g.reci(getString(R.string.glas_saobracaj, u != null ? u : 0,
                        getString(milje() ? R.string.glas_mi_jed : R.string.glas_km_jed), sta));
            }
        }''')
    # milje: EuroRoadInfo ima Podaci.milje (britanski autoputevi), MotorwayInfo/InterstateInfo su uvek u miljama
    pod = open(os.path.join(JAVA, 'Podaci.java'), encoding='utf-8').read()
    if 'public boolean milje' in pod: m = 'p.milje'
    elif 'MILJA' in pod: m = 'true'
    else: m = 'false'
    s = s.replace('p != null && MILJE_POLJE', 'p != null && ' + m)
    open(p, 'w', encoding='utf-8').write(s)
print('gotovo:', PAKET)
