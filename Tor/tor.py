import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt
from stem import Signal
from stem.control import Controller
from PyQt5.QtGui import QPalette

# Tor başlatma ve trafik yönlendirme fonksiyonları
def start_tor(controller, log_text_widget):
    try:
        controller.authenticate(password="your_tor_password")
        controller.signal(Signal.NEWNYM)
        log_text_widget.append("Tor bağlantısı başarıyla başlatıldı.")
        return True
    except Exception as e:
        log_text_widget.append(f"Tor başlatılamadı: {e}")
        return False

def route_traffic_through_tor():
    try:
        # Tüm trafik Tor'a yönlendiriliyor
        os.system('sudo iptables -t nat -A OUTPUT -m owner ! --uid-owner tor -p tcp --dport 9050 -j REDIRECT --to-port 9050')
        os.system('sudo iptables -A OUTPUT -m owner ! --uid-owner tor -d 127.0.0.1 -j REJECT')
        
        # DNS sızıntılarını engelleme
        os.system('sudo iptables -A OUTPUT -p udp --dport 53 -j REJECT')
        os.system('sudo iptables -A OUTPUT -p tcp --dport 53 -j REJECT')
        return "Tüm trafik Tor ağına yönlendirildi ve DNS sızıntıları engellendi."
    except Exception as e:
        return f"İnternet trafiği yönlendirilemedi: {e}"

class TorApp(QWidget):
    def __init__(self):
        super().__init__()

        # Pencere başlığı ve boyutu
        self.setWindowTitle("Golge Linux Tor Yönlendirme Aracı")
        self.setGeometry(100, 100, 1200, 800)  # Geniş pencere
        self.setMinimumSize(1500, 850)

        # Arka plan rengini koyu mor yapma
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Background, QColor(48, 25, 52))  # Koyu mor
        self.setPalette(palette)

        # Logo ekleme (orta yerleştirilecek)
        self.logo_label = QLabel(self)
        self.logo_pixmap = QPixmap("Tor/logo.png")  # Burada logo.png, çalıştırdığınız dizinde yer almalı
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)

        # Açıklama kısmı (alt kısmına yerleştirilecek)
        self.description_label = QLabel(
            "Golge Linux, internet trafiğinizi Tor ağı üzerinden yönlendirerek anonimlik sağlar. Bu araç, tüm internet bağlantılarınızı Tor ağından yapmaya zorlar, böylece çevrimiçi gizliliğiniz maksimum düzeye çıkar. Ancak, unutmayın ki Tor Browser kullanırken JavaScript'i kapalı tutmanız önemlidir. Aksi takdirde, kimlik bilgileriniz sızabilir ve çevrimiçi izlenmeniz mümkün olabilir.\n\n"
            "Tor ağı ile güvendesiniz, ancak anonimliğinizi kötü amaçlarla kullanmak, yasa dışı faaliyetlere katılmak veya zarar vermek kesinlikle kabul edilemez. Golge Linux , sadece güvenliğinizi sağlamak için tasarlanmış bir işletim sistemidir ve doğru amaçlarla kullanılmalıdır. Lütfen güvenliği ve etik kuralları göz önünde bulundurarak kullanın.\n\n"
            "Unutmayın: Tor ve anonimlik araçlarını sadece yasal ve etik amaçlarla kullanın."
        )
        self.description_label.setStyleSheet(""" 
            font-size: 18px; 
            color: white; 
            text-align: center; 
            margin-top: 30px;
            line-height: 1.5;
            font-weight: 400;
        """)
        self.description_label.setWordWrap(True)

        # Tor başlatma ve trafik yönlendirme butonu
        self.start_button = QPushButton("Tor Başlat ve Trafiği Yönlendir", self)
        self.start_button.setStyleSheet("""
            font-size: 20px;
            padding: 20px;
            background-color: #4CAF50;
            color: white;
            border-radius: 12px;
            border: 2px solid #388E3C;
            text-align: center;
            transition: all 0.3s ease;
        """)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.start_and_route)

        # Sonuçları gösterecek etiket
        self.result_label = QLabel("", self)
        self.result_label.setStyleSheet("font-size: 18px; color: white; padding-top: 20px; text-align: center;")
        self.result_label.setWordWrap(True)

        # Bilgi mesajı
        self.info_label = QLabel(
            " \nHer yerde herkes için gizlilik.\n-Golge Linux",
            self
        )
        self.info_label.setStyleSheet("font-size: 14px; color: white; text-align: center; margin-top: 20px;")
        self.info_label.setWordWrap(True)

        # Logları göstermek için QTextEdit widget'ı
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet("""
            font-size: 14px;
            color: white;
            background-color: #2E1D3C;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #5A4A6E;
        """)
        self.log_text_edit.setPlaceholderText("Bağlantı logları burada gösterilecek...")

        # Yatay düzen
        layout = QVBoxLayout()
        layout.addWidget(self.logo_label)  # Logo merkezi
        layout.addWidget(self.description_label)  # Açıklama alt kısımda
        layout.addWidget(self.start_button)  # Buton
        layout.addWidget(self.log_text_edit)  # Logları gösteren alan
        layout.addWidget(self.result_label)  # Sonuçlar
        layout.addWidget(self.info_label)  # Bilgi mesajı

        # Arayüzün ana yerleşimini belirleme
        self.setLayout(layout)

    def start_and_route(self):
        self.log_text_edit.clear()  # Önceki logları temizle
        self.log_text_edit.append("Tor bağlantısı başlatılıyor...")

        try:
            with Controller.from_port(port=9051) as controller:
                # Tor devrelerini görüntüle
                controller.add_event_listener(self.on_tor_status)
                if start_tor(controller, self.log_text_edit):
                    route_message = route_traffic_through_tor()
                    self.result_label.setText(f"<b>{route_message}</b>")
                else:
                    self.result_label.setText("Tor bağlantısı başlatılamadı.")
        except Exception as e:
            self.log_text_edit.append(f"Hata: {str(e)}")
            self.result_label.setText(f"Hata oluştu: {str(e)}")

    def on_tor_status(self, event):
        """Tor ağının durumunu dinleyerek, bağlantı durumu değiştikçe bilgi gösterir."""
        if event.state == "ONION":
            self.log_text_edit.append("Tor bağlantısı başarıyla kurulmuştur.")
        else:
            self.log_text_edit.append(f"Durum: {event.state}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TorApp()
    window.show()
    sys.exit(app.exec_())
