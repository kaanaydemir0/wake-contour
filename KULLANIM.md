# Wake Contour · Kurulum ve kullanım

## Hızlı başlangıç

### Programı açma
Program klasöründeki Baslat.cmd dosyasına çift tıklayın. Program boş tablo ve başlangıç ekranıyla açılır. Herhangi bir tablo otomatik yüklenmez.

### İlk grafiğinizi oluşturma
1. CSV / TSV aç düğmesiyle hız oranı tablonuzu seçin.
2. Excel kullanıyorsanız ilk satırdaki yarıçaplar ve ilk sütundaki açılar dahil tüm tabloyu kopyalayın. Programın solundaki metin alanına tıklayıp Ctrl+V ile yapıştırın. Mevcut metni değiştirmek için önce Ctrl+A kullanın.
3. Grafik ayarlarından Hız oranı Vx/Vs veya İz katsayısı w seçin. Girdi her zaman Vx/Vs olmalıdır.
4. Grafiği çiz / güncelle düğmesine basın.
5. PNG / SVG kaydet ile grafiği kaydedin.

### Tabloyu düzenleme
Sol alandaki sayıları doğrudan değiştirebilirsiniz. Değişiklikten sonra Grafiği çiz / güncelle düğmesine basın. CSV kaydet düğmesi düzenlenen tabloyu bir CSV dosyasına kaydeder.

Yeni dosya açarken veya programı kapatırken kaydedilmemiş tablo değişiklikleri varsa uyarı verilir. Grafiği kaydetmek tablonun bağımsız CSV kaydıyla aynı işlem değildir; grafik dışa aktarılırken ayrıca bir girdi kopyası oluşturulur.

### Yardımı açma
Yardım > Kurulum ve kullanım kılavuzu yolunu kullanın veya F1'e basın. Kılavuz internet bağlantısı olmadan açılır. Sekmeler arasında geçiş yapabilir, kaydırabilir ve seçtiğiniz metni Ctrl+C ile kopyalayabilirsiniz. Escape tuşu yardım penceresini kapatır.

## Kurulum

### Mevcut bilgisayarda çalıştırma
Baslat.cmd dosyasına çift tıklayın. Başlatıcı programın kendi .venv ortamını kullanır. Bu ortam yoksa kurulu Python'dan veya bilgisayarda bulunan Codex Python ortamından oluşturur.

NumPy ve Matplotlib eksikse ilk çalıştırmada internetten indirilir. Paketler kurulduktan sonra grafik çizimi ve yardım için internet gerekmez. Paketler bu programın .venv klasörüne kurulur.

### Başka bir Windows bilgisayara kurma
1. Resmî Python dağıtımından Python 3.10 veya daha yeni bir sürüm kurun. Kurulumda Tcl/Tk desteği ve Python başlatıcısı (py) bulunmalı; python komutu kullanılacaksa PATH seçeneğini etkinleştirin.
2. Program klasörünü kopyalayın. Eski bilgisayarın .venv klasörünü taşımayın; sanal ortamlar kurulduğu bilgisayara bağlıdır.
3. Baslat.cmd dosyasına çift tıklayın. Başlatıcı yeni bilgisayarda ortamı oluşturup paketleri yükler.

Kopyada Baslat.cmd, start.ps1, wake_app.py, wake_plot.py, KULLANIM.md ve requirements.txt aynı klasörde bulunmalı. assets klasörü uygulamanın ikonunu içerir; bu klasörü de birlikte taşıyın. KULLANIM.md uygulamanın içindeki yardımın kaynağıdır.

### Elle kurulum
PowerShell'i program klasöründe açıp şu komutları çalıştırın:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe wake_app.py
```

py komutu yoksa ilk komutta py -3 yerine python kullanabilirsiniz. Python sürümünün en az 3.10 olduğundan emin olun.

requirements-lock.txt doğrulanmış ortamın tam paket sürümlerini saklar. Aynı sürümleri kullanmak için paket kurulumunda requirements.txt yerine requirements-lock.txt seçebilirsiniz; Python sürümü ve platform uyumlu olmalıdır.

### Kurulumu denetleme
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 -CheckOnly
```

Bu komut ortamı/paketleri hazırlar ve arayüzü açmadan durur. İlk kurulumda eksik paketlerin indirilmesi gerekebilir.

## Tablo biçimi

### Satır ve sütunların anlamı
İlk hücre angle_deg veya Angle gibi bir başlık olabilir. İlk satırın kalan hücreleri boyutsuz r/R yarıçaplarıdır. İlk sütundaki değerler derece cinsinden açılardır. İç hücreler Vx/Vs eksenel hız oranlarıdır.

Biçimi göstermek için hazırlanmış küçük bir tablo:

```csv
angle_deg,0.2,0.4,0.7,1.0
0,0.30,0.35,0.40,0.45
90,0.60,0.80,0.95,1.05
180,0.50,0.75,0.90,0.95
```

Bu sayılar yalnızca dosya biçimini gösterir; kendi ölçüm veya hesap verinizi girin.

### Desteklenen dosya ve ayırıcılar
- CSV: hücreler virgülle, ondalıklar noktayla ayrılır.
- Noktalı virgüllü CSV: hücreler noktalı virgülle ayrılır; ondalık virgül veya nokta kullanılabilir.
- TSV veya Excel'den yapıştırma: hücreler sekmeyle ayrılır; ondalık virgül veya nokta kullanılabilir.
- Boşlukla ayrılmış metin: başlığı angle_deg gibi boşluksuz yazın.
- .xlsx ve PDF doğrudan okunmaz. Excel'den kopyalayıp yapıştırın veya CSV olarak kaydedin.

Ondalık virgüllü satır örneği (noktalı virgül ayırıcı):
```text
0;0,30;0,35;0,40;0,45
```

### Veri kuralları
- En az iki açı satırı ve iki yarıçap sütunu gerekir.
- Açılar 0–360 derece aralığında, artan sırada ve tekrarsız olmalıdır.
- r/R değerleri sıfır veya pozitif, artan sırada ve tekrarsız olmalıdır. r/R > 1 verileri de girilebilir.
- Eşit aralık zorunlu değildir. Tüm veri satırlarında hücre sayısı aynı olmalıdır.
- Boş hücre, NaN, sonsuz değer veya sayısal olmayan girdi kabul edilmez.
- 0 ve 360 derece birlikte girilirse hız satırları eşit olmalıdır. Tam çevre veride 0 derece satırını 360 derece olarak da ekleyin.
- r/R=0 girilirse bütün açılarda merkez hızı aynı olmalıdır; bu sütun tek bir fiziksel noktadır.
- Vx/Vs > 1 ve negatif hız oranları korunur; otomatik kırpma uygulanmaz.

## Grafik ve kayıt

### Hız oranı ve iz katsayısı
Hız oranı q = Vx/Vs, yerel eksenel hızın gemi hızına oranıdır. İz katsayısı w = 1 - q ile hesaplanır. Görüntüleme seçimi girdi tablosunun türünü değiştirmez: tabloya her zaman q değerleri girin.

Örneğin q=0.4 için w=0.6 olur. q>1 olan bölgelerde negatif w fiziksel olarak yerel hızlanmayı gösterebilir ve korunur.

### Koordinatlar ve konturlar
0 derece yukarı, 90 derece sağ, 180 derece aşağı yönündedir. Koordinatlar:
```text
x/R = (r/R) sin(theta)
y/R = (r/R) cos(theta)
```

Koordinatlar ve renk skalası boyutsuzdur. Konturlar eş hız oranı veya eş iz katsayısı çizgileridir; akım çizgileri değildir. Renklerin sayısal karşılığını sağdaki renk skalasından okuyun. Skala her tabloda otomatik belirlenir; farklı grafikleri yalnızca renklerine göre karşılaştırmayın.

### İnterpolasyon ve simetri
Ölçüm noktaları arasında açı ve yarıçap doğrultularında lineer interpolasyon yapılır. Kaynak noktalar korunur; veri alanı dışına ekstrapolasyon yapılmaz. En küçük yarıçapın içi, veri yoksa boş kalır. İnterpolasyon yeni bir ölçüm veya CFD çözümü değildir.

Tam disk seçeneği yalnızca 0–180 derece aralığındaki tabloları merkez düzlemine göre aynalar. Sol taraf bağımsız ölçüm değildir; simetri varsayımı başlıkta yazılır ve türetilen noktalar farklı işaretlenir. Zaten 0–360 derece veriniz varsa bu seçeneği kullanmayın.

### Grafik ayarları ve araç çubuğu
Verilen / aynalanan noktaları göster seçeneği veri noktalarını görünür kılar. Hedef renk bandı sayısı renk aralıklarını ayarlar; okunaklı sınırlar seçildiği için gerçek bant sayısı farklı olabilir.

Grafiğin altındaki araç çubuğundan yakınlaştırma, kaydırma ve başlangıç görünümüne dönüş yapılabilir. Tablo veya ayar değiştiğinde ana Grafiği çiz / güncelle düğmesini kullanın.

### Grafik ve veriyi kaydetme
PNG / SVG kaydet düğmesi mevcut tablo/ayarlarla grafiği yeniden çizer ve kayıt penceresini açar:
- PNG: 300 dpi raster görüntü.
- SVG: büyütüldüğünde keskin kalan vektörel çizim.

Seçtiğiniz ad contour.png ise yanında contour.input.csv ve contour.settings.json da saklanır. CSV kullanılan girdi tablosunu, JSON alan seçimini, simetriyi ve diğer yöntem ayarlarını içerir. Bu dosyaları grafikle birlikte tutun. Aynı isimle yeniden kaydetmek mevcut çıktı ve eşlik eden dosyaları değiştirir.

Yeniden açmak için .input.csv dosyasını CSV / TSV aç ile yükleyin ve JSON'daki ayarları seçin. JSON otomatik içe aktarılmaz. Düzenlenen tablonun bağımsız kopyası için CSV kaydet kullanın.

## Sorun giderme

### Python bulunamıyor
Python 3.10 veya daha yeni bir sürüm kurun. py veya python komutunun çalıştığını kontrol edin. Başlatıcının hata iletisi gösterdiği konsolu kapatmadan okuyun.

### Paket indirilemiyor
İlk kurulum internet erişimi gerektirir. Bağlantıyı kontrol edip Baslat.cmd dosyasını yeniden çalıştırın. Elle kurulum için Kurulum sekmesindeki pip komutunu kullanın.

### Tcl/Tk hatası
Tkinter arayüzü için Python'un Tcl/Tk bileşeni gerekir. Python kurulumunu bu bileşenle onarın veya tamamlayın. pip install tkinter kullanmayın; Tkinter standart Python dağıtımının bir parçasıdır.

### Hücre sayısı veya sayı biçimi hatası
Başlık dahil tüm satırlarda sütun sayısını kontrol edin. Ondalık virgül ile CSV ayırıcı virgülünü karıştırmayın; ondalık virgül için sekme veya noktalı virgül kullanın. Hata iletisindeki satır ve sütuna bakın.

### Tablo boş veya grafik değişmedi
Sol alana verinizi yapıştırın ya da dosya açın. Tablo/ayar değişiklikleri grafiği otomatik güncellemez; Grafiği çiz / güncelle düğmesine basın.

### Tam disk çizilemiyor
Simetrik tam disk seçeneği, ilk açısı 0 ve son açısı 180 derece olan tablolar için geçerlidir. Farklı bir sektör veya zaten tam çevre veri kullanıyorsanız seçeneği kapatın.

### Komut satırından grafik üretme
Program klasöründe PowerShell açın. Girdi yolunu kendi CSV dosyanızla değiştirin:
```powershell
.\.venv\Scripts\python.exe wake_plot.py --input "veriler.csv" --output "output\contour.png"
.\.venv\Scripts\python.exe wake_plot.py --input "veriler.csv" --output "output\wake.svg" --field wake
.\.venv\Scripts\python.exe wake_plot.py --input "veriler.csv" --output "output\full.png" --full-disc
```

Grafik dosyası üretirken --input zorunludur. Çıktı yolu verilmezse masaüstü arayüzü açılır. Komut satırı çıktısı yalnızca grafik dosyasıdır; eşlik eden CSV/JSON kayıtları uygulamadaki PNG / SVG kaydet düğmesiyle oluşturulur.
