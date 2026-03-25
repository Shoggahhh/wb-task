import json
from typing import Any
from pathlib import Path
from collections.abc import Iterator

from logger.logger import logger


def get_idx(json_file_path: Path) -> list:
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_file_path}: {e}")
        return []

    idx_lst = []
    for idx in json_data["products"]:
        idx_lst.append(idx.get("id"))

    return idx_lst


def get_hosts(json_file_path: Path) -> list:
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            hosts_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_file_path}: {e}")
        return []

    hosts_list = (
        hosts_data.get("origin", {}).get("mediabasket_route_map", [])[0].get("hosts")
    )

    return hosts_list


def create_url_card(idx_list: list, hosts_list: list) -> list:
    if not idx_list or not hosts_list:
        return []

    card_lst = []
    for idx in idx_list:
        idx_str = str(idx)
        vol = f"vol{idx_str[:4]}"
        part = f"part{idx_str[:6]}"
        short_idx = int(idx_str[:4])

        for host_config in hosts_list:
            range_from = host_config.get("vol_range_from")
            range_to = host_config.get("vol_range_to")
            host = host_config.get("host")

            if range_from <= short_idx <= range_to:
                card_url = f"https://{host}/{vol}/{part}/{idx}/info/ru/card.json"
                card_lst.append(card_url)
    return card_lst


def create_photo_url(id_nm: int, id_img: int, host_list: list) -> str:
    photo_url = ""
    str_id_nm = str(id_nm)
    vol = f"vol{str_id_nm[:4]}"
    part = f"part{str_id_nm[:6]}"
    short_idx = int(str_id_nm[:4])

    for host_config in host_list:
        range_from = host_config.get("vol_range_from")
        range_to = host_config.get("vol_range_to")
        host = host_config.get("host")

        if range_from <= short_idx <= range_to:
            photo_url = f"https://{host}/{vol}/{part}/{id_nm}/images/big/{id_img}.webp"
    return photo_url


def get_info_from_card(
    parser_card: Iterator[dict], hosts_list: list
) -> Iterator[tuple[str, Any]]:
    for card in parser_card:
        nm_id = card.get("nm_id")

        if not nm_id:
            logger(f"No nm_id in card, Skip: {card}")
            continue

        imt_name = card.get("imt_name")
        description = card.get("description")
        certificate = card.get("certificate")

        size_list = []
        sizes_table = card.get("sizes_table") or {}
        for size in sizes_table.get("values", []):
            if "tech_size" in size:
                size_list.append(size["tech_size"])

        photo_url_list = []
        media = card.get("media") or {}
        photo_count = media.get("photo_count", 0)
        if nm_id and photo_count:
            for i in range(1, photo_count + 1):
                photo_url_list.append(
                    create_photo_url(id_nm=nm_id, id_img=i, host_list=hosts_list)
                )

        product_url = (
            f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx" if nm_id else None
        )

        card_data = {
            "nm_id": str(nm_id),
            "imt_name": imt_name,
            "sizes_table": size_list,
            "photo_url_list": photo_url_list,
            "description": description,
            "certificate": certificate,
            "product_url": product_url,
        }

        options = card.get("options", [])
        if options:
            for i in options:
                name = i.get("name")
                value = i.get("value")
                if name:
                    card_data[name] = value

        yield str(nm_id), card_data


def get_info_from_idx_json(idx_json_file: Path) -> dict[str, Any]:
    new_data = {}

    try:
        with open(idx_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.info(f"File not found: {idx_json_file}")
        return new_data
    except json.JSONDecodeError as e:
        logger.info(f"Invalid JSON in {idx_json_file}: {e}")
        return new_data

    data = data.get("products", [])

    for product in data:
        nm_id = product.get("id")

        if nm_id is None:
            continue

        price_basic = None
        price_product = None

        brand = product.get("brand")
        brand_id = product.get("brandId")
        rating = product.get("reviewRating")
        sizes = product.get("sizes", [])

        for item in sizes:
            price_info = item.get("price", {})
            if price_info:
                price_basic = price_info.get("basic")
                price_product = price_info.get("product")
                if price_basic is not None and price_product is not None:
                    break

        if price_basic is not None:
            price_basic = int(price_basic) // 100

        if price_product is not None:
            price_product = int(price_product) // 100

        brand_url = f"https://www.wildberries.ru/brands/{brand_id}-{brand.lower().replace(' ', '-')}"
        new_data[nm_id] = {
            "nm_id": str(nm_id),
            "brand": brand,
            "brand_id": brand_id,
            "rating": rating,
            "price_basic": price_basic,
            "price_product": price_product,
            "brand_url": brand_url,
        }

    return new_data
