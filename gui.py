import sys
import os
import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QSystemTrayIcon,
    QMenu, QMessageBox, QFrame, QScrollArea, QTabWidget, QLineEdit,
    QRadioButton, QButtonGroup, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QColor, QAction, QPixmap, QPainter, QBrush, QPen

from presets_data import PRESETS
from engine import ZapretEngine, is_admin, restart_as_admin, LISTS_DIR
from tester import StrategyTester, TargetResult, PresetBenchmarkResult

# Modern GitHub / Windows 11 Dark QSS Theme
DARK_STYLESHEET = """
QMainWindow {
    background-color: #0d1117;
}
QWidget {
    color: #e6edf3;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #30363d;
    background-color: #161b22;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #0d1117;
    border: 1px solid #30363d;
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #8b949e;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #161b22;
    color: #58a6ff;
    border-bottom: 2px solid #1f6feb;
}
QTabBar::tab:hover:!selected {
    background: #21262d;
    color: #c9d1d9;
}
QFrame.card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px;
}
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    color: #c9d1d9;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}
QPushButton:pressed {
    background-color: #161b22;
}
QPushButton.primary {
    background-color: #238636;
    border: 1px solid #2ea043;
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
    padding: 12px 24px;
}
QPushButton.primary:hover {
    background-color: #2ea043;
}
QPushButton.danger {
    background-color: #da3633;
    border: 1px solid #f85149;
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
    padding: 12px 24px;
}
QPushButton.danger:hover {
    background-color: #b62324;
}
QPushButton.accent {
    background-color: #1f6feb;
    border: 1px solid #388bfd;
    color: #ffffff;
}
QPushButton.accent:hover {
    background-color: #388bfd;
}
QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #e6edf3;
    min-height: 24px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
    color: #e6edf3;
}
QTextEdit, QLineEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px;
    color: #e6edf3;
    selection-background-color: #1f6feb;
}
QTextEdit:focus, QLineEdit:focus, QComboBox:focus {
    border: 1px solid #58a6ff;
}
QProgressBar {
    border: 1px solid #30363d;
    border-radius: 6px;
    text-align: center;
    background-color: #0d1117;
    color: #ffffff;
    font-weight: bold;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #238636;
    border-radius: 5px;
}
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    gridline-color: #21262d;
    color: #e6edf3;
}
QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 6px;
    border: 1px solid #30363d;
    font-weight: bold;
}
QScrollBar:vertical {
    border: none;
    background: #0d1117;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #8b949e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

def create_app_icon(color="#238636"):
    """Creates a high-DPI in-memory icon with a shield & zap symbol."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Circle background
    painter.setBrush(QBrush(QColor(color)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 16, 16)

    # Draw Zap / Lightning bolt in white
    painter.setBrush(QBrush(QColor("#ffffff")))
    from PyQt6.QtGui import QPolygon
    from PyQt6.QtCore import QPoint
    points = QPolygon([
        QPoint(34, 12),
        QPoint(18, 34),
        QPoint(31, 34),
        QPoint(27, 52),
        QPoint(46, 28),
        QPoint(33, 28),
    ])
    painter.drawPolygon(points)
    painter.end()
    return QIcon(pixmap)

# ----------------------------------------------------
# Background Threads for Async Testing
# ----------------------------------------------------
class QuickTestThread(QThread):
    finished_signal = pyqtSignal(list)

    def __init__(self, tester: StrategyTester):
        super().__init__()
        self.tester = tester

    def run(self):
        results = self.tester.test_current_connection()
        self.finished_signal.emit(results)

class BenchmarkThread(QThread):
    progress_signal = pyqtSignal(int, int, str, object)
    completed_signal = pyqtSignal(list)

    def __init__(self, tester: StrategyTester, preset_ids: list[str]):
        super().__init__()
        self.tester = tester
        self.preset_ids = preset_ids

    def run(self):
        def on_prog(current, total, title, res):
            self.progress_signal.emit(current, total, title, res)

        results = self.tester.benchmark_presets(self.preset_ids, progress_callback=on_prog)
        self.completed_signal.emit(results)

# ----------------------------------------------------
# Main Application Window
# ----------------------------------------------------
class ZapretControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = ZapretEngine(log_callback=self.on_log_message)
        self.tester = StrategyTester(self.engine)
        self.active_benchmark_thread = None
        self.active_test_thread = None

        self.setWindowTitle("Zapret Control Ultimate · DPI Bypass Suite")
        self.resize(980, 720)
        self.setMinimumSize(850, 600)
        self.setWindowIcon(create_app_icon("#8957e5"))

        # Setup System Tray
        self.init_tray()

        # Build UI
        self.init_ui()

        # Status Update Timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start(1500)

        # Refresh initial status
        self.refresh_status()

    def init_tray(self):
        self.tray = QSystemTrayIcon(create_app_icon("#8957e5"), self)
        tray_menu = QMenu()

        self.action_toggle = QAction("Запустить", self)
        self.action_toggle.triggered.connect(self.toggle_process)
        tray_menu.addAction(self.action_toggle)

        tray_menu.addSeparator()
        action_show = QAction("Открыть главное окно", self)
        action_show.triggered.connect(self.show_window)
        tray_menu.addAction(action_show)

        action_quit = QAction("Выход", self)
        action_quit.triggered.connect(self.quit_app)
        tray_menu.addAction(action_quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self.engine.stop_process()
        QApplication.quit()

    def closeEvent(self, event):
        if self.engine.config.get("minimize_to_tray", True):
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "Zapret Control",
                "Приложение работает в фоновом режиме. Кликните для открытия.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self.engine.stop_process()
            event.accept()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Banner
        header = self.create_header()
        main_layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_dashboard_tab(), "Панель управления")
        self.tabs.addTab(self.create_presets_tab(), "Пресеты (22 стратегии)")
        self.tabs.addTab(self.create_benchmark_tab(), "Авто-подбор стратегии")
        self.tabs.addTab(self.create_lists_tab(), "Списки сайтов")
        self.tabs.addTab(self.create_logs_tab(), "Журнал и диагностика")

        main_layout.addWidget(self.tabs)

    # ----------------------------------------------------
    # Header Widget
    # ----------------------------------------------------
    def create_header(self) -> QWidget:
        header = QFrame()
        header.setProperty("class", "card")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)

        # App Info
        info_layout = QVBoxLayout()
        title_label = QLabel("⚡ ZAPRET CONTROL ULTIMATE")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #58a6ff;")

        self.lbl_subtitle = QLabel("Автоматический обход DPI · YouTube 4K, Discord RTC & Voice")
        self.lbl_subtitle.setStyleSheet("color: #8b949e;")

        info_layout.addWidget(title_label)
        info_layout.addWidget(self.lbl_subtitle)
        layout.addLayout(info_layout)

        layout.addStretch()

        # Admin status badge
        admin_state = is_admin()
        lbl_admin = QLabel("🛡 РЕЖИМ АДМИНИСТРАТОРА" if admin_state else "⚠ НЕТ ПРАВ АДМИНИСТРАТОРА")
        lbl_admin.setStyleSheet(
            "background-color: #238636; color: #fff; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 11px;"
            if admin_state else
            "background-color: #da3633; color: #fff; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 11px;"
        )
        layout.addWidget(lbl_admin)

        if not admin_state:
            btn_restart_admin = QPushButton("Перезапустить с правами")
            btn_restart_admin.setStyleSheet("background-color: #da3633; color: white;")
            btn_restart_admin.clicked.connect(restart_as_admin)
            layout.addWidget(btn_restart_admin)

        return header

    # ----------------------------------------------------
    # TAB 1: Dashboard
    # ----------------------------------------------------
    def create_dashboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Big Status & Master Action Card
        status_card = QFrame()
        status_card.setProperty("class", "card")
        sc_layout = QVBoxLayout(status_card)

        top_row = QHBoxLayout()
        self.lbl_status_icon = QLabel("🔴")
        self.lbl_status_icon.setFont(QFont("Segoe UI", 24))

        status_text_layout = QVBoxLayout()
        self.lbl_status_title = QLabel("ЗАЩИТА ОСТАНОВЛЕНА")
        self.lbl_status_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_status_title.setStyleSheet("color: #da3633;")

        self.lbl_status_detail = QLabel("Нажмите «Запустить», чтобы активировать обход DPI для вашего провайдера.")
        self.lbl_status_detail.setStyleSheet("color: #8b949e;")

        status_text_layout.addWidget(self.lbl_status_title)
        status_text_layout.addWidget(self.lbl_status_detail)

        top_row.addWidget(self.lbl_status_icon)
        top_row.addLayout(status_text_layout)
        top_row.addStretch()

        # Big Toggle Button
        self.btn_master_toggle = QPushButton("ЗАПУСТИТЬ ЗАЩИТУ")
        self.btn_master_toggle.setProperty("class", "primary")
        self.btn_master_toggle.setMinimumWidth(220)
        self.btn_master_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_master_toggle.clicked.connect(self.toggle_process)
        top_row.addWidget(self.btn_master_toggle)

        sc_layout.addLayout(top_row)
        layout.addWidget(status_card)

        # Active Preset & Quick Switcher Card
        preset_card = QFrame()
        preset_card.setProperty("class", "card")
        pc_layout = QVBoxLayout(preset_card)

        pc_title = QLabel("АКТИВНЫЙ ПРЕСЕТ ОБХОДА")
        pc_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        pc_title.setStyleSheet("color: #8b949e;")
        pc_layout.addWidget(pc_title)

        combo_row = QHBoxLayout()
        self.combo_dashboard_preset = QComboBox()
        for pid, pdata in PRESETS.items():
            self.combo_dashboard_preset.addItem(f"{pdata['title']} — {pdata['description'][:60]}...", pid)
        self.combo_dashboard_preset.addItem("Custom — Пользовательские аргументы", "custom")

        # Select saved preset
        curr_preset = self.engine.config.get("active_preset", "general")
        idx = self.combo_dashboard_preset.findData(curr_preset)
        if idx >= 0:
            self.combo_dashboard_preset.setCurrentIndex(idx)
        self.combo_dashboard_preset.currentIndexChanged.connect(self.on_dashboard_preset_changed)

        combo_row.addWidget(self.combo_dashboard_preset, stretch=3)

        btn_benchmark_shortcut = QPushButton("⚡ Подобрать лучший")
        btn_benchmark_shortcut.setProperty("class", "accent")
        btn_benchmark_shortcut.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        combo_row.addWidget(btn_benchmark_shortcut, stretch=1)

        pc_layout.addLayout(combo_row)

        self.lbl_preset_explanation = QLabel()
        self.lbl_preset_explanation.setStyleSheet("color: #58a6ff; font-size: 12px; margin-top: 4px;")
        self.update_preset_explanation(curr_preset)
        pc_layout.addWidget(self.lbl_preset_explanation)

        layout.addWidget(preset_card)

        # Options & Mode Card (Game Filter, Windows Service)
        options_card = QFrame()
        options_card.setProperty("class", "card")
        oc_layout = QVBoxLayout(options_card)

        oc_title = QLabel("РЕЖИМЫ И ОПТИМИЗАЦИИ")
        oc_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        oc_title.setStyleSheet("color: #8b949e;")
        oc_layout.addWidget(oc_title)

        opt_grid = QHBoxLayout()

        # Game Filter Switch
        gf_box = QVBoxLayout()
        lbl_gf = QLabel("Игровой фильтр (Discord Voice & Игры):")
        lbl_gf.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.combo_game_filter = QComboBox()
        self.combo_game_filter.addItem("Выключен (порты 80, 443)", "disabled")
        self.combo_game_filter.addItem("Включен (TCP + UDP 1024-65535)", "both")
        self.combo_game_filter.addItem("Только UDP (Discord Voice / STUN)", "udp")
        self.combo_game_filter.addItem("Только TCP", "tcp")

        curr_gf = self.engine.config.get("game_filter", "disabled")
        idx_gf = self.combo_game_filter.findData(curr_gf)
        if idx_gf >= 0:
            self.combo_game_filter.setCurrentIndex(idx_gf)
        self.combo_game_filter.currentIndexChanged.connect(self.on_game_filter_changed)

        gf_box.addWidget(lbl_gf)
        gf_box.addWidget(self.combo_game_filter)
        opt_grid.addLayout(gf_box)

        opt_grid.addSpacing(20)

        # Windows Service Controls
        srv_box = QVBoxLayout()
        lbl_srv = QLabel("Служба Windows (Автозапуск в фоне):")
        lbl_srv.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

        srv_btns = QHBoxLayout()
        self.btn_install_service = QPushButton("Установить как службу")
        self.btn_install_service.clicked.connect(self.install_service_click)

        self.btn_remove_service = QPushButton("Удалить службу")
        self.btn_remove_service.clicked.connect(self.remove_service_click)

        srv_btns.addWidget(self.btn_install_service)
        srv_btns.addWidget(self.btn_remove_service)

        srv_box.addWidget(lbl_srv)
        srv_box.addLayout(srv_btns)
        opt_grid.addLayout(srv_box)

        oc_layout.addLayout(opt_grid)
        layout.addWidget(options_card)

        # Quick Live Connectivity Check
        test_card = QFrame()
        test_card.setProperty("class", "card")
        tc_layout = QHBoxLayout(test_card)

        self.lbl_quick_status = QLabel("Статус подключения: не проверялся")
        self.lbl_quick_status.setStyleSheet("color: #8b949e;")

        self.btn_run_quick_test = QPushButton("Проверить доступность (YouTube, Discord)")
        self.btn_run_quick_test.clicked.connect(self.run_quick_test)

        tc_layout.addWidget(self.lbl_quick_status)
        tc_layout.addStretch()
        tc_layout.addWidget(self.btn_run_quick_test)
        layout.addWidget(test_card)

        layout.addStretch()
        return widget

    def update_preset_explanation(self, preset_id: str):
        if preset_id == "custom":
            self.lbl_preset_explanation.setText("Используются пользовательские аргументы из вкладки «Пресеты».")
            return
        preset = PRESETS.get(preset_id)
        if preset:
            self.lbl_preset_explanation.setText(f"ℹ {preset['description']}")

    def on_dashboard_preset_changed(self):
        new_preset = self.combo_dashboard_preset.currentData()
        self.engine.config.set("active_preset", new_preset)
        self.update_preset_explanation(new_preset)
        if self.engine.is_process_running():
            self.engine.log(f"Перезапуск с новым пресетом: {new_preset}", "INFO")
            self.engine.start_process(new_preset)

    def on_game_filter_changed(self):
        new_gf = self.combo_game_filter.currentData()
        self.engine.config.set("game_filter", new_gf)
        if self.engine.is_process_running():
            self.engine.log(f"Обновлен режим игрового фильтра: {new_gf}. Перезапуск процесса...", "INFO")
            self.engine.start_process()

    # ----------------------------------------------------
    # TAB 2: Presets Library (All 22 Strategies)
    # ----------------------------------------------------
    def create_presets_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        top_info = QLabel("Полный каталог стратегий обхода DPI из zapret-discord-youtube v1.10.2")
        top_info.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(top_info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)

        # Group by category
        categories = ["Рекомендуемые", "Альтернативные", "Fake TLS", "Simple Fake", "Экспериментальные"]
        
        self.preset_buttons = {}

        for cat in categories:
            cat_header = QLabel(f"● {cat.upper()}")
            cat_header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            cat_header.setStyleSheet("color: #58a6ff; margin-top: 10px;")
            scroll_layout.addWidget(cat_header)

            for pid, pdata in PRESETS.items():
                if pdata["category"] != cat:
                    continue

                p_frame = QFrame()
                p_frame.setProperty("class", "card")
                pf_layout = QHBoxLayout(p_frame)

                desc_layout = QVBoxLayout()
                lbl_title = QLabel(pdata["title"])
                lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                lbl_desc = QLabel(pdata["description"])
                lbl_desc.setStyleSheet("color: #8b949e;")
                lbl_desc.setWordWrap(True)

                desc_layout.addWidget(lbl_title)
                desc_layout.addWidget(lbl_desc)
                pf_layout.addLayout(desc_layout, stretch=4)

                btn_select = QPushButton("Выбрать")
                btn_select.setFixedWidth(110)
                btn_select.clicked.connect(lambda checked, p=pid: self.select_preset(p))
                self.preset_buttons[pid] = btn_select
                pf_layout.addWidget(btn_select, stretch=1)

                scroll_layout.addWidget(p_frame)

        # Custom Arguments Section
        custom_header = QLabel("● CUSTOM (ПОЛЬЗОВАТЕЛЬСКИЙ ПРОФИЛЬ)")
        custom_header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        custom_header.setStyleSheet("color: #f0883e; margin-top: 15px;")
        scroll_layout.addWidget(custom_header)

        custom_card = QFrame()
        custom_card.setProperty("class", "card")
        cc_layout = QVBoxLayout(custom_card)

        lbl_c_desc = QLabel("Введите собственные флаги запуска winws.exe:")
        lbl_c_desc.setStyleSheet("color: #8b949e;")
        self.txt_custom_args = QTextEdit()
        self.txt_custom_args.setPlaceholderText("--wf-tcp=80,443 --filter-tcp=443 --dpi-desync=fake,split ...")
        self.txt_custom_args.setText(self.engine.config.get("custom_args", ""))
        self.txt_custom_args.setFixedHeight(80)

        cc_btn_row = QHBoxLayout()
        btn_save_custom = QPushButton("Сохранить и выбрать Custom")
        btn_save_custom.clicked.connect(self.save_custom_args)
        cc_btn_row.addStretch()
        cc_btn_row.addWidget(btn_save_custom)

        cc_layout.addWidget(lbl_c_desc)
        cc_layout.addWidget(self.txt_custom_args)
        cc_layout.addLayout(cc_btn_row)
        scroll_layout.addWidget(custom_card)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self.update_preset_buttons_highlight()
        return widget

    def select_preset(self, preset_id: str):
        self.engine.config.set("active_preset", preset_id)
        # update dashboard dropdown
        idx = self.combo_dashboard_preset.findData(preset_id)
        if idx >= 0:
            self.combo_dashboard_preset.blockSignals(True)
            self.combo_dashboard_preset.setCurrentIndex(idx)
            self.combo_dashboard_preset.blockSignals(False)

        self.update_preset_explanation(preset_id)
        self.update_preset_buttons_highlight()

        if self.engine.is_process_running():
            self.engine.start_process(preset_id)

        QMessageBox.information(self, "Пресет выбран", f"Активным выбран пресет:\n{preset_id}")

    def save_custom_args(self):
        args = self.txt_custom_args.toPlainText().strip()
        self.engine.config.set("custom_args", args)
        self.select_preset("custom")

    def update_preset_buttons_highlight(self):
        active = self.engine.config.get("active_preset", "general")
        for pid, btn in self.preset_buttons.items():
            if pid == active:
                btn.setText("✔ Активен")
                btn.setStyleSheet("background-color: #238636; color: #fff; font-weight: bold;")
            else:
                btn.setText("Выбрать")
                btn.setStyleSheet("")

    # ----------------------------------------------------
    # TAB 3: Auto-Benchmark / Provider Strategy Finder
    # ----------------------------------------------------
    def create_benchmark_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        info_card = QFrame()
        info_card.setProperty("class", "card")
        ic_layout = QVBoxLayout(info_card)

        lbl_bm_title = QLabel("⚡ Интеллектуальный авто-подбор стратегии для вашего провайдера")
        lbl_bm_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_bm_desc = QLabel(
            "Приложение автоматически протестирует ключевые стратегии на YouTube (пробив блокировки потока 16-32КБ) "
            "и Discord (шлюз и CDN), после чего определит лучшую и самую быструю стратегию для вашей сети."
        )
        lbl_bm_desc.setStyleSheet("color: #8b949e;")
        lbl_bm_desc.setWordWrap(True)

        ic_layout.addWidget(lbl_bm_title)
        ic_layout.addWidget(lbl_bm_desc)

        btn_row = QHBoxLayout()
        self.btn_start_benchmark = QPushButton("🚀 НАЧАТЬ ТЕСТИРОВАНИЕ СТРАТЕГИЙ")
        self.btn_start_benchmark.setProperty("class", "primary")
        self.btn_start_benchmark.clicked.connect(self.start_benchmark)

        self.btn_stop_benchmark = QPushButton("Остановить")
        self.btn_stop_benchmark.setProperty("class", "danger")
        self.btn_stop_benchmark.setEnabled(False)
        self.btn_stop_benchmark.clicked.connect(self.stop_benchmark)

        btn_row.addWidget(self.btn_start_benchmark)
        btn_row.addWidget(self.btn_stop_benchmark)
        btn_row.addStretch()

        ic_layout.addLayout(btn_row)
        layout.addWidget(info_card)

        # Progress bar
        self.bm_progress = QProgressBar()
        self.bm_progress.setValue(0)
        self.lbl_bm_status = QLabel("Готов к тестированию")
        self.lbl_bm_status.setStyleSheet("color: #58a6ff;")

        layout.addWidget(self.lbl_bm_status)
        layout.addWidget(self.bm_progress)

        # Results Table
        self.table_benchmark = QTableWidget()
        self.table_benchmark.setColumnCount(5)
        self.table_benchmark.setHorizontalHeaderLabels([
            "Стратегия", "Статус", "YouTube (Stream)", "Discord Gateway", "Пинг"
        ])
        self.table_benchmark.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_benchmark.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_benchmark.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_benchmark.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_benchmark.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table_benchmark)

        # Apply best button
        self.btn_apply_best = QPushButton("✔ Применить лучшую найденную стратегию")
        self.btn_apply_best.setProperty("class", "primary")
        self.btn_apply_best.setEnabled(False)
        self.btn_apply_best.clicked.connect(self.apply_best_strategy)
        layout.addWidget(self.btn_apply_best)

        self.benchmark_results_cache = []
        return widget

    def start_benchmark(self):
        if not is_admin():
            QMessageBox.warning(
                self,
                "Требуются права Администратора",
                "Авто-подбор стратегий переключает драйвер WinDivert. Пожалуйста, перезапустите приложение от имени Администратора!"
            )
            return

        # Choose top representative strategies for quick & thorough benchmark
        benchmark_candidates = [
            "general",
            "general (ALT)",
            "general (ALT2)",
            "general (ALT4)",
            "general (ALT6)",
            "general (ALT10)",
            "general (ALT11)",
            "general (FAKE TLS AUTO)",
            "general (SIMPLE FAKE)"
        ]

        self.btn_start_benchmark.setEnabled(False)
        self.btn_stop_benchmark.setEnabled(True)
        self.btn_apply_best.setEnabled(False)
        self.table_benchmark.setRowCount(0)
        self.bm_progress.setMaximum(len(benchmark_candidates))
        self.bm_progress.setValue(0)
        self.benchmark_results_cache.clear()

        self.active_benchmark_thread = BenchmarkThread(self.tester, benchmark_candidates)
        self.active_benchmark_thread.progress_signal.connect(self.on_benchmark_progress)
        self.active_benchmark_thread.completed_signal.connect(self.on_benchmark_completed)
        self.active_benchmark_thread.start()

    def stop_benchmark(self):
        if self.tester:
            self.tester.cancel()
        self.lbl_bm_status.setText("Тестирование прервано пользователем.")
        self.btn_start_benchmark.setEnabled(True)
        self.btn_stop_benchmark.setEnabled(False)

    def on_benchmark_progress(self, current, total, title, res: PresetBenchmarkResult):
        self.bm_progress.setValue(current)
        self.lbl_bm_status.setText(f"Тестирование ({current}/{total}): {title}...")

        # Add row to table
        row = self.table_benchmark.rowCount()
        self.table_benchmark.insertRow(row)

        item_title = QTableWidgetItem(res.preset_title)
        
        status_text = "РАБОТАЕТ" if res.is_working else "БЛОКИРУЕТСЯ"
        item_status = QTableWidgetItem(status_text)
        item_status.setForeground(QColor("#238636" if res.is_working else "#da3633"))

        # Details
        yt_stream = "OK" if len(res.details) > 0 and res.details[0].success else "FAIL"
        dc_gate = "OK" if len(res.details) > 2 and res.details[2].success else "FAIL"

        item_yt = QTableWidgetItem(yt_stream)
        item_yt.setForeground(QColor("#238636" if yt_stream == "OK" else "#da3633"))

        item_dc = QTableWidgetItem(dc_gate)
        item_dc.setForeground(QColor("#238636" if dc_gate == "OK" else "#da3633"))

        item_lat = QTableWidgetItem(f"{res.avg_latency_ms} ms")

        self.table_benchmark.setItem(row, 0, item_title)
        self.table_benchmark.setItem(row, 1, item_status)
        self.table_benchmark.setItem(row, 2, item_yt)
        self.table_benchmark.setItem(row, 3, item_dc)
        self.table_benchmark.setItem(row, 4, item_lat)

        self.benchmark_results_cache.append(res)

    def on_benchmark_completed(self, results: list[PresetBenchmarkResult]):
        self.btn_start_benchmark.setEnabled(True)
        self.btn_stop_benchmark.setEnabled(False)

        working = [r for r in results if r.is_working]
        if working:
            best = working[0]
            self.lbl_bm_status.setText(f"✔ Тестирование завершено! Рекомендуемая стратегия: {best.preset_title}")
            self.btn_apply_best.setEnabled(True)
            self.btn_apply_best.setText(f"✔ Применить лучшую стратегию: {best.preset_title}")
        else:
            self.lbl_bm_status.setText("⚠ Ни одна из проверенных стратегий не сработала на 100%. Попробуйте ALT12 или Fake TLS.")

    def apply_best_strategy(self):
        working = [r for r in self.benchmark_results_cache if r.is_working]
        if working:
            best = working[0]
            self.select_preset(best.preset_id)
            self.tabs.setCurrentIndex(0)

    # ----------------------------------------------------
    # TAB 4: Lists Editor
    # ----------------------------------------------------
    def create_lists_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lbl_info = QLabel("Управление пользовательскими списками доменов")
        lbl_info.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_info)

        tabs_lists = QTabWidget()

        # User List (list-general-user.txt)
        user_list_file = LISTS_DIR / "list-general-user.txt"
        w_user, self.txt_user_list = self.create_list_editor(
            user_list_file,
            "Свои сайты для разблокировки (list-general-user.txt)",
            "Добавляйте домены по одному на строку (например: rutracker.org, instagram.com)"
        )
        tabs_lists.addTab(w_user, "Пользовательские домены")

        # Exclude List (list-exclude-user.txt)
        exclude_list_file = LISTS_DIR / "list-exclude-user.txt"
        w_exclude, self.txt_exclude_list = self.create_list_editor(
            exclude_list_file,
            "Исключения (list-exclude-user.txt)",
            "Сайты, которые должны работать напрямую без обхода DPI (например: банки, гос. сервисы)"
        )
        tabs_lists.addTab(w_exclude, "Исключения (Прямой доступ)")

        layout.addWidget(tabs_lists)
        return widget

    def create_list_editor(self, file_path: Path, title: str, subtitle: str):
        w = QWidget()
        l = QVBoxLayout(w)

        lbl_t = QLabel(title)
        lbl_t.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet("color: #8b949e;")

        txt = QTextEdit()
        txt.setFont(QFont("Consolas", 11))

        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    txt.setText(f.read())
            except Exception:
                pass

        btn_save = QPushButton("Сохранить список")
        btn_save.clicked.connect(lambda: self.save_list_file(file_path, txt.toPlainText()))

        l.addWidget(lbl_t)
        l.addWidget(lbl_s)
        l.addWidget(txt)
        l.addWidget(btn_save)
        return w, txt

    def save_list_file(self, file_path: Path, content: str):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Сохранено", f"Файл {file_path.name} успешно обновлен.")
            if self.engine.is_process_running():
                self.engine.start_process()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось сохранить файл: {e}")

    # ----------------------------------------------------
    # TAB 5: Logs & Diagnostics
    # ----------------------------------------------------
    def create_logs_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        top_row = QHBoxLayout()
        lbl_title = QLabel("Живой журнал вывода winws.exe и системных событий:")
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        btn_clear = QPushButton("Очистить журнал")
        btn_clear.clicked.connect(self.clear_logs)

        top_row.addWidget(lbl_title)
        top_row.addStretch()
        top_row.addWidget(btn_clear)
        layout.addLayout(top_row)

        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setFont(QFont("Consolas", 10))
        self.txt_logs.setStyleSheet("background-color: #0d1117; color: #58a6ff; border: 1px solid #30363d;")
        layout.addWidget(self.txt_logs)

        return widget

    def on_log_message(self, message: str, level: str):
        color = "#e6edf3"
        if level == "ERROR":
            color = "#f85149"
        elif level == "WARNING":
            color = "#d29922"
        elif level == "SUCCESS":
            color = "#3fb950"

        # Append HTML
        safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.txt_logs.append(f"<span style='color:{color};'>{safe_msg}</span>")

    def clear_logs(self):
        self.txt_logs.clear()

    # ----------------------------------------------------
    # Actions & Process Control
    # ----------------------------------------------------
    def toggle_process(self):
        if self.engine.is_process_running():
            self.engine.stop_process()
        else:
            self.engine.start_process()
        self.refresh_status()

    def refresh_status(self):
        is_proc_running = self.engine.is_process_running()
        srv_status = self.engine.get_service_status()

        if is_proc_running:
            self.lbl_status_icon.setText("🟢")
            self.lbl_status_title.setText("ЗАЩИТА АКТИВНА (ПРОЦЕСС)")
            self.lbl_status_title.setStyleSheet("color: #238636;")
            self.lbl_status_detail.setText("Трафик фильтруется драйвером WinDivert. YouTube и Discord работают.")
            self.btn_master_toggle.setText("ОСТАНОВИТЬ ЗАЩИТУ")
            self.btn_master_toggle.setProperty("class", "danger")
            self.action_toggle.setText("Остановить")
            self.tray.setIcon(create_app_icon("#238636"))
        elif srv_status == "running":
            self.lbl_status_icon.setText("🟢")
            self.lbl_status_title.setText("СЛУЖБА WINDOWS АКТИВНА")
            self.lbl_status_title.setStyleSheet("color: #238636;")
            self.lbl_status_detail.setText("Zapret работает как системная служба Windows (автозапуск).")
            self.btn_master_toggle.setText("ОСТАНОВИТЬ СЛУЖБУ")
            self.btn_master_toggle.setProperty("class", "danger")
            self.action_toggle.setText("Остановить службу")
            self.tray.setIcon(create_app_icon("#238636"))
        else:
            self.lbl_status_icon.setText("🔴")
            self.lbl_status_title.setText("ЗАЩИТА ОСТАНОВЛЕНА")
            self.lbl_status_title.setStyleSheet("color: #da3633;")
            self.lbl_status_detail.setText("Нажмите «Запустить», чтобы активировать обход DPI для вашего провайдера.")
            self.btn_master_toggle.setText("ЗАПУСТИТЬ ЗАЩИТУ")
            self.btn_master_toggle.setProperty("class", "primary")
            self.action_toggle.setText("Запустить")
            self.tray.setIcon(create_app_icon("#da3633"))

        # Re-apply CSS property
        self.btn_master_toggle.style().unpolish(self.btn_master_toggle)
        self.btn_master_toggle.style().polish(self.btn_master_toggle)

    def install_service_click(self):
        if not is_admin():
            QMessageBox.warning(self, "Требуется UAC", "Для создания службы запустите приложение с правами Администратора!")
            return
        # Stop process if running
        if self.engine.is_process_running():
            self.engine.stop_process()
        self.engine.install_service()
        self.refresh_status()

    def remove_service_click(self):
        if not is_admin():
            QMessageBox.warning(self, "Требуется UAC", "Для удаления службы запустите приложение с правами Администратора!")
            return
        self.engine.uninstall_service()
        self.refresh_status()

    def run_quick_test(self):
        self.lbl_quick_status.setText("Проверка доступности...")
        self.btn_run_quick_test.setEnabled(False)

        def on_finished(results: list[TargetResult]):
            self.btn_run_quick_test.setEnabled(True)
            success_count = sum(1 for r in results if r.success)
            total = len(results)
            if success_count == total:
                self.lbl_quick_status.setText(f"✔ Все сервисы доступны ({success_count}/{total})")
                self.lbl_quick_status.setStyleSheet("color: #238636; font-weight: bold;")
            elif success_count > 0:
                self.lbl_quick_status.setText(f"⚠ Частичная доступность ({success_count}/{total})")
                self.lbl_quick_status.setStyleSheet("color: #d29922; font-weight: bold;")
            else:
                self.lbl_quick_status.setText(f"❌ Сервисы заблокированы ({success_count}/{total}). Смените стратегию!")
                self.lbl_quick_status.setStyleSheet("color: #da3633; font-weight: bold;")

        self.active_test_thread = QuickTestThread(self.tester)
        self.active_test_thread.finished_signal.connect(on_finished)
        self.active_test_thread.start()

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = ZapretControlWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
