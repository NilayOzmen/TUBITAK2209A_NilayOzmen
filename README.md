# Diplomatik Krizler ve Siber Saldırılar: Türkiye Örneği

Türkiye'nin taraf olduğu diplomatik krizlerin devlet destekli ve hacktivist siber saldırıları tetikleyip tetiklemediğini
açık verilerle inceleyen TÜBİTAK 2209-A araştırma projesinin veri hattı ve analiz kodları.

İncelenen krizler: 2015 Rusya uçak krizi (24.11.2015), 2017 Türkiye–Hollanda krizi (11.03.2017) ve
2019 Barış Pınarı Harekâtı (09.10.2019). Her kriz için önceki ve sonraki 60 gün karşılaştırılıyor.

> **Durum:** Ön çalışma (pilot). Buradaki sonuçlar küçük bir örnekleme dayanıyor ve kesin bulgu olarak okunmamalı.

## Klasör yapısı
```
src/              Python betikleri (veri indirme, süzme, birleştirme, analiz)
data/processed/   Türetilmiş veri setleri ve test sonuçları
data/raw/         Ham veri (depoda yok; aşağıdaki adımlarla indirilir)
outputs/          Grafikler ve aday haber listeleri
KODLAMA_KILAVUZU.md  Olayların nasıl kodlandığına dair kurallar
```

Ana veri seti: `data/processed/olaylar_v03.csv` (49 kayıt, 25'i sayıma dahil). Haberlerden elle kodlanan olaylar ve kaynak bağlantıları
`data/processed/haber_kodlama.csv` dosyasında.

## Kurulum ve çalıştırma
```bash
pip install -r requirements.txt
```

EuRepoC verisi indirme betiğiyle gelmiyor. [Zenodo](https://doi.org/10.5281/zenodo.14965395) sayfasından
`eurepoc_global_dataset_1_3.csv` dosyasını indirip `data/raw/eurepoc/` klasörüne koyun.

Betikler şu sırayla çalıştırılır:
```bash
# 1. Veri toplama
python3 src/eurepoc_turkiye.py        # EuRepoC'den Türkiye'yi içeren olaylar
python3 src/hackmageddon_indir.py     # Hackmageddon zaman çizelgeleri
python3 src/gdelt_indir.py            # GDELT olay dosyaları (~6 GB indirilir, 168 MB saklanır)
python3 src/gkg_siber_haber.py        # İngilizce siber saldırı haberleri (GDELT GKG)
python3 src/gkg_ceviri_tara.py barispinari_2019   # Türkçe haberler (GDELT çeviri katmanı), kriz ±14 gün
python3 src/gkg_ceviri_tara.py rusya_2015
python3 src/gkg_ceviri_tara.py hollanda_2017

# 2. Süzme (sonrasında aday listeleri elle incelenir)
python3 src/gkg_aday.py
python3 src/gkg_ceviri_aday.py barispinari_2019   # rusya_2015 ve hollanda_2017 için de çalıştırılır

# 3. Birleştirme, kodlama ve analiz
python3 src/birlestir.py
python3 src/gdelt_gerginlik.py
python3 src/pilot_analiz.py
python3 src/hipotez_testleri.py
```

Aday haberlerin gerçekten bir saldırıyı anlatıp anlatmadığına insan karar veriyor; bu adım otomatik değil.
Kodlama kuralları `KODLAMA_KILAVUZU.md` dosyasında.

## Veri kaynakları ve lisanslar

- **Kod:** MIT lisansı (`LICENSE`).
- **EuRepoC** (European Repository of Cyber Incidents), Global Dataset v1.3.2, CC BY-NC 4.0. EuRepoC'den türetilen
  tablolar (`eurepoc_turkiye.csv` vb.) aynı lisansa tabidir; ticari amaçla kullanılamaz.
- **GDELT** (Leetaru ve Schrodt, 2013): açık veri, kaynak gösterilerek kullanılabilir.
- **Hackmageddon** (Paolo Passeri, hackmageddon.com): ham sayfalar ve kayıtların tam dökümü depoda paylaşılmıyor;
  `src/hackmageddon_indir.py` ile yeniden oluşturulabilir. Veri setinde yalnızca kodlanan olaylar ve kaynak bağlantıları var.

## Çalışma günlüğü

Aşağıdaki bölümler ön çalışmanın adım adım kaydıdır.

### Ön çalışma bulguları (25.10.2026)

**EuRepoC:** 3.414 olayın 121'i Türkiye'yi içeriyor (2007–2024). Kriz pencerelerinde (±60 gün):

| Kriz | Önce | Sonra | Not |
|---|---|---|---|
| 2015 Rusya | 0 | 7 | 5'i TR–RUS ikilisi; TurkHackTeam kriz ertesi günü Rusya Merkez Bankası'na saldırdı |
| 2017 Hollanda | 1 | 1 | Türk hacktivistler kriz günü Hollanda sitelerine saldırdı |
| 2019 Barış Pınarı | 1 | 2 | Hiçbiri TR–ABD ikilisi değil |

Türkiye olaylarının %50'sinin başlangıç tarihi yalnızca ay düzeyinde (ayın 1'i) kodlanmış.

**GDELT:** 363 günlük dosya tarandı, Türkiye'nin taraf olduğu 1,12 milyon olay kaydı çıkarıldı.

| Kriz | Günlük olay (önce → sonra) | Goldstein (önce → sonra) | Ton (önce → sonra) |
|---|---|---|---|
| Rusya 2015 | 217 → 828 | +0,87 → −2,45 | −3,05 → −4,12 |
| Hollanda 2017 | 22 → 203 | −0,48 → −0,41 | −3,18 → −3,08 |
| Barış Pınarı 2019 (ABD) | 137 → 435 | +1,06 → +0,70 | −1,86 → −2,89 |

Hollanda krizinde gerginlik 11 Mart'tan ~7 gün önce (miting yasakları) başlıyor; kriz başlangıç tarihi için duyarlılık analizi gerekli.

### Pilot kodlama (26.10.2026)

Ek kaynak: **Hackmageddon** siber saldırı zaman çizelgeleri (36 yazı, 1.927 olay, gün düzeyinde tarih).
`src/hackmageddon_indir.py` → `src/birlestir.py` → elle kodlama (`data/processed/elle_kodlama.csv`) → `src/pilot_analiz.py`.
Kurallar: `KODLAMA_KILAVUZU.md`. Son veri seti: `data/processed/olaylar_v01.csv` (27 kayıt, 12'si sayıma dahil).

| Kriz | Önce (60 gün) | Sonra (60 gün) | Kriz ikilisi: önce → sonra | p (tek yönlü) |
|---|---|---|---|---|
| Rusya 2015 | 0 | 8 | 0 → 6 | 0,004 |
| Hollanda 2017 | 1 | 3 | 0 → 2 | 0,31 |
| Barış Pınarı 2019 | 0 | 0 | 0 → 0 | — |
| Üçü birlikte | 1 | 11 | 0 → 8 | 0,003 |

Test: eşit uzunluktaki pencerelerde Poisson oranlarının eşitliği için koşullu binom testi.
Sayıma dahil 12 olayın **tamamı hacktivist**; devlet destekli kayıtların hepsi uzun süreli kampanya ya da ifşa tarihli olduğu için sayım dışı kaldı.

### Haber taraması ve v02 (26.10.2026)

- **GKG taraması:** 363 günlük GDELT GKG dosyasından CYBER_ATTACK temalı ve Türkiye geçen 17.948 haber kaydı çıkarıldı
  (`src/gkg_siber_haber.py`). URL anahtar kelime filtresi sonrası 4.273 tekil aday; Türkiye'ye özgü URL'lerle 1.073'e,
  başlık gruplamasıyla ~430 tekil hikâyeye indirildi (`src/gkg_aday.py`, `outputs/gkg_tekil.txt`). Hepsi elle incelendi.
- **Web taraması:** Barış Pınarı dönemi için 7 hedefli arama yapıldı.
- Yeni kodlanan olaylar `data/processed/haber_kodlama.csv` dosyasında (9 kayıt, kaynak bağlantılı).
- **Barış Pınarı penceresi:** İngilizce GKG'de ve web aramasında tarihli, atfı olan Türkiye ile ilgili hacktivist olay bulunamadı.
  27.10.2019 Türk Telekom/Garanti DDoS'u fail ve gerekçe içermediği için `belirsiz` kodlandı.
  Sınırlılık: GKG 1.0 ağırlıklı olarak İngilizce haberleri kapsar.

Son veri seti `data/processed/olaylar_v02.csv`: 36 kayıt, 17'si sayıma dahil.

| Kriz | Tüm olaylar (önce → sonra) | p | Kriz ikilisi (önce → sonra) | p |
|---|---|---|---|---|
| Rusya 2015 | 1 → 10 | 0,006 | 0 → 7 | 0,008 |
| Hollanda 2017 | 3 → 3 | 0,66 | 0 → 2 | 0,25 |
| Barış Pınarı 2019 | 0 → 0 | — | 0 → 0 | — |
| Üçü birlikte | 4 → 13 | 0,025 | 0 → 9 | 0,002 |

### Hipotez testleri — pilot (26.10.2026)

`src/hipotez_testleri.py` (girdi: `olaylar_v02.csv`, sayıma dahil 17 olay).

- **H1:** Poisson GLM, 242 gün (Rusya + Hollanda; Barış Pınarı'nda olay olmadığı için modele girmez).
  Tüm olaylar: IRR = 3,20, %95 GA [1,04; 9,80], p = 0,042; aşırı yayılım 1,09 (Poisson uygun).
  Eğim modeli: seviye/eğim değişimi ayrı ayrı anlamlı değil (az olay). Karşı tarafa yönelik olaylar: 0 → 9,
  tam ayrışma nedeniyle Poisson tanımsız; kesin koşullu test p = 0,002.
- **H2:** Fisher kesin testi, Türkiye kaynaklı hacktivist saldırılar: önce 0/3, sonra 9/11 karşı tarafa; p = 0,028.
- **H3:** Kriz öncesi ağ 6 düğüm/3 bağ (merkez yok), kriz sonrası 15 düğüm/11 bağ; Rusya 7 saldırıyla merkez,
  dört farklı Türk grubu (Turk Hack Team, Ayyıldız Tim, Börteçine Siber Tim, WKPF) aynı hedefe yakınsıyor.
  Küçük ağlarda yoğunluk ölçütü yanıltıcı (düğüm sayısı arttıkça düşer); permütasyon testi bu örneklemle anlamsız.
- **H4:** Rusya penceresi, 121 gün. Goldstein → saldırı Granger p = 0,48–0,78 (1–7 gün); ton → saldırı p = 0,05–0,12
  (4–5 gün gecikmede sınırda, 14 test yapıldığı için anlamlı sayılmamalı). İlk karşı tarafa saldırı ile
  Goldstein'daki kırılma aynı gün (gün 0): gerginlik saldırıyı öncelemiyor, eş zamanlı.

### Türkçe kaynak taraması — Barış Pınarı (26.10.2026)

- **Kaynak:** GDELT 2.0 çeviri (Translingual) GKG katmanı, 25.09–23.10.2019 (kriz ±14 gün), 2.777 adet 15 dakikalık dosya
  (`src/gkg_ceviri_tara.py`). **450.942 Türkçe haber** tarandı; başlık filtresiyle 174 tekil aday (`src/gkg_ceviri_aday.py`,
  `outputs/gkg_ceviri_adaylar.txt`), hepsi elle incelendi.
- **Bulunan olaylar** (`haber_kodlama.csv`): Turkz Grup'un PKK yanlısı hesapları ele geçirmesi (+4), isimsiz Türk
  hacker'ların PKK/PYD bağlantılı onlarca siteyi kapatması (+8); Türkiye'yi hedef alan iki atıfsız saldırı (Yeni Akit +0,
  Özel Sporcular Federasyonu +8) `belirsiz`. Kriz öncesi 14 günde Türkiye ile ilgili hacktivist olay yok.
- **Kodlama kararı:** Barış Pınarı'nda krizin karşı tarafı **PYD/PKK ve ABD** olarak tanımlandı (harekâtın doğrudan hedefi
  devlet dışı aktör; diplomatik tepki ABD/AB'den).
- **Sınırlılık:** Türkçe çeviri katmanı yalnızca Barış Pınarı için ve ±14 günle tarandı; Rusya ve Hollanda dönemleri
  yalnızca İngilizce kaynaklarla tarandı.

#### Güncel sonuçlar

| Test | Sonuç |
|---|---|
| H1 Poisson (3 kriz, 363 gün, 19 olay) | IRR = 3,69, %95 GA [1,22; 11,11], p = 0,020 |
| Karşı tarafa yönelik olaylar | 0 → 11, kesin test p = 0,0005 |
| H2 Fisher (Türk kaynaklı hacktivist) | önce 0/3, sonra 11/13 karşı tarafa, p = 0,018 |
| H3 | Kriz sonrası ağ 18 düğüm/13 bağ; merkezler RU (7), PYD/PKK (2) |

### Türkçe tarama — Rusya ve Hollanda, v03 (28.10.2026)

- `src/gkg_ceviri_tara.py rusya_2015|hollanda_2017`: GDELT çeviri katmanı, kriz ±14 gün, 2 × 2.784 dosya.
  **1.006.109** (Rusya) + **703.942** (Hollanda) Türkçe haber; Barış Pınarı ile birlikte ~2,16 milyon.
- 2015–2017 dosyalarında `PAGE_TITLE` alanı yok; `src/gkg_ceviri_aday.py` başlık yerine URL metnini (slug) kullanıyor.
  Aday listeleri `outputs/gkg_ceviri_adaylar_*.txt`; Türkiye ve karşı tarafla ilgili olanlar elle incelendi,
  önemli olanların haber metni açılarak doğrulandı.
- Yeni kodlanan 9 olay (`haber_kodlama.csv`):
  Skorsky → yüzlerce Rus sitesi (**23.11.2015, krizden 1 gün önce**, Bayırbucak Türkmenlerine saldırılar protestosu);
  Skorsky → Ermeni siteleri (07.12.2015); Skorsky → Rus devlet siteleri (25.12.2015); Sputnik Türkiye DDoS (belirsiz, sayım dışı);
  Pawn Storm/APT28 → BYEGM (14.01.2016, tek kaynak, sayım dışı); Turkz → Ermenistan Parlamentosu (26.02.2017);
  Aslan Neferler Tim → Rotterdam Havalimanı (12.03.2017, havalimanı reddetti, sayım dışı); Turkz → Drunen Telecom (13.03.2017);
  Privatehackers.com → Versio'daki Hollanda siteleri (13.03.2017). Akıncılar'ın 13–14.03 saldırıları (Rumag, Hollanda Merkez Bankası)
  mükerrer kuralı (≤3 gün, aynı saldırgan ve hedef ülke) gereği 11.03 kaydıyla birleştirildi.
- **Kodlama notu:** Rusya penceresinde ilk karşı tarafa saldırı kriz gününden 1 gün önce. Bu, krizin tarihinin tek bir güne
  indirgenmesinin sınırlılığını gösteriyor (Rusya'nın Bayırbucak bombardımanı 20–23 Kasım'da gerginliği zaten artırmıştı).

`olaylar_v03.csv`: 49 kayıt, 25'i sayıma dahil (tamamı hacktivist). Türkçe çeviri katmanından gelen olay sayısı: 11.

| Test | v02 | v03 |
|---|---|---|
| H1 Poisson, tüm olaylar | IRR 3,69 [1,22; 11,11], p = 0,020 | IRR 3,11 [1,24; 7,80], p = 0,015 |
| Karşı tarafa yönelik olaylar | 0 → 11, kesin test p = 0,0005 | 1 → 14, IRR 13,8 [1,8; 104,7], p = 0,011 |
| H2 Fisher (Türk kaynaklı hacktivist) | 0/3 → 11/13, p = 0,018 | 1/5 → 14/17, p = 0,021 |
| H3 kriz sonrası merkezler | RU 7, PYD/PKK 2 | RU 8, NL 3, TR 2, PYD/PKK 2 |
| H4 Granger (endeks, 1–7 gün) | Rusya p ≥ 0,05 | Rusya p = 0,12–0,59; Hollanda p = 0,48–0,99 (anlamlı değil) |

H4 gerginlik endeksiyle (Goldstein ve ton z-puanlarının ortalaması; `gerginlik_endeksi_*.csv`) ve iki gösterge ayrı ayrı
test ediliyor. H1 eğim modelinde kriz sonrası eğim negatif (IRR/gün 0,94, p = 0,043): saldırılar krizin hemen ardından yoğunlaşıp sönümleniyor.
EuRepoC'deki Türkiye kayıtlarında başlangıç tarihi yalnızca ay düzeyinde olanların oranı: devlet destekli %79, hacktivist %21.

## Henüz yapılmayanlar

- 30 ve 90 günlük pencerelerle ve kriz tarihini bir hafta kaydırarak sağlamlık analizi
- 2015–2025 kriz dışı dönemle karşılaştırma
- PCA ağırlıklı gerginlik endeksi
- İkinci kodlayıcı için Cohen's Kappa hesabı
- CFR Cyber Operations Tracker kayıtlarının elle eklenmesi

