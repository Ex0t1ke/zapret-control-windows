import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { REAL_PRESETS, type Preset } from "./presets";
import { Bridge, type TargetStatus, type BenchmarkResult } from "./bridge";

const icons = {
  brand: (
    <>
      <path d="M12 2.75 20 6v5.6c0 4.6-3.1 7.7-8 9.65-4.9-1.95-8-5.05-8-9.65V6l8-3.25Z" />
      <path d="m8.5 12 2.25 2.25 4.75-4.75" />
    </>
  ),
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </>
  ),
  layers: (
    <>
      <path d="m12 3 9 5-9 5-9-5 9-5Z" />
      <path d="m3 12 9 5 9-5M3 16l9 5 9-5" />
    </>
  ),
  scan: (
    <>
      <path d="M8 4H5a1 1 0 0 0-1 1v3m12-4h3a1 1 0 0 1 1 1v3m0 8v3a1 1 0 0 1-1 1h-3m-8 0H5a1 1 0 0 1-1-1v-3M12 8v8m-4-4h8" />
    </>
  ),
  globe: (
    <>
      <circle cx="12" cy="12" r="9" />
      <ellipse cx="12" cy="12" rx="4" ry="9" />
      <path d="M3 12h18" />
    </>
  ),
  terminal: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m7 10 2.5 2L7 14m5 0h4" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2m0 15v2m9.5-9.5h-2m-15 0h-2m16.2-6.7-1.4 1.4M6.7 17.3l-1.4 1.4m13.4 0-1.4-1.4M6.7 6.7 5.3 5.3" />
    </>
  ),
  moon: <path d="M20.4 15.5A8.8 8.8 0 0 1 8.5 3.6a8.8 8.8 0 1 0 11.9 11.9Z" />,
  shield: (
    <>
      <path d="M12 22s7.5-3.4 7.5-9.6V5.5L12 2 4.5 5.5v6.9C4.5 18.6 12 22 12 22Z" />
      <path d="M12 8v4m0 3h.01" />
    </>
  ),
  shieldCheck: (
    <>
      <path d="M12 22s7.5-3.4 7.5-9.6V5.5L12 2 4.5 5.5v6.9C4.5 18.6 12 22 12 22Z" />
      <path d="m8.7 12 2.2 2.2 4.4-4.4" />
    </>
  ),
  chevronRight: <path d="m9 6 6 6-6 6" />,
  chevronDown: <path d="m6 9 6 6 6-6" />,
  play: (
    <path
      d="M8 5.2a.6.6 0 0 1 .9-.5l10 6.8a.6.6 0 0 1 0 1l-10 6.8a.6.6 0 0 1-.9-.5Z"
      fill="currentColor"
      stroke="none"
    />
  ),
  stop: <rect x="5" y="5" width="14" height="14" rx="2" fill="currentColor" stroke="none" />,
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5m0-8h.01" />
    </>
  ),
  game: (
    <>
      <path d="M7.3 7h9.4a4 4 0 0 1 3.9 3.2l1 4.8a2.6 2.6 0 0 1-4.3 2.5l-2.2-2H8.9l-2.2 2A2.6 2.6 0 0 1 2.4 15l1-4.8A4 4 0 0 1 7.3 7Z" />
      <path d="M8 9.5v4m-2-2h4m5.5 0h.01m2.5-1.4h.01" />
    </>
  ),
  monitor: (
    <>
      <rect x="3" y="4" width="18" height="13" rx="2" />
      <path d="M12 17v4m-4 0h8" />
    </>
  ),
  activity: <path d="M2.5 12h4l3-6 4.5 12 3-6h4.5" />,
  refresh: (
    <>
      <path d="M20.7 9a9 9 0 0 0-15-3.6L3.5 7.7m0 0V3m0 4.7H8m-4.7 7.3a9 9 0 0 0 15 3.6l2.2-2.3m0 0V21m0-4.7H16" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  trash: (
    <>
      <path d="M4 7h16m-14 0 1 13h10l1-13M9 7V4h6v3m-5 4v5m4-5v5" />
    </>
  ),
  check: <path d="m5 12 4.5 4.5L19 7" />,
} satisfies Record<string, ReactNode>;

type IconName = keyof typeof icons;

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {icons[name]}
    </svg>
  );
}

const pages = [
  {
    id: "dashboard",
    icon: "dashboard",
    title: "Панель управления",
    description: "Управление защитой, пресетами и сетевыми настройками.",
  },
  {
    id: "presets",
    icon: "layers",
    title: "Пресеты",
    description: "Выберите профиль, который будет применяться при запуске защиты.",
  },
  {
    id: "auto",
    icon: "scan",
    title: "Авто-подбор",
    description: "Автоматический подбор оптимальной стратегии для вашего провайдера.",
  },
  {
    id: "sites",
    icon: "globe",
    title: "Списки сайтов",
    description: "Управляйте списком доменов для защиты.",
  },
  {
    id: "logs",
    icon: "terminal",
    title: "Журнал и диагностика",
    description: "История действий, вывод winws.exe и результаты проверки сети.",
  },
] as const;

type Page = (typeof pages)[number]["id"];
type Result = "idle" | "running" | "done";
type Log = { id: number; time: string; message: string };

function CardHeading({
  icon,
  title,
  description,
}: {
  icon: IconName;
  title: string;
  description: string;
}) {
  return (
    <div className="card-heading">
      <span className="card-icon">
        <Icon name={icon} size={19} />
      </span>
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}) {
  return (
    <div className="select-wrap">
      <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)}>
        {children}
      </select>
      <span className="select-arrow">
        <Icon name="chevronDown" size={16} />
      </span>
    </div>
  );
}

function StatusGraphic() {
  return (
    <svg
      className="status-graphic"
      viewBox="0 0 480 164"
      fill="none"
      preserveAspectRatio="xMaxYMid slice"
      aria-hidden="true"
    >
      <defs>
        <pattern id="status-grid" width="21" height="21" patternUnits="userSpaceOnUse">
          <path d="M21 0H0v21" stroke="currentColor" strokeOpacity=".22" />
        </pattern>
      </defs>
      <path d="M0 0h480v164H0z" fill="url(#status-grid)" />
      <g stroke="currentColor">
        <circle cx="306" cy="82" r="69" opacity=".32" />
        <circle cx="306" cy="82" r="103" opacity=".22" />
        <circle cx="306" cy="82" r="137" opacity=".14" />
        <path d="M306 9v146M232 82h148" opacity=".24" />
        <path d="m306 30 42 17v30c0 27-17 44-42 56-25-12-42-29-42-56V47l42-17Z" opacity=".3" />
        <path d="M239 78v8m-4-4h8m131-4v8m-4-4h8m-72-72v8m-4-4h8m-4 130v8m-4-4h8" opacity=".55" />
      </g>
    </svg>
  );
}

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [active, setActive] = useState(false);
  const [presetId, setPresetId] = useState<string>(REAL_PRESETS[0].id);
  const [gameMode, setGameMode] = useState("disabled");
  const [installed, setInstalled] = useState(false);
  const [isAdmin, setIsAdmin] = useState(true);
  const [availability, setAvailability] = useState<Result>("idle");
  const [availabilitySummary, setAvailabilitySummary] = useState("5 / 5 доступны");
  const [availabilityList, setAvailabilityList] = useState<TargetStatus[]>([]);
  const [auto, setAuto] = useState<Result>("idle");
  const [recommended, setRecommended] = useState<string>("general (ALT)");
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult[]>([]);
  const [domains, setDomains] = useState<string[]>(["youtube.com", "discord.com", "googlevideo.com"]);
  const [domain, setDomain] = useState("");
  const [domainError, setDomainError] = useState("");
  const [logs, setLogs] = useState<Log[]>([]);
  const nextLogId = useRef(1);

  const currentPage = pages.find((item) => item.id === page)!;
  const selectedPreset = REAL_PRESETS.find((item) => item.id === presetId) || REAL_PRESETS[0];

  function addLog(message: string) {
    const id = nextLogId.current++;
    const time = new Date().toLocaleTimeString("ru-RU");
    setLogs((entries) => [{ id, time, message }, ...entries]);
  }

  // Load real state on mount
  useEffect(() => {
    Bridge.getInitialState().then((state) => {
      setActive(state.active);
      if (state.preset) {
        const match = REAL_PRESETS.find(p => p.id === state.preset || p.name === state.preset);
        if (match) setPresetId(match.id);
      }
      setGameMode(state.gameMode || "disabled");
      setInstalled(state.serviceInstalled);
      setIsAdmin(state.isAdmin);
      if (state.domains && state.domains.length) {
        setDomains(state.domains);
      }
      if (state.logs && state.logs.length) {
        setLogs(state.logs);
      }
    });

    const interval = setInterval(async () => {
      if (window.pywebview?.api) {
        try {
          const s = await Bridge.getInitialState();
          setActive(s.active);
          setInstalled(s.serviceInstalled);
          if (s.logs && s.logs.length > logs.length) {
            setLogs(s.logs);
          }
        } catch {
          // ignore
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  async function changePreset(id: string) {
    if (id === presetId) return;
    setPresetId(id);
    const p = REAL_PRESETS.find(item => item.id === id) || REAL_PRESETS[0];
    addLog(`Выбран пресет «${p.title}».`);
    await Bridge.setPreset(id);
  }

  async function toggleProtection() {
    const nextState = !active;
    setActive(nextState);
    if (nextState) {
      addLog(`Запуск winws.exe с пресетом «${selectedPreset.title}»...`);
      const ok = await Bridge.startProtection(presetId);
      if (!ok) {
        setActive(false);
        addLog("Не удалось запустить winws.exe. Проверьте права администратора.");
      } else {
        addLog("Защита успешно запущена. Трафик фильтруется WinDivert.");
      }
    } else {
      addLog("Остановка защиты...");
      await Bridge.stopProtection();
      addLog("Защита остановлена.");
    }
  }

  async function checkAvailability() {
    setAvailability("running");
    addLog("Запущена проверка доступности YouTube и Discord...");
    const res = await Bridge.checkAvailability();
    setAvailability("done");
    setAvailabilitySummary(`${res.count_ok} / ${res.total} доступны`);
    setAvailabilityList(res.details || []);
    addLog(`Проверка завершена: ${res.count_ok} из ${res.total} сервисов доступны.`);
  }

  async function runAuto() {
    setAuto("running");
    addLog("Запущен интеллектуальный подбор стратегии для вашего провайдера...");
    const res = await Bridge.runBenchmark();
    setAuto("done");
    setRecommended(res.recommended);
    setBenchmarkResults(res.results || []);
    const recPreset = REAL_PRESETS.find(p => p.id === res.recommended) || REAL_PRESETS[1];
    addLog(`Авто-подбор завершён! Рекомендованная стратегия: ${recPreset.title}`);
  }

  async function addDomain(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = domain.trim().toLowerCase().replace(/\.$/, "");
    if (!/^(?:[a-z\d](?:[a-z\d-]{0,61}[a-z\d])?\.)+[a-z\d](?:[a-z\d-]{0,61}[a-z\d])?$/.test(value)) {
      setDomainError("Введите домен без протокола и пути, например example.com.");
      return;
    }
    if (domains.includes(value)) {
      setDomainError("Этот домен уже есть в списке.");
      return;
    }
    setDomains([...domains, value]);
    setDomain("");
    setDomainError("");
    addLog(`Добавлен домен ${value}.`);
    await Bridge.addDomain(value);
  }

  async function removeDomain(item: string) {
    setDomains(domains.filter((value) => value !== item));
    addLog(`Удалён домен ${item}.`);
    await Bridge.removeDomain(item);
  }

  return (
    <div className="app-shell" data-theme={theme}>
      <aside className="sidebar" aria-label="Боковая панель">
        <button
          className="brand"
          onClick={() => setPage("dashboard")}
          aria-label="Zapret, на панель управления"
        >
          <span className="brand-mark">
            <Icon name="brand" size={23} />
          </span>
          <span className="brand-type">
            <strong>zapret</strong>
            <span>DESKTOP CONTROL</span>
          </span>
        </button>

        <nav className="navigation" aria-label="Разделы">
          <p className="nav-label">Рабочая область</p>
          {pages.map((item) => (
            <button
              className="nav-item"
              key={item.id}
              aria-current={page === item.id ? "page" : undefined}
              onClick={() => setPage(item.id)}
              title={item.title}
            >
              <Icon name={item.icon} size={18} />
              <span>{item.title}</span>
              {item.id === "presets" && <small>{REAL_PRESETS.length}</small>}
            </button>
          ))}
        </nav>

        <div className="appearance">
          <p className="nav-label">Оформление</p>
          <div className="theme-control" role="group" aria-label="Цветовая тема">
            <button
              onClick={() => setTheme("dark")}
              aria-pressed={theme === "dark"}
              aria-label="Тёмная тема"
              title="Тёмная тема"
            >
              <Icon name="moon" size={15} />
              <span>Тёмная</span>
            </button>
            <button
              onClick={() => setTheme("light")}
              aria-pressed={theme === "light"}
              aria-label="Светлая тема"
              title="Светлая тема"
            >
              <Icon name="sun" size={15} />
              <span>Светлая</span>
            </button>
          </div>
        </div>
      </aside>

      <div className="app-body">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Рабочая область</span>
            <Icon name="chevronRight" size={13} />
            <strong>{currentPage.title}</strong>
          </div>
          <details className="admin">
            <summary>
              <Icon name={isAdmin ? "shieldCheck" : "shield"} size={15} />
              <span>{isAdmin ? "Режим администратора" : "Запуск без прав UAC"}</span>
              <Icon name="chevronDown" size={13} />
            </summary>
            <p>
              {isAdmin
                ? "Драйвер WinDivert активен с полными системными привилегиями."
                : "Для перехвата трафика и установки службы требуются права Администратора."}
              {!isAdmin && (
                <button
                  className="button secondary"
                  style={{ marginTop: 8, width: "100%" }}
                  onClick={() => Bridge.restartAsAdmin()}
                >
                  Перезапустить с UAC
                </button>
              )}
            </p>
          </details>
        </header>

        <main className="workspace">
          <div className="page-heading">
            <h1>{currentPage.title}</h1>
            <p>{currentPage.description}</p>
          </div>

          {page === "dashboard" && (
            <div className="dashboard">
              <section className="panel status-panel" data-active={active}>
                <StatusGraphic />
                <div className="status-content">
                  <span className="status-icon">
                    <Icon name={active ? "shieldCheck" : "shield"} size={28} />
                  </span>
                  <div>
                    <div className="status-label">
                      <span />
                      Статус защиты
                    </div>
                    <h2 aria-live="polite">{active ? "Защита запущена" : "Защита остановлена"}</h2>
                    <p>
                      {active
                        ? `Активен пресет: ${selectedPreset.title}. YouTube и Discord работают без задержек.`
                        : "Запустите защиту, чтобы применить выбранную стратегию обхода DPI."}
                    </p>
                  </div>
                </div>
                <button
                  className={`button status-action ${active ? "secondary" : "primary"}`}
                  onClick={toggleProtection}
                >
                  <Icon name={active ? "stop" : "play"} size={18} />
                  {active ? "Остановить защиту" : "Запустить защиту"}
                </button>
              </section>

              <section className="panel preset-panel">
                <CardHeading
                  icon="layers"
                  title="Активный пресет"
                  description="Стратегия, которая применяется при запуске защиты."
                />
                <div className="preset-controls">
                  <Select label="Активный пресет" value={presetId} onChange={changePreset}>
                    {REAL_PRESETS.map((profile) => (
                      <option key={profile.id} value={profile.id}>
                        {profile.title} — {profile.category}
                      </option>
                    ))}
                  </Select>
                  <button className="button secondary" onClick={() => setPage("auto")}>
                    <Icon name="scan" size={17} />
                    Подобрать пресет
                  </button>
                </div>
                <p className="field-help">
                  <Icon name="info" size={15} />
                  {selectedPreset.description}
                </p>
              </section>

              <section className="optimization" aria-labelledby="optimization-title">
                <h2 className="section-label" id="optimization-title">
                  Режимы и оптимизация
                </h2>
                <div className="settings-grid">
                  <div className="panel settings-panel">
                    <CardHeading
                      icon="game"
                      title="Игровой фильтр"
                      description="Для онлайн-игр и голосовых каналов Discord."
                    />
                    <Select
                      label="Игровой фильтр"
                      value={gameMode}
                      onChange={async (value) => {
                        setGameMode(value);
                        addLog(
                          `Игровой фильтр: ${value === "both" ? "включён (TCP+UDP)" : value === "udp" ? "только UDP" : "выключен"}.`
                        );
                        await Bridge.setGameFilter(value);
                      }}
                    >
                      <option value="disabled">Выключен (порты 80, 443)</option>
                      <option value="both">Включён (TCP + UDP 1024-65535)</option>
                      <option value="udp">Только UDP (Discord Voice / STUN)</option>
                      <option value="tcp">Только TCP</option>
                    </Select>
                  </div>
                  <div className="panel settings-panel">
                    <CardHeading
                      icon="monitor"
                      title="Служба Windows"
                      description={
                        installed
                          ? "Служба zapret установлена и активна в автозапуске."
                          : "Автозапуск защиты в фоновом режиме до входа в систему."
                      }
                    />
                    <div className="service-controls">
                      <button
                        className="button secondary"
                        disabled={installed}
                        onClick={async () => {
                          setInstalled(true);
                          addLog("Установка службы Windows zapret...");
                          await Bridge.installService();
                          addLog("Служба Windows успешно установлена!");
                        }}
                      >
                        <Icon name="plus" size={16} />
                        Установить службу
                      </button>
                      <button
                        className="button secondary"
                        disabled={!installed}
                        onClick={async () => {
                          setInstalled(false);
                          addLog("Остановка и удаление службы Windows zapret...");
                          await Bridge.uninstallService();
                          addLog("Служба Windows удалена.");
                        }}
                      >
                        <Icon name="trash" size={15} />
                        Удалить
                      </button>
                    </div>
                  </div>
                </div>
              </section>

              <section className="panel availability-panel">
                <CardHeading
                  icon="activity"
                  title="Доступность сервисов"
                  description={
                    availability === "done"
                      ? `Результат: ${availabilitySummary}.`
                      : "Проверка потокового видео YouTube (chunk 16-32КБ) и голосовых шлюзов Discord."
                  }
                />
                <div className="availability-controls">
                  <span
                    className={`result-pill ${availability === "done" ? "complete" : ""}`}
                    role="status"
                  >
                    <span />
                    {availability === "done"
                      ? availabilitySummary
                      : availability === "running"
                        ? "Проверка…"
                        : "Не проверено"}
                  </span>
                  <button
                    className="button secondary"
                    onClick={checkAvailability}
                    disabled={availability === "running"}
                  >
                    <Icon name="refresh" size={16} />
                    Проверить
                  </button>
                </div>
              </section>
            </div>
          )}

          {page === "presets" && (
            <section className="panel detail-panel">
              <CardHeading
                icon="layers"
                title="Библиотека пресетов"
                description={`${REAL_PRESETS.length} проверенных стратегии обхода из zapret-discord-youtube.`}
              />
              <div className="detail-list">
                {REAL_PRESETS.map((profile) => (
                  <div className="detail-row" key={profile.id}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <h3>{profile.title}</h3>
                        <span style={{ fontSize: 11, padding: "2px 6px", borderRadius: 4, background: "var(--hover)", color: "var(--accent)" }}>
                          {profile.category}
                        </span>
                      </div>
                      <p>{profile.description}</p>
                    </div>
                    <button
                      className="button secondary"
                      aria-pressed={presetId === profile.id}
                      onClick={() => changePreset(profile.id)}
                      disabled={presetId === profile.id}
                    >
                      {presetId === profile.id ? (
                        <>
                          <Icon name="check" size={16} />
                          Активен
                        </>
                      ) : (
                        "Выбрать"
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}

          {page === "auto" && (
            <section className="panel detail-panel">
              <CardHeading
                icon="scan"
                title="Подбор стратегии"
                description="Тестирование каждой стратегии на YouTube (пробив TCP 16-20КБ) и Discord."
              />
              <div className="detail-actions">
                <button className="button primary" disabled={auto === "running"} onClick={runAuto}>
                  <Icon name="scan" size={17} />
                  {auto === "running" ? "Тестируем стратегии…" : "Начать подбор для моего провайдера"}
                </button>
              </div>
              <div role="status">
                {auto === "running" && (
                  <p className="field-help">Выполняется последовательное тестирование пресетов. Это займет ~15 секунд...</p>
                )}
                {auto === "done" && (
                  <div className="detail-row bordered-row">
                    <div>
                      <h3>
                        {REAL_PRESETS.find(p => p.id === recommended)?.title || recommended}
                      </h3>
                      <p>Рекомендованная и самая быстрая стратегия для вашей сети.</p>
                    </div>
                    <button
                      className="button secondary"
                      onClick={() => changePreset(recommended)}
                      disabled={presetId === recommended}
                    >
                      {presetId === recommended ? "Уже активен" : "Применить"}
                    </button>
                  </div>
                )}
              </div>
            </section>
          )}

          {page === "sites" && (
            <section className="panel detail-panel">
              <CardHeading
                icon="globe"
                title="Домены (list-general-user.txt)"
                description="Пользовательский список доменов для выборочной разблокировки."
              />
              <form className="domain-form" onSubmit={addDomain}>
                <input
                  aria-label="Домен"
                  aria-invalid={!!domainError}
                  aria-describedby={domainError ? "domain-error" : undefined}
                  placeholder="example.com"
                  maxLength={253}
                  value={domain}
                  onChange={(event) => {
                    setDomain(event.target.value);
                    setDomainError("");
                  }}
                />
                <button className="button primary">
                  <Icon name="plus" size={17} />
                  Добавить
                </button>
              </form>
              {domainError && (
                <p className="field-help domain-error" id="domain-error">
                  {domainError}
                </p>
              )}
              <div className="detail-list">
                {domains.length === 0 && <p className="empty-state">Список доменов пуст.</p>}
                {domains.map((item) => (
                  <div className="detail-row" key={item}>
                    <h3 className="domain-name">{item}</h3>
                    <button
                      className="button secondary icon-button"
                      type="button"
                      aria-label={`Удалить ${item}`}
                      onClick={() => removeDomain(item)}
                    >
                      <Icon name="trash" size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}

          {page === "logs" && (
            <div className="dashboard">
              <section className="panel detail-panel">
                <CardHeading
                  icon="activity"
                  title="Диагностика сервисов"
                  description="Результаты проверки доступности основных ресурсов."
                />
                <div className="detail-actions">
                  <button
                    className="button secondary"
                    onClick={checkAvailability}
                    disabled={availability === "running"}
                  >
                    <Icon name="refresh" size={16} />
                    {availability === "running" ? "Проверка…" : "Проверить доступность"}
                  </button>
                </div>
                {availability === "done" && availabilityList.length > 0 && (
                  <ul className="service-results" aria-label="Результаты проверки">
                    {availabilityList.map((service) => (
                      <li key={service.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <Icon name={service.success ? "check" : "trash"} size={15} />
                          {service.name}
                        </span>
                        <span style={{ fontSize: 11, color: service.success ? "var(--green)" : "var(--accent)" }}>
                          {service.success ? `${service.latency_ms} ms` : service.error || "Блок"}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <section className="panel detail-panel">
                <div className="detail-toolbar">
                  <CardHeading
                    icon="terminal"
                    title="Журнал событий"
                    description="Логи вывода процесса winws.exe и системных действий."
                  />
                  <button
                    className="button secondary"
                    disabled={!logs.length}
                    onClick={async () => {
                      setLogs([]);
                      await Bridge.clearLogs();
                    }}
                  >
                    <Icon name="trash" size={16} />
                    Очистить
                  </button>
                </div>
                <div className="detail-list">
                  {logs.length ? (
                    <ul className="log-list">
                      {logs.map((entry) => (
                        <li key={entry.id}>
                          <time>{entry.time}</time>
                          <span>{entry.message}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="empty-state">В журнале пока нет событий.</p>
                  )}
                </div>
              </section>
            </div>
          )}
        </main>

        <footer className="statusbar">
          <span className="session-label">
            <i style={{ background: active ? "var(--green)" : "var(--accent)" }} />
            {active ? "Защита активна" : "Защита остановлена"}
            <span className="footer-divider" />
            WinDivert 1.4 · Все порты защищены
          </span>
          <span className="version-label">
            ZAPRET CONTROL <span>v1.10.2</span>
          </span>
        </footer>
      </div>
    </div>
  );
}
