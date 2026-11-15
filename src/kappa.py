"""Kodlayıcılar arası güvenilirlik: ikinci kodlayıcı formu ve Cohen's Kappa hesabı.

Kodlama kılavuzu (bölüm 7): olayların %20'si ikinci bir kodlayıcı (danışman) tarafından bağımsız kodlanır;
aktor_turu ve kriz_ikilisi için Cohen's Kappa hesaplanır (kabul eşiği 0,70). Az sayıda olayda Kappa yanıltıcı
olabileceğinden yüzde uyum da raporlanır. saldiri_turu ve sayima_dahil ek olarak raporlanır.

Kullanım:
  python3 src/kappa.py form       # olaylar_v03.csv'den %20'lik örneklemi seçer ve boş kodlama formunu yazar
  python3 src/kappa.py hesapla    # doldurulmuş formu birinci kodlamayla karşılaştırır

Form: data/processed/ikinci_kodlayici_formu.csv
  Danışman yalnızca boş sütunları (aktor_turu, saldiri_turu, kriz_ikilisi, sayima_dahil) doldurur; birinci
  kodlayıcının kodları formda yer almaz. Geçerli değerler KODLAMA_KILAVUZU.md dosyasındadır.
Çıktılar: data/processed/kappa_sonuc.csv (değişken başına Kappa ve yüzde uyum),
          data/processed/kappa_anlasmazliklar.csv (birlikte çözülecek kayıtlar)
"""
import math, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data/processed"
FORM = P / "ikinci_kodlayici_formu.csv"
TOHUM = 2209                      # örneklem seçimi tekrarlanabilir olsun diye sabit
DEGISKENLER = ["aktor_turu", "kriz_ikilisi", "saldiri_turu", "sayima_dahil"]
ANA = ["aktor_turu", "kriz_ikilisi"]     # kılavuzdaki kabul eşiği bu ikisi için
GECERLI = {"aktor_turu": {"devlet_destekli", "hacktivist", "suc", "belirsiz"},
           "kriz_ikilisi": {"evet", "hayir"},
           "saldiri_turu": {"ddos", "tahrifat", "veri_sizintisi", "hesap_ele_gecirme", "casusluk", "diger"},
           "sayima_dahil": {"evet", "hayir"}}
BILGI = ["olay_id", "kriz", "tarih", "tarih_kesinligi", "saldirgan", "saldirgan_ulke", "hedef", "hedef_ulke",
         "kaynak", "kaynak_url", "aciklama"]


def cohen_kappa(a, b):
    a, b = list(a), list(b)
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    kategoriler = set(a) | set(b)
    pe = sum((a.count(k) / n) * (b.count(k) / n) for k in kategoriler)
    if pe == 1:                   # iki kodlayıcı da tek bir kategori kullandıysa Kappa tanımsız
        return po, float("nan")
    return po, (po - pe) / (1 - pe)


def form():
    d = pd.read_csv(P / "olaylar_v03.csv")
    n = math.ceil(len(d) * 0.20)
    # Kaynak türüne göre tabakalı seçim: haber ve veri tabanı kayıtları orantılı temsil edilsin
    d["tabaka"] = d.kaynak.str.contains("haber").map({True: "haber", False: "veri_tabani"})
    pay = (d.tabaka.value_counts(normalize=True) * n).round().astype(int)
    ornek = pd.concat([d[d.tabaka == t].sample(k, random_state=TOHUM) for t, k in pay.items()])
    f = ornek[BILGI].sort_values("olay_id").copy()
    for c in DEGISKENLER:
        f[c] = ""
    f["kodlayici_notu"] = ""
    if FORM.exists():
        sys.exit(f"{FORM.name} zaten var; üzerine yazmamak için durduruldu. Yeniden üretmek için dosyayı silin.")
    f.to_csv(FORM, index=False)
    print(f"{len(f)} olay seçildi ({len(d)} olayın %20'si): {pay.to_dict()}")
    print(f"Form: {FORM}")


def hesapla():
    f = pd.read_csv(FORM, dtype=str).fillna("")
    d = pd.read_csv(P / "olaylar_v03.csv", dtype=str).fillna("").set_index("olay_id")
    eksik = [c for c in DEGISKENLER if (f[c].str.strip() == "").any()]
    if eksik:
        sys.exit(f"Formda boş hücre var: {eksik}. Önce formun tamamlanması gerekiyor.")
    for c in DEGISKENLER:
        hatali = sorted(set(f[c].str.strip()) - GECERLI[c])
        if hatali:
            sys.exit(f"{c} sütununda geçersiz değer: {hatali}. Geçerli: {sorted(GECERLI[c])}")
    satir, anlasmazlik = [], []
    for c in DEGISKENLER:
        birinci = [d.loc[i, c] for i in f.olay_id]
        ikinci = f[c].str.strip().tolist()
        po, k = cohen_kappa(birinci, ikinci)
        esik = ("geçti" if k >= 0.70 else "geçmedi") if c in ANA and k == k else ""
        satir.append(dict(degisken=c, n=len(f), yuzde_uyum=round(po * 100, 1),
                          kappa=round(k, 3) if k == k else "tanımsız", esik_0_70=esik))
        for i, x, y in zip(f.olay_id, birinci, ikinci):
            if x != y:
                anlasmazlik.append(dict(olay_id=i, degisken=c, birinci_kodlayici=x, ikinci_kodlayici=y,
                                        kaynak_url=d.loc[i, "kaynak_url"]))
    t = pd.DataFrame(satir)
    t.to_csv(P / "kappa_sonuc.csv", index=False)
    pd.DataFrame(anlasmazlik, columns=["olay_id", "degisken", "birinci_kodlayici", "ikinci_kodlayici",
                                       "kaynak_url"]).to_csv(P / "kappa_anlasmazliklar.csv", index=False)
    print(t.to_string(index=False))
    print(f"\n{len(anlasmazlik)} anlaşmazlık kappa_anlasmazliklar.csv dosyasına yazıldı; birlikte çözülecek.")


if __name__ == "__main__":
    {"form": form, "hesapla": hesapla}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
