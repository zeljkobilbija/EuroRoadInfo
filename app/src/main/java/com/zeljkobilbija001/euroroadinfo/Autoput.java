package com.zeljkobilbija001.euroroadinfo;

/** Jedan autoput na početnom ekranu (NL A2, BE A10, LU A1…). */
public final class Autoput {
    public final String zemlja;   // "DE", "FR", "IT", "NL", "BE" ili "LU"
    public final String ref;      // "A2"
    public final String id;       // "NL-A2" (jedinstven, jer A1 postoji u sve tri zemlje)
    public final String ruta;     // "Amsterdam – Utrecht – Eindhoven – Maastricht"
    public final String datoteka; // "autoputevi/nl-a2.json" ili null ako podaci još ne postoje

    public Autoput(String zemlja, String ref, String ruta, String datoteka) {
        this.zemlja = zemlja;
        this.ref = ref;
        this.id = zemlja + "-" + ref;
        this.ruta = ruta;
        this.datoteka = datoteka;
    }

    /** Oznaka kao na tabli: "A2", u Nemačkoj "A 2". */
    public String oznaka() {
        return "DE".equals(zemlja) ? ref.replaceFirst("^A", "A ") : ref;
    }

    /** Štit kao na tablama: crven u Holandiji, Francuskoj i Švajcarskoj, zelen u Italiji, plav u Nemačkoj, Austriji, Belgiji i Luksemburgu. */
    public int stit() {
        if ("NL".equals(zemlja) || "FR".equals(zemlja) || "CH".equals(zemlja)) return R.drawable.bg_stit;
        if ("IT".equals(zemlja)) return R.drawable.bg_stit_zeleni;
        return R.drawable.bg_stit_plavi;
    }

    public boolean dostupan() {
        return datoteka != null;
    }
}
