package com.zeljkobilbija001.euroroadinfo;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Stanje na putu za jedan autoput: upozorenja (kolone, udesi, opasnosti) i trenutna zatvaranja
 * sa javnog API-ja Autobahn GmbH (verkehr.autobahn.de, bez ključa).
 */
public final class StanjeNaPutu {

    public interface Odgovor {
        /** Poziva se na glavnoj niti; null ako podaci nisu stigli. */
        void stiglo(List<Dogadjaj> dogadjaji);
    }

    private static final String API = "https://verkehr.autobahn.de/o/autobahn/";
    /** Austrija: EVIS.AT / ASFINAG (CC BY 4.0) preko našeg posrednika – lični EVIS ključ je samo na serveru. */
    private static final String EVIS = "https://evis-posrednik.zeljkobilbija.workers.dev/vesti?put=";
    private static final ExecutorService NIT = Executors.newSingleThreadExecutor();

    private StanjeNaPutu() { }

    /** Velika Britanija: Engleska – National Highways preko našeg posrednika (ključ samo na serveru, isti oblik kao EVIS);
     *  Vels – Traffic Wales RSS (M4); Severna Irska – TrafficWatchNI RSS. */
    /** Švajcarska: FEDRO/ASTRA Traffic Data Platform preko posrednika (ključ samo na serveru, obrađeni zapisi). */
    private static final String CH = "https://evis-posrednik.zeljkobilbija.workers.dev/ch?put=";
    /** Beneluks: NDW (NL), Verkeerscentrum Vlaanderen (BE – Flandrija), CITA (LU); vesti već smeštene na autoput ("NL-A2"). */
    private static final String BNL = "https://evis-posrednik.zeljkobilbija.workers.dev/bnl?put=";
    private static final String NH = "https://evis-posrednik.zeljkobilbija.workers.dev/uk?put=";
    private static final String WALES = "https://traffic.wales/feeds/";
    private static final String NI = "https://rss.trafficwatchni.com/trafficwatchni_incidents_rss.xml";
    /** Škotski autoputevi – Traffic Scotland još nije uključen (čeka se dozvola). */
    private static final java.util.Set<String> SKOTSKA = new java.util.HashSet<>(java.util.Arrays.asList(
            "GB-M8", "GB-M9", "GB-M73", "GB-M74", "GB-M77", "GB-M80", "GB-M90", "GB-A74M"));

    /** Izvori: Nemačka (Autobahn GmbH), Austrija (EVIS.AT / ASFINAG), Francuska (Bison Futé, Action B i C), Švajcarska (FEDRO),
     *  Velika Britanija bez Škotske; ostale zemlje kasnije. */
    public static boolean podrzan(String autoputId) {
        if (autoputId == null) return false;
        return autoputId.startsWith("DE-") || autoputId.startsWith("AT-") || autoputId.startsWith("NI-")
                || autoputId.startsWith("FR-") || autoputId.startsWith("CH-")
                || autoputId.startsWith("NL-") || autoputId.startsWith("BE-") || autoputId.startsWith("LU-")
                || (autoputId.startsWith("GB-") && !SKOTSKA.contains(autoputId));
    }

    public static void ucitaj(Context c, String autoput, Odgovor odgovor) {
        Context app = c.getApplicationContext();
        Handler glavna = new Handler(Looper.getMainLooper());
        NIT.execute(() -> {
            List<Dogadjaj> l;
            try {
                l = preuzmi(app, autoput);
            } catch (Exception e) {
                l = null;
            }
            List<Dogadjaj> konacno = l;
            glavna.post(() -> odgovor.stiglo(konacno));
        });
    }

    /**
     * Preuzimanje na tekućoj niti (i za proveru u pozadini). Najnovija poruka ide prva bez obzira
     * na važnost (važnost pokazuje boja), poruke bez vremena na kraj; isto vreme: važnija prva.
     * Francuska: poruke „Action C“ (bezbednost) uvek prve (licenca).
     */
    public static List<Dogadjaj> preuzmi(Context c, String autoput) throws Exception {
        if (!podrzan(autoput)) return new ArrayList<>();
        String ref = autoput.substring(3); // "DE-A8" -> "A8", "AT-S6" -> "S6"
        List<Dogadjaj> l = new ArrayList<>();
        if (autoput.startsWith("FR-")) {
            l.addAll(Francuska.preuzmi(c, autoput, ref));
        } else if (autoput.startsWith("CH-")) {
            Autoput ap = Autoputevi.poId(autoput);
            l.addAll(Dogadjaj.izCh(get(CH + ref), c == null || ap == null ? null : Podaci.za(c, ap)));
        } else if (autoput.startsWith("NL-") || autoput.startsWith("BE-") || autoput.startsWith("LU-")) {
            Autoput ap = Autoputevi.poId(autoput);
            l.addAll(Dogadjaj.izCh(get(BNL + autoput), c == null || ap == null ? null : Podaci.za(c, ap)));
        } else if (autoput.startsWith("AT-")) {
            l.addAll(Dogadjaj.izEvis(get(EVIS + ref)));
        } else if (autoput.startsWith("NI-")) {
            l.addAll(Dogadjaj.izNi(get(NI), ref));
        } else if (autoput.startsWith("GB-")) {
            l.addAll(Dogadjaj.izEvis(get(NH + java.net.URLEncoder.encode(ref, "UTF-8"))));
            if ("M4".equals(ref)) { // M4 ide i kroz Vels
                l.addAll(Dogadjaj.izWales(get(WALES + "incidents-events/rss.xml"), ref, false));
                l.addAll(Dogadjaj.izWales(get(WALES + "roadworks/rss.xml"), ref, true));
            }
        } else {
            l.addAll(Dogadjaj.izJsona(get(API + ref + "/services/warning"), "warning"));
            l.addAll(Dogadjaj.izJsona(get(API + ref + "/services/closure"), "closure"));
        }
        Collections.sort(l, (a, b) -> a.bezbednost != b.bezbednost ? (a.bezbednost ? -1 : 1)
                : a.pocetak != b.pocetak ? Long.compare(b.pocetak, a.pocetak)
                : Integer.compare(a.vrsta, b.vrsta));
        return l;
    }

    private static String get(String adresa) throws Exception {
        HttpURLConnection v = (HttpURLConnection) new URL(adresa).openConnection();
        v.setConnectTimeout(10000);
        v.setReadTimeout(20000);
        v.setRequestProperty("User-Agent", "AutobahnInfo-Android");
        v.setRequestProperty("Accept", "*/*");
        try {
            if (v.getResponseCode() != 200) throw new Exception("HTTP " + v.getResponseCode());
            StringBuilder sb = new StringBuilder();
            try (BufferedReader r = new BufferedReader(
                    new InputStreamReader(v.getInputStream(), StandardCharsets.UTF_8))) {
                String red;
                while ((red = r.readLine()) != null) sb.append(red).append('\n');
            }
            return sb.toString();
        } finally {
            v.disconnect();
        }
    }
}
