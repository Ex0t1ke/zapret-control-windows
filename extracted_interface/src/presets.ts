export interface Preset {
  id: string;
  name: string;
  title: string;
  description: string;
  category: string;
}

export const REAL_PRESETS: Preset[] = [
  {
    id: "general",
    name: "General (Стандарт)",
    title: "General (Стандарт)",
    description: "Базовая стратегия. Multisplit + Fake TLS (Google/4PDA) + Discord RTC. Подходит для большинства сетей.",
    category: "Рекомендуемые"
  },
  {
    id: "general (ALT)",
    name: "General ALT 1",
    title: "General ALT 1",
    description: "Альтернативная нарезка пакетов и Fake TLS. Отлично работает на Дом.ру, ТТК и Ростелеком Юг/Урал.",
    category: "Рекомендуемые"
  },
  {
    id: "general (ALT2)",
    name: "General ALT 2",
    title: "General ALT 2",
    description: "Увеличенный split-pos и авто-TTL. Рекомендуется для Ростелеком Волга и Северо-Запад.",
    category: "Рекомендуемые"
  },
  {
    id: "general (ALT3)",
    name: "General ALT 3",
    title: "General ALT 3",
    description: "Агрессивный desync для сложных ТСПУ со сбросом TCP RST.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT4)",
    name: "General ALT 4",
    title: "General ALT 4",
    description: "Оптимизация под видеопотоки googlevideo с обходом блокировки по SNI.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT5)",
    name: "General ALT 5",
    title: "General ALT 5",
    description: "Облегченный режим для медленных соединений и слабых роутеров.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT6)",
    name: "General ALT 6",
    title: "General ALT 6",
    description: "Вариант со сплитом в 1 байт и модифицированным TCP Window.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT7)",
    name: "General ALT 7",
    title: "General ALT 7",
    description: "Подмена контрольных сумм и fake-sni для подавления эвристического анализа.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT8)",
    name: "General ALT 8",
    title: "General ALT 8",
    description: "Специфический профиль для провайдеров с глубоким разбором QUIC.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT9)",
    name: "General ALT 9",
    title: "General ALT 9",
    description: "Комбинированный метод с разделением ClientHello на 3 сегмента.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT10)",
    name: "General ALT 10",
    title: "General ALT 10",
    description: "Профиль с защитой от TCP freeze (зависание видео на 16-20 КБ).",
    category: "Альтернативные"
  },
  {
    id: "general (ALT11)",
    name: "General ALT 11",
    title: "General ALT 11",
    description: "Расширенный профиль для максимальной совместимости с Discord Voice.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT12)",
    name: "General ALT 12",
    title: "General ALT 12",
    description: "Новая модификация сплита и фейк-пакетов под осенние сигнатуры ТСПУ.",
    category: "Альтернативные"
  },
  {
    id: "general (ALT13)",
    name: "General ALT 13",
    title: "General ALT 13",
    description: "Усиленный desync против свежих фильтров РКН.",
    category: "Альтернативные"
  },
  {
    id: "general (FAKE TLS AUTO)",
    name: "Fake TLS Auto",
    title: "Fake TLS Auto",
    description: "Автоматическая генерация фейкового TLS ClientHello. Подходит для мобильных провайдеров.",
    category: "Fake TLS"
  },
  {
    id: "general (FAKE TLS AUTO ALT)",
    name: "Fake TLS Auto ALT",
    title: "Fake TLS Auto ALT",
    description: "Fake TLS с другим порядком отправки пакетов.",
    category: "Fake TLS"
  },
  {
    id: "general (FAKE TLS AUTO ALT2)",
    name: "Fake TLS Auto ALT 2",
    title: "Fake TLS Auto ALT 2",
    description: "Fake TLS со смешанными autottl параметрами.",
    category: "Fake TLS"
  },
  {
    id: "general (FAKE TLS AUTO ALT3)",
    name: "Fake TLS Auto ALT 3",
    title: "Fake TLS Auto ALT 3",
    description: "Fake TLS со строгой проверкой контрольных сумм.",
    category: "Fake TLS"
  },
  {
    id: "general (SIMPLE FAKE)",
    name: "Simple Fake",
    title: "Simple Fake",
    description: "Простой фейковый desync без глубокой сегментации. Минимальная задержка.",
    category: "Simple Fake"
  },
  {
    id: "general (SIMPLE FAKE ALT)",
    name: "Simple Fake ALT",
    title: "Simple Fake ALT",
    description: "Simple Fake с альтернативным TTL.",
    category: "Simple Fake"
  },
  {
    id: "general (SIMPLE FAKE ALT2)",
    name: "Simple Fake ALT 2",
    title: "Simple Fake ALT 2",
    description: "Simple Fake с повторами фейковых пакетов.",
    category: "Simple Fake"
  },
  {
    id: "general (EXP)",
    name: "Experimental (EXP)",
    title: "Experimental (EXP)",
    description: "Экспериментальные параметры обхода для тестирования новых методов.",
    category: "Экспериментальные"
  }
];
