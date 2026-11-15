# Olay Kodlama Kılavuzu (sürüm 0.1 — pilot)

Bu kılavuz, farklı kaynaklardan gelen siber olayların tek bir veri setinde birleştirilmesi
için kullanılan kuralları tanımlar. Proje önerisindeki "yazılı kodlama protokolü" budur.

## 1. Kapsama ölçütü
Bir olay, aşağıdakilerden **en az biri** sağlanıyorsa veri setine girer:
- Hedef ülke Türkiye, ya da
- Saldırganın ülkesi Türkiye ya da saldırgan kendini Türk olarak tanımlıyor (ör. Turk Hack Team, Ayyıldız Tim).

Olay tarihi ilgili krizin ±60 günlük penceresinde olmalıdır.

## 2. Değişkenler

| Değişken | Açıklama | Değerler |
|---|---|---|
| `olay_id` | Benzersiz kimlik | `K{kriz}-{sıra}` |
| `tarih` | Saldırının başlangıç tarihi | YYYY-AA-GG |
| `tarih_kesinligi` | Tarihin hassasiyeti | `gun` / `ay` |
| `kriz` | İlgili kriz penceresi | `rusya_2015` / `hollanda_2017` / `barispinari_2019` |
| `gun_farki` | Kriz gününe göre gün | −60 … +60 |
| `saldirgan` | Saldıran aktörün adı | serbest metin; bilinmiyorsa `?` |
| `saldirgan_ulke` | Saldırganın ülkesi | ISO-2 kod; bilinmiyorsa boş |
| `hedef` | Hedef kurum/sistem | serbest metin |
| `hedef_ulke` | Hedef ülke | ISO-2 kod |
| `hedef_sektor` | Hedef sektörü | `kamu` / `finans` / `medya` / `kritik_altyapi` / `ozel` / `bireyler` / `diger` |
| `aktor_turu` | Aktör türü (bkz. 3) | `devlet_destekli` / `hacktivist` / `suc` / `belirsiz` |
| `saldiri_turu` | Saldırı tekniği | `ddos` / `tahrifat` / `veri_sizintisi` / `hesap_ele_gecirme` / `casusluk` / `diger` |
| `kriz_ikilisi` | Olay krizin karşı tarafıyla mı ilgili? (bkz. 4) | `evet` / `hayir` |
| `kaynaklar` | Olayın geçtiği veri tabanları | `eurepoc`, `hackmageddon`, `haber` (birden fazla olabilir) |
| `kaynak_url` | Birincil haber bağlantısı | URL |
| `not` | Kodlayıcı notu | serbest metin |

## 3. Aktör türü kuralları (1.1.1'deki tanımla uyumlu)
- **devlet_destekli:** Kaynakta bir devletle bağlantısı ya da sponsorluğu atfedilen grup.
  EuRepoC `initiator_category` = State / State affiliated actor; Hackmageddon sınıfı CE veya CW **ve** bir devlete atıf var.
- **hacktivist:** Devlet bağlantısı atfedilmeyen ve siyasi motivasyonunu açıkça ilan eden grup.
  EuRepoC `initiator_subcategory` = Hacktivist(s); Hackmageddon sınıfı H.
- **suc:** Mali kazanç amaçlı (Hackmageddon CC, EuRepoC Criminal(s)). Ana analizlere (H1–H2) **dahil edilmez**,
  sağlamlık analizinde ayrıca raporlanır.
- **belirsiz:** Yukarıdakilerin hiçbirine yeterli bilgi yok.

## 4. Kriz ikilisi kuralı
`kriz_ikilisi = evet` ancak şu durumlarda verilir:
- Bir taraf Türkiye, diğer taraf krizin karşı ülkesi (Rusya / Hollanda / ABD), **ya da**
- Saldırgan saldırıyı krize açıkça bağlıyor (ör. mesajında krize atıf var).

## 5. Mükerrer kayıt kuralı
İki kayıt **aynı olay** sayılır, eğer tarih farkı ≤ 3 gün, hedef ülke aynı ve hedef ya da saldırgan adı örtüşüyorsa.
Bu durumda tek satır tutulur; tarih için **gün düzeyindeki** kaynak esas alınır, `kaynaklar` alanına her iki kaynak yazılır.

## 6. Sayım dışı bırakılan kayıtlar (pilot kodlamada eklendi)
Aşağıdaki kayıtlar veri setinde tutulur ama günlük/haftalık sayım analizlerine (H1, H2, H4) **girmez**
(`sayima_dahil = hayir`, gerekçe `not` alanına yazılır):
- **Uzun süreli kampanya:** Birden fazla ay/yıla yayılan ve başlangıcı yalnızca ay düzeyinde bilinen operasyonlar
  (ör. Dragonfly 2.0, 2015–2017).
- **İfşa tarihi:** Kaydın tarihi saldırının değil, araştırma raporunun yayımlandığı gün olan casusluk kampanyaları
  (ör. Hackmageddon'da "Researchers discover…" ile başlayan CE kayıtları).
- **Türkiye'ye özgü olmayan:** Türkiye, onlarca hedef ülkeden yalnızca biri olarak geçiyorsa.
- **suc** kategorisindeki olaylar (bkz. 3).

## 7. Güvenilirlik
Olayların %20'si ikinci bir kodlayıcı (danışman) tarafından bağımsız kodlanır; `aktor_turu` ve `kriz_ikilisi`
için Cohen's Kappa hesaplanır (kabul eşiği 0,70).
