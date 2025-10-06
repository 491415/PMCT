import logging
import re
from typing import List

import requests
from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje URL-ova svih datoteka za proslijeđeni datum sa web-stranice trgovačkog lanca BOSO.

    Args:
        datum_cijena (str): Datum za koji se dohvaćaju cijene.

    Returns:
        List[str]: Lista URL-ova za preuzimanje datoteka sa cijenama.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.BOSO, datum_cijena), "html.parser"
    )
    links = soup.find_all("a", href=True)

    urls = [
        link["href"] for link in links if datum_cijena in link["href"] and link["href"]
    ]

    if len(urls) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Pronađeno {len(urls)} datoteka za preuzimanje.")

    return urls


def _get_nonce() -> str:
    """
    Dohvaća nonce vrijednost koja je potrebna kada se preuzimaju datoteke iz prošlosti za
    trgovački lanac BOSO.

    Returns:
        str: Nonce (Number used once).

    Raises:
        ValueError: Ako nonce nije pronađen.
    """
    html = requests.get(
        TrgLanci.BOSO.cijene_url, headers={"User-Agent": "Mozilla/5.0"}
    ).text
    match = re.search(
        r'marketshop_csv_ajax\s*=\s*{.*?"nonce"\s*:\s*"([a-zA-Z0-9]+)"', html
    )

    if match:
        return match.group(1)

    error_msg = "Nonce nije pronađen!"
    logging.error(error_msg)
    raise ValueError(error_msg)


def get_files_past_date(datum_cijena: str) -> List[str]:
    """
    Dohvaća URL-ove datoteka trgovačkog lanca BOSO za datum u prošlosti.

    Args:
        datum_cijena (str): Datum u prošlosti.

    Returns:
        List[str]: Lista URL-ova za preuzimanje datoteka.
    """
    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.BOSO, datum_cijena), "html.parser"
    )
    store_options = soup.select("select#marketshop-filter option")
    stores = [opt["value"] for opt in store_options if opt["value"]]

    urls = []

    for store in stores:
        data = {
            "action": "filter_by_marketshop",
            "marketshop": store,
            "nonce": _get_nonce(),
        }
        post_response = requests.post(
            "https://www.boso.hr/wp-admin/admin-ajax.php", data=data
        )
        json_data = post_response.json()
        html = json_data["data"]["html"]
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table.marketshop-files-table tbody tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                link_datum = cells[2].text.strip()
                if link_datum == datum_cijena:
                    link_tag = row.find("a", href=True)
                    if link_tag:
                        link = link_tag["href"]
                        urls.append(link)
                        break

    if len(urls) == 0:
        logging.warning(
            f"Nisu pronađeni linkovi za preuzimanje datoteka za datum {datum_cijena}"
        )

    logging.info(f"Pronađeno {len(urls)} linkova za preuzimanje datoteka.")

    return urls


def clean_naziv(value: str) -> str:
    """
    Čišćenje naziv proizvoda trgovačkog lanca BOSO jer iako je UTF-8 encoding,
    pojavljuju se znakovi 'Æ' i 'È'. Također umjesto 'x' i 'Č' se pojavljuje '?'
    pa je i to ispravljeno.

    Args:
        value (str): Vrijednost stupca 'naziv' iz datoteke cijena.

    Returns:
        str: Očišćeni string.
    """
    if "?AŠE" in value:
        value = "PODMETAČ IBAMBUS ZA ČAŠE 4/1"
    if "42?42 CM RAKETA LUNA" in value.upper():
        value = "PUZZL 42/1 42x42 CM RAKETA LUNA"
    if "42?42 CM KOČIJA LUNA" in value.upper():
        value = "PUZZL 42/1 42x42 CM KOČIJA LUNA"
    if "Æ" in value.upper():
        value = value.upper().replace("Æ", "Ć")
    if "È" in value.upper():
        value = value.upper().replace("È", "Č")
    return value
