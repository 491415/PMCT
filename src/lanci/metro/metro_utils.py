import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def _get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih naziva datoteka cijena trgovačkog lanca Metro.

    Args:
         datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista naziva datoteka cijena za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    # YYYYmmdd format datuma
    datum_cijena_split = datum_cijena.split(".")
    file_datum_cijena = (
        f"{datum_cijena_split[2]}{datum_cijena_split[1]}{datum_cijena_split[0]}"
    )

    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.METRO, datum_cijena), "html.parser"
    )
    links = soup.find_all("a", href=True)

    files = [
        link["href"]
        for link in links
        if file_datum_cijena in link["href"] and link["href"]
    ]

    if len(files) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Dohvaćeno {len(files)} datoteka cjenika.")

    return files


def create_file_urls(datum_cijena: str) -> List[str]:
    """
    Kreiranje punog URL-a za preuzimanje datoteka cijena trgovačkog lanca Metro.

    Args:
        datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista URL-ova za preuzimanje datoteka cijena.
    """
    full_urls = []

    for file_name in _get_all_files(datum_cijena):
        full_url = urljoin(TrgLanci.METRO.cijene_url, file_name)
        full_urls.append(full_url)

    return full_urls


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik_METRO_DatumVrijeme_DucanID_Adresa,_Grad
    Primjer: cash_and_carry_prodavaonica_METRO_20250926T0630_S10_JANKOMIR_31,_ZAGREB

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # 'cash_and_carry_prodavaonica_METRO_20250926T0630_S10_'
    throwaway_pattern = r".*_METRO_.*_S\d{2}_"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'JANKOMIR_31,_ZAGREB'
    data_part = filename[throwaway_match.end() :]

    # Split u listu dijelova
    # ['JANKOMIR_31', 'ZAGREB']
    data_parts = data_part.split(",_")

    address = data_parts[0].replace("_", " ")
    city = " ".join(data_parts[1:]).title()

    return address, city
