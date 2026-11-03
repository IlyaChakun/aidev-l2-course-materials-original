-- Knowledge curator: 20 sources.
-- The same file is loaded into both SQLite and PostgreSQL.
--
-- Distribution by status: collected 7, rated 7, summarized 6.
-- score is the usefulness of the source. Edge cases: id 6 (score 0), id 15 (score 100).
-- For sources in the collected status the summary field is empty.
-- All links point to public documentation and specifications, checked on 02.08.2026.

INSERT INTO sources (id, title, url, kind, topic, summary, status, score, last_modified) VALUES
(1,  'PostgreSQL: Concurrency Control',
     'https://www.postgresql.org/docs/current/mvcc.html',
     'documentation', 'Базы данных',
     NULL, 'collected', 62, '2026-07-30 09:10:00'),

(2,  'Kafka Documentation',
     'https://kafka.apache.org/documentation/',
     'documentation', 'Очереди и потоки',
     NULL, 'collected', 55, '2026-07-30 11:25:00'),

(3,  'Kubernetes Concepts',
     'https://kubernetes.io/docs/concepts/',
     'documentation', 'Инфраструктура',
     NULL, 'collected', 48, '2026-07-30 14:40:00'),

(4,  'Docker: Build cache',
     'https://docs.docker.com/build/cache/',
     'documentation', 'Инфраструктура',
     NULL, 'collected', 51, '2026-07-31 08:55:00'),

(5,  'nginx: ngx_http_core_module',
     'https://nginx.org/en/docs/http/ngx_http_core_module.html',
     'reference', 'Сети',
     NULL, 'collected', 43, '2026-07-31 10:30:00'),

(6,  'Grafana Loki Documentation',
     'https://grafana.com/docs/loki/latest/',
     'documentation', 'Наблюдаемость',
     NULL, 'collected', 0, '2026-07-31 13:15:00'),

(7,  'Elastic Guide',
     'https://www.elastic.co/guide/index.html',
     'documentation', 'Поиск',
     NULL, 'collected', 39, '2026-08-01 09:45:00'),

(8,  'SQLite: Write-Ahead Logging',
     'https://www.sqlite.org/wal.html',
     'documentation', 'Базы данных',
     'Описывает режим журналирования, при котором читатели не блокируют писателя. Ключевое для практики: контрольная точка не происходит сама по себе при активных читателях, из-за чего файл журнала может расти неограниченно. Полезно как объяснение, почему встроенная база внезапно занимает больше места, чем сами данные.',
     'rated', 84, '2026-07-27 10:20:00'),

(9,  'RFC 9110: HTTP Semantics',
     'https://www.rfc-editor.org/rfc/rfc9110.html',
     'specification', 'Сети',
     'Сводит воедино семантику HTTP, ранее размазанную по нескольким документам. Практическая ценность в точных определениях идемпотентности и безопасности методов, а также в разборе условных запросов. Читается тяжело, но снимает большинство споров о том, что должен делать метод.',
     'rated', 91, '2026-07-27 15:35:00'),

(10, 'Python: asyncio',
     'https://docs.python.org/3/library/asyncio.html',
     'documentation', 'Языки и рантаймы',
     'Справочник по асинхронному вводу-выводу в стандартной библиотеке. Наиболее полезны разделы про группы задач и отмену: именно там сосредоточены ошибки, которые в продакшене выглядят как зависшие корутины и проглоченные исключения.',
     'rated', 76, '2026-07-28 09:50:00'),

(11, 'MDN: HTTP Caching',
     'https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching',
     'guide', 'Сети',
     'Практическое объяснение заголовков кеширования с примерами. Ценно тем, что разбирает разницу между хранением и переиспользованием ответа, а также типичные комбинации директив, которые дают не тот эффект, которого ждут.',
     'rated', 73, '2026-07-28 14:05:00'),

(12, 'OpenTelemetry Documentation',
     'https://opentelemetry.io/docs/',
     'documentation', 'Наблюдаемость',
     'Единый стандарт сбора трасс, метрик и логов. Полезно как точка отсчёта при выборе между вендорскими агентами: описывает модель данных и границы ответственности между инструментированием и бэкендом.',
     'rated', 69, '2026-07-29 11:30:00'),

(13, 'Prometheus: Metric and label naming',
     'https://prometheus.io/docs/practices/naming/',
     'guide', 'Наблюдаемость',
     'Короткий документ про именование метрик и меток. Ценность непропорциональна объёму: соблюдение этих правил определяет, можно ли будет строить агрегаты по метрике через год, а нарушения обходятся переписыванием дашбордов.',
     'rated', 66, '2026-07-29 16:15:00'),

(14, 'Git: git-bisect',
     'https://git-scm.com/docs/git-bisect',
     'reference', 'Инструменты разработки',
     'Справка по двоичному поиску коммита, вносящего регрессию. Практическая ценность в режиме с автоматическим скриптом проверки: превращает многочасовой ручной поиск в одну команду при наличии воспроизводимого теста.',
     'rated', 71, '2026-07-30 12:50:00'),

(15, 'RFC 6570: URI Template',
     'https://www.rfc-editor.org/rfc/rfc6570.html',
     'specification', 'Протоколы',
     'Определяет синтаксис шаблонов URI и правила подстановки. Прямо применимо там, где ресурсы адресуются шаблоном вида db://entity/{id}: документ описывает уровни выразительности шаблонов и правила экранирования, которые обычно реализуют интуитивно и неправильно.',
     'summarized', 100, '2026-07-22 10:00:00'),

(16, 'JSON-RPC 2.0 Specification',
     'https://www.jsonrpc.org/specification',
     'specification', 'Протоколы',
     'Спецификация помещается на одну страницу и описывает формат запроса, ответа, уведомления и пакетной отправки, а также стандартные коды ошибок. Практическая ценность в кодах: -32601 и -32602 различают отсутствующий метод и неверные параметры, и по ним диагностика делается быстрее, чем по тексту сообщения.',
     'summarized', 88, '2026-07-23 13:20:00'),

(17, 'RFC 7519: JSON Web Token',
     'https://www.rfc-editor.org/rfc/rfc7519.html',
     'specification', 'Безопасность',
     'Определяет формат токена и набор стандартных полей. Наиболее полезная часть — раздел про проверку: перечисляет, что именно обязан проверить получатель, включая алгоритм подписи. Большинство известных ошибок вокруг токенов сводятся к пропуску одного из этих пунктов.',
     'summarized', 94, '2026-07-24 09:40:00'),

(18, 'Redis: Develop',
     'https://redis.io/docs/latest/develop/',
     'documentation', 'Базы данных',
     'Раздел про работу с данными и структуры. Полезен разбор сценариев вытеснения и того, как выбранная политика меняет поведение под нехватку памяти: это то место, где хранилище кеша начинает вести себя не так, как ожидает приложение.',
     'summarized', 79, '2026-07-25 11:55:00'),

(19, 'ClickHouse: Introduction',
     'https://clickhouse.com/docs/en/intro',
     'documentation', 'Аналитика',
     'Вводный раздел про колоночное хранение и его следствия. Практическая ценность в честном описании того, для чего система не предназначена: точечные обновления и частые удаления остаются дорогими, и это определяет, где её ставить, а где нет.',
     'summarized', 82, '2026-07-26 15:10:00'),

(20, 'Model Context Protocol: Specification 2026-07-28',
     'https://modelcontextprotocol.io/specification/2026-07-28',
     'specification', 'Протоколы',
     'Действующая ревизия протокола. Ключевое изменение относительно предыдущих: протокол стал stateless, запросы самодостаточны, а согласование возможностей происходит на каждом запросе. Это меняет требования к серверу и делает устаревшей значительную часть ранее написанных материалов.',
     'summarized', 97, '2026-07-28 17:30:00');
