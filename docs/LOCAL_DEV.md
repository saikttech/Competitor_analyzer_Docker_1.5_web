# 🛠 Локальная разработка в VSCode

## Шаг 1: Подготовка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
# Вставьте ключи в .env