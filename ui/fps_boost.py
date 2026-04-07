"""
SRK Boost - FPS Boost Page
Selectable tweaks with tooltips and confirmation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QCheckBox, QGridLayout, QProgressBar,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import logging
from core.i18n import tr
from ui.confirm_dialog import ConfirmDialog

logger = logging.getLogger(__name__)

TWEAKS = [
    {
        "key": "power",
        "name_key": "tweak_power",
        "desc_key": "tweak_power_desc",
        "risk": "low",
        "tooltip": "Changes Windows power plan to High Performance.\n\nEffect: CPU runs at maximum speed without throttling.\nRevert: Automatically restored when you use Restore feature.\nRisk: Slightly higher power consumption.",
        "tooltip_tr": "Windows güç planını Yüksek Performans olarak değiştirir.\n\nEtki: CPU kısıtlama olmadan maksimum hızda çalışır.\nGeri alma: Geri Yükle özelliğiyle otomatik geri alınır.\nRisk: Biraz daha yüksek güç tüketimi.",
    },
    {
        "key": "gamebar",
        "name_key": "tweak_gamebar",
        "desc_key": "tweak_gamebar_desc",
        "risk": "low",
        "tooltip": "Disables Xbox Game Bar via registry.\n\nEffect: Frees CPU/GPU resources used by Game Bar overlay.\nRevert: Re-enabled by Restore feature.\nRisk: Cannot use Win+G shortcut.",
        "tooltip_tr": "Xbox Game Bar'ı kayıt defteri üzerinden devre dışı bırakır.\n\nEtki: Game Bar kaplaması tarafından kullanılan CPU/GPU kaynaklarını serbest bırakır.\nGeri alma: Geri Yükle özelliğiyle yeniden etkinleştirilir.\nRisk: Win+G kısayolunu kullanamazsınız.",
    },
    {
        "key": "sysmain",
        "name_key": "tweak_sysmain",
        "desc_key": "tweak_sysmain_desc",
        "risk": "low",
        "tooltip": "Stops and disables the SysMain (Superfetch) service.\n\nEffect: Reduces disk I/O and memory usage during gaming.\nRevert: Service re-enabled by Restore feature.\nRisk: App launch may be slightly slower on next boot.",
        "tooltip_tr": "SysMain (Superfetch) servisini durdurur ve devre dışı bırakır.\n\nEtki: Oyun sırasında disk G/Ç ve bellek kullanımını azaltır.\nGeri alma: Servis Geri Yükle özelliğiyle yeniden etkinleştirilir.\nRisk: Bir sonraki açılışta uygulamalar biraz daha yavaş başlayabilir.",
    },
    {
        "key": "diagtrack",
        "name_key": "tweak_diagtrack",
        "desc_key": "tweak_diagtrack_desc",
        "risk": "low",
        "tooltip": "Stops the Connected User Experiences and Telemetry service.\n\nEffect: Stops Windows from sending diagnostic data, freeing resources.\nRevert: Re-enabled by Restore feature.\nRisk: Windows telemetry will be disabled.",
        "tooltip_tr": "Bağlı Kullanıcı Deneyimleri ve Telemetri servisini durdurur.\n\nEtki: Windows'un tanılama verisi göndermesini durdurarak kaynakları serbest bırakır.\nGeri alma: Geri Yükle özelliğiyle yeniden etkinleştirilir.\nRisk: Windows telemetrisi devre dışı kalacak.",
    },
    {
        "key": "visual",
        "name_key": "tweak_visual",
        "desc_key": "tweak_visual_desc",
        "risk": "low",
        "tooltip": "Sets Windows visual effects to 'Adjust for best performance'.\n\nEffect: Disables animations, shadows, and transparency.\nRevert: Restored to previous settings by Restore feature.\nRisk: Windows will look more basic/plain.",
        "tooltip_tr": "Windows görsel efektlerini 'En iyi performans için ayarla' olarak ayarlar.\n\nEtki: Animasyonları, gölgeleri ve saydamlığı devre dışı bırakır.\nGeri alma: Geri Yükle özelliğiyle önceki ayarlara geri yüklenir.\nRisk: Windows daha basit görünecek.",
    },
    {
        "key": "memory",
        "name_key": "tweak_memory",
        "desc_key": "tweak_memory_desc",
        "risk": "low",
        "tooltip": "Clears the Windows standby memory list.\n\nEffect: Immediately frees cached memory for active processes.\nRevert: Not needed - memory fills naturally.\nRisk: None - safe operation.",
        "tooltip_tr": "Windows bekleme belleği listesini temizler.\n\nEtki: Önbelleğe alınan belleği aktif işlemler için anında serbest bırakır.\nGeri alma: Gerekli değil - bellek doğal olarak dolar.\nRisk: Yok - güvenli işlem.",
    },
    {
        "key": "gpu",
        "name_key": "tweak_gpu",
        "desc_key": "tweak_gpu_desc",
        "risk": "medium",
        "tooltip": "Sets GPU hardware scheduling preference to High Performance.\n\nEffect: GPU prioritizes performance over power saving.\nRevert: Restored by Restore feature.\nRisk: Higher GPU power consumption and heat.",
        "tooltip_tr": "GPU donanım zamanlama tercihini Yüksek Performans olarak ayarlar.\n\nEtki: GPU güç tasarrufundan performansı önceliklendirir.\nGeri alma: Geri Yükle özelliğiyle geri alınır.\nRisk: Daha yüksek GPU güç tüketimi ve ısı.",
    },
    {
        "key": "search",
        "name_key": "tweak_search",
        "desc_key": "tweak_search_desc",
        "risk": "medium",
        "tooltip": "Disables the Windows Search indexing service.\n\nEffect: Reduces background disk usage during gaming.\nRevert: Re-enabled by Restore feature.\nRisk: Windows Search may be slower until re-enabled.",
        "tooltip_tr": "Windows Arama dizinleme servisini devre dışı bırakır.\n\nEtki: Oyun sırasında arka plan disk kullanımını azaltır.\nGeri alma: Geri Yükle özelliğiyle yeniden etkinleştirilir.\nRisk: Yeniden etkinleştirilene kadar Windows Arama daha yavaş olabilir.",
    },
]


INPUT_LAG_TWEAKS = [
    {
        "key": "core_parking",
        "name": "Disable CPU Core Parking",
        "name_tr": "CPU Çekirdek Parkını Devre Dışı Bırak",
        "desc": "Prevents Windows from disabling CPU cores, eliminating micro-stutter",
        "desc_tr": "Windows'un CPU çekirdeklerini devre dışı bırakmasını engeller",
        "risk": "low",
        "tooltip": "CPU Core Parking powers off unused cores to save energy.\nIn gaming this causes micro-stutters when cores 'wake up'.\nDisabling it keeps all cores ready instantly.\n\nEffect: Reduces stutters, lower input lag\nRisk: Slightly higher idle power usage",
        "tooltip_tr": "CPU çekirdek parkı, enerji tasarrufu için kullanılmayan çekirdekleri kapatır.\nOyunlarda bu mikro takılmalara neden olur.\n\nEtki: Takılmalar azalır, input lag düşer\nRisk: Biraz daha yüksek boşta güç tüketimi",
        "func": "disable_cpu_core_parking",
        "restore_func": "restore_cpu_core_parking",
    },
    {
        "key": "dpc_latency",
        "name": "Reduce DPC Latency",
        "name_tr": "DPC Gecikmesini Azalt",
        "desc": "Forces kernel data to stay in RAM, reducing Deferred Procedure Call delays",
        "desc_tr": "Çekirdek verilerini RAM'de tutar, DPC gecikmelerini azaltır",
        "risk": "low",
        "tooltip": "DPC (Deferred Procedure Call) is how Windows handles urgent tasks.\nHigh DPC latency causes audio glitches and input lag.\nThis tweak forces pageable code to stay in physical RAM.\n\nEffect: Lower audio latency, reduced input lag\nRisk: Slightly higher RAM usage",
        "tooltip_tr": "DPC yüksek öncelikli görevleri yönetir.\nYüksek DPC gecikmesi ses sorunlarına ve input laga yol açar.\n\nEtki: Daha düşük input lag\nRisk: Biraz daha yüksek RAM kullanımı",
        "func": "disable_dpc_latency",
        "restore_func": "restore_dpc_latency",
    },
    {
        "key": "network_latency",
        "name": "Optimize Network Latency",
        "name_tr": "Ağ Gecikmesini Optimize Et",
        "desc": "Disable Nagle's algorithm and TCP auto-tuning for lower ping",
        "desc_tr": "Nagle algoritmasını devre dışı bırakır, ping'i düşürür",
        "risk": "low",
        "tooltip": "Nagle's algorithm bundles small TCP packets together.\nIn games this adds 20-50ms of network latency.\nDisabling it sends packets immediately.\n\nAlso sets NetworkThrottlingIndex to max for game traffic priority.\n\nEffect: Lower ping, more consistent network\nRisk: Very slight increase in network overhead",
        "tooltip_tr": "Nagle algoritması küçük TCP paketlerini birleştirir.\nOyunlarda 20-50ms ağ gecikmesi ekler.\n\nEtki: Daha düşük ping\nRisk: Çok az ağ yükü artışı",
        "func": "optimize_network_latency",
        "restore_func": "restore_network_latency",
    },
    {
        "key": "mouse_accel",
        "name": "Disable Mouse Acceleration",
        "name_tr": "Fare Hızlanmasını Devre Dışı Bırak",
        "desc": "Disables 'Enhance Pointer Precision' for consistent, predictable mouse input",
        "desc_tr": "Fare hareketlerini tutarlı ve öngörülebilir yapar",
        "risk": "low",
        "tooltip": "Mouse acceleration changes pointer speed based on how fast you move.\nThis makes aiming inconsistent in FPS games.\nDisabling it gives 1:1 mouse-to-cursor movement.\n\nEffect: More precise aiming, consistent mouse feel\nRisk: Mouse may feel slower initially - adjust DPI if needed",
        "tooltip_tr": "Fare hızlanması hareket hızına göre imleç hızını değiştirir.\nFPS oyunlarında nişan almayı tutarsız yapar.\n\nEtki: Daha hassas nişan alma\nRisk: Fare ilk başta yavaş hissedebilir",
        "func": "disable_mouse_acceleration",
        "restore_func": "restore_mouse_acceleration",
    },
    {
        "key": "mpo",
        "name": "Disable MPO (Multi-Plane Overlay)",
        "name_tr": "MPO'yu Devre Dışı Bırak",
        "desc": "Fixes micro-stutters and black screen issues caused by GPU overlay",
        "desc_tr": "GPU kaplamasından kaynaklanan mikro takılmaları ve siyah ekranı düzeltir",
        "risk": "medium",
        "tooltip": "MPO is a GPU feature that causes micro-stutters and black screen flashes.\nDisabling it is recommended by NVIDIA for competitive gaming.\nThis is a registry tweak that takes effect after restart.\n\nEffect: Eliminates micro-stutters, fixes black screen flashes\nRisk: Requires restart to take effect",
        "tooltip_tr": "MPO mikro takılmalara ve siyah ekran yanıpönmelerine neden olur.\nNVIDIA tarafından rekabetçi oyunlar için devre dışı bırakılması önerilir.\n\nEtki: Mikro takılmalar ortadan kalkar\nRisk: Etkili olması için yeniden başlatma gerekir",
        "func": "disable_mpo",
        "restore_func": "restore_mpo",
    },
    {
        "key": "timer_res",
        "name": "Optimize Timer Resolution",
        "name_tr": "Zamanlayıcı Çözünürlüğünü Optimize Et",
        "desc": "Sets Windows timer to 0.5ms for consistent frame pacing",
        "desc_tr": "Windows zamanlayıcısını 0.5ms'ye ayarlar, tutarlı kare zamanlaması sağlar",
        "risk": "low",
        "tooltip": "Windows default timer resolution is 15.6ms.\nGames benefit from a lower resolution (0.5ms) for consistent frame delivery.\nThis uses bcdedit to enable platform tick.\n\nEffect: More consistent frame pacing, lower frame time variance\nRisk: Very minimal, widely used by competitive gamers",
        "tooltip_tr": "Windows varsayılan zamanlayıcı çözünürlüğü 15.6ms'dir.\nDaha düşük çözünürlük tutarlı kare teslimi sağlar.\n\nEtki: Daha tutarlı kare zamanlaması\nRisk: Çok minimal",
        "func": "set_timer_resolution",
        "restore_func": "restore_timer_resolution",
    },
    {
        "key": "fullscreen_opt",
        "name": "Disable Fullscreen Optimizations",
        "name_tr": "Tam Ekran Optimizasyonlarını Devre Dışı Bırak",
        "desc": "Disables Windows fullscreen optimizations that add latency",
        "desc_tr": "Gecikme ekleyen Windows tam ekran optimizasyonlarını devre dışı bırakır",
        "risk": "low",
        "tooltip": "Windows Fullscreen Optimizations convert exclusive fullscreen to borderless.\nThis adds input lag. Disabling it restores true exclusive fullscreen.\n\nEffect: True exclusive fullscreen = lower input lag\nRisk: Some games may not support exclusive fullscreen",
        "tooltip_tr": "Windows tam ekran optimizasyonları özel tam ekranı kenarlıksız pencereye dönüştürür.\nBu input lag ekler.\n\nEtki: Gerçek özel tam ekran = daha düşük input lag\nRisk: Bazı oyunlar özel tam ekranı desteklemeyebilir",
        "func": "disable_fullscreen_optimizations",
        "restore_func": "restore_fullscreen_optimizations",
    },
]


INGAME_TWEAKS = [
    {
        "key": "win32_priority",
        "name": "Maximize Foreground Priority",
        "name_tr": "Ön Plan Önceliğini Maksimize Et",
        "desc": "Gives the active game 3x more CPU time than background apps",
        "desc_tr": "Aktif oyuna arka plan uygulamalardan 3 kat daha fazla CPU süresi verir",
        "risk": "low",
        "tooltip": "Win32PrioritySeparation controls how Windows distributes CPU time.\nSetting it to 0x26 gives the foreground app (your game) maximum CPU priority.\nThis is the #1 recommended tweak by Blur Busters and competitive gaming communities.\n\nEffect: Game gets 3x more CPU time, smoother gameplay\nRisk: Background apps run slower while gaming (this is intentional)",
        "tooltip_tr": "Win32PrioritySeparation, Windows'un CPU süresini nasıl dağıttığını kontrol eder.\n0x26 değeri oyuna maksimum CPU önceliği verir.\n\nEtki: Oyun 3 kat daha fazla CPU süresi alır\nRisk: Arka plan uygulamalar daha yavaş çalışır (bu kasıtlı)",
        "func": "set_win32_priority_separation",
        "restore_func": "restore_win32_priority_separation",
    },
    {
        "key": "gpu_priority",
        "name": "Maximize GPU Priority",
        "name_tr": "GPU Önceliğini Maksimize Et",
        "desc": "Sets GPU scheduling to highest priority for minimum render latency",
        "desc_tr": "GPU zamanlamasını en yüksek önceliğe ayarlar, render gecikmesini düşürür",
        "risk": "low",
        "tooltip": "Sets Games task's GPU Priority to 8 (max), Priority to 6, Scheduling to High.\nThis tells Windows to immediately process GPU commands from games.\nPopular tweak on Blur Busters forums and competitive gaming subreddits.\n\nEffect: Lower render latency, GPU commands processed faster\nRisk: None - widely used safe tweak",
        "tooltip_tr": "Oyunların GPU Önceliğini 8 (maks), Önceliği 6, Zamanlamayı Yüksek olarak ayarlar.\n\nEtki: Daha düşük render gecikmesi\nRisk: Yok - yaygın kullanılan güvenli tweak",
        "func": "set_gpu_priority",
        "restore_func": "restore_gpu_priority",
    },
    {
        "key": "hags",
        "name": "Enable HAGS",
        "name_tr": "HAGS'yi Etkinleştir",
        "desc": "Hardware Accelerated GPU Scheduling — GPU manages its own memory for lower latency",
        "desc_tr": "GPU kendi belleğini yönetir, CPU overhead'i azaltır",
        "risk": "medium",
        "tooltip": "HAGS lets the GPU manage its own VRAM scheduling instead of the CPU.\nReduces CPU-to-GPU communication overhead.\nRecommended for RTX 30/40 series and RX 6000/7000 series.\nRequires restart to take effect.\n\nEffect: Lower GPU latency, better frame pacing\nRisk: Some older GPUs may have driver issues - requires restart",
        "tooltip_tr": "HAGS, GPU'nun kendi VRAM zamanlamasını yönetmesini sağlar.\nRTX 30/40 ve RX 6000/7000 serisi için önerilir.\n\nEtki: Daha düşük GPU gecikmesi\nRisk: Eski GPU'larda sorun çıkabilir - yeniden başlatma gerekir",
        "func": "enable_hags",
        "restore_func": "restore_hags",
    },
    {
        "key": "cpu_responsiveness",
        "name": "100% CPU for Games",
        "name_tr": "Oyunlar için %100 CPU",
        "desc": "Allocates all multimedia CPU resources to games (default 80%)",
        "desc_tr": "Tüm multimedia CPU kaynaklarını oyunlara ayırır (varsayılan %80)",
        "risk": "low",
        "tooltip": "SystemResponsiveness=0 gives all multimedia processing resources to the foreground app.\nDefault value 20 reserves 20% for background multimedia tasks.\nSetting to 0 gives games 100% of these resources.\n\nEffect: More CPU cycles for game audio and rendering\nRisk: Background media may stutter - fine during gaming",
        "tooltip_tr": "SystemResponsiveness=0, tüm multimedia kaynaklarını ön plan uygulamaya verir.\nVarsayılan 20 değeri %20'yi arka plan için ayırır.\n\nEtki: Oyun ses ve render için daha fazla CPU\nRisk: Arka plan medya takılabilir",
        "func": "set_cpu_responsiveness",
        "restore_func": "restore_cpu_responsiveness",
    },
    {
        "key": "defender_gaming",
        "name": "Pause Defender During Gaming",
        "name_tr": "Oyun Sırasında Defender'ı Duraklat",
        "desc": "Temporarily disables real-time scanning to prevent mid-game CPU spikes",
        "desc_tr": "Oyun ortasında CPU spikelarını önlemek için gerçek zamanlı taramayı duraklatır",
        "risk": "medium",
        "tooltip": "Windows Defender sometimes scans game files in real-time, causing sudden CPU spikes.\nThis temporarily disables real-time scanning during gaming.\nFull protection remains (manual scanning still works).\n\nEffect: Eliminates random CPU spikes from antivirus scanning\nRisk: PC is temporarily less protected - re-enable after gaming",
        "tooltip_tr": "Windows Defender zaman zaman oyun dosyalarını gerçek zamanlı tarar ve CPU spike'larına neden olur.\nBu, gerçek zamanlı taramayı geçici olarak devre dışı bırakır.\n\nEtki: Antivirüs kaynaklı CPU spike'ları ortadan kalkar\nRisk: Oyun sırasında koruma azalır",
        "func": "disable_windows_defender_gaming",
        "restore_func": "restore_windows_defender_gaming",
    },
    {
        "key": "spectre",
        "name": "Disable CPU Security Mitigations",
        "name_tr": "CPU Güvenlik Azaltmalarını Devre Dışı Bırak",
        "desc": "Disables Spectre/Meltdown patches for 5-15% raw CPU performance gain",
        "desc_tr": "Spectre/Meltdown yamalarını devre dışı bırakır, %5-15 CPU performans artışı",
        "risk": "high",
        "tooltip": "Spectre and Meltdown CPU security patches reduce performance by 5-15%.\nDisabling them recovers this performance for gaming.\n\nWARNING: This reduces security against side-channel attacks.\nOnly recommended for dedicated gaming PCs not used for banking/work.\n\nEffect: 5-15% CPU performance increase\nRisk: HIGH - Security vulnerability. Only for dedicated gaming rigs.",
        "tooltip_tr": "Spectre/Meltdown güvenlik yamaları performansı %5-15 düşürür.\nDevre dışı bırakmak bu performansı geri kazandırır.\n\nUYARI: Yan kanal saldırılarına karşı güvenliği azaltır.\n\nEtki: %5-15 CPU performans artışı\nRisk: YÜKSEK - Yalnızca oyun amaçlı PC'ler için",
        "func": "disable_spectre_meltdown",
        "restore_func": "restore_spectre_meltdown",
    },
]


class BoostWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, selected_keys):
        super().__init__()
        self.selected_keys = selected_keys

    def run(self):
        try:
            from core.restore import RestoreManager
            rm = RestoreManager()
            rm.create_restore_point("Before FPS Boost")
            self.progress.emit(10, "Restore point created...")

            import core.optimizer as opt_module
            key_to_func = {
                # FPS Boost tweaks
                "power": getattr(opt_module, "set_high_performance_power_plan", None),
                "gamebar": getattr(opt_module, "disable_game_bar", None),
                "sysmain": getattr(opt_module, "disable_sysmain", None),
                "diagtrack": getattr(opt_module, "disable_diagtrack", None),
                "visual": getattr(opt_module, "optimize_visual_effects", None),
                "memory": getattr(opt_module, "clear_standby_memory", None),
                "gpu": getattr(opt_module, "set_gpu_max_performance", None),
                "search": getattr(opt_module, "disable_search_indexing", None),
                # Input lag tweaks
                "core_parking": getattr(opt_module, "disable_cpu_core_parking", None),
                "dpc_latency": getattr(opt_module, "disable_dpc_latency", None),
                "network_latency": getattr(opt_module, "optimize_network_latency", None),
                "mouse_accel": getattr(opt_module, "disable_mouse_acceleration", None),
                "mpo": getattr(opt_module, "disable_mpo", None),
                "timer_res": getattr(opt_module, "set_timer_resolution", None),
                "fullscreen_opt": getattr(opt_module, "disable_fullscreen_optimizations", None),
                # In-game performance tweaks
                "win32_priority": getattr(opt_module, "set_win32_priority_separation", None),
                "gpu_priority": getattr(opt_module, "set_gpu_priority", None),
                "hags": getattr(opt_module, "enable_hags", None),
                "cpu_responsiveness": getattr(opt_module, "set_cpu_responsiveness", None),
                "defender_gaming": getattr(opt_module, "disable_windows_defender_gaming", None),
                "spectre": getattr(opt_module, "disable_spectre_meltdown", None),
            }

            total = len(self.selected_keys)
            for i, key in enumerate(self.selected_keys):
                pct = 10 + int((i / total) * 85)
                self.progress.emit(pct, f"Applying: {key}...")
                func = key_to_func.get(key)
                if func:
                    func()

            self.progress.emit(100, "Done!")
            self.finished.emit(True, "FPS Boost applied successfully!")
        except Exception as e:
            self.finished.emit(False, str(e))


# Mapping from tweak key to restore function name
KEY_TO_RESTORE = {
    # FPS Boost tweaks
    "power": "restore_power_plan",
    "gamebar": "restore_game_bar",
    "sysmain": "restore_sysmain",
    "diagtrack": "restore_diagtrack",
    "visual": "restore_visual_effects",
    "gpu": "restore_gpu_mode",
    "search": "restore_search_indexing",
    # Input lag tweaks
    "core_parking": "restore_cpu_core_parking",
    "dpc_latency": "restore_dpc_latency",
    "network_latency": "restore_network_latency",
    "mouse_accel": "restore_mouse_acceleration",
    "mpo": "restore_mpo",
    "timer_res": "restore_timer_resolution",
    "fullscreen_opt": "restore_fullscreen_optimizations",
    # In-game performance tweaks
    "win32_priority": "restore_win32_priority_separation",
    "gpu_priority": "restore_gpu_priority",
    "hags": "restore_hags",
    "cpu_responsiveness": "restore_cpu_responsiveness",
    "defender_gaming": "restore_windows_defender_gaming",
    "spectre": "restore_spectre_meltdown",
}


class TweakCard(QFrame):
    restore_requested = pyqtSignal(str)  # emits tweak key

    def __init__(self, tweak: dict, parent=None):
        super().__init__(parent)
        self.tweak = tweak
        self.setObjectName("tweakCard")
        self.setStyleSheet("""
            QFrame#tweakCard {
                background: #12121a;
                border: 1px solid #2a1a4a;
                border-radius: 10px;
                padding: 4px;
            }
            QFrame#tweakCard:hover {
                border-color: #6c63ff;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 24px; height: 24px;
                border-radius: 6px;
                border: 2px solid #6c63ff;
                background: #0a0a0f;
            }
            QCheckBox::indicator:checked {
                background: #6c63ff;
                border: 2px solid #6c63ff;
                image: none;
            }
            QCheckBox::indicator:hover {
                border-color: #00d4ff;
            }
        """)
        layout.addWidget(self.checkbox)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        name_row = QHBoxLayout()
        self.name_lbl = QLabel(tr(tweak["name_key"]))
        self.name_lbl.setStyleSheet("color: #e0e0ff; font-weight: bold; font-size: 13px;")
        name_row.addWidget(self.name_lbl)

        risk = tweak["risk"]
        risk_color = "#00ff88" if risk == "low" else "#ffaa00"
        risk_text = tr("risk_low") if risk == "low" else tr("risk_medium")
        risk_lbl = QLabel(risk_text)
        risk_lbl.setStyleSheet(f"color: {risk_color}; font-size: 11px; padding: 2px 8px; border: 1px solid {risk_color}; border-radius: 8px;")
        name_row.addWidget(risk_lbl)
        name_row.addStretch()
        text_layout.addLayout(name_row)

        self.desc_lbl = QLabel(tr(tweak["desc_key"]))
        self.desc_lbl.setStyleSheet("color: #6060a0; font-size: 12px;")
        self.desc_lbl.setWordWrap(True)
        text_layout.addWidget(self.desc_lbl)

        layout.addLayout(text_layout)

        # "Default" restore button — only show if tweak has a restore function
        key = tweak.get("key", "")
        if key in KEY_TO_RESTORE:
            self.default_btn = QPushButton("↩ Default")
            self.default_btn.setFixedWidth(90)
            self.default_btn.setFixedHeight(28)
            self.default_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #6060a0;
                    border: 1px solid #3a3a5a;
                    border-radius: 6px;
                    font-size: 11px;
                    padding: 2px 6px;
                }
                QPushButton:hover {
                    color: #e0e0ff;
                    border-color: #6c63ff;
                }
                QPushButton:pressed {
                    background: #1e1e2e;
                }
            """)
            self.default_btn.setToolTip(f"Restore this tweak to its default Windows setting")
            self.default_btn.clicked.connect(lambda: self.restore_requested.emit(key))
            layout.addWidget(self.default_btn)
        else:
            self.default_btn = None

        from core.i18n import get_language
        tooltip = tweak["tooltip_tr"] if get_language() == "tr" else tweak["tooltip"]
        self.setToolTip(tooltip)
        self.setCursor(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def get_key(self) -> str:
        return self.tweak["key"]


class InputLagTweakCard(QFrame):
    """TweakCard variant for INPUT_LAG_TWEAKS (uses direct name/desc strings)."""
    restore_requested = pyqtSignal(str)  # emits tweak key

    def __init__(self, tweak: dict, parent=None):
        super().__init__(parent)
        self.tweak = tweak
        self.setObjectName("inputLagCard")
        self.setStyleSheet("""
            QFrame#inputLagCard {
                background: #0f1220;
                border: 1px solid #1a2a4a;
                border-radius: 10px;
                padding: 4px;
            }
            QFrame#inputLagCard:hover {
                border-color: #00d4ff;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 24px; height: 24px;
                border-radius: 6px;
                border: 2px solid #00d4ff;
                background: #0a0a0f;
            }
            QCheckBox::indicator:checked {
                background: #00d4ff;
                border: 2px solid #00d4ff;
                image: none;
            }
            QCheckBox::indicator:hover {
                border-color: #6c63ff;
            }
        """)
        layout.addWidget(self.checkbox)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        name_row = QHBoxLayout()
        from core.i18n import get_language
        lang = get_language()
        display_name = tweak["name_tr"] if lang == "tr" else tweak["name"]
        self.name_lbl = QLabel(display_name)
        self.name_lbl.setStyleSheet("color: #e0e0ff; font-weight: bold; font-size: 13px;")
        name_row.addWidget(self.name_lbl)

        risk = tweak["risk"]
        risk_color = "#00d4ff" if risk == "low" else "#ffaa00"
        risk_text = tr("risk_low") if risk == "low" else tr("risk_medium")
        risk_lbl = QLabel(risk_text)
        risk_lbl.setStyleSheet(f"color: {risk_color}; font-size: 11px; padding: 2px 8px; border: 1px solid {risk_color}; border-radius: 8px;")
        name_row.addWidget(risk_lbl)
        name_row.addStretch()
        text_layout.addLayout(name_row)

        display_desc = tweak["desc_tr"] if lang == "tr" else tweak["desc"]
        self.desc_lbl = QLabel(display_desc)
        self.desc_lbl.setStyleSheet("color: #506080; font-size: 12px;")
        self.desc_lbl.setWordWrap(True)
        text_layout.addWidget(self.desc_lbl)

        layout.addLayout(text_layout)

        key = tweak.get("key", "")
        if key in KEY_TO_RESTORE:
            self.default_btn = QPushButton("↩ Default")
            self.default_btn.setFixedWidth(90)
            self.default_btn.setFixedHeight(28)
            self.default_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #506080;
                    border: 1px solid #1a3a5a;
                    border-radius: 6px;
                    font-size: 11px;
                    padding: 2px 6px;
                }
                QPushButton:hover {
                    color: #e0e0ff;
                    border-color: #00d4ff;
                }
                QPushButton:pressed {
                    background: #0e1e2e;
                }
            """)
            self.default_btn.setToolTip(f"Restore this tweak to its default Windows setting")
            self.default_btn.clicked.connect(lambda: self.restore_requested.emit(key))
            layout.addWidget(self.default_btn)
        else:
            self.default_btn = None

        tooltip = tweak["tooltip_tr"] if lang == "tr" else tweak["tooltip"]
        self.setToolTip(tooltip)
        self.setCursor(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def get_key(self) -> str:
        return self.tweak["key"]


class InGameTweakCard(QFrame):
    """TweakCard variant for INGAME_TWEAKS (orange accent, supports high risk badge)."""
    restore_requested = pyqtSignal(str)

    def __init__(self, tweak: dict, parent=None):
        super().__init__(parent)
        self.tweak = tweak
        self.setObjectName("inGameCard")
        self.setStyleSheet("""
            QFrame#inGameCard {
                background: #120f0a;
                border: 1px solid #3a2010;
                border-radius: 10px;
                padding: 4px;
            }
            QFrame#inGameCard:hover {
                border-color: #f97316;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 24px; height: 24px;
                border-radius: 6px;
                border: 2px solid #f97316;
                background: #0a0a0f;
            }
            QCheckBox::indicator:checked {
                background: #f97316;
                border: 2px solid #f97316;
                image: none;
            }
            QCheckBox::indicator:hover {
                border-color: #fb923c;
            }
        """)
        layout.addWidget(self.checkbox)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        name_row = QHBoxLayout()
        from core.i18n import get_language
        lang = get_language()
        display_name = tweak["name_tr"] if lang == "tr" else tweak["name"]
        self.name_lbl = QLabel(display_name)
        self.name_lbl.setStyleSheet("color: #ffe0c0; font-weight: bold; font-size: 13px;")
        name_row.addWidget(self.name_lbl)

        risk = tweak["risk"]
        if risk == "low":
            risk_color = "#f97316"
            risk_text = tr("risk_low")
        elif risk == "medium":
            risk_color = "#ffaa00"
            risk_text = tr("risk_medium")
        else:  # high
            risk_color = "#ff4444"
            risk_text = tr("risk_high")
        risk_lbl = QLabel(risk_text)
        risk_lbl.setStyleSheet(f"color: {risk_color}; font-size: 11px; padding: 2px 8px; border: 1px solid {risk_color}; border-radius: 8px;")
        name_row.addWidget(risk_lbl)
        name_row.addStretch()
        text_layout.addLayout(name_row)

        display_desc = tweak["desc_tr"] if lang == "tr" else tweak["desc"]
        self.desc_lbl = QLabel(display_desc)
        self.desc_lbl.setStyleSheet("color: #806040; font-size: 12px;")
        self.desc_lbl.setWordWrap(True)
        text_layout.addWidget(self.desc_lbl)

        layout.addLayout(text_layout)

        key = tweak.get("key", "")
        if key in KEY_TO_RESTORE:
            self.default_btn = QPushButton("↩ Default")
            self.default_btn.setFixedWidth(90)
            self.default_btn.setFixedHeight(28)
            self.default_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #806040;
                    border: 1px solid #3a2010;
                    border-radius: 6px;
                    font-size: 11px;
                    padding: 2px 6px;
                }
                QPushButton:hover {
                    color: #ffe0c0;
                    border-color: #f97316;
                }
                QPushButton:pressed {
                    background: #1e1008;
                }
            """)
            self.default_btn.setToolTip("Restore this tweak to its default Windows setting")
            self.default_btn.clicked.connect(lambda: self.restore_requested.emit(key))
            layout.addWidget(self.default_btn)
        else:
            self.default_btn = None

        tooltip = tweak["tooltip_tr"] if lang == "tr" else tweak["tooltip"]
        self.setToolTip(tooltip)
        self.setCursor(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def get_key(self) -> str:
        return self.tweak["key"]


class FpsBoostPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._build_ui()

    def _make_collapsible_section(self, title: str, subtitle: str, accent: str, expanded: bool = True) -> dict:
        """Creates a collapsible section frame. Returns {frame, body (QVBoxLayout)}."""
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet(f"""
            QFrame#card {{
                background: rgba(12,10,22,0.95);
                border: 1px solid {accent}22;
                border-radius: 14px;
            }}
        """)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Toggle header
        header_btn = QPushButton()
        header_btn.setCheckable(True)
        header_btn.setChecked(expanded)
        header_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent}12;
                border: none;
                border-radius: 14px;
                padding: 14px 20px;
                text-align: left;
            }}
            QPushButton:hover {{ background: {accent}1e; }}
            QPushButton:checked {{ border-radius: 14px 14px 0 0; }}
        """)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(12)

        arrow_lbl = QLabel("▼" if expanded else "▶")
        arrow_lbl.setStyleSheet(f"color: {accent}; font-size: 11px; background: transparent; min-width: 16px;")
        h_layout.addWidget(arrow_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {accent}; font-size: 16px; font-weight: 900; background: transparent;")
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("color: rgba(160,150,220,0.45); font-size: 11px; background: transparent;")
        text_col.addWidget(title_lbl)
        text_col.addWidget(sub_lbl)
        h_layout.addLayout(text_col)
        h_layout.addStretch()

        header_btn.setLayout(h_layout)
        outer.addWidget(header_btn)

        # Body container
        body_container = QWidget()
        body_container.setVisible(expanded)
        body_container.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body_container)
        body_layout.setContentsMargins(20, 12, 20, 16)
        body_layout.setSpacing(8)
        outer.addWidget(body_container)

        def _toggle(checked):
            body_container.setVisible(checked)
            arrow_lbl.setText("▼" if checked else "▶")

        header_btn.toggled.connect(_toggle)
        return {"frame": frame, "body": body_layout}

    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Wrap everything in a scroll area for small screen support
        outer_scroll = QScrollArea()
        outer_scroll.setWidgetResizable(True)
        outer_scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(outer_scroll)

        outer_container = QWidget()
        outer_scroll.setWidget(outer_container)
        main_layout = QVBoxLayout(outer_container)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel(tr("fps_boost_title"))
        title.setStyleSheet("color: #e0e0ff; font-size: 22px; font-weight: 900;")
        header.addWidget(title)
        header.addStretch()

        self.select_all_btn = QPushButton("☑  Select All")
        self.select_all_btn.setStyleSheet("background: rgba(108,99,255,0.12); color: #8b83ff; border: 1px solid rgba(108,99,255,0.35); border-radius: 8px; padding: 6px 14px; font-weight: 600;")
        self.select_all_btn.clicked.connect(self._select_all)
        header.addWidget(self.select_all_btn)

        self.deselect_btn = QPushButton("☐  Deselect All")
        self.deselect_btn.setStyleSheet("background: rgba(60,55,100,0.12); color: #6060a0; border: 1px solid rgba(60,55,100,0.3); border-radius: 8px; padding: 6px 14px; font-weight: 600;")
        self.deselect_btn.clicked.connect(self._deselect_all)
        header.addWidget(self.deselect_btn)
        main_layout.addLayout(header)

        desc = QLabel(tr("fps_boost_desc"))
        desc.setStyleSheet("color: #6060a0; font-size: 13px;")
        main_layout.addWidget(desc)

        # Tweaks list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        self.tweaks_layout = QVBoxLayout(scroll_widget)
        self.tweaks_layout.setSpacing(8)
        self.tweaks_layout.setContentsMargins(0, 0, 0, 0)

        self.tweak_cards = []
        for tweak in TWEAKS:
            card = TweakCard(tweak)
            card.restore_requested.connect(self._restore_single_tweak)
            self.tweaks_layout.addWidget(card)
            self.tweak_cards.append(card)

        self.tweaks_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # --- Input Lag Reduction Section (Collapsible) ---
        il_section = self._make_collapsible_section(
            title=tr("input_lag_title"),
            subtitle=tr("input_lag_desc"),
            accent="#00d4ff",
            expanded=False,
        )
        il_body = il_section["body"]
        main_layout.addWidget(il_section["frame"])

        il_sel_row = QHBoxLayout()
        self.il_select_all_btn = QPushButton("☑  Select All")
        self.il_select_all_btn.setStyleSheet("background: rgba(0,212,255,0.1); color: #00d4ff; border: 1px solid rgba(0,212,255,0.3); border-radius: 7px; padding: 5px 12px; font-size: 11px; font-weight: 600;")
        self.il_select_all_btn.clicked.connect(self._il_select_all)
        self.il_deselect_btn = QPushButton("☐  Deselect All")
        self.il_deselect_btn.setStyleSheet("background: rgba(0,150,180,0.08); color: #506080; border: 1px solid rgba(0,150,180,0.2); border-radius: 7px; padding: 5px 12px; font-size: 11px; font-weight: 600;")
        self.il_deselect_btn.clicked.connect(self._il_deselect_all)
        il_sel_row.addStretch()
        il_sel_row.addWidget(self.il_select_all_btn)
        il_sel_row.addWidget(self.il_deselect_btn)
        il_body.addLayout(il_sel_row)

        self.il_tweak_cards = []
        for tweak in INPUT_LAG_TWEAKS:
            card = InputLagTweakCard(tweak)
            card.restore_requested.connect(self._restore_single_tweak)
            il_body.addWidget(card)
            self.il_tweak_cards.append(card)

        il_btn_row = QHBoxLayout()
        il_btn_row.addStretch()
        self.apply_il_btn = QPushButton(tr("apply_input_lag"))
        self.apply_il_btn.setObjectName("cyan_btn")
        self.apply_il_btn.setFixedHeight(42)
        self.apply_il_btn.clicked.connect(self._confirm_and_boost_il)
        il_btn_row.addWidget(self.apply_il_btn)
        il_body.addLayout(il_btn_row)

        # --- In-Game Performance Section (Collapsible) ---
        ig_section = self._make_collapsible_section(
            title=tr("ingame_title"),
            subtitle=tr("ingame_desc"),
            accent="#f97316",
            expanded=False,
        )
        ig_body = ig_section["body"]
        main_layout.addWidget(ig_section["frame"])

        ig_sel_row = QHBoxLayout()
        self.ig_select_all_btn = QPushButton("☑  Select All")
        self.ig_select_all_btn.setStyleSheet("background: rgba(249,115,22,0.1); color: #f97316; border: 1px solid rgba(249,115,22,0.3); border-radius: 7px; padding: 5px 12px; font-size: 11px; font-weight: 600;")
        self.ig_select_all_btn.clicked.connect(self._ig_select_all)
        self.ig_deselect_btn = QPushButton("☐  Deselect All")
        self.ig_deselect_btn.setStyleSheet("background: rgba(180,80,0,0.08); color: #806040; border: 1px solid rgba(180,80,0,0.2); border-radius: 7px; padding: 5px 12px; font-size: 11px; font-weight: 600;")
        self.ig_deselect_btn.clicked.connect(self._ig_deselect_all)
        ig_sel_row.addStretch()
        ig_sel_row.addWidget(self.ig_select_all_btn)
        ig_sel_row.addWidget(self.ig_deselect_btn)
        ig_body.addLayout(ig_sel_row)

        self.ig_tweak_cards = []
        for tweak in INGAME_TWEAKS:
            card = InGameTweakCard(tweak)
            card.restore_requested.connect(self._restore_single_tweak)
            ig_body.addWidget(card)
            self.ig_tweak_cards.append(card)

        ig_btn_row2 = QHBoxLayout()
        ig_btn_row2.addStretch()
        self.apply_ig_btn = QPushButton(tr("apply_ingame"))
        self.apply_ig_btn.setObjectName("orange_btn")
        self.apply_ig_btn.setFixedHeight(42)
        self.apply_ig_btn.clicked.connect(self._confirm_and_boost_ig)
        ig_btn_row2.addWidget(self.apply_ig_btn)
        ig_body.addLayout(ig_btn_row2)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: #1e1e2e; border-radius: 6px; height: 8px; text-align: center; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6c63ff, stop:1 #00d4ff); border-radius: 6px; }
        """)
        main_layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #6060a0; font-size: 12px;")
        self.status_lbl.setVisible(False)
        main_layout.addWidget(self.status_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        self.restore_btn = QPushButton(tr("restore"))
        self.restore_btn.setStyleSheet("background: #1e1e2e; color: #6060a0; border: 1px solid #2a2a3e; border-radius: 8px; padding: 10px 24px; font-size: 13px;")
        self.restore_btn.clicked.connect(self._restore)
        btn_row.addWidget(self.restore_btn)
        btn_row.addStretch()

        self.apply_btn = QPushButton(tr("apply_selected"))
        self.apply_btn.setObjectName("boost_btn")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6c63ff, stop:1 #8b5cf6);
                color: white; border: none; border-radius: 10px;
                padding: 12px 36px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c73ff, stop:1 #9b6cf6);
            }
            QPushButton:disabled { background: #2a2a3e; color: #6060a0; }
        """)
        self.apply_btn.clicked.connect(self._confirm_and_boost)
        btn_row.addWidget(self.apply_btn)
        main_layout.addLayout(btn_row)

    def _select_all(self):
        for card in self.tweak_cards:
            card.checkbox.setChecked(True)

    def _deselect_all(self):
        for card in self.tweak_cards:
            card.checkbox.setChecked(False)

    def _il_select_all(self):
        for card in self.il_tweak_cards:
            card.checkbox.setChecked(True)

    def _il_deselect_all(self):
        for card in self.il_tweak_cards:
            card.checkbox.setChecked(False)

    def _ig_select_all(self):
        for card in self.ig_tweak_cards:
            card.checkbox.setChecked(True)

    def _ig_deselect_all(self):
        for card in self.ig_tweak_cards:
            card.checkbox.setChecked(False)

    def _confirm_and_boost_ig(self):
        selected = [c for c in self.ig_tweak_cards if c.is_checked()]
        if not selected:
            return

        from core.i18n import get_language
        lang = get_language()
        actions = []
        for c in selected:
            tweak = next(t for t in INGAME_TWEAKS if t["key"] == c.get_key())
            actions.append(tweak["name_tr"] if lang == "tr" else tweak["name"])

        dlg = ConfirmDialog(
            title=tr("ingame_title"),
            description=tr("ingame_desc"),
            actions=actions,
            show_restore_note=True,
            parent=self
        )
        if dlg.exec():
            self._run_boost([c.get_key() for c in selected])

    def _confirm_and_boost_il(self):
        selected = [c for c in self.il_tweak_cards if c.is_checked()]
        if not selected:
            return

        from core.i18n import get_language
        lang = get_language()
        actions = []
        for c in selected:
            tweak = next(t for t in INPUT_LAG_TWEAKS if t["key"] == c.get_key())
            actions.append(tweak["name_tr"] if lang == "tr" else tweak["name"])

        dlg = ConfirmDialog(
            title=tr("input_lag_title"),
            description=tr("input_lag_desc"),
            actions=actions,
            show_restore_note=True,
            parent=self
        )
        if dlg.exec():
            self._run_boost([c.get_key() for c in selected])

    def _confirm_and_boost(self):
        selected = [c for c in self.tweak_cards if c.is_checked()]
        if not selected:
            return

        actions = [tr(TWEAKS[[t["key"] for t in TWEAKS].index(c.get_key())]["name_key"]) for c in selected]

        dlg = ConfirmDialog(
            title=tr("fps_boost_title"),
            description=tr("fps_boost_desc"),
            actions=actions,
            show_restore_note=True,
            parent=self
        )
        if dlg.exec():
            self._run_boost([c.get_key() for c in selected])

    def _run_boost(self, keys):
        self.apply_btn.setEnabled(False)
        self.apply_il_btn.setEnabled(False)
        self.apply_ig_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_lbl.setVisible(True)

        self._worker = BoostWorker(keys)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, value, msg):
        self.progress_bar.setValue(value)
        self.status_lbl.setText(msg)

    def _on_finished(self, success, msg):
        self.apply_btn.setEnabled(True)
        self.apply_il_btn.setEnabled(True)
        self.apply_ig_btn.setEnabled(True)
        if success:
            self.status_lbl.setText(tr("done") + " - " + msg)
            self.status_lbl.setStyleSheet("color: #00ff88; font-size: 12px;")
        else:
            self.status_lbl.setText(tr("error") + ": " + msg)
            self.status_lbl.setStyleSheet("color: #ff4444; font-size: 12px;")

    def _restore(self):
        try:
            from core.restore import RestoreManager
            rm = RestoreManager()
            rm.restore_latest()
            self.status_lbl.setText("Restored successfully!")
            self.status_lbl.setStyleSheet("color: #00ff88; font-size: 12px;")
            self.status_lbl.setVisible(True)
        except Exception as e:
            self.status_lbl.setText(f"Restore failed: {e}")
            self.status_lbl.setStyleSheet("color: #ff4444; font-size: 12px;")
            self.status_lbl.setVisible(True)

    def _restore_single_tweak(self, key: str):
        """Restore a single tweak to its default Windows setting."""
        restore_func_name = KEY_TO_RESTORE.get(key)
        if not restore_func_name:
            return
        try:
            import core.optimizer as opt_module
            fn = getattr(opt_module, restore_func_name, None)
            if fn is None:
                raise AttributeError(f"No restore function: {restore_func_name}")
            ok, msg = fn()
            self.status_lbl.setVisible(True)
            if ok:
                self.status_lbl.setText(f"✓ {key.title()} restored: {msg}")
                self.status_lbl.setStyleSheet("color: #00ff88; font-size: 12px;")
            else:
                self.status_lbl.setText(f"⚠ {key.title()} restore: {msg}")
                self.status_lbl.setStyleSheet("color: #ffaa00; font-size: 12px;")
        except Exception as e:
            self.status_lbl.setText(f"Restore failed: {e}")
            self.status_lbl.setStyleSheet("color: #ff4444; font-size: 12px;")
            self.status_lbl.setVisible(True)
