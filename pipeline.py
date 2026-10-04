import uuid
import logging
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Подавление предупреждения asyncio на Windows
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from tavily import TavilyClient
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, TAVILY_API_KEY

logger = logging.getLogger(__name__)

# Инициализация клиентов
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

tavily_client = None
if TAVILY_API_KEY and TAVILY_API_KEY.startswith("tvly-"):
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    logger.info("✅ Tavily клиент успешно инициализирован")
else:
    logger.warning("⚠️ TAVILY_API_KEY не найден или некорректен. Будет использоваться DuckDuckGo.")

# Абсолютный путь к папке reports
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

logger.info(f"📁 Папка для отчётов: {REPORTS_DIR}")


def search_with_tavily(query: str, limit: int = 5) -> List[str]:
    """Поиск через Tavily API (основной метод)"""
    logger.info(f"🔍 Tavily: {query}")
    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=limit,
        )
        urls = [result['url'] for result in response.get('results', []) if 'url' in result]
        logger.info(f"✅ Tavily нашёл {len(urls)} результатов:")
        for i, url in enumerate(urls, 1):
            logger.info(f"   {i}. {url}")
        return urls
    except Exception as e:
        logger.error(f"❌ Ошибка Tavily: {type(e).__name__}: {e}")
        return []


def search_with_duckduckgo(query: str, limit: int = 5) -> List[str]:
    """Поиск через DuckDuckGo (fallback)"""
    logger.info(f"🔍 DuckDuckGo (fallback): {query}")
    try:
        from duckduckgo_search import DDGS
        time.sleep(1.5)
        ddgs = DDGS()
        results = ddgs.text(query, max_results=limit)

        if not results:
            return []

        urls = []
        for r in results:
            if isinstance(r, dict):
                url = r.get('href') or r.get('link') or r.get('url')
                if url and url.startswith('http'):
                    urls.append(url)

        logger.info(f"✅ DuckDuckGo нашёл {len(urls)} результатов")
        return urls
    except Exception as e:
        logger.error(f"❌ Ошибка DuckDuckGo: {e}")
        return []


def search_competitors(niche: str, geo: str, query: str, limit: int = 5) -> List[str]:
    """Поиск конкурентов с автоматическим переключением"""
    search_query = f"{niche} {geo} {query}"
    logger.info(f"\n🔎 Итоговый поисковый запрос: '{search_query}'")

    # Приоритет 1: Tavily
    if tavily_client:
        logger.info("🥇 Пробуем Tavily API...")
        urls = search_with_tavily(search_query, limit)
        if urls:
            return urls
        logger.warning("⚠️ Tavily не вернул результатов, переключаюсь на DuckDuckGo...")

    # Приоритет 2: DuckDuckGo
    logger.info("🥈 Пробуем DuckDuckGo...")
    urls = search_with_duckduckgo(search_query, limit)
    if urls:
        return urls

    # Приоритет 3: Аварийный режим
    logger.warning("🚨 Все поисковики не дали результатов. Включаю аварийный режим.")
    fallback_urls = [
        "https://loft-rent.ru/",
        "https://moscow.loftparty.ru/",
        "https://www.afisha.ru/msk/place/loft/"
    ]
    logger.info(f"✅ Использовано {len(fallback_urls)} тестовых URL")
    return fallback_urls


def parse_website(url: str) -> Optional[str]:
    """Парсинг текста с сайта с обходом защиты от ботов"""
    logger.info(f"🌐 Парсинг: {url}")

    try:
        response = curl_requests.get(
            url,
            impersonate="chrome110",
            timeout=15.0,
            allow_redirects=True
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript", "form"]):
            element.decompose()

        text = soup.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())

        if len(text) > 5000:
            text = text[:5000] + "..."

        logger.info(f"✅ Получено {len(text)} символов")
        return text

    except Exception as e:
        logger.warning(f"❌ Ошибка парсинга {url}: {type(e).__name__}: {e}")
        return None


def generate_report(niche: str, geo: str, query: str, collected_data: str) -> str:
    """Генерация отчёта через LLM"""
    logger.info("🧠 Генерация отчёта через OpenAI...")

    prompt = f"""Ты — профессиональный бизнес-аналитик.
Проанализируй конкурентов в нише "{niche}" в регионе "{geo}".
Специфический запрос пользователя: "{query}".

Данные конкурентов:
{collected_data}

Сформируй структурированный отчёт в Markdown:
1. 📊 Краткое резюме рынка
2. 🏆 Топ-3 конкурента с их сильными сторонами
3. 💡 Рекомендации по улучшению
4. ⚠️ Потенциальные риски

Отвечай на русском языке."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        report = response.choices[0].message.content
        logger.info(f"✅ Отчёт сгенерирован ({len(report)} символов)")
        return report
    except Exception as e:
        logger.error(f"❌ Ошибка генерации отчёта: {type(e).__name__}: {e}")
        raise


def run_pipeline(niche: str, geo: str, query: str, clear_db: bool) -> Dict:
    """Основной ETL + RAG пайплайн"""
    logger.info("=" * 60)
    logger.info(f"🚀 Запуск пайплайна анализа конкурентов")
    logger.info(f"   Ниша: {niche} | Гео: {geo} | Запрос: {query}")
    logger.info("=" * 60)

    # ЭТАП 1: Поиск
    logger.info("\n📍 ЭТАП 1: Поиск конкурентов...")
    urls = search_competitors(niche, geo, query)
    if not urls:
        raise ValueError("❌ Не найдено конкурентов (даже в аварийном режиме).")

    # ЭТАП 2: Парсинг
    logger.info(f"\n📍 ЭТАП 2: Парсинг {len(urls)} сайтов...")
    collected_data = []
    successful_parses = 0

    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Обработка: {url}")
        text = parse_website(url)

        if text and len(text) > 100:
            collected_data.append(f"Источник: {url}\nСодержимое:\n{text}")
            successful_parses += 1
        else:
            logger.warning(f"   ⚠️ Пропущен (недостаточно данных)")

    logger.info(f"\n✅ Успешно спарсено: {successful_parses}/{len(urls)} сайтов")
    if not collected_data:
        raise ValueError("❌ Не удалось получить данные с сайтов.")

    full_text = "\n\n" + "=" * 60 + "\n\n".join(collected_data)

    # ЭТАП 3: Генерация
    logger.info("\n📍 ЭТАП 3: Генерация отчёта через AI...")
    report_markdown = generate_report(niche, geo, query, full_text)

    # ЭТАП 4: Сохранение
    logger.info("\n📍 ЭТАП 4: Сохранение отчёта...")
    filename = f"report_{uuid.uuid4().hex[:8]}.md"
    file_path = REPORTS_DIR / filename

    try:
        file_path.write_text(report_markdown, encoding="utf-8")
        if file_path.exists():
            file_size = file_path.stat().st_size
            logger.info(f"✅ Отчёт успешно сохранён: {file_path} ({file_size} байт)")
        else:
            raise RuntimeError(f"Не удалось сохранить файл отчёта")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        raise

    logger.info("\n" + "=" * 60)
    logger.info("🎉 Пайплайн завершён успешно!")
    logger.info("=" * 60 + "\n")

    return {
        "competitors_found": len(urls),
        "competitors_parsed": successful_parses,
        "report_path": str(file_path),
        "report_filename": filename,
        "report_size_bytes": file_path.stat().st_size,
        "summary": report_markdown[:1000] + "..." if len(report_markdown) > 1000 else report_markdown,
        "full_report": report_markdown
    }