import streamlit as st
import requests
import time
import os
import io
from pathlib import Path
import markdown
from xhtml2pdf import pisa

# Импорты для принудительной подмены шрифтов в xhtml2pdf
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xhtml2pdf.default import DEFAULT_FONT

# --- Конфигурация ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "sk-test-123")

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
FONTS_DIR = Path(__file__).parent / "fonts"
FONTS_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Competitor Analyzer v1.5",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State ---
if 'task_id' not in st.session_state:
    st.session_state.task_id = None
if 'result' not in st.session_state:
    st.session_state.result = None

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def start_analysis(niche: str, geo: str, query: str, clear_db: bool):
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json={"niche": niche, "geo": geo, "query": query, "clear_db": clear_db},
            headers=HEADERS,
            timeout=60
        )
        if response.status_code == 200:
            return True, response.json()['task_id'], "✅ Задача успешно отправлена в очередь!"
        return False, None, f"❌ Ошибка API ({response.status_code}): {response.text}"
    except Exception as e:
        return False, None, f"❌ Ошибка: {str(e)}"


def check_status(task_id: str):
    try:
        response = requests.get(f"{API_BASE_URL}/analyze/{task_id}", headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def convert_md_to_pdf(markdown_text: str) -> bytes:
    """Конвертирует Markdown в PDF с ГАРАНТИРОВАННОЙ поддержкой кириллицы"""
    try:
        font_regular_path = FONTS_DIR / "DejaVuSans.ttf"
        font_bold_path = FONTS_DIR / "DejaVuSans-Bold.ttf"

        # 1. Проверка наличия файлов
        if not font_regular_path.exists():
            st.error(f"❌ Файл не найден: {font_regular_path.name}")
            return None
        if not font_bold_path.exists():
            st.error(f"❌ Файл не найден: {font_bold_path.name}")
            return None

        # 2. 🚀 КЛЮЧЕВОЙ ШАГ: Регистрация и ПОДМЕНА шрифтов по умолчанию
        # Это заставляет xhtml2pdf использовать наш шрифт вместо Helvetica везде
        pdfmetrics.registerFont(TTFont('DejaVu', str(font_regular_path)))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', str(font_bold_path)))
        
        DEFAULT_FONT['helvetica'] = 'DejaVu'
        DEFAULT_FONT['helvetica-bold'] = 'DejaVu-Bold'
        DEFAULT_FONT['helvetica-oblique'] = 'DejaVu'
        DEFAULT_FONT['helvetica-boldoblique'] = 'DejaVu-Bold'

        # 3. Конвертация Markdown в HTML
        html_content = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])

        # 4. CSS (теперь мы можем смело использовать helvetica, т.к. мы его подменили, или явно DejaVu)
        css_style = """
        @page { size: A4; margin: 2cm; }
        body { font-family: 'DejaVu', sans-serif; font-size: 11pt; color: #000000; }
        h1 { font-family: 'DejaVu-Bold', sans-serif; font-size: 18pt; border-bottom: 1px solid #000000; padding-bottom: 5pt; margin-top: 15pt; }
        h2 { font-family: 'DejaVu-Bold', sans-serif; font-size: 14pt; margin-top: 12pt; }
        h3 { font-family: 'DejaVu-Bold', sans-serif; font-size: 12pt; }
        p { font-family: 'DejaVu', sans-serif; margin-bottom: 10pt; }
        ul, ol { font-family: 'DejaVu', sans-serif; margin-bottom: 10pt; }
        li { font-family: 'DejaVu', sans-serif; margin-bottom: 5pt; }
        strong, b { font-family: 'DejaVu-Bold', sans-serif; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 10pt; }
        th, td { border: 1px solid #000000; padding: 5pt; font-family: 'DejaVu', sans-serif; }
        th { font-family: 'DejaVu-Bold', sans-serif; background-color: #f0f0f0; }
        """

        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>{css_style}</style>
</head>
<body>
    {html_content}
</body>
</html>"""

        # 5. Генерация PDF
        pdf_buffer = io.BytesIO()
        pdf = pisa.pisaDocument(
            io.StringIO(full_html),
            pdf_buffer,
            encoding='utf-8'
        )

        if pdf.err:
            st.error(f"❌ Ошибка рендеринга PDF: {pdf.err}")
            return None

        return pdf_buffer.getvalue()

    except Exception as e:
        st.error(f"❌ Критическая ошибка: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None


# --- UI ---
st.title("🔍 Competitor Analyzer v1.5")
st.markdown("*Автоматический RAG-анализ конкурентов с экспортом в PDF*")

with st.sidebar:
    st.header("⚙️ Настройки")
    st.text_input("API Base URL", value=API_BASE_URL, disabled=True)
    
    st.markdown("---")
    st.subheader("🔧 Диагностика шрифтов")
    st.write(f"**Путь:** `{FONTS_DIR}`")
    
    if FONTS_DIR.exists():
        files_in_fonts = list(FONTS_DIR.glob("*.ttf"))
        if files_in_fonts:
            st.success("✅ Шрифты найдены!")
            for f in files_in_fonts:
                size_kb = f.stat().st_size / 1024
                st.caption(f"📄 {f.name} ({size_kb:.1f} KB)")
        else:
            st.warning("⚠️ Папка `fonts` не содержит файлов .ttf")
    else:
        st.error("❌ Папка `fonts` не существует")

    st.markdown("---")
    st.subheader("🔧 API")
    if st.button("🏥 Проверить API", use_container_width=True):
        try:
            health = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if health.status_code == 200:
                st.success("✅ API доступен")
            else:
                st.error(f"❌ Статус: {health.status_code}")
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

# Основная форма
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    niche = st.text_input("🎯 Ниша", value="кофейни")
    geo = st.text_input("📍 География", value="Москва")

with col2:
    query = st.text_area("🔎 Детальный запрос", value="спешелти кофе с веганскими десертами", height=110)
    clear_db = st.checkbox("🗑️ Очистить БД", value=False)

if st.button("🚀 Запустить анализ", type="primary", use_container_width=True):
    if not niche or not geo or not query:
        st.error("Заполните все поля!")
    else:
        with st.spinner("Отправка задачи..."):
            success, task_id, message = start_analysis(niche, geo, query, clear_db)
            if success:
                st.session_state.task_id = task_id
                st.session_state.result = None
                st.success(message)
                st.rerun()
            else:
                st.error(message)

# Мониторинг
if st.session_state.task_id:
    st.markdown("---")
    st.subheader(f"📈 Статус: `{st.session_state.task_id}`")

    status_data = check_status(st.session_state.task_id)

    if status_data:
        current_status = status_data.get('status')

        if current_status in ["PENDING", "STARTED"]:
            meta = status_data.get('meta', {})
            stage = meta.get('stage', 'Обработка...')
            with st.status(stage, expanded=True):
                st.write(f"**Этап:** {stage}")
                st.progress(0.5)
                time.sleep(2)
                st.rerun()

        elif current_status == "SUCCESS":
            st.success("✅ Анализ завершён!")
            result = status_data.get('result', {})

            if isinstance(result, dict) and 'data' in result:
                data = result['data']
                if isinstance(data, dict) and 'report_path' in data:
                    filename = Path(data['report_path']).name
                    local_file_path = REPORTS_DIR / filename

                    if local_file_path.exists():
                        report_content = local_file_path.read_text(encoding='utf-8')

                        st.markdown("### 📄 Сгенерированный отчёт")
                        st.markdown(report_content)

                        st.markdown("---")
                        st.markdown("#### 💾 Скачать отчёт")
                        col_btn1, col_btn2 = st.columns(2)

                        with col_btn1:
                            st.download_button(
                                label="📝 Скачать Markdown (.md)",
                                data=report_content,
                                file_name=filename,
                                mime="text/markdown",
                                use_container_width=True
                            )

                        with col_btn2:
                            with st.spinner("🎨 Формирование PDF..."):
                                pdf_bytes = convert_md_to_pdf(report_content)
                                if pdf_bytes:
                                    pdf_filename = filename.replace('.md', '.pdf')
                                    st.download_button(
                                        label="📄 Скачать PDF (.pdf)",
                                        data=pdf_bytes,
                                        file_name=pdf_filename,
                                        mime="application/pdf",
                                        use_container_width=True,
                                        type="secondary"
                                    )
                                else:
                                    st.error("Не удалось создать PDF")
                    else:
                        st.warning(f"⚠️ Файл не найден: `{local_file_path}`")

            if st.button("🔄 Новый анализ", use_container_width=True):
                st.session_state.task_id = None
                st.rerun()

        elif current_status == "FAILURE":
            st.error(f"❌ Ошибка: {status_data.get('error')}")
            if st.button("🔄 Попробовать снова"):
                st.session_state.task_id = None
                st.rerun()