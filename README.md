
# 🚀 RAG Competitor Analyzer v1.5

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B?logo=streamlit)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?logo=celery)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%20%2B%20pgvector-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

**Автоматизированный ETL + RAG пайплайн** для глубокого анализа конкурентов с современным веб-интерфейсом и экспортом профессиональных отчетов в PDF (с полной поддержкой кириллицы).

[📚 Документация](#-использование) • [🐛 Сообщить о баге](https://github.com/your-username/Competitor-Analyzer-MAX/issues) • [💡 Идеи](https://github.com/your-username/Competitor-Analyzer-MAX/discussions)

</div>

---

## 📖 О проекте

Система **самостоятельно** находит компании-конкуренты в интернете, парсит тексты их сайтов (с обходом базовой защиты от ботов), очищает данные от SEO-спама и генерирует **структурированный аналитический отчет** в форматах Markdown и PDF на основе пользовательского запроса с помощью LLM.

### ✨ Ключевые возможности

- 💻 **Современный Web UI** на Streamlit с отображением прогресса выполнения в реальном времени.
- 📄 **Экспорт в PDF** с профессиональной версткой и **100% поддержкой кириллицы** (кроссплатформенно: Windows, macOS, Linux, Docker).
- 🔄 **Асинхронная обработка** через Celery + Redis (исключает таймауты при долгих запросах).
- 🔍 **Каскадный умный поиск**: Tavily API → DuckDuckGo (с экспоненциальной задержкой при Rate Limit) → Fallback URL.
- 🛡️ **Обход защиты сайтов** через `curl-cffi` (имитация TLS-отпечатка реального браузера Chrome).
- 🌍 **Работа в РФ** без VPN через совместимые прокси (ProxyAPI, OpenRouter).
- 🐳 **Гибкий запуск**: полная контейнеризация через Docker Compose или удобная локальная отладка в VS Code.

---

## 🏗 Архитектура

```mermaid
graph TD
    A[👤 Пользователь] --> B[Streamlit Web UI :8501]
    B -->|1. HTTP POST /analyze| C[FastAPI Server :8000]
    C -->|2. Ставит задачу| D[(Redis Queue)]
    C -->|3. Возвращает task_id| B
    D -->|4. Забирает задачу| E[Celery Worker]
    E -->|5. Поиск| F[Tavily API / DuckDuckGo]
    E -->|6. Парсинг| G[Сайты конкурентов через curl-cffi]
    E -->|7. RAG + LLM| H[OpenAI / ProxyAPI]
    E -->|8. Генерация и сохранение| I[./reports/*.md]
    I -->|9. Конвертация| J[PDF через xhtml2pdf + DejaVu Fonts]
    B -->|10. Polling статуса| C
```

---

## 🛠 Стек технологий

| Категория | Технологии |
|-----------|------------|
| **Frontend** | Streamlit 1.31, Markdown, xhtml2pdf |
| **Backend API** | FastAPI 0.109, Uvicorn, Pydantic 2.6 |
| **Очередь задач** | Celery 5.3, Redis 7 |
| **База данных** | PostgreSQL 15 + `pgvector` + `pg_trgm`, SQLAlchemy 2.0 |
| **Парсинг** | `curl-cffi` (обход Cloudflare), `beautifulsoup4` |
| **Поиск** | Tavily Search API, DuckDuckGo Search |
| **AI / LLM** | OpenAI API (`gpt-3.5-turbo`) через ProxyAPI / OpenRouter |
| **Инфраструктура** | Docker, Docker Compose, VS Code Debugger |

---

## 🚀 Быстрый старт (Локальная разработка)

Этот режим рекомендуется для разработки, так как позволяет использовать breakpoints и hot-reload в VS Code.

### 1. Требования
- Python **3.11** или **3.12**
- Docker Desktop (для запуска PostgreSQL и Redis)
- API-ключи: OpenAI (или ProxyAPI/OpenRouter) и Tavily (опционально, но рекомендуется)

### 2. Установка
```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/Competitor-Analyzer-MAX.git
cd Competitor-Analyzer-MAX

# Создайте виртуальное окружение (ВАЖНО: Python 3.11 или 3.12)
python -m venv .venv
source .venv/bin/activate  # Для Windows: .venv\Scripts\activate

# Обновите pip и установите зависимости
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Настройка окружения
```bash
cp .env.example .env
```
Откройте `.env` и вставьте ваши ключи:
```env
OPENAI_API_KEY=sk-ваш_ключ
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1  # Или https://openrouter.ai/api/v1
TAVILY_API_KEY=tvly-ваш_ключ  # Получите бесплатно на app.tavily.com
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/competitors_db
REDIS_URL=redis://localhost:6379/0
API_BASE_URL=http://localhost:8000
```

### 4. Запуск инфраструктуры (Docker)
Запускаем только базу данных и очередь сообщений:
```bash
docker compose up db redis -d
```

### 5. Запуск приложения в VS Code
Откройте панель **Run and Debug** (`Ctrl+Shift+D`) и по очереди запустите:
1. ▶️ **Python: FastAPI**
2. ▶️ **Python: Celery Worker**
3. ▶️ **Python: Streamlit**

---

## 📄 Важное примечание по экспорту в PDF

Для корректного отображения **русского языка (кириллицы)** в PDF-отчетах на любой операционной системе, в проекте используется шрифт *DejaVu Sans*.

1. Скачайте архив шрифтов: [DejaVu Fonts TTF](https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip)
2. Распакуйте его.
3. Скопируйте два файла из папки `ttf` в папку `fonts/` в корне вашего проекта:
   - `DejaVuSans.ttf`
   - `DejaVuSans-Bold.ttf`

*Без этих файлов PDF будет генерироваться с квадратиками (■■■■) вместо русских букв.*

---

## 📡 Использование

### Через Web UI
1. Откройте в браузере: **http://localhost:8501**
2. Заполните форму (например: *Ниша: кофейни, Гео: Москва, Запрос: спешелти кофе с веганскими десертами*).
3. Нажмите **🚀 Запустить анализ**.
4. После завершения нажмите **📄 Скачать PDF (.pdf)** для получения красиво отформатированного документа формата A4.

### Через REST API
```bash
# 1. Запуск задачи
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer sk-test-123" \
  -H "Content-Type: application/json" \
  -d '{"niche":"кофейни","geo":"Москва","query":"спешелти","clear_db":false}'

# 2. Проверка статуса (замените {task_id} на полученный ID)
curl http://localhost:8000/analyze/{task_id} \
  -H "Authorization: Bearer sk-test-123"
```

---

## 🐛 Решение типичных проблем

<details>
<summary><b>❌ SSL: CERTIFICATE_VERIFY_FAILED при pip install</b></summary>
Корпоративный антивирус или прокси подменяет SSL-сертификаты. Решение:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```
</details>

<details>
<summary><b>❌ В PDF вместо текста квадратики (■■■■)</b></summary>
Убедитесь, что файлы <code>DejaVuSans.ttf</code> и <code>DejaVuSans-Bold.ttf</code> лежат в папке <code>fonts/</code> в корне проекта. Перезапустите Streamlit после их добавления.
</details>

<details>
<summary><b>❌ OpenAI возвращает ошибку 403 (unsupported_country_region_territory)</b></summary>
Официальный API OpenAI блокирует запросы из РФ. Используйте прокси-сервисы, полностью совместимые с API OpenAI:
- <b>ProxyAPI</b>: <code>https://api.proxyapi.ru/openai/v1</code>
- <b>OpenRouter</b>: <code>https://openrouter.ai/api/v1</code>
</details>

<details>
<summary><b>❌ DuckDuckGo возвращает Ratelimit</b></summary>
Система автоматически переключится на Tavily API или аварийные URL. Для стабильной работы настоятельно рекомендуется получить бесплатный ключ на <a href="https://app.tavily.com/">app.tavily.com</a>.
</details>

---

## 🔮 Roadmap (v1.6+)

- [ ] 💾 **История запросов в БД**: вывод списка прошлых анализов с ссылками на файлы прямо в Sidebar Streamlit.
- [ ] 🧠 **Cross-Encoder Reranker**: улучшение точности RAG-выдачи перед отправкой в LLM.
- [ ] 🎭 **Playwright**: парсинг сложных сайтов с тяжелым JavaScript (SPA).
- [ ] 📊 **Langfuse**: мониторинг стоимости токенов и задержек LLM-запросов.
- [ ] 📧 **Email-отчеты**: автоматическая отправка сгенерированного PDF на почту по завершении задачи.

---

## 🤝 Вклад в проект

Pull Request'ы приветствуются! 🎉 Для серьезных изменений, пожалуйста, сначала откройте **Issue**, чтобы мы могли обсудить идею.

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

---

## 📄 Лицензия

Проект распространяется под лицензией **MIT**. См. файл [LICENSE](LICENSE) для подробностей.

---

<div align="center">

**⭐ Если проект оказался полезным — поставьте звезду на GitHub!**

Сделано с ❤️ для русскоязычного AI-сообщества

</div>
```
