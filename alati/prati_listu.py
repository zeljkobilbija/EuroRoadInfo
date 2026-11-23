"""
Ekran autoputa u Vožnji: red „Vi ste ovde“ sa strelicom uvek ostaje na ekranu, sa sledeća dva mesta ispred
(želja korisnika 23.11.2026). Ako vozač sam pomeri listu, praćenje stoji 20 s.
  python alati/prati_listu.py <projekat>
"""
import os, sys

KOREN = os.path.abspath(sys.argv[1])
JAVA = next(d for d, _, f in os.walk(os.path.join(KOREN, 'app', 'src', 'main', 'java')) if 'AutoputActivity.java' in f)
p = os.path.join(JAVA, 'AutoputActivity.java')
s = open(p, encoding='utf-8').read()
if 'pratiListu' in s:
    print('vec ima', os.path.basename(KOREN)); sys.exit()

def zameni(old, new):
    global s
    assert old in s, old[:70]
    s = s.replace(old, new, 1)

# 1) poziv posle svake postavke strelice
zameni('''        adapter.postaviOvde(i, d.kmZaPrikaz(mojKm), tekst, mojSmer != '?', mojSmer != '?' && mojSmer != smer);
    }''', '''        adapter.postaviOvde(i, d.kmZaPrikaz(mojKm), tekst, mojSmer != '?', mojSmer != '?' && mojSmer != smer);
        pratiListu();
    }

    /** Do kada vozač sam gleda listu (posle pomeranja prstom praćenje stoji 20 s). */
    private long rucnoDo;

    /**
     * Vožnja na ovom autoputu: red „Vi ste ovde“ uvek na ekranu, sa sledeća dva mesta ispred (u obrnutoj
     * listi su iznad strelice, inače ispod nje).
     */
    private void pratiListu() {
        if (!VoznjaService.radi || System.currentTimeMillis() < rucnoDo) return;
        int poz = adapter.pozicijaOvde();
        if (poz < 0) return;
        boolean ispredIznad = mojSmer != '?' && mojSmer != smer;
        int cilj = ispredIznad ? Math.max(0, poz - 2) : poz;
        LinearLayoutManager lm = (LinearLayoutManager) lista.getLayoutManager();
        if (lm == null || lm.findFirstVisibleItemPosition() == cilj) return;
        lm.scrollToPositionWithOffset(cilj, Izgled.dp(this, 8));
    }''')

# 2) pomeranje prstom zaustavlja praćenje na 20 s
zameni('''        lista = findViewById(R.id.lista);''', '''        lista = findViewById(R.id.lista);
        lista.addOnScrollListener(new androidx.recyclerview.widget.RecyclerView.OnScrollListener() {
            @Override
            public void onScrollStateChanged(@androidx.annotation.NonNull androidx.recyclerview.widget.RecyclerView rv, int stanje) {
                if (stanje == androidx.recyclerview.widget.RecyclerView.SCROLL_STATE_DRAGGING) {
                    rucnoDo = System.currentTimeMillis() + 20_000L;
                }
            }
        });''')
open(p, 'w', encoding='utf-8').write(s)
print('ok', os.path.basename(KOREN))
