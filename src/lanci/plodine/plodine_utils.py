import logging
import re
from typing import Optional, Tuple

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_zip_link(datum_cijena: str) -> str | None:
    """
    Dohvaćanje URL-a zip datoteke za proslijeđeni datum cijena
    trgovačkog lanca Plodine.

    Args:
        datum_cijena (str): Datum objave cijena.

    Returns:
        str | None: URL datoteke ili None ako ne postoji za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nije pronađena zip datoteka za proslijeđeni datum.
    """
    # dd_mm_YYYY format datuma
    file_datum_cijena = datum_cijena.replace(".", "_")

    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.PLODINE, datum_cijena), "html.parser"
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

    Format: Oblik_Adresni_Dio_Postanski broj_Grad_DucanID_Broj pohrane_DatumVrijeme
    Primjer: HIPERMARKET_ANTE_STARCEVICA_21_10290_ZAPRESIC_064_135_26092025022535

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '_064_135_26092025022535'
    throwaway_pattern = r"_(\d+)_(\d+)_(\d+)"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'HIPERMARKET_ANTE_STARCEVICA_21_10290_ZAPRESIC'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['HIPERMARKET', 'ANTE', 'STARCEVICA', '21', '10290', 'ZAPRESIC']
    data_parts = data_part.split("_")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # ['ANTE', 'STARCEVICA', '21', '10290', 'ZAPRESIC']
    parts = data_parts[1:]
    # 'ANTE STARCEVICA 21 10290 ZAPRESIC
    parts = " ".join(parts)

    # Novi pattern za pronalazak podataka
    # ^(.+?) - pronalazi adresu
    # \s+(\d{5}) - pronalazi poštanski broj
    # \s+(.+)$ - pronalazi grad (sve nakon poštanskog broja)
    data_pattern = r"^(.+?)\s+(\d{5})\s+(.+)"

    match = re.search(data_pattern, parts)

    if match:
        address = match.group(1).upper()  # Adresa
        city = match.group(3).title()  # Grad

        return address, city

    return None, None
