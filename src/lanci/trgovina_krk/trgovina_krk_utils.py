import logging
import re
from typing import Any, List, Optional, Tuple

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova datoteka cijena trgovačkog lanca Trgovina Krk.

    Args:
         datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista URL-ova datoteka cijena za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    # ddmmYYYY format datuma
    file_datum_cijena = datum_cijena.replace(".", "")

    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.TRGOVINA_KRK, datum_cijena), "html.parser"
    )
    links = soup.find_all("a", href=True)

    urls = [
        link["href"]
        for link in links
        if file_datum_cijena in link["href"] and link["href"]
    ]

    if len(urls) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Dohvaćeno {len(urls)} datoteka cjenika.")

    return urls


def clean_sifra(value: Any) -> Any:
    """
    Čišćenje šifre proizvoda trgovačkog lanca Trgovina Krk.

    Args:
        value (str): Vrijednost stupca 'Šifra proizvoda' iz datoteke cijena.

    Returns:
        str: Očišćeni string.
    """
    if "8,00741E+12" in str(value):
        value = None
    return value


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik_Adresni dio_Grad_DucanID_Broj pohrane_Datum_Vrijeme
    Primjer: Supermarket_Andrije Gredicaka 12b_OROSLAVJE_121180_2808_01102025_07_28_25

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '_121180_2808_01102025_07_28_25'
    throwaway_pattern = r"_(\d+)_(\d+)_(\d+)_.*"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'Supermarket_Andrije Gredicaka 12b_OROSLAVJE'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['Supermarket', 'Andrije Gredicaka 12b', 'OROSLAVJE']
    data_parts = data_part.split("_")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # ['Andrije Gredicaka 12b', 'OROSLAVJE']
    parts = data_parts[1:]

    city = parts[-1].title()
    address = parts[0].upper()

    return address, city
