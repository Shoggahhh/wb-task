import json
import time
from typing import Any
from collections.abc import Iterator
from urllib.parse import urlencode

import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from pathlib import Path
from logger.logger import logger


# "пальто из натуральной шерсти"


def parse_content(url: str, page, headers: dict[str, Any] = None) -> str:
    page.set_extra_http_headers(headers=headers)
    page.goto(url)
    page.wait_for_timeout(5000)
    content = page.content()
    return content


def parse_good_ids(query: str, file_name_json: Path, max_pages: int = 3) -> None:
    search_url_template = (
        "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search"
    )

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru-RU,ru;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    base_params = {
        "ab_testid": False,
        "appType": 1,
        "curr": "rub",
        "dest": -1257786,
        "hide_vflags": 4294967296,
        "inheritFilters": False,
        "lang": "ru",
        "query": query,
        "resultset": "catalog",
        "sort": "popular",
        "spp": 30,
        "suppressSpellcheck": False,
    }

    all_products = []
    seen_ids = set()

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers(headers=headers)

        for page_num in range(1, max_pages + 1):
            logger.info(f"Parsing page: {page_num}/{max_pages}")

            base_params["page"] = page_num
            query_params = urlencode(base_params)
            search_url = f"{search_url_template}?{query_params}"

            try:
                content = parse_content(url=search_url, page=page, headers=headers)

                json_data = content.split('pre-wrap;">')[1].split("</pre>")[0]
                json_data = json.loads(json_data)

                products = json_data.get("products", [])

                if not products:
                    break

                for product in products:
                    product_id = product.get("id")
                    if product_id and product_id not in seen_ids:
                        seen_ids.add(product_id)
                        all_products.append(product)

                if page_num < max_pages:
                    time.sleep(2)

            except Exception as e:
                logger.error(f"Error from page {page_num}: {e}")
                break

        browser.close()

    result_data = {
        "products": all_products,
        "total_pages": len(all_products) // 100 + 1,
    }

    with open(file_name_json, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=4)


def parse_hosts(file_name_json: Path) -> None:
    stream_url = "https://cdn.wbbasket.ru/api/v3/upstreams"

    response = requests.get(stream_url)
    json_data = response.json()

    with open(file_name_json, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)


def parse_cards(cards_urls: list) -> Iterator[dict[str, Any]]:
    for url in cards_urls:
        logger.info(url)
        try:
            response = requests.get(url=url, timeout=5)
            response.raise_for_status()
            card_data = response.json()
            yield card_data
        except requests.exceptions.Timeout:
            logger.error(f"Timeout: {url}")
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            continue
