# Parser WB
- uv install
- run main

## Architecture
### Parsing
- Поиск: Playwright (1 сессия, т.к. эндпоинт требует браузерные заголовки [parse_good_ids](https://github.com/Shoggahhh/wb-task/blob/0b060a91c313bea8fa8fccf6471f42b223ced8bc/wb_parser/wb_parser.py#L22))
- Сбор cdn-hosts: requests (Для генерации ссылок, прямые запросы [parse_hosts](https://github.com/Shoggahhh/wb-task/blob/0b060a91c313bea8fa8fccf6471f42b223ced8bc/wb_parser/wb_parser.py#L98))
- Карточки: requests (прямые запросы к внутреннему API [parse_cards](https://github.com/Shoggahhh/wb-task/blob/0b060a91c313bea8fa8fccf6471f42b223ced8bc/wb_parser/wb_parser.py#L108))
- Хранение: SQLite с merge для надёжности
- Экспорт: pandas → Excel

### Handler
- Обработчики полученной data