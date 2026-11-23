"""
Dugi pritisak na 🔊 (kartica Vožnja): izbor šta glas javlja – autoput/km/pravac, odmorišta, saobraćaj.
  python alati/glas_izbor.py <projekat>      (posle glas_ugradi.py; ponovno pokretanje ne pravi duplikate)
"""
import os, re, sys

KOREN = os.path.abspath(sys.argv[1])
MAIN = os.path.join(KOREN, 'app', 'src', 'main')
JAVA = next(d for d, _, f in os.walk(os.path.join(MAIN, 'java')) if 'Glas.java' in f)

T = {  # polozaj, odmorista, saobracaj
 '': ["Motorway, kilometre and direction", "Service areas and fuel ahead", "Traffic warnings"],
 'sr': ["Autoput, kilometar i pravac", "Odmorišta i pumpe ispred", "Upozorenja o saobraćaju"],
 'hr': ["Autocesta, kilometar i smjer", "Odmorišta i benzinske ispred", "Upozorenja o prometu"],
 'sl': ["Avtocesta, kilometer in smer", "Počivališča in črpalke pred vami", "Prometna opozorila"],
 'de': ["Autobahn, Kilometer und Richtung", "Raststätten und Tankstellen voraus", "Verkehrswarnungen"],
 'it': ["Autostrada, chilometro e direzione", "Aree di servizio e distributori davanti", "Avvisi sul traffico"],
 'fr': ["Autoroute, kilomètre et direction", "Aires et stations devant vous", "Alertes trafic"],
 'es': ["Autopista, kilómetro y dirección", "Áreas de servicio y gasolineras por delante", "Avisos de tráfico"],
 'pt': ["Autoestrada, quilómetro e direção", "Áreas de serviço e bombas à frente", "Avisos de trânsito"],
 'nl': ["Snelweg, kilometer en richting", "Verzorgingsplaatsen en tankstations vooruit", "Verkeerswaarschuwingen"],
 'pl': ["Autostrada, kilometr i kierunek", "MOP-y i stacje przed tobą", "Ostrzeżenia drogowe"],
 'cs': ["Dálnice, kilometr a směr", "Odpočívky a čerpací stanice před vámi", "Dopravní varování"],
 'sk': ["Diaľnica, kilometer a smer", "Odpočívadlá a čerpacie stanice pred vami", "Dopravné varovania"],
 'hu': ["Autópálya, kilométer és irány", "Pihenőhelyek és benzinkutak előttünk", "Forgalmi figyelmeztetések"],
 'ro': ["Autostradă, kilometru și direcție", "Zone de servicii și benzinării înainte", "Avertizări de trafic"],
 'el': ["Αυτοκινητόδρομος, χιλιόμετρο και κατεύθυνση", "Σταθμοί εξυπηρέτησης και καύσιμα μπροστά", "Προειδοποιήσεις κυκλοφορίας"],
 'ru': ["Автомагистраль, километр и направление", "Зоны отдыха и АЗС впереди", "Предупреждения о движении"],
 'tr': ["Otoyol, kilometre ve yön", "Öndeki dinlenme tesisleri ve akaryakıt", "Trafik uyarıları"],
}
res = os.path.join(MAIN, 'res')
for d in sorted(os.listdir(res)):
    if not re.fullmatch(r'values(-[a-z]{2})?', d): continue
    p = os.path.join(res, d, 'strings.xml')
    jez = d[7:] if d != 'values' else ''
    if not os.path.exists(p) or jez not in T: continue
    s = open(p, encoding='utf-8').read()
    if 'glas_izbor_polozaj' in s: continue
    red = ''.join('    <string name="%s">%s</string>\n' % (k, v.replace("'", "\\'"))
                  for k, v in zip(['glas_izbor_polozaj', 'glas_izbor_odmorista', 'glas_izbor_saobracaj'], T[jez]))
    open(p, 'w', encoding='utf-8').write(s.replace('</resources>', red + '</resources>'))

# Glas: vrste poruka
p = os.path.join(JAVA, 'Glas.java'); s = open(p, encoding='utf-8').read()
if 'public static boolean vrsta' not in s:
    s = s.replace('''    public Glas(Context c) {''', '''    /** Vrsta poruke: "polozaj", "odmorista", "saobracaj" (dugi pritisak na 🔊); podrazumevano sve. */
    public static boolean vrsta(Context c, String vrsta) {
        return c.getSharedPreferences(PODESAVANJA, Context.MODE_PRIVATE).getBoolean(vrsta, true);
    }

    public static void postaviVrstu(Context c, String vrsta, boolean da) {
        c.getSharedPreferences(PODESAVANJA, Context.MODE_PRIVATE).edit().putBoolean(vrsta, da).apply();
    }

    /** Izgovori poruku date vrste, ako je ta vrsta uključena. */
    public void reci(String tekst, String vrsta) {
        if (vrsta(c, vrsta)) reci(tekst);
    }

    /** Prozor sa izborom šta glas javlja. */
    public static void izbor(Context c) {
        String[] k = {"polozaj", "odmorista", "saobracaj"};
        String[] n = {c.getString(R.string.glas_izbor_polozaj), c.getString(R.string.glas_izbor_odmorista),
                c.getString(R.string.glas_izbor_saobracaj)};
        boolean[] da = {vrsta(c, k[0]), vrsta(c, k[1]), vrsta(c, k[2])};
        new androidx.appcompat.app.AlertDialog.Builder(c)
                .setTitle(R.string.glas_dugme)
                .setMultiChoiceItems(n, da, (dlg, i, izabrano) -> postaviVrstu(c, k[i], izabrano))
                .setPositiveButton(android.R.string.ok, null)
                .show();
    }

    public Glas(Context c) {''', 1)
    open(p, 'w', encoding='utf-8').write(s)

# VoznjaService: vrste
p = os.path.join(JAVA, 'VoznjaService.java'); s = open(p, encoding='utf-8').read()
if '"polozaj")' not in s:
    s = s.replace('''getString(milje() ? R.string.glas_mi_naziv : R.string.glas_km_naziv), kuda));''',
                  '''getString(milje() ? R.string.glas_mi_naziv : R.string.glas_km_naziv), kuda), "polozaj");''')
    s = s.replace('''            g.reci(t);
        }''', '''            g.reci(t, "odmorista");
        }''')
    s = s.replace('''getString(milje() ? R.string.glas_mi_jed : R.string.glas_km_jed), sta));''',
                  '''getString(milje() ? R.string.glas_mi_jed : R.string.glas_km_jed), sta), "saobracaj");''')
    assert '"polozaj")' in s and '"odmorista")' in s, p
    open(p, 'w', encoding='utf-8').write(s)

# kartica: dugi pritisak
for ime in ('VoznjaKartica.java', 'MainActivity.java'):
    p = os.path.join(JAVA, ime)
    if not os.path.exists(p): continue
    s = open(p, encoding='utf-8').read()
    if 'voznjaGlas' not in s or 'Glas.izbor' in s: continue
    old = '''                glas.setText(da ? "🔊" : "🔇");
            });'''
    assert old in s, p
    s = s.replace(old, old + '''
            // dugi pritisak: izbor šta glas javlja
            glas.setOnLongClickListener(v -> {
                Glas.izbor(v.getContext());
                return true;
            });''', 1)
    open(p, 'w', encoding='utf-8').write(s)
print('ok', os.path.basename(KOREN))
