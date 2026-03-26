from logger.logger import logger
from wb_handler.wb_handler import (
    get_idx,
    get_info_from_card,
    get_info_from_idx_json,
    get_hosts,
    create_url_card,
)
from wb_parser.wb_parser import (
    parse_cards,
    parse_hosts,
    parse_good_ids,
)
from db.db import (
    init_db,
    load_initial_data,
    update_by_id,
    export_to_excel,
)

from config.config import (
    JSON_PATH,
    XLSX_PATH,
    IDX_JSON,
    HOSTS_JSON,
    XLSX_FILE,
)


if __name__ == "__main__":
    JSON_PATH.mkdir(parents=True, exist_ok=True)
    XLSX_PATH.mkdir(parents=True, exist_ok=True)

    # Парсинг сырых данных и сохранение в json
    logger.info("parse")
    parse_good_ids(
        query="пальто из натуральной шерсти", file_name_json=IDX_JSON, max_pages=5
    )
    parse_hosts(file_name_json=HOSTS_JSON)

    # Получение данных из json
    logger.info("handler get_idx get_hosts")
    idx_list = get_idx(json_file_path=IDX_JSON)
    hosts_list = get_hosts(json_file_path=HOSTS_JSON)

    logger.info("handler get_info")
    info_from_idx = get_info_from_idx_json(idx_json_file=IDX_JSON)

    # Подключение к БД
    logger.info("db init")
    init_db()

    # Добавление данных с парсига в БД
    logger.info("load_initial_data")
    load_initial_data(info_from_idx=info_from_idx)

    cards_urls = create_url_card(idx_list=idx_list, hosts_list=hosts_list)

    parsed_cards = parse_cards(cards_urls=cards_urls)

    for nm_id, card_data in get_info_from_card(
        parser_card=parsed_cards, hosts_list=hosts_list
    ):
        update_by_id(nm_id, card_data)
        logger.info(f"Save: {nm_id}")

    # Экспорт в excel
    export_to_excel(XLSX_FILE)
