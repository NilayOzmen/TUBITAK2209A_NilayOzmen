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
python3 src/gkg_ceviri_tara.py barispinari_2019 60   # Türkçe haberler (GDELT çeviri katmanı), kriz ±60 gün
python3 src/gkg_ceviri_tara.py rusya_2015 60          # (kriz başına ~11.600 dosya, ~1 saat; ikinci argüman
python3 src/gkg_ceviri_tara.py hollanda_2017 60       #  verilmezse ±14 gün; indirilmiş dosyalar atlanır)

# 2. Süzme (sonrasında aday listeleri elle incelenir)
python3 src/gkg_aday.py
python3 src/gkg_ceviri_aday.py barispinari_2019   # rusya_2015 ve hollanda_2017 için de çalıştırılır

# 3. Birleştirme, kodlama ve analiz
python3 src/birlestir.py
python3 src/gdelt_gerginlik.py
python3 src/pilot_analiz.py          # olaylar_v03.csv
python3 src/tarama121.py             # v03 + tarama121_kodlama.csv → olaylar_v04.csv (ana veri seti)
python3 src/hipotez_testleri.py

# 4. Sağlamlık analizleri
python3 src/hackmageddon_genislet.py   # ±90 gün için ek Hackmageddon ayları (src klasöründen çalıştırın)
python3 src/saglamlik.py

# 5. Kriz dışı karşılaştırma (src klasöründen çalıştırın; indirme ~15 dk)
python3 src/hackmageddon_tum.py
python3 src/kriz_disi.py

# 6. Tırmanan kriz örneği: Brunson 2018 (indirmeler için gdelt_indir.py, gkg_siber_haber.py
#    ve gkg_ceviri_tara.py brunson_2018; olaylar brunson_kodlama.csv'de elle kodlanır)
python3 src/brunson.py
python3 src/tirmanan_krizler.py     # Brunson + Doğu Akdeniz, beş krizli havuzlanmış H4 modeli
python3 src/catisma_olcusu.py       # H4: yalnız çatışma olaylarına dayanan gerginlik ölçüsü

# 7. Kodlayıcılar arası güvenilirlik (danışman formu doldurduktan sonra)
python3 src/kappa.py hesapla
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

### Sağlamlık analizleri (15.11.2026)

`src/saglamlik.py`, sonuçlar `data/processed/saglamlik.csv`. H1 = Poisson IRR (kriz sabit etkili), H2 = Fisher (tek yönlü).

| Senaryo | Tüm olaylar (önce → sonra) | IRR, p | Karşı tarafa (önce → sonra) | p | H2 | p |
|---|---|---|---|---|---|---|
| Pencere ±30 | 4 → 10 | 2,42; 0,135 | 1 → 7 | 0,074 | 1/4 → 7/8 | 0,067 |
| Pencere ±45 | 6 → 17 | 2,77; 0,032 | 1 → 12 | 0,018 | 1/5 → 12/15 | 0,031 |
| Pencere ±60 (ana) | 6 → 19 | 3,11; 0,015 | 1 → 14 | 0,011 | 1/5 → 14/17 | 0,021 |
| Kriz tarihi −7 gün (±53) | 4 → 19 | 4,66; 0,005 | 0 → 13 | 0,0001 | 0/3 → 13/17 | 0,031 |
| Kriz tarihi 0 (±53) | 6 → 18 | 2,94; 0,022 | 1 → 13 | 0,014 | 1/5 → 13/16 | 0,025 |
| Kriz tarihi +7 gün (±53) | 12 → 13 | 1,06; 0,878 | 7 → 8 | 0,824 | 7/11 → 8/11 | 0,500 |
| Yalnız veri tabanları ±60 | 1 → 11 | 10,82; 0,023 | 0 → 8 | 0,004 | 0/1 → 8/9 | 0,200 |
| Yalnız veri tabanları ±90 | 1 → 12 | 11,87; 0,018 | 0 → 8 | 0,004 | 0/1 → 8/10 | 0,273 |
| Rusya hariç | 4 → 7 | 1,72; 0,386 | 0 → 6 | 0,016 | 0/4 → 6/7 | 0,015 |
| Hollanda hariç | 2 → 14 | 6,89; 0,011 | 1 → 10 | 0,029 | 1/1 → 10/12 | 1,000 |
| Barış Pınarı hariç | 6 → 17 | 2,79; 0,031 | 1 → 12 | 0,018 | 1/5 → 12/15 | 0,031 |

Yorum:
- **Pencere:** Yön her pencerede aynı. ±30 günde olay sayısı azaldığı için anlamlılık sınırın altına iniyor; ±45 ve ±60 günde anlamlı.
- **Kriz tarihi:** Tarih bir hafta öne alınınca etki güçleniyor (Skorsky'nin 23.11.2015 saldırısı da "sonra"ya geçiyor), bir hafta
  sonraya alınınca kayboluyor. Saldırılar krizin ilk haftasında yoğunlaştığı için tarih sonraya kaydırılınca bu saldırılar "önce"
  dönemine düşüyor. Yani kırılma kriz tarihinin hemen çevresinde; etki gecikmeli değil, ani ve kısa süreli (eğim modeliyle tutarlı).
- **±90 gün:** Yalnız veri tabanı kaynaklarıyla ±60 ve ±90 gün sonuçları neredeyse aynı. 60–90 gün arasında 13 aday kayıttan yalnızca
  biri sayıma girdi (Turk Hack Team, Ferrari müzesi, +61. gün); kodlama gerekçeleri `olaylar_bant_60_90.csv` dosyasında. Ek dönemler için
  Hackmageddon'dan 6 zaman çizelgesi daha indirildi (`src/hackmageddon_genislet.py`).
- **Kriz dışarıda bırakma:** Toplam saldırı artışı büyük ölçüde Rusya krizine dayanıyor; Rusya çıkarılınca anlamlı değil. Buna karşılık
  karşı tarafa yönelik saldırı artışı ve hedef kayması (H2) Rusya olmadan da anlamlı. Hollanda çıkarılınca H2 test edilemiyor, çünkü
  kriz öncesinde yalnızca bir Türk hacktivist saldırısı kalıyor.

### PCA ağırlıklı gerginlik endeksi (16.11.2026)

Yöntemdeki "eşit ağırlık varsayımı PCA ile kontrol edilecek" adımı için not: İki standart göstergeyle (Goldstein ve ton)
PCA'nın birinci bileşeni matematiksel olarak her zaman eşit ağırlık verir (0,5 / 0,5); bu nedenle kontrol, GDELT'teki
üçüncü bir göstergeyle, günlük çatışma olayı payıyla (`catisma_orani`) yapıldı. Sonuçlar `h4_pca_agirliklari.csv`
ve `h4_granger.csv` (`endeks_pca`) dosyalarında.

| Kriz | Ağırlıklar (Goldstein / ton / çatışma payı) | Açıklanan varyans | Eşit ağırlıklı endeksle korelasyon |
|---|---|---|---|
| Rusya 2015 | 0,35 / 0,29 / 0,36 | %80 | 0,98 |
| Hollanda 2017 | 0,40 / 0,20 / 0,41 | %61 | 0,88 |

PCA endeksiyle de Granger testi anlamlı değil (Rusya p = 0,15–0,52; Hollanda p = 0,49–1,00). H4 sonucu endeksin
nasıl ağırlıklandırıldığına bağlı değil.

### Kodlayıcılar arası güvenilirlik (16.11.2026)

`src/kappa.py form` ile olayların %20'si (49 olaydan 10'u; kaynak türüne göre tabakalı, sabit tohum 2209) seçildi ve
`data/processed/ikinci_kodlayici_formu.csv` oluşturuldu. Formda birinci kodlayıcının kodları yok; danışman `aktor_turu`,
`kriz_ikilisi`, `saldiri_turu` ve `sayima_dahil` sütunlarını `KODLAMA_KILAVUZU.md`'deki değerlerle doldurur.
`src/kappa.py hesapla` değişken başına Cohen's Kappa ve yüzde uyumu `kappa_sonuc.csv` dosyasına, anlaşmazlıkları
`kappa_anlasmazliklar.csv` dosyasına yazar (kabul eşiği: `aktor_turu` ve `kriz_ikilisi` için 0,70).

### Kriz dışı karşılaştırma (16.11.2026)

`src/hackmageddon_tum.py` ile Hackmageddon'ın 2015–2024 arasındaki 245 zaman çizelgesi indirildi (19.425 kayıt);
`src/kriz_disi.py` EuRepoC ile birlikte 1 Temmuz 2015 – 30 Kasım 2024 dönemini inceliyor. Sonuçlar `data/processed/kriz_disi_*.csv`,
grafik `outputs/kriz_disi_plasebo.png`.

- **Kapsam ve sınırlılıklar:** Yalnız veri tabanı kaynakları (haber taraması kriz pencereleriyle sınırlı). On yıllık veri elle
  kodlanamadığından kriz ve kriz dışı dönemler aynı otomatik kurallarla kodlandı: hacktivist, gün düzeyinde tarihli, Türkiye saldırgan
  ya da hedef, en fazla üç hedef ülke. Hackmageddon 2015'in ilk yarısında tabloları resim olarak yayımladığı için dönem Temmuz 2015'te
  başlıyor; 2020'deki beş yarım aylık zaman çizelgesi (sunucu hatası) alınamadı ve bu 76 gün dışarıda bırakıldı. 2021 sonrası tablolarda
  saldırı tarihi (`Date Occurred`) esas alındı, yoksa bildirim tarihi kullanıldı.
- **Doğrulama:** Otomatik kodlama kriz pencerelerinde elle kodlanmış v03 veri tabanı kayıtlarına yakın sonuç veriyor
  (Rusya 0 → 7 / elle 0 → 8; Hollanda 1 → 2 / elle 1 → 3; Barış Pınarı 0 → 0).
- Dönemde 50 hacktivist olay var, 37'si Türkiye kaynaklı.

| Test | Tüm hacktivist olaylar | Türkiye kaynaklı |
|---|---|---|
| Kriz sonrası 60 gün / kriz dışı günlük oran (yıl sabit etkili Poisson) | IRR 4,29 [1,79; 10,28], p = 0,001 | IRR 4,05 [1,40; 11,75], p = 0,010 |
| Kriz öncesi 60 gün / kriz dışı | IRR 0,62, p = 0,66 | IRR 0,85, p = 0,89 |
| Plasebo: 3 krizde toplam (sonra − önce) | +8; rastgele tarihlerde ort. −0,17; p = 0,001 | +5; ort. −0,06; p = 0,056 |
| Plasebo: yalnız Rusya | +7; p < 0,001 | +6; p < 0,001 |
| Plasebo: Hollanda / Barış Pınarı | p = 0,28 / 0,74 | p = 0,87 / 0,74 |

Yorum: Kriz sonrası dönemlerde hacktivist saldırı oranı kriz dışı taban orana göre yaklaşık dört kat yüksek; kriz öncesi dönem ise
taban orandan farklı değil. Rastgele 10.000 "sahte kriz" çekilişinin yalnızca %0,1'i gerçek krizler kadar büyük bir artış üretti.
Etki büyük ölçüde Rusya krizinden geliyor; Hollanda ve Barış Pınarı olayları veri tabanlarında çok az (Barış Pınarı olayları yalnızca
Türkçe haberlerde bulunmuştu, Hollanda'daki Akıncılar saldırısı Hackmageddon'da faili belirtilmeden kayıtlı).

**H3 kriz dışı karşılaştırma:** Türkiye kaynaklı saldırıların tek bir yabancı ülkede yoğunlaşması Rusya krizinden sonra %83 (RU),
rastgele kriz dışı 61 günlük pencerelerde ortalama %54 (p = 0,37). Veri tabanlarında kriz dışı dönemde Türkiye kaynaklı saldırı çok az
olduğundan (105 pencerede en az 3 saldırı var) H3 bu kaynaklarla anlamlı biçimde test edilemiyor; kriz dışı dönemler için de haber
taraması gerekir.

### H4'ün genişletilmesi: Barış Pınarı, kriz türü ve havuzlanmış model (16.11.2026)

Soru: Uçak düşürme gibi ani krizlerde krizden önce gerginlik beklemek anlamlı mı? Erken uyarı mantığı yalnızca tırmanan
krizlerde geçerli olabilir. Bunu test etmek için `hipotez_testleri.py` H4 bölümüne üç ekleme yapıldı:

1. **Barış Pınarı H4'e eklendi.** Saldırıların hedefi PYD/PKK olduğundan gerginlik Türkiye–Suriye ikilisiyle ölçüldü
   (`gdelt_gunluk_2019_SYR.csv`); Türkiye–ABD alternatif olarak raporlandı. Karşı tarafa yönelik yalnızca 2 saldırı günü var.
2. **Kriz türü** (`h4_kriz_turu.csv`): kriz öncesi 14 günde gerginlik endeksinin eğimi.

| Kriz | Günlük eğim (p) | Tür |
|---|---|---|
| Rusya 2015 (TR–RUS) | 0,050 (0,28) | ani |
| Hollanda 2017 (TR–NLD) | −0,025 (0,51) | ani |
| Barış Pınarı 2019 (TR–SYR) | −0,036 (0,57) | ani |
| Barış Pınarı 2019 (TR–USA) | 0,079 (0,027) | tırmanan |

   Rusya'da kriz öncesi son 14 gündeki gerginlik önceki dönemden bile düşük; uçağın düşürülmesi beklenmedik bir şok.
   Tırmanma yalnızca Barış Pınarı öncesindeki Türkiye–ABD ilişkisinde görülüyor (6 Ekim çekilme kararı ve sonrası).

3. **Granger (endeks, 1–7 gün):** Rusya p = 0,12–0,59; Hollanda p = 0,48–0,99; Barış Pınarı TR–SYR p = 0,06–0,38;
   Barış Pınarı TR–USA p = 0,007–0,011 (1–3 gün), sonra anlamsız. Anlamlı çıkan tek seri, kriz türü analizinde tırmanan
   çıkan tek seri; ancak yalnızca 2 saldırı gününe dayandığı için çok kırılgan.
4. **Havuzlanmış Poisson** (`h4_havuz.csv`, 3 kriz, 342 gün, 15 saldırı):

| Model | Önceki 1–3 günün gerginliği, IRR (1 SS) | p |
|---|---|---|
| Yalnız gecikmeli gerginlik + kriz sabit etkisi | 3,16 [1,24; 8,06] | 0,016 |
| + aynı günün gerginliği + kriz sonrası kukla | 2,26 [0,64; 7,94] | 0,202 |
| Önceki 1–7 gün, yalnız gecikmeli | 3,82 [1,17; 12,50] | 0,027 |
| Önceki 1–7 gün, + aynı gün + kriz sonrası | 1,79 [0,42; 7,65] | 0,431 |

   Gecikmeli gerginlik tek başına saldırıları öngörüyor gibi görünüyor, ama kriz sonrası kukla eklenince etki kayboluyor.
   Yani ilişkiyi kriz şokunun kendisi taşıyor: kriz başlayınca hem gerginlik hem saldırılar yükseliyor; kriz dönemi içinde
   gerginlikteki günlük değişimler saldırıları ayrıca öngörmüyor.

**Sonuç:** Bu üç kriz, H4'ün erken uyarı mantığını test etmek için uygun değil; ikisi açıkça ani kriz, Hollanda'da da kriz öncesi
14 günde tırmanma eğilimi yok. H4'ü anlamlı biçimde test etmek için tırmanan krizlerin (ör. 2018 ABD–Brunson krizi, 2020 Doğu
Akdeniz gerginliği) örnekleme eklenmesi gerekir.

### Tırmanan kriz örneği: 2018 ABD–Türkiye (Brunson) krizi (16.11.2026)

İlk üç kriz ani kriz olduğu için H4'ün erken uyarı mantığı test edilemiyordu. Gerginliğin haftalar içinde tırmandığı Brunson krizi
eklendi: 26 Temmuz yaptırım tehdidi, 1 Ağustos bakanlara yaptırım, 3 Ağustos Türkiye'nin karşılığı, 10 Ağustos gümrük vergilerinin
ikiye katlanması. **Kriz tarihi 10 Ağustos 2018** (tepe nokta), 1 Ağustos alternatif. Karşı taraf ABD.

- **Veri:** GDELT olay dosyaları (121 gün), İngilizce GKG (121 gün, 333 aday), Türkçe çeviri katmanı (±14 gün, 444.533 haber, 219 aday),
  EuRepoC ve Hackmageddon. Ana veri hattı değiştirilmedi; olaylar `data/processed/brunson_kodlama.csv` dosyasında kaynak bağlantıları
  ve gerekçeleriyle elle kodlandı → `olaylar_brunson_2018.csv` (10 kayıt, 8'i sayıma dahil).
- **Kodlanan olaylar:** Ayyıldız Tim → Stéphane Bern (FR, 05.08, kriz öncesi); Ayyıldız Tim → Trump şirket siteleri ve NBC muhabiri
  Peter Alexander (10–12.08); Aslan Neferler Tim → American Federal Bank ve Trump otel siteleri (15–18.08); Ayyıldız Tim → NYT, Bloomberg,
  Fox gazetecileri (24.08); AsparTim → usfinanceinc.com (24.08); Ayyıldız Tim → Shahid Kapoor (IN, 06.09); Akıncılar → Mısır MENA (11.09);
  Ayyıldız Tim → Peter King'in kampanya sitesi (05.10). Sayım dışı: Diyarbakır Valisi hesabı ve Mersin SMS saldırısı (fail belirsiz).
  Doğrulanamayan Lewandowski hesabı haberi kodlanmadı. **Türk gruplarının ABD hedefli saldırılarının çoğu yalnızca Türkçe kaynaklarda var.**
- **Not:** Ayyıldız Tim'in ABD'li gazetecilerin hesaplarını ele geçirme kampanyası Ocak 2018'den beri sürüyordu; krizden sonraki
  saldırılar kısmen var olan bir kampanyanın yoğunlaşması. ±60 günlük kriz öncesi pencerede bu kampanyaya ait ABD hedefli kayıt bulunmadı.

| Test | 10 Ağustos | 1 Ağustos (alternatif) |
|---|---|---|
| H1 tüm olaylar (önce → sonra, kesin binom) | 1 → 7, p = 0,037 | 0 → 7, p = 0,008 |
| H1 karşı tarafa (ABD) | 0 → 5, p = 0,033 | 0 → 4, p = 0,065 |
| H2 Türk hacktivistlerde karşı tarafın payı | 0/1 → 5/7, p = 0,38 | 0/0 → 4/7, test edilemez |
| H4 Granger, TR–USA endeksi (1 / 2 / 3 gün) | p = 0,009 / 0,030 / 0,070 | p = 0,002 / 0,008 / 0,020 |

**Kriz türü** (`h4_kriz_turu_dort_kriz.csv`; tırmanan = kriz öncesi 14 günde eğim anlamlı pozitif ya da gerginlik önceki döneme göre
≥ 1 SS yüksek): Rusya −0,66 SS, Hollanda 0,38, Barış Pınarı (TR–SYR) 0,14 → ani; **Brunson 1,55 SS → tırmanan**.

**Havuzlanmış Poisson, dört kriz** (`h4_havuz_dort_kriz.csv`, 472 gün, 20 karşı tarafa saldırı):

| Model | Önceki 1–3 günün gerginliği, IRR (1 SS) | p |
|---|---|---|
| Yalnız gecikmeli gerginlik + kriz sabit etkisi | 3,44 [1,65; 7,17] | 0,001 |
| + aynı günün gerginliği + kriz sonrası kukla | 3,23 [1,25; 8,37] | 0,016 |

Üç ani krizle bu modelde gecikmeli gerginliğin etkisi kriz sonrası kukla eklenince kayboluyordu (p = 0,20). Tırmanan Brunson krizi
eklenince etki kriz şokundan bağımsız olarak anlamlı kalıyor: gerginlik 1 SS arttığında sonraki günlerde karşı tarafa saldırı
olasılığı yaklaşık üç kat artıyor. **Yorum:** Gerginlik ölçümü ani krizlerde erken uyarı vermiyor, ama tırmanan krizlerde saldırıları
1–2 gün önceden haber veriyor. Bu bulgu tek bir tırmanan krize ve 5 saldırı gününe dayanıyor; başka tırmanan krizlerle (ör. 2020 Doğu
Akdeniz) sınanması gerekir.

### İkinci tırmanan kriz denemesi: 2020 Türkiye–Yunanistan (Doğu Akdeniz) krizi (16.11.2026)

`src/tirmanan_krizler.py` (brunson.py'nin genelleştirilmiş hali) Brunson ve Doğu Akdeniz krizlerini aynı yöntemle analiz ediyor ve beş krizi
havuzlanmış H4 modeline alıyor. **Kriz tarihi 10 Ağustos 2020** (Oruç Reis'in gönderilmesi), 12 Ağustos (fırkateyn çarpışması) alternatif;
karşı taraf Yunanistan.

- **Veri:** GDELT olay dosyaları, İngilizce GKG (339 aday), Türkçe çeviri katmanı (±14 gün, 416.391 haber, 178 aday). EuRepoC'de dönemde Türkiye
  kaydı yok; Hackmageddon'ın Temmuz–Ekim 2020 zaman çizelgelerinin dördü sitede kaldırılmış (sunucu hatası, yazar yorumlarda doğruluyor).
  Olaylar neredeyse tamamen haberlerden geliyor ve İngilizce kaynakların çoğu Yunan basını (Greek City Times); bu krizdeki kapsam diğerleriyle
  tam karşılaştırılabilir değil.
- **Kodlanan olaylar** (`dogu_akdeniz_kodlama.csv` → `olaylar_dogu_akdeniz_2020.csv`, 9 kayıt, 8'i sayıma dahil): RootAyyıldız → Yunan İçişleri
  Bakanlığı iddiası (11.06, Yunan tarafı yalanladı, sayım dışı); Anonymous Greece → RootAyyıldız forumu ve Türk sağlık kayıtları (14.06);
  Aslan Neferler Tim → American Federal Bank (05.08, ABD); RootAyyıldız → Yunan Çalışma Bakanlığı (14.08); TurkDef → Toyota Yunanistan (15.08);
  Anonymous Greece → Türk devlet siteleri (18.08); adı belirtilmemiş Türk hackerlar → Doğu Makedonya-Trakya bölge yönetimi, askeri hastane ve
  istihbarat servisi siteleri (18.08); Türk hacker → Dimokratia gazetesi (19.09); Anonymous Greece → TBMM alt alan adı (08.10, gerekçe
  Ermenistan). Türk–Yunan siber çatışması 2020 başından beri sürüyordu (Ocak'ta Yunan bakanlıkları, 8 Haziran'da Halkidona belediyesi ve
  karşılığında Türk Dışişleri ve Savunma bakanlıkları; pencere dışında).

| Test | 10 Ağustos 2020 |
|---|---|
| H1 tüm olaylar (önce → sonra) | 2 → 6, p = 0,15 |
| H1 karşı tarafla ilgili | 1 → 6, p = 0,065 |
| H2 Türk hacktivistlerde karşı tarafın payı | 0/1 → 4/4, p = 0,20 |
| H4 Granger, TR–GRC endeksi (1–7 gün) | p = 0,29–0,59 |

**Kriz türü: "ani" çıktı.** GDELT'e göre Türkiye–Yunanistan gerginliği kriz tarihinden önce değil, Temmuz ortasında (Ayasofya kararı ve
21 Temmuz'daki ilk Oruç Reis NAVTEX'i) zirve yaptı, arabuluculukla düştü ve 10 Ağustos'ta yeniden yükseldi:

| Dönem (gün) | −60…−31 | −30…−15 | −14…−1 | 0…14 | 15…60 |
|---|---|---|---|---|---|
| Doğu Akdeniz endeksi | −0,15 | 0,42 | 0,03 | 0,20 | −0,12 |
| Brunson endeksi | −0,65 | −0,13 | 1,08 | 0,66 | −0,08 |

Bu kriz düz bir tırmanma değil, dalgalı ve uzun süreli bir gerginlik. Ayrıca krizden sonra Goldstein ortalaması pozitif (1,34): yoğun
diplomasi (arabuluculuk, görüşmeler) GDELT'te işbirliği olarak kodlandığı için **Goldstein ortalaması diplomasinin yoğun olduğu krizlerde
gerginliği olduğundan düşük gösterebiliyor.** Bu nedenle Doğu Akdeniz, H4 bulgusunu ikinci bir tırmanan krizle sınamak için uygun çıkmadı.

**Havuzlanmış Poisson, beş kriz** (`h4_havuz_bes_kriz.csv`, 590 gün, 27 karşı tarafla ilgili saldırı):

| Model | IRR | p |
|---|---|---|
| Önceki 1–3 günün gerginliği + kriz sabit etkisi | 2,57 [1,35; 4,90] | 0,004 |
| + aynı günün gerginliği + kriz sonrası kukla | 2,04 [0,89; 4,67] | 0,093 |
| Gecikmeli gerginlik × tırmanan kriz etkileşimi | 3,53 [0,71; 17,60] | 0,124 |
| Yalnız tırmanan kriz (Brunson), kontrollerle | 5,24 [1,33; 20,61] | 0,018 |
| Yalnız ani krizler (dört kriz), kontrollerle | 1,33 [0,50; 3,53] | 0,57 |

**Sonuç:** Gerginliğin saldırıları önceden göstermesi şimdilik yalnızca bir krizde (Brunson) görülüyor; ani ya da dalgalı krizlerde böyle
bir ilişki yok. Etkileşim terimi yön olarak bunu destekliyor ama anlamlı değil. H4 için daha güçlü kanıt, GDELT'te tırmanması net ölçülebilen
başka krizler ya da Goldstein ortalaması yerine yalnızca çatışma olaylarına dayanan bir gerginlik ölçüsü gerektiriyor.

### H4: çatışmaya dayalı gerginlik ölçüsü (16.11.2026)

Doğu Akdeniz analizi, Goldstein ortalamasının çatışma ve işbirliği olaylarını birlikte ortaladığını, bu yüzden yoğun diplomasinin
yaşandığı krizlerde gerginliği olduğundan düşük gösterebildiğini ortaya koydu. `src/catisma_olcusu.py` yalnızca çatışma olaylarına
(GDELT QuadClass 3 sözlü, 4 maddi çatışma) dayanan iki ölçüyle H4 analizlerini beş kriz için tekrarlıyor:

- **Çatışma yoğunluğu:** log(1 + Σ |Goldstein| × anma sayısı), yalnız çatışma olayları.
- **Ağırlıklı çatışma payı:** çatışma olaylarının ağırlığının bütün olayların ağırlığına oranı (haber ilgisinin genel artışından etkilenmez).

Sonuçlar `h4_catisma_*.csv`, grafik `outputs/h4_catisma_olcusu.png`.

**Kriz türü** (kriz öncesi 14 günde ölçünün önceki döneme göre farkı, SS):

| Kriz | Goldstein + ton endeksi | Çatışma yoğunluğu | Çatışma payı |
|---|---|---|---|
| Rusya 2015 | −0,75 ani | −0,65 ani | −0,86 ani |
| Hollanda 2017 | 0,50 ani | **1,26 tırmanan** | **1,17 tırmanan** |
| Barış Pınarı 2019 | 0,17 ani | 0,49 ani | 0,39 ani |
| Brunson 2018 | **1,83 tırmanan** | **1,84 tırmanan** | **1,63 tırmanan** |
| Doğu Akdeniz 2020 | −0,03 ani | 0,17 ani | −0,09 ani |

Çatışma ölçüleriyle Hollanda krizi de tırmanan çıkıyor: çatışma yoğunluğu kriz gününden yaklaşık bir hafta önce (miting yasakları,
"Nazi" açıklamaları) yükselmeye başlıyor; Goldstein ortalaması bu tırmanmayı göstermiyordu. Doğu Akdeniz ise her üç ölçüyle de ani:
gerginlik Temmuz ortasında zirve yapıp düşmüştü.

**Granger** (en küçük p, 1–7 gün): çatışma yoğunluğuyla Hollanda p < 0,001, Brunson p = 0,014, Barış Pınarı p = 0,003 (yalnız 2 saldırı
günü), Rusya p = 0,30, Doğu Akdeniz p = 0,52.

**Havuzlanmış Poisson, beş kriz** (önceki 1–3 günün ölçüsü + aynı gün + kriz sonrası kukla + kriz sabit etkisi; 27 saldırı):

| Ölçü | Beş kriz | Etkileşim: gecikmeli × tırmanan | Yalnız tırmanan | Yalnız ani |
|---|---|---|---|---|
| Çatışma yoğunluğu | 1,57, p = 0,21 | **8,28 [2,34; 29,37], p = 0,001** | **5,02, p = 0,015** (Brunson, Hollanda) | 0,87, p = 0,76 |
| Çatışma payı | 1,14, p = 0,70 | 3,81, p = 0,068 | 2,71, p = 0,14 | 0,78, p = 0,56 |
| Goldstein + ton endeksi | 1,72, p = 0,12 | 2,97, p = 0,11 | 4,05, p = 0,018 (Brunson) | 1,22, p = 0,62 |

**Yorum:** Gerginlik, kriz öncesinde tırmanan krizlerde saldırıları önceden gösteriyor, ani krizlerde göstermiyor. Çatışma yoğunluğuyla
bu fark istatistiksel olarak anlamlı (etkileşim p = 0,001) ve artık iki krize (Brunson, Hollanda) dayanıyor.

**Sınırlılıklar:**
- Bu ölçü sonuçlar görüldükten sonra, Doğu Akdeniz'deki ölçüm sorunu üzerine eklendi; ön kayıtlı bir analiz değil.
  Doğu Akdeniz sınıflaması bu ölçüyle de değişmedi.
- Çatışma yoğunluğu haber hacmine de bağlı; hacmi dışarıda bırakan çatışma payıyla etki aynı yönde ama zayıf
  (etkileşim p = 0,068). Sinyalin bir kısmı genel medya ilgisinden geliyor olabilir.
- Tırmanan krizlerde toplam 9 saldırı var; Granger sonuçları birkaç saldırı gününe dayanıyor.

### Türkçe taramanın 121 güne genişletilmesi ve v04 (17.11.2026)
Önerideki 1. hedef doğrultusunda GDELT çeviri katmanı taraması üç ana krizin ±60 gününe genişletildi
(kriz başına 11.616 dosya; Rusya 4,1 milyon, Hollanda 2,9 milyon, Barış Pınarı 1,8 milyon Türkçe haber).
Tarama betiği tek geçişte arama yapacak biçimde hızlandırıldı; eski yöntemle aynı çıktıyı verdiği bir dosya
üzerinde doğrulandı.

- Aday başlıklar (Rusya 2.779, Hollanda 2.431, Barış Pınarı 757 tekil başlık) önce saldırı fiili + taraf
  (ülke ya da bilinen Türk grubu) süzgecinden geçirildi, aynı haberin kopyaları birleştirildi; ±14 gün dışındaki
  adaylar okunup önemli olanların haber metni açıldı. Süzgecin dışında kalan başlıklar da ayrıca gözden geçirildi.
- **GDELT tarih uyarısı:** Çeviri katmanı bazı eski haberleri geç taradığı için tarihleri yanlış gösterebiliyor
  (ör. "Türk hackerlardan büyük saldırı" 2011, RedHack–YÖK belgeleri 2013 haberi çıktı). Bu yüzden her yeni
  olayın tarihi haber kaynağından doğrulandı.
- **Yeni olaylar (14):** Rusya: Türk Hack Team "Vatan Operasyonu" (28.09.2015, ~4.100 site), Cyber Warrior
  Akıncılar → Rusya Parlamentosu ve İçişleri Bakanlığı (02.01.2016), Yaşartim → Barış İçin Akademisyenler sitesi
  (14.01.2016), Türk Hack Team → Russian Standard Bank ve Alfa-Bank (19.01.2016). Hollanda: Ayyıldız Tim → Hammer
  Films (17.01.2017), Turkz → İran Kültür ve Turizm Bakanlığı (26.01.2017), Türk Hack Team → Fitch (08.02.2017),
  Turkz → Almanya ve Hollanda'da 100+ site (20.02.2017, kriz öncesi), Aslan Neferler Tim → Zürih Havalimanı ve 24
  İsviçre sitesi (27.03.2017), Ayyıldız Tim → Hüsnü Bozkurt'un Twitter hesabı (04.04.2017), Peter Pilz'in sitesi
  (22.04.2017, saldırgan belirsiz, sayım dışı). Barış Pınarı: RootAyyıldız → Laos Cumhurbaşkanlığı (14.08.2019) ve
  Hindistan Bihar Eğitim Bakanlığı (18.08.2019), Mardin Life gazetesi (13.09.2019, saldırgan belirsiz, sayım dışı).
- **Mevcut kayıtlara bağlananlar (3, mükerrer kuralı):** Ayyıldız Tim'in 19 bin Rus vatandaşının bilgileri ve
  S7 Havayolları saldırısı RUS-40'a (tarih 26.12.2015'e çekildi); RedHack'in 24.12.2015 banka saldırısını
  üstlenmesi RUS-37'ye eklendi.
- v03'teki olay numaraları korundu (ikinci kodlayıcı formu bunlara dayanıyor). `olaylar_v04.csv`: 63 kayıt,
  37'si sayıma dahil (v03: 49 / 25). Kodlama: `data/processed/tarama121_kodlama.csv`.

**Sonuçlar (v04; v03 karşılığı parantez içinde):**

| Test | v04 | v03 |
|---|---|---|
| H1, tüm olaylar (önce→sonra) | 13→24, IRR 1,82 [0,92; 3,57], p = 0,083 | 6→19, IRR 3,11, p = 0,015 |
| H1, karşı tarafla ilgili olaylar | 2→16, IRR 7,87 [1,81; 34,22], p = 0,006 | 1→14, IRR 13,77, p = 0,011 |
| H2, karşı tarafı hedef alma payı | 2/12 → 16/22, Fisher p = 0,002 | 1/5 → 14/17, p = 0,021 |
| H4 (Granger) | değişmedi (karşı tarafa yönelik günlük seriler büyük ölçüde aynı) | |
| Kriz dışı karşılaştırma | değişmedi (yalnız Hackmageddon'a dayanıyor): kriz sonrası IRR 4,29, p = 0,001 | |

Yorum: v03'te Türkçe tarama yalnızca krizin ±14 gününü kapsıyordu; kriz tarihine yakın günler daha yoğun
aranmış oluyordu. 121 günlük taramayla arama yoğunluğu pencere boyunca eşitlendi. Bunun sonucunda **toplam**
saldırı sayısındaki artış zayıfladı ve 0,05 düzeyinde anlamlılığını yitirdi; buna karşılık **krizin karşı tarafına
yönelik** saldırılardaki artış ve hedef kayması (H2) güçlendi. Bulgu şöyle özetlenebilir: krizler Türk
hacktivistlerinin toplam faaliyetini sınırlı ölçüde artırıyor, asıl etkisi faaliyeti krizin karşı tarafına
yöneltmesi. Tek tip kaynağa dayanan kriz dışı karşılaştırma (Hackmageddon) kriz sonrası artışı göstermeye devam
ediyor. Sağlamlık tablosu (`saglamlik.csv`) da v04 ile yenilendi: karşı tarafa yönelik saldırılar ±45 ve ±60
pencerelerinde, kriz tarihini 7 gün geri almada ve Hollanda ya da Barış Pınarı çıkarıldığında anlamlı; ±30 gün
penceresinde, tarih 7 gün ileri alındığında ve Rusya krizi çıkarıldığında (p = 0,10) anlamlı değil. Yani sonuç
en çok Rusya krizine dayanıyor.

### Brunson ve Doğu Akdeniz: Türkçe taramanın 121 güne genişletilmesi (18.11.2026)
Aynı tarama iki tırmanan kriz örneği için de ±60 güne genişletildi (Brunson 2,0 milyon, Doğu Akdeniz 1,8 milyon
Türkçe haber). Yeni kayıtlar `brunson_kodlama.csv` ve `dogu_akdeniz_kodlama.csv` dosyalarına eklendi:

- Brunson: Vakıf Katılım Bankası sitesindeki döviz kurlarının değiştirilmesi (10.09.2018, saldırgan belirsiz, sayım
  dışı). "Türk hacker grubu Yunanistan Cumhurbaşkanlığı sitesini hackledi" (25.08.2018) haberinin sayfası artık
  açılmıyor ve başka kaynakta doğrulanamadı; eklenmedi. Yeni sayılan olay yok.
- Doğu Akdeniz: Ayyıldız Tim → Yunanistan Ekonomi ve Kalkınma Bakanlığı (03.09.2020, kriz ikilisi), RedHack →
  Güzelyurt ve Susuz belediyeleri (01.07.2020, Türkiye içi), Güney Ege Bölge Başkanlığı sitesi (12.06.2020, saldırgan
  adlandırılmamış, sayım dışı). "Türk hackerlar Yunanistan Çevre ve Enerji Bakanlığı'nı hackledi" (06.09.2020) haberi
  doğrulanamadı; eklenmedi.

Sonuçlar (`tirmanan_sonuc.csv`, `h4_*_bes_kriz.csv`, `h4_catisma_*.csv`; önceki değer parantez içinde):
- Doğu Akdeniz H1 tüm olaylar 3→7, p = 0,18; karşı tarafla ilgili 1→7, p = 0,037; H2 0/2 → 5/5, p = 0,048.
  Brunson değişmedi (1→7, p = 0,037; karşı tarafla ilgili 0→5, p = 0,033).
- Havuzlanmış H4, Goldstein–ton endeksi, beş kriz: IRR 2,65, p = 0,002; yalnız tırmanan (Brunson) 5,24, p = 0,018;
  yalnız ani 1,93, p = 0,15.
- Çatışma yoğunluğu ölçüsü: etkileşim (gecikmeli gerginlik × tırmanan) 4,45, p = 0,005 (8,28, p = 0,001); yalnız
  tırmanan krizler 2,78, p = 0,074 (5,02, p = 0,015); yalnız ani krizler 0,86, p = 0,72. Tırmanan krizlerdeki etki
  Hollanda'ya kriz öncesi eklenen Turkz saldırısı (20.02.2017) nedeniyle zayıfladı; ani ve tırmanan krizler arasındaki
  fark anlamlı kalıyor.

**Hedef 1 durumu:** Önerideki üç kriz için 63 kayıt (37'si sayıma dahil); hedef en az 80 olay. İki tırmanan krizle
birlikte toplam 86 kayıt var. Öneri metnine göre tek kaynakta geçen olaylar yalnızca duyarlılık analizinde
kullanılacak; şu ana kadar tek kaynaklı hacktivist olaylar notla sayıma alındı (ör. AsparTim, Hammer Films, Laos).
Bu tutarsızlığın giderilmesi gerekiyor (aşağıda).

### Tek kaynaklı olaylar ve duyarlılık analizi (18.11.2026)
Öneri metni tek kaynakta geçen olayların yalnızca duyarlılık analizinde kullanılacağını söylüyor; kodlamada ise
tek kaynaklı hacktivist olaylar notla sayıma alınmıştı. Tutarlılık için kural kılavuza yazıldı (bölüm 6.1):
tek kaynaklı olaylar ana analizde kalıyor, `tek_kaynak.csv` dosyasında gerekçeleriyle listeleniyor ve sağlamlık
analizinde dışarıda bırakılıyor. Sayıma dahil haber kaynaklı olaylar Türkçe ve İngilizce aday listelerinde
olay başına aranarak kaç farklı sitede geçtiği sayıldı; 10 olay tek kaynaklı çıktı (üç ana krizde 5: Laos,
Turkz → PKK yanlısı hesaplar, Hammer Films, Turkz → İran, Turkz → Ermenistan Parlamentosu; Brunson'da AsparTim;
Doğu Akdeniz'de ANT → American Federal Bank ve Greek City Times'ın tek kaynak olduğu üç Anonymous Greece saldırısı).

| Senaryo (±60 gün, üç ana kriz) | Tüm olaylar | Karşı tarafla ilgili | H2 |
|---|---|---|---|
| Ana analiz | 13→24, IRR 1,82, p = 0,083 | 2→16, IRR 7,87, p = 0,006 | 2/12 → 16/22, p = 0,002 |
| Tek kaynaklılar hariç | 9→23, IRR 2,51, p = 0,019 | 2→15, IRR 7,38, p = 0,008 | 2/8 → 15/21, p = 0,033 |

Tek kaynaklı olayların çoğu kriz öncesine düştüğü için bunlar çıkarılınca toplam artış yeniden anlamlı oluyor;
karşı tarafa yönelik artış ve hedef kayması her iki durumda da anlamlı. Tırmanan krizlerde (`tirmanan_sonuc.csv`):
Brunson karşı tarafla ilgili 0→4, p = 0,065 (ana analizde 0→5, p = 0,033); Doğu Akdeniz 0→5, p = 0,033 (1→7,
p = 0,037). H4 serileri bu senaryoda yeniden hesaplanmadı.

## Henüz yapılmayanlar

- H4 için tek kaynaklı olaylar hariç duyarlılık analizi
- H3 için kriz dışı dönemlerde de haber taraması
- H4 bulgusunu önceden belirlenmiş ölçüyle yeni tırmanan krizlerde sınamak
- İkinci kodlayıcının (danışman) formu doldurması ve Kappa'nın hesaplanması
- CFR Cyber Operations Tracker kayıtlarının elle eklenmesi

