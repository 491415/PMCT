import logging
import re
from typing import Optional, Tuple

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_zip_link(datum_cijena: str) -> str | None:
    """
    Dohvaćanje URL-a zip datoteke za proslijeđeni datum cijena
    trgovačkog lanca Lidl.

    Args:
        datum_cijena (str): Datum objave cijena.

    Returns:
        str | None: URL datoteke ili None ako ne postoji za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nije pronađena zip datoteka za proslijeđeni datum.
    """
    # dd_mm_YYYY format
    split_datum_cijena = datum_cijena.split(".")
    file_datum_cijena = (
        f"{split_datum_cijena[0]}_{split_datum_cijena[1]}_{split_datum_cijena[2]}"
    )

    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.LIDL, datum_cijena), "html.parser"
    )
    links = soup.find_all("a", href=True)

    url = None

    for link in links:
        if file_datum_cijena in link["href"] and link["href"].endswith(".zip"):
            url = link["href"]

    if not url:
        error_msg = f"Nije pronađena zip datoteka za datum {datum_cijena}"
        logging.warning(error_msg)
        raise RuntimeError(error_msg)

    logging.info(f"Pronađena zip datoteka {url} za datum {datum_cijena}.")

    return url


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik DucanID_Adresa_Postanski broj_Grad_1_Datum_Vrijeme
    Primjer: Supermarket 105_Zeleno polje_8 A_31000_Osijek_1_26.09.2025_7.15h

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '_1_26.09.2025_7.15h'
    throwaway_pattern = r"_[0-9]_(\d{2}.\d{2}.\d{4})_.*"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'Supermarket 105_Zeleno polje_8 A_31000_Osijek'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['Supermarket 105', 'Zeleno polje', '8 A', '31000', 'Osijek']
    data_parts = data_part.split("_")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # Zeleno polje 8 A 31000 Osijek
    parts = data_parts[1:]
    parts = " ".join(parts)

    # Novi pattern za pronalazak podataka
    # ^(.+?) - pronalazi adresu
    # \s+(\d{5}) - pronalazi poštanski broj
    # \s+(.+)$ - pronalazi grad (sve nakon poštanskoh broja)
    data_pattern = r"^(.+?)\s+(\d{5})\s+(.+)"

    match = re.search(data_pattern, parts)

    if match:
        address = match.group(1).upper()  # Adresa
        city = match.group(3)  # Grad

        return address, city

    return None, None
