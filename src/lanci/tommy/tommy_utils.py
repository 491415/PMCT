import logging
import re
from typing import Any, List, Optional, Tuple

import requests


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova datoteka cijena trgovačkog lanca Tommy.

    Args:
         datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista URL-ova datoteka cijena za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    # YYYY-mm-dd format datuma
    datum_cijena_split = datum_cijena.split(".")
    file_datum_cijena = (
        f"{datum_cijena_split[2]}-{datum_cijena_split[1]}-{datum_cijena_split[0]}"
    )

    urls = []

    params = {
        "itemsPerPage": "200",
        "date": {file_datum_cijena},
    }

    response = requests.get(
        "https://spiza.tommy.hr/api/v2/shop/store-prices-tables", params=params
    )
    if response.status_code == 200:
        data = response.json()
        for item in data.get("hydra:member", []):
            csv_path = item["@id"]
            base_url = "https://spiza.tommy.hr"
            url = base_url + csv_path
            urls.append(url)

    if len(urls) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Dohvaćeno {len(urls)} datoteka cjenika.")

    return urls


def clean_naziv(value: Any) -> Any:
    """
    Čišćenje naziv proizvoda trgovačkog lanca Tommy.

    Args:
        value (str): Vrijednost stupca 'naziv' iz datoteke cijena.

    Returns:
        str: Očišćeni string.
    """
    if "DINGAÈ" in value:
        value = "VINO DINGAČ 0,75 L ROSO"

    return value


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik, Adresni dio, Poštanski broj Grad, DucanID, Broj pohrane, Datum Vrijeme
    Primjer: SUPERMARKET, ANTE STARČEVIĆA 6, 20260 KORČULA, 10180, 144, 20251004 0530

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # ', 10180, 144, 20251004 0530'
    throwaway_pattern = r", (\d+), (\d+), (\d+) (\d+)"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'SUPERMARKET, ANTE STARČEVIĆA 6, 20260 KORČULA'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['SUPERMARKET', ' ANTE STARČEVIĆA 6', ' 20260 KORČULA']
    data_parts = data_part.split(",")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # [' ANTE STARČEVIĆA 6', ' 20260 KORČULA']
    parts = data_parts[1:]

    address = parts[0].strip()
    city = parts[1][6:].strip()

    return address, city
