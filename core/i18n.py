"""
SRK Boost - Internationalization (i18n)
Supports: English (en), Turkish (tr)
"""

import json
import os

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".srk_boost", "settings.json")

TRANSLATIONS = {
    "en": {
        # Main Window
        "app_name": "SRK Boost",
        "dashboard": "Dashboard",
        "fps_boost": "FPS Boost",
        "scanner": "System Scanner",
        "cleaner": "Cleaner",
        "game_mode": "Game Mode",
        "startup": "Startup Manager",
        "drivers": "Driver Manager",
        "settings": "Settings",
        # Dashboard
        "system_health": "System Health",
        "cpu_usage": "CPU Usage",
        "ram_usage": "RAM Usage",
        "disk_usage": "Disk Usage",
        "performance": "Performance",
        "temperature": "Temperature",
        # FPS Boost
        "fps_boost_title": "FPS Boost",
        "fps_boost_desc": "Select the optimizations to apply:",
        "apply_selected": "Apply Selected",
        "restore": "Restore",
        "tweak_power": "High Performance Power Plan",
        "tweak_power_desc": "Sets the power plan to High Performance, maximizing CPU speed.",
        "tweak_gamebar": "Disable Xbox Game Bar",
        "tweak_gamebar_desc": "Disables Xbox Game Bar which consumes resources in the background.",
        "tweak_sysmain": "Disable SysMain (Superfetch)",
        "tweak_sysmain_desc": "Stops the SysMain service to reduce disk usage and memory overhead.",
        "tweak_diagtrack": "Disable DiagTrack",
        "tweak_diagtrack_desc": "Stops Windows telemetry service, freeing resources.",
        "tweak_visual": "Optimize Visual Effects",
        "tweak_visual_desc": "Disables Windows animations and transparency for better performance.",
        "tweak_memory": "Clear Standby Memory",
        "tweak_memory_desc": "Releases cached memory back to available pool.",
        "tweak_gpu": "GPU Performance Mode",
        "tweak_gpu_desc": "Sets GPU scheduling to prefer performance over power saving.",
        "tweak_search": "Disable Search Indexing",
        "tweak_search_desc": "Stops Windows Search indexing to reduce disk I/O during gaming.",
        "risk_low": "Low Risk",
        "risk_medium": "Medium Risk",
        # Game Mode
        "game_mode_title": "Game Mode",
        "game_mode_desc": "Select background processes to terminate:",
        "kill_selected": "Kill Selected",
        "process_name": "Process",
        "process_cpu": "CPU %",
        "process_ram": "RAM (MB)",
        "process_desc": "Description",
        "activate_game_mode": "Activate Game Mode",
        "deactivate_game_mode": "Deactivate Game Mode",
        # Cleaner
        "cleaner_title": "System Cleaner",
        "scan": "Scan",
        "clean": "Clean Selected",
        "scanning": "Scanning...",
        "cleaning": "Cleaning...",
        # Driver Manager
        "driver_title": "Driver Manager",
        "driver_name": "Device",
        "driver_version": "Version",
        "driver_date": "Date",
        "driver_status": "Status",
        "driver_action": "Action",
        "driver_uptodate": "Up to date",
        "driver_update": "Update available",
        "driver_unknown": "Unknown",
        "check_update": "Check Update",
        "refresh": "Refresh",
        # Settings
        "settings_title": "Settings",
        "language": "Language",
        "theme": "Theme",
        "restore_points": "Restore Points",
        "about": "About",
        # Common
        "ok": "OK",
        "cancel": "Cancel",
        "proceed": "Proceed",
        "close": "Close",
        "yes": "Yes",
        "no": "No",
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "confirm": "Confirm",
        "loading": "Loading...",
        "done": "Done",
        "admin_warning": "Some features require administrator privileges. Run as Admin for full functionality.",
    },
    "tr": {
        # Main Window
        "app_name": "SRK Boost",
        "dashboard": "Panel",
        "fps_boost": "FPS Hızlandır",
        "scanner": "Sistem Tarayıcı",
        "cleaner": "Temizleyici",
        "game_mode": "Oyun Modu",
        "startup": "Başlangıç Yöneticisi",
        "drivers": "Sürücü Yöneticisi",
        "settings": "Ayarlar",
        # Dashboard
        "system_health": "Sistem Sağlığı",
        "cpu_usage": "CPU Kullanımı",
        "ram_usage": "RAM Kullanımı",
        "disk_usage": "Disk Kullanımı",
        "performance": "Performans",
        "temperature": "Sıcaklık",
        # FPS Boost
        "fps_boost_title": "FPS Hızlandırma",
        "fps_boost_desc": "Uygulanacak optimizasyonları seçin:",
        "apply_selected": "Seçilenleri Uygula",
        "restore": "Geri Yükle",
        "tweak_power": "Yüksek Performans Güç Planı",
        "tweak_power_desc": "Güç planını Yüksek Performans olarak ayarlar, CPU hızını maksimize eder.",
        "tweak_gamebar": "Xbox Game Bar'ı Devre Dışı Bırak",
        "tweak_gamebar_desc": "Arka planda kaynak tüketen Xbox Game Bar'ı devre dışı bırakır.",
        "tweak_sysmain": "SysMain'i Devre Dışı Bırak",
        "tweak_sysmain_desc": "Disk kullanımını ve bellek yükünü azaltmak için SysMain servisini durdurur.",
        "tweak_diagtrack": "DiagTrack'i Devre Dışı Bırak",
        "tweak_diagtrack_desc": "Kaynak tüketen Windows telemetri servisini durdurur.",
        "tweak_visual": "Görsel Efektleri Optimize Et",
        "tweak_visual_desc": "Daha iyi performans için Windows animasyonlarını ve saydamlığını devre dışı bırakır.",
        "tweak_memory": "Bekleyen Belleği Temizle",
        "tweak_memory_desc": "Önbelleğe alınan belleği kullanılabilir havuza serbest bırakır.",
        "tweak_gpu": "GPU Performans Modu",
        "tweak_gpu_desc": "GPU zamanlamasını güç tasarrufundan performansa geçirir.",
        "tweak_search": "Arama Dizinlemeyi Devre Dışı Bırak",
        "tweak_search_desc": "Oyun sırasında disk G/Ç'yi azaltmak için Windows Arama dizinlemesini durdurur.",
        "risk_low": "Düşük Risk",
        "risk_medium": "Orta Risk",
        # Game Mode
        "game_mode_title": "Oyun Modu",
        "game_mode_desc": "Sonlandırılacak arka plan işlemlerini seçin:",
        "kill_selected": "Seçilenleri Kapat",
        "process_name": "İşlem",
        "process_cpu": "CPU %",
        "process_ram": "RAM (MB)",
        "process_desc": "Açıklama",
        "activate_game_mode": "Oyun Modunu Etkinleştir",
        "deactivate_game_mode": "Oyun Modunu Devre Dışı Bırak",
        # Cleaner
        "cleaner_title": "Sistem Temizleyici",
        "scan": "Tara",
        "clean": "Seçilenleri Temizle",
        "scanning": "Taranıyor...",
        "cleaning": "Temizleniyor...",
        # Driver Manager
        "driver_title": "Sürücü Yöneticisi",
        "driver_name": "Cihaz",
        "driver_version": "Sürüm",
        "driver_date": "Tarih",
        "driver_status": "Durum",
        "driver_action": "İşlem",
        "driver_uptodate": "Güncel",
        "driver_update": "Güncelleme mevcut",
        "driver_unknown": "Bilinmiyor",
        "check_update": "Güncelle",
        "refresh": "Yenile",
        # Settings
        "settings_title": "Ayarlar",
        "language": "Dil",
        "theme": "Tema",
        "restore_points": "Geri Yükleme Noktaları",
        "about": "Hakkında",
        # Common
        "ok": "Tamam",
        "cancel": "İptal",
        "proceed": "Devam Et",
        "close": "Kapat",
        "yes": "Evet",
        "no": "Hayır",
        "success": "Başarılı",
        "error": "Hata",
        "warning": "Uyarı",
        "confirm": "Onayla",
        "loading": "Yükleniyor...",
        "done": "Tamamlandı",
        "admin_warning": "Bazı özellikler yönetici ayrıcalığı gerektirir. Tam işlevsellik için Yönetici olarak çalıştırın.",
    }
}

_current_lang = "en"

def load_language():
    global _current_lang
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
                _current_lang = data.get("language", "en")
    except:
        _current_lang = "en"

def set_language(lang: str):
    global _current_lang
    if lang in TRANSLATIONS:
        _current_lang = lang
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            data = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE) as f:
                    data = json.load(f)
            data["language"] = lang
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except:
            pass

def get_language() -> str:
    return _current_lang

def tr(key: str) -> str:
    lang = TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"])
    return lang.get(key, TRANSLATIONS["en"].get(key, key))

load_language()

# Scanner translations - patch
_scanner_en = {
    "scan_hardware": "Scan Hardware",
    "scan_click_hint": "Click 'Scan Hardware' to detect your components.",
    "processor": "Processor",
    "graphics_card": "Graphics Card",
    "memory_ram": "Memory (RAM)",
    "motherboard": "Motherboard",
    "operating_system": "Operating System",
    "scanner_title": "System Scanner",
    "scanner_desc": "Detailed hardware information",
}
_scanner_tr = {
    "scan_hardware": "Donanımı Tara",
    "scan_click_hint": "Bileşenlerinizi algılamak için 'Donanımı Tara'ya tıklayın.",
    "processor": "İşlemci",
    "graphics_card": "Ekran Kartı",
    "memory_ram": "Bellek (RAM)",
    "motherboard": "Anakart",
    "operating_system": "İşletim Sistemi",
    "scanner_title": "Sistem Tarayıcı",
    "scanner_desc": "Detaylı donanım bilgisi",
}
TRANSLATIONS["en"].update(_scanner_en)
TRANSLATIONS["tr"].update(_scanner_tr)

# Additional UI strings
_extra_en = {
    "select_all": "Select All",
    "deselect_all": "Deselect All",
    "kill_selected": "Kill Selected",
    "activate_game_mode": "Activate Game Mode",
    "deactivate_game_mode": "Deactivate Game Mode",
    "refresh": "Refresh",
    "scan": "Scan",
    "clean": "Clean Selected",
    "check_update": "Check Update",
    "search_update": "Search Update",
    "apply_selected": "Apply Selected",
    "restore": "Restore",
    "delete_selected": "Delete Selected",
}
_extra_tr = {
    "select_all": "Tümünü Seç",
    "deselect_all": "Seçimi Kaldır",
    "kill_selected": "Seçilenleri Kapat",
    "activate_game_mode": "Oyun Modunu Etkinleştir",
    "deactivate_game_mode": "Oyun Modunu Devre Dışı Bırak",
    "refresh": "Yenile",
    "scan": "Tara",
    "clean": "Seçilenleri Temizle",
    "check_update": "Güncellemeyi Kontrol Et",
    "search_update": "Güncelleme Ara",
    "apply_selected": "Seçilenleri Uygula",
    "restore": "Geri Yükle",
    "delete_selected": "Seçilenleri Sil",
}
TRANSLATIONS["en"].update(_extra_en)
TRANSLATIONS["tr"].update(_extra_tr)

TRANSLATIONS["en"]["speedtest"] = "Speed Test"
TRANSLATIONS["tr"]["speedtest"] = "Hız Testi"

TRANSLATIONS["en"]["network"] = "Network Optimizer"
TRANSLATIONS["tr"]["network"] = "Ağ Optimizörü"

# Sidebar subtitles
TRANSLATIONS["en"]["nav_sub_dashboard"]      = "System overview and live stats"
TRANSLATIONS["tr"]["nav_sub_dashboard"]      = "Sistem göstergesi ve canlı istatistikler"
TRANSLATIONS["en"]["nav_sub_fps_boost"]      = "One-click performance optimization"
TRANSLATIONS["tr"]["nav_sub_fps_boost"]      = "Tek tıkla performans optimizasyonu"
TRANSLATIONS["en"]["nav_sub_game_profiles"]  = "Per-game tweak presets"
TRANSLATIONS["tr"]["nav_sub_game_profiles"]  = "Oyuna özel ayar profilleri"
TRANSLATIONS["en"]["nav_sub_benchmark"]      = "Before/after performance comparison"
TRANSLATIONS["tr"]["nav_sub_benchmark"]      = "Öncesi/sonrası performans karşılaştırması"
TRANSLATIONS["en"]["nav_sub_scanner"]        = "Detailed hardware information"
TRANSLATIONS["tr"]["nav_sub_scanner"]        = "Detaylı donanım bilgisi"
TRANSLATIONS["en"]["nav_sub_driver_manager"] = "Check and update device drivers"
TRANSLATIONS["tr"]["nav_sub_driver_manager"] = "Cihaz sürücülerini kontrol et ve güncelle"
TRANSLATIONS["en"]["nav_sub_cleaner"]        = "Remove junk files and caches"
TRANSLATIONS["tr"]["nav_sub_cleaner"]        = "Geçici dosyaları ve önbellekleri temizle"
TRANSLATIONS["en"]["nav_sub_game_mode"]      = "Kill background processes"
TRANSLATIONS["tr"]["nav_sub_game_mode"]      = "Arka plan işlemlerini kapat"
TRANSLATIONS["en"]["nav_sub_startup"]        = "Control boot-time programs"
TRANSLATIONS["tr"]["nav_sub_startup"]        = "Başlangıç programlarını yönet"
TRANSLATIONS["en"]["nav_sub_network"]        = "Ping reducer & live monitor"
TRANSLATIONS["tr"]["nav_sub_network"]        = "Ping düşürücü ve canlı izleme"
TRANSLATIONS["en"]["nav_sub_speedtest"]      = "Internet speed test"
TRANSLATIONS["tr"]["nav_sub_speedtest"]      = "İnternet hız testi"
TRANSLATIONS["en"]["nav_sub_backup"]         = "Create and manage restore points"
TRANSLATIONS["tr"]["nav_sub_backup"]         = "Geri yükleme noktaları oluştur ve yönet"
TRANSLATIONS["en"]["nav_sub_settings"]       = "Preferences and restore points"
TRANSLATIONS["tr"]["nav_sub_settings"]       = "Tercihler ve geri yükleme noktaları"

TRANSLATIONS["en"]["backup"] = "Backup & Restore"
TRANSLATIONS["tr"]["backup"] = "Yedek & Geri Yükle"

# Input Lag Reduction section
TRANSLATIONS["en"]["input_lag_title"] = "Input Lag Reduction"
TRANSLATIONS["tr"]["input_lag_title"] = "Input Lag Azaltma"
TRANSLATIONS["en"]["input_lag_desc"] = "Advanced tweaks for competitive gaming - minimize mouse and keyboard delay"
TRANSLATIONS["tr"]["input_lag_desc"] = "Rekabetçi oyunlar için gelişmiş ayarlar - fare ve klavye gecikmesini minimize et"
TRANSLATIONS["en"]["apply_input_lag"] = "Apply Input Lag Tweaks"
TRANSLATIONS["tr"]["apply_input_lag"] = "Input Lag Ayarlarını Uygula"

# In-Game Performance section
TRANSLATIONS["en"]["ingame_title"] = "In-Game Performance"
TRANSLATIONS["tr"]["ingame_title"] = "Oyun İçi Performans"
TRANSLATIONS["en"]["ingame_desc"] = "Maximize resources while gaming"
TRANSLATIONS["tr"]["ingame_desc"] = "Oyun sırasında kaynakları maksimize et"
TRANSLATIONS["en"]["apply_ingame"] = "Apply In-Game Tweaks"
TRANSLATIONS["tr"]["apply_ingame"] = "Oyun İçi Ayarları Uygula"
TRANSLATIONS["en"]["risk_high"] = "High Risk"
TRANSLATIONS["tr"]["risk_high"] = "Yüksek Risk"

# Game Profiles
TRANSLATIONS["en"]["game_profiles"] = "Game Profiles"
TRANSLATIONS["tr"]["game_profiles"] = "Oyun Profilleri"

# Benchmark
TRANSLATIONS["en"]["benchmark"] = "Benchmark"
TRANSLATIONS["tr"]["benchmark"] = "Benchmark"

# Auto Game Mode
TRANSLATIONS["en"]["auto_game_mode"] = "Auto Game Mode"
TRANSLATIONS["tr"]["auto_game_mode"] = "Otomatik Oyun Modu"
TRANSLATIONS["en"]["auto_game_mode_desc"] = "Automatically apply tweaks when a game is detected"
TRANSLATIONS["tr"]["auto_game_mode_desc"] = "Oyun algılandığında ayarları otomatik uygula"

# RAM auto clean
TRANSLATIONS["en"]["ram_auto_clean"] = "Auto RAM Clean"
TRANSLATIONS["tr"]["ram_auto_clean"] = "Otomatik RAM Temizleme"
