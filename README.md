<div align="center">

# ⚡ Zapret Desktop Control

**Современный графический интерфейс для утилиты Zapret (`winws.exe`) с авто-подбором стратегий под провайдера, полной библиотекой из 22 боевых пресетов и интеграцией службы Windows.**

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue?style=for-the-badge&logo=windows)](https://github.com/Ex0t1ke/zapret-control-windows)
[![Python](https://img.shields.io/badge/Python-3.12+-yellow?style=for-the-badge&logo=python)](https://github.com/Ex0t1ke/zapret-control-windows)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Tailwind-61dafb?style=for-the-badge&logo=react)](https://github.com/Ex0t1ke/zapret-control-windows)
[![Zapret](https://img.shields.io/badge/Core-Zapret%20v1.10.2-orange?style=for-the-badge)](https://github.com/bol-van/zapret)
[![Release](https://img.shields.io/badge/Release-v1.0.0-green?style=for-the-badge)](https://github.com/Ex0t1ke/zapret-control-windows/releases)

[**📥 Скачать готовый релиз (.ZIP)**](https://github.com/Ex0t1ke/zapret-control-windows/releases/latest) • [**📖 Документация**](#-возможности) • [**⚙ Сборка из исходников**](#-сборка-из-исходников)

</div>

---

## 🌟 Возможности

* 🎨 **Современный интерфейс:** Полностью кастомный дизайн в тёмной и светлой теме с боковым сайдбаром, отзывчивой анимацией и статусом защиты в реальном времени.
* 🚀 **Интеллектуальный авто-подбор (Бенчмарк):** Автоматическое последовательное тестирование стратегий на YouTube (пробив TCP 16–32 КБ) и Discord (шлюзы и голосовой RTC), замер пинга и рекомендация идеальной стратегии для вашего интернет-провайдера в один клик.
* 🎛 **Матрица из 22 боевых стратегий (из `zapret-discord-youtube`):**
  * `General (Стандарт)` — Multisplit + Fake TLS (Google/4PDA) + Discord RTC.
  * `General ALT 1` – `ALT 13` — различные алгоритмы нарезки пакетов (`split-pos`, `seqovl`), autottl и desync repeats под фильтры ТСПУ (Ростелеком, Дом.ру, МТС, Билайн, ТТК и др.).
  * `Fake TLS Auto (1..3)` — генерация фейкового ClientHello для мобильных провайдеров.
  * `Simple Fake (1..2)` — облегченный desync без глубокой фрагментации.
  * `EXP` — экспериментальные методы обхода.
* 🎮 **Игровой фильтр (Game Filter):** Динамическое переключение портов (`1024-65535` TCP/UDP) для онлайн-игр (Dota 2, CS2, Valorant, Apex, League of Legends) и голосовых комнат Discord.
* 🛡 **Режим системной службы Windows:** Возможность установить `winws.exe` как системную службу Windows (`sc.exe`), работающую в фоне с автозапуском до входа пользователя в систему.
* 🌐 **Управление списками сайтов:** Встроенный редактор пользовательских доменов (`list-general-user.txt`) и исключений напрямую из интерфейса.
* 📋 **Журнал событий:** Отображение реального консольного вывода `stdout` / `stderr` процесса `winws.exe` с авто-очисткой.

---

## 🚀 Быстрый запуск

1. Перейдите на страницу [**Releases**](https://github.com/Ex0t1ke/zapret-control-windows/releases/latest).
2. Скачайте архив **`ZapretControl-v1.0.0-Windows-x64.zip`**.
3. Распакуйте в любую удобную папку.
4. Запустите **`ZapretDesktopControl.exe`** (программа автоматически запросит права Администратора для загрузки драйвера WinDivert).
5. Нажмите **«Запустить защиту»** или перейдите в **«Авто-подбор»**, чтобы найти лучшую стратегию под вашего провайдера.

---

## 🛠 Сборка из исходников

Требования:
* Windows 10 / 11 (x64)
* Python 3.12+
* Node.js v18+

### 1. Клонирование репозитория
```bash
git clone https://github.com/Ex0t1ke/zapret-control-windows.git
cd zapret-control-windows
```

### 2. Установка зависимостей Python
```bash
pip install -r requirements.txt
```

### 3. Сборка фронтенда
```bash
cd extracted_interface
npm install
npm run build
cd ..
```

### 4. Запуск в режиме разработки
```bash
start_gui.bat
```

### 5. Сборка автономного исполняемого файла
```bash
pyinstaller ZapretDesktopControl.spec
```

---

## ⚠️ Важная информация
Для работы утилиты требуется драйвер **WinDivert**, который взаимодействует с сетевым стеком Windows на уровне ядра. Для этого приложению необходимы права Администратора.

---

## 📜 Лицензия
Проект распространяется под лицензией MIT. Использует бинарники утилиты [Zapret](https://github.com/bol-van/zapret) и драйвер [WinDivert](https://reqrypt.org/windivert.html).
