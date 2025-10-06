import logging
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup
from environs import env
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def _get_urls_current_date(datum_cijena: str, text: str) -> List[str]:
    """
    Dohvaćanje URL-ova datoteka trgovačkog lanca NTL-a prema proslijeđenom
    HTML-u i trenutnom datumu.

    Args:
        datum_cijena (str): Trenutni datum.
        text (str): HTML stranice.

    Returns:
        List[str]: Lista URL-ova za trenutni datum.
    """
    datum_cijena_split = datum_cijena.split(".")
    file_datum_cijena = (
        f"{datum_cijena_split[0]}{datum_cijena_split[1]}{datum_cijena_split[2]}"
    )

    soup = BeautifulSoup(text, "html.parser")
    all_links = soup.find_all("a", download=True, href=True)

    file_links = []

    for link in all_links:
        file_links.append(link.get("href"))

    urls = []

    for file in file_links:
        if file_datum_cijena in file and file:
            urls.append(file)

    return urls


def get_all_files_current_date() -> List[str]:
    """
    Dohvaćanje svih URL-ova za preuzimanje datoteka cijena trgovačkog
    lanca NTL-a za trenutni datum.

    Returns:
        List[str]: Lista URL-ova sa datotekama cijena za trenutni datum.
    """
    datum_cijena = datetime.now().strftime(env("DATE_FORMAT"))

    return _get_urls_current_date(
        datum_cijena, get_data_from_source(TrgLanci.NTL, datum_cijena)
    )


def get_all_files_past_date(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova za preuzimanje datoteka cijena trgovačkog
    lanca NTL-a za prošle datum.

    Args:
        datum_cijena (str): Datum cijena iz prošlosti.

    Returns:
        List[str]: Lista URL-ova sa datotekama cijena za prošli datum.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    # YYYY-mm-dd
    datum_cijena_split = datum_cijena.split(".")
    option_datum_cijena = (
        f"{datum_cijena_split[2]}-{datum_cijena_split[1]}-{datum_cijena_split[0]}"
    )

    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.NTL, datum_cijena), "html.parser"
    )
    options = soup.select('select[name="date"] option')
    date_values = [
        opt["value"]
        for opt in options
        if "value" in opt.attrs and "odaberi datum" not in opt.text.lower()
    ]

    if option_datum_cijena in date_values:
        url = f"{TrgLanci.NTL.cijene_url}?date={option_datum_cijena}"
        return _get_urls_current_date(datum_cijena, requests.get(url).text)
    else:
        warn_msg = f"Nije pronađena stranica za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)


def clean_naziv(value: str) -> str:
    """
    Čišćenje pojedinih naziva proizvoda NTL-a (ima ? umjesto Đ i Ž).

    Args:
        value (str): Vrijednost stupca naziva proizvoda.

    Returns:
        str: Ispravljena vrijednost stupca naziva proizvoda.
    """
    if "ŽICA ZA POSU?E S DRŠKOM" in value:
        value = "ŽICA ZA POSUĐE S DRŠKOM"

    if "POWER INOX SPU?VICA 2/1" in value:
        value = "VILEDA GLITZI POWER INOX SPUŽVICA 2/1"

    if "POWER MAGICNA SPU?VA" in value:
        value = "VILEDA MIRACLEAN POWER MAGICNA SPUŽVA"

    if "VRAŽJA KAN?A" in value:
        value = "KREMA VRAŽJA KANĐA 250 ML"

    return value
