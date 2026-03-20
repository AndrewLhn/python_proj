# GitHub Data Extraction Project

## 📊 Описание проекта
Проект для извлечения данных из GitHub API с последующим сохранением и анализом.

## ✅ Что умеет делать:
- Извлекает данные о репозиториях (звезды, форки, описание и т.д.)
- Получает список контрибьюторов
- Проверяет качество данных
- Сохраняет в JSON, CSV и HTML форматах
- Создает интерактивный дашборд

## 🚀 Использование

### Запуск основного скрипта:
```bash
python src/extract_github_data.py

python view_results.py
Экспорт в CSV:
python export_to_csv.py
Создание дашборда: python create_dashboard.py

Структура проекта
.
├── src/
│   ├── extract_github_data.py    # Основной скрипт
│   └── utils/
│       ├── s3_uploader.py         # Загрузка данных
│       └── data_validator.py      # Валидация
├── output/                         # Результаты
├── logs/                          # Логи
└── config/                        # Конфигурация
Для использования GitHub API с высоким лимитом: export GITHUB_TOKEN="your_token_here"
📝 Лицензия
MIT
