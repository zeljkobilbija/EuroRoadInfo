package com.zeljkobilbija001.euroroadinfo;

import android.content.Context;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Francuska: Bison Futé (DGITM, DATEX II 2.0) uz potpisane licence „Action C“ (bezbednost na putu – prikazuje
 * se pre ostalih) i „Action B“ (sav saobraćaj, i autoputevi sa naplatom). Login je samo na posredniku
 * (evis-posrednik /fr), koji fajlove prosleđuje neizmenjene. Licenca traži uz svaku poruku
 * „Information fournie par …“ + proizvođača i vreme poslednjeg ažuriranja. Preneto iz AutoroutesInfo.
 */
final class Francuska {

    private static final String POSREDNIK = "https://evis-posrednik.zeljkobilbija.workers.dev/fr?tok=";
    private static final long KES_MS = 60_000L;

    private static final Pattern SITUACIJA = Pattern.compile(
            "<ns2:situation id=\"([^\"]+)\"[^>]*>([\\s\\S]*?)</ns2:situation>");
    private static final Pattern ZAPIS = Pattern.compile(
            "<ns2:situationRecord [^>]*xsi:type=\"ns2:(\\w+)\"[^>]*>([\\s\\S]*?)</ns2:situationRecord>");
    private static final Pattern PUT = Pattern.compile("<ns2:roadNumber>\\s*([A-Z])0*(\\d+[A-Za-z]?)\\s*</ns2:roadNumber>");
    private static final Pattern POCETAK = Pattern.compile("<ns2:overallStartTime>([^<]+)</ns2:overallStartTime>");
    private static final Pattern KRAJ = Pattern.compile("<ns2:overallEndTime>([^<]+)</ns2:overallEndTime>");
    private static final Pattern KOMENTAR = Pattern.compile(
            "<ns2:generalPublicComment>[\\s\\S]*?<ns2:value[^>]*>([^<]*)</ns2:value>");
    private static final Pattern OD = Pattern.compile("<ns2:from [^>]*>[\\s\\S]*?<ns2:latitude>([-\\d.]+)</ns2:latitude>\\s*<ns2:longitude>([-\\d.]+)</ns2:longitude>");
    private static final Pattern DO = Pattern.compile("<ns2:to [^>]*>[\\s\\S]*?<ns2:latitude>([-\\d.]+)</ns2:latitude>\\s*<ns2:longitude>([-\\d.]+)</ns2:longitude>");
    private static final Pattern TACKA = Pattern.compile("<ns2:latitude>([-\\d.]+)</ns2:latitude>\\s*<ns2:longitude>([-\\d.]+)</ns2:longitude>");
    private static final Pattern MESTO_C = Pattern.compile(
            "<ns2:alertCMethod4(Primary|Secondary)PointLocation>[\\s\\S]*?<ns2:alertCLocationName>[\\s\\S]*?<ns2:value[^>]*>([^<]*)</ns2:value>");
    private static final Pattern VERS = Pattern.compile("^De (.+?) vers (.+)$");
    private static final Pattern PROIZVODJAC = Pattern.compile(
            "<ns2:sourceName>[\\s\\S]*?<ns2:value[^>]*>([^<]*)</ns2:value>");
    private static final Pattern ORGANIZACIJA = Pattern.compile("<ns2:sourceIdentification>([^<]+)<");
    private static final Pattern AZURIRANO = Pattern.compile("<ns2:situationVersionTime>([^<]+)<");
    private static final Pattern ZAVRSEN = Pattern.compile("<ns2:end>true</ns2:end>");

    /** Jedan tok (C ili B) sa svojim kešom. */
    private static final class Tok {
        final String ime;
        String tekst, izmenjen;
        long vreme;

        Tok(String ime) {
            this.ime = ime;
        }
    }

    private static final Tok TOK_C = new Tok("c"), TOK_B = new Tok("b");

    private Francuska() { }

    /** Poruke za jedan francuski autoput ("FR-A7" → ref "A7"); C pre B, isti id samo jednom. */
    static List<Dogadjaj> preuzmi(Context c, String autoputId, String ref) throws Exception {
        String xmlC = null, xmlB = null;
        Exception greska = null;
        try {
            xmlC = podaci(TOK_C);
        } catch (Exception e) {
            greska = e;
        }
        try {
            xmlB = podaci(TOK_B);
        } catch (Exception e) {
            greska = e;
        }
        if (xmlC == null && xmlB == null) throw greska;
        long sad = System.currentTimeMillis();
        Autoput ap = Autoputevi.poId(autoputId);
        Podaci p = c == null || ap == null ? null : Podaci.za(c, ap);
        String put = ref.toUpperCase(Locale.ROOT);
        List<Dogadjaj> l = new ArrayList<>();
        Set<String> vidjeni = new HashSet<>();
        dodaj(l, vidjeni, xmlC, true, put, p, sad);
        dodaj(l, vidjeni, xmlB, false, put, p, sad);
        return l;
    }

    private static void dodaj(List<Dogadjaj> l, Set<String> vidjeni, String xml, boolean bezbednost,
                              String put, Podaci p, long sad) {
        if (xml == null) return;
        Matcher m = SITUACIJA.matcher(xml);
        while (m.find()) {
            String sit = m.group(2);
            if (vidjeni.contains(m.group(1)) || !putevi(sit).contains(put)) continue;
            Dogadjaj d = izDatex(m.group(1), sit, sad, bezbednost, p);
            if (d == null) continue;
            vidjeni.add(m.group(1));
            l.add(d);
        }
    }

    private static String podaci(Tok tok) throws Exception {
        synchronized (tok) {
            long sad = System.currentTimeMillis();
            if (tok.tekst != null && sad - tok.vreme < KES_MS) return tok.tekst;
            HttpURLConnection v = (HttpURLConnection) new URL(POSREDNIK + tok.ime).openConnection();
            v.setConnectTimeout(10000);
            v.setReadTimeout(30000);
            v.setRequestProperty("User-Agent", "EuroRoadInfo-Android");
            v.setRequestProperty("Accept", "application/xml, text/xml");
            // gzip: HttpURLConnection ga sam traži i raspakuje (ne postavljati Accept-Encoding ručno)
            if (tok.tekst != null && tok.izmenjen != null) v.setRequestProperty("If-Modified-Since", tok.izmenjen);
            try {
                int kod = v.getResponseCode();
                if (kod == 304 && tok.tekst != null) {
                    tok.vreme = sad;
                    return tok.tekst;
                }
                if (kod != 200) throw new Exception("HTTP " + kod);
                StringBuilder sb = new StringBuilder("b".equals(tok.ime) ? 4_600_000 : 1_000_000);
                try (BufferedReader r = new BufferedReader(
                        new InputStreamReader(v.getInputStream(), StandardCharsets.UTF_8))) {
                    char[] buf = new char[65536];
                    int n;
                    while ((n = r.read(buf)) > 0) sb.append(buf, 0, n);
                }
                tok.tekst = sb.toString();
                tok.izmenjen = v.getHeaderField("Last-Modified");
                tok.vreme = sad;
                return tok.tekst;
            } finally {
                v.disconnect();
            }
        }
    }

    /** Oznake puteva iz situacije: "A7", "N20". */
    private static Set<String> putevi(String sit) {
        Set<String> s = new LinkedHashSet<>();
        Matcher m = PUT.matcher(sit);
        while (m.find()) s.add(m.group(1) + m.group(2).toUpperCase(Locale.ROOT));
        return s;
    }

    /** null ako situacija nije aktuelna (planirana, istekla, završena) ili nije stvarna. */
    private static Dogadjaj izDatex(String id, String sit, long sad, boolean bezbednost, Podaci p) {
        if (sit.contains("<ns2:informationStatus>") && !sit.contains("<ns2:informationStatus>real")) return null;
        int zapisa = 0, zavrsenih = 0;
        for (Matcher x = ZAPIS.matcher(sit); x.find(); ) zapisa++;
        for (Matcher x = ZAVRSEN.matcher(sit); x.find(); ) zavrsenih++;
        if (zapisa > 0 && zavrsenih >= zapisa) return null;
        long pocetak = 0, kraj = 0;
        Matcher mp = POCETAK.matcher(sit);
        while (mp.find()) {
            long t = vreme(mp.group(1));
            if (t > 0 && (pocetak == 0 || t < pocetak)) pocetak = t;
        }
        Matcher mk = KRAJ.matcher(sit);
        while (mk.find()) kraj = Math.max(kraj, vreme(mk.group(1)));
        if (pocetak > sad + 10 * 60_000L) return null; // planirano, još nije počelo
        if (kraj > 0 && kraj < sad) return null;

        int vrsta = Dogadjaj.OSTALO;
        boolean samoKvar = true;
        List<String> naziviZapisa = new ArrayList<>();
        Matcher mz = ZAPIS.matcher(sit);
        while (mz.find()) {
            String tip = mz.group(1), z = mz.group(2);
            int v = vrsta(tip, z);
            vrsta = Math.min(vrsta, v);
            if (!(tip.equals("VehicleObstruction") && z.contains("brokenDownVehicle"))
                    && v <= Dogadjaj.KOLONA) samoKvar = false;
            String n = naziv(tip, z);
            if (!naziviZapisa.contains(n)) naziviZapisa.add(n);
        }

        Set<String> komentari = new LinkedHashSet<>();
        String smer = "";
        Matcher mc = KOMENTAR.matcher(sit);
        while (mc.find()) {
            String k = xml(mc.group(1)).trim();
            if (k.isEmpty() || k.startsWith("DIR ") || k.startsWith("Point particulier")) continue;
            Matcher v = VERS.matcher(k);
            if (v.matches() && smer.isEmpty()) smer = "→ " + v.group(2).trim();
            komentari.add(k);
        }
        StringBuilder opis = new StringBuilder(String.join(" · ", naziviZapisa));
        for (String k : komentari) opis.append(opis.length() > 0 ? ". " : "").append(k);
        // licenca: „Information fournie par …“ + proizvođač + vreme poslednjeg ažuriranja
        Matcher mi = PROIZVODJAC.matcher(sit);
        // proizvođač: "Société concessionnaire d'autoroute/ASF" → "ASF", "…/DIR Nord" → "DIR Nord"; inače sourceName
        Matcher mo2 = ORGANIZACIJA.matcher(sit);
        String proizvodjac = mo2.find() ? xml(mo2.group(1)).replaceFirst("^.*/", "").trim() : "";
        if (proizvodjac.isEmpty() && mi.find()) proizvodjac = xml(mi.group(1)).trim();
        Matcher ma = AZURIRANO.matcher(sit);
        long azurirano = ma.find() ? vreme(ma.group(1)) : 0;
        opis.append("\nInformation fournie par ").append(proizvodjac.isEmpty() ? "Bison Futé" : proizvodjac);
        if (azurirano > 0) opis.append(" · mise à jour ")
                .append(new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.FRANCE).format(new Date(azurirano)));

        String prim = "", sek = "";
        Matcher ml = MESTO_C.matcher(sit);
        while (ml.find()) {
            if ("Primary".equals(ml.group(1)) && prim.isEmpty()) prim = xml(ml.group(2)).trim();
            if ("Secondary".equals(ml.group(1)) && sek.isEmpty()) sek = xml(ml.group(2)).trim();
        }
        String deonica = sek.isEmpty() || sek.equals(prim) ? prim : prim.isEmpty() ? sek : sek + " – " + prim;

        double lat = Double.NaN, lon = Double.NaN, lat2 = Double.NaN, lon2 = Double.NaN;
        Matcher mo = OD.matcher(sit), md = DO.matcher(sit);
        if (mo.find() && md.find()) {
            lat = broj(mo.group(1));
            lon = broj(mo.group(2));
            lat2 = broj(md.group(1));
            lon2 = broj(md.group(2));
            if (Math.abs(lat - lat2) < 1e-5 && Math.abs(lon - lon2) < 1e-5) lat2 = lon2 = Double.NaN;
        } else {
            Matcher mt = TACKA.matcher(sit);
            if (mt.find()) {
                lat = broj(mt.group(1));
                lon = broj(mt.group(2));
            }
        }
        // tačka sa smerom samo u tekstu ("De Marseille vers Lyon"): druga tačka 5 km dalje u tom smeru
        if (Double.isNaN(lat2) && !Double.isNaN(lat) && smer.length() > 2) {
            double[] t = drugaTacka(p, lat, lon, smer.substring(2).trim());
            if (t != null) {
                lat2 = t[0];
                lon2 = t[1];
            }
        }
        return Dogadjaj.izFrancuske(id, vrsta, deonica, smer, opis.toString(), pocetak,
                lat, lon, lat2, lon2, samoKvar, bezbednost);
    }

    /** Druga tačka 5 km dalje duž autoputa ka cilju (kraj autoputa ili izlaz tog imena); null ako se ne zna. */
    private static double[] drugaTacka(Podaci p, double lat, double lon, String cilj) {
        if (p == null) return null;
        Stavka naj = null;
        double nd = Double.MAX_VALUE;
        for (Stavka s : p.stavke) {
            if (!s.imaKoordinate()) continue;
            double d = km(lat, lon, s.lat, s.lon);
            if (d < nd) {
                nd = d;
                naj = s;
            }
        }
        if (naj == null || nd > 3 || naj.deonica < 0 || naj.deonica >= p.deonice.size()) return null;
        Deonica d = p.deonice.get(naj.deonica);
        Set<String> r = reci(cilj);
        boolean plus = !Collections.disjoint(r, reci(d.plus));
        boolean minus = !Collections.disjoint(r, reci(d.minus));
        if (plus == minus) {
            Stavka c = null;
            for (Stavka s : p.stavke) {
                if (s.deonica == naj.deonica && Math.abs(s.km - naj.km) > 1
                        && !Collections.disjoint(r, reci(s.naziv))) {
                    if (c == null || Math.abs(s.km - naj.km) < Math.abs(c.km - naj.km)) c = s;
                }
            }
            if (c != null) {
                plus = c.km > naj.km;
                minus = !plus;
            }
        }
        if (plus == minus) return null;
        return naKm(p, naj.deonica, naj.km + (plus ? 5 : -5));
    }

    private static double[] naKm(Podaci p, int deonica, double km) {
        Stavka pre = null, posle = null;
        for (Stavka s : p.stavke) {
            if (s.deonica != deonica || !s.imaKoordinate()) continue;
            if (s.km <= km && (pre == null || s.km > pre.km)) pre = s;
            if (s.km >= km && (posle == null || s.km < posle.km)) posle = s;
        }
        if (pre == null && posle == null) return null;
        if (pre == null) return new double[]{posle.lat, posle.lon};
        if (posle == null || posle.km - pre.km < 0.01) return new double[]{pre.lat, pre.lon};
        double u = (km - pre.km) / (posle.km - pre.km);
        return new double[]{pre.lat + u * (posle.lat - pre.lat), pre.lon + u * (posle.lon - pre.lon)};
    }

    private static double km(double la1, double lo1, double la2, double lo2) {
        double x = Math.toRadians(lo2 - lo1) * Math.cos(Math.toRadians((la1 + la2) / 2));
        double y = Math.toRadians(la2 - la1);
        return 6371 * Math.sqrt(x * x + y * y);
    }

    private static Set<String> reci(String s) {
        String n = java.text.Normalizer.normalize(s, java.text.Normalizer.Form.NFD)
                .replaceAll("\\p{M}", "").toLowerCase(Locale.ROOT);
        Set<String> r = new HashSet<>();
        for (String w : n.split("[^a-z0-9]+")) {
            if (w.length() >= 3 && !w.equals("sur") && !w.equals("les") && !w.equals("des")) r.add(w);
        }
        return r;
    }

    private static int vrsta(String tip, String z) {
        switch (tip) {
            case "Accident":
                return Dogadjaj.UDES;
            case "AbnormalTraffic":
                return z.contains("slowTraffic") || z.contains("heavyTraffic") ? Dogadjaj.SPORO : Dogadjaj.KOLONA;
            case "RoadOrCarriagewayOrLaneManagement":
                if (z.contains("SlipRoad") || z.contains("exit") && z.contains("Closed")) return Dogadjaj.PRILAZ;
                if (z.contains("roadClosed") || z.contains("carriagewayClosures")) return Dogadjaj.ZATVORENO;
                return Dogadjaj.TRAKA;
            case "VehicleObstruction":
            case "GeneralObstruction":
            case "AnimalPresenceObstruction":
            case "EnvironmentalObstruction":
            case "InfrastructureDamageObstruction":
            case "PoorEnvironmentConditions":
            case "WeatherRelatedRoadConditions":
            case "NonWeatherRelatedRoadConditions":
                return Dogadjaj.OPASNOST;
            case "MaintenanceWorks":
            case "ConstructionWorks":
            case "RoadworksManagement":
                return Dogadjaj.TRAKA;
            default:
                return Dogadjaj.OSTALO;
        }
    }

    /** Francuski naziv zapisa za opis. */
    private static String naziv(String tip, String z) {
        switch (tip) {
            case "Accident": return "Accident";
            case "AbnormalTraffic":
                return z.contains("slowTraffic") || z.contains("heavyTraffic") ? "Ralentissement" : "Bouchon";
            case "RoadOrCarriagewayOrLaneManagement":
                if (z.contains("roadClosed") || z.contains("carriagewayClosures")) return "Route fermée";
                if (z.contains("laneClosures")) return "Voie(s) fermée(s)";
                return "Restriction de circulation";
            case "VehicleObstruction":
                return z.contains("brokenDownVehicle") ? "Véhicule en panne" : "Véhicule arrêté";
            case "GeneralObstruction": return "Obstacle";
            case "AnimalPresenceObstruction": return "Animaux sur la chaussée";
            case "EnvironmentalObstruction": return "Obstacle naturel";
            case "InfrastructureDamageObstruction": return "Dégâts sur la chaussée";
            case "PoorEnvironmentConditions":
            case "WeatherRelatedRoadConditions": return "Conditions météo";
            case "NonWeatherRelatedRoadConditions": return "Chaussée dangereuse";
            case "MaintenanceWorks":
            case "ConstructionWorks": return "Travaux";
            case "SpeedManagement": return "Limitation de vitesse";
            case "ReroutingManagement": return "Déviation";
            default: return "Information";
        }
    }

    private static double broj(String s) {
        try {
            return Double.parseDouble(s);
        } catch (NumberFormatException e) {
            return Double.NaN;
        }
    }

    /** ISO vreme sa vremenskom zonom ("2026-11-26T04:30:49.072+01:00"). */
    private static long vreme(String iso) {
        String s = iso.trim();
        for (String f : new String[]{"yyyy-MM-dd'T'HH:mm:ss.SSSXXX", "yyyy-MM-dd'T'HH:mm:ssXXX"}) {
            try {
                Date d = new SimpleDateFormat(f, Locale.US).parse(s);
                if (d != null) return d.getTime();
            } catch (Exception ignored) {
            }
        }
        return 0;
    }

    private static String xml(String t) {
        return t.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"")
                .replace("&#39;", "'").replace("&apos;", "'").replace("&amp;", "&");
    }
}
