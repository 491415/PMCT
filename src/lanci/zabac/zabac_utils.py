import logging
import re
from typing import Any, List

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova datoteka cijena trgovačkog lanca Žabac.

    Args:
         datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista URL-ova datoteka cijena za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.ZABAC, datum_cijena), "html.parser"
    )
    links = soup.find_all("a", href=True)

    urls = [
        link["href"] for link in links if datum_cijena in link["href"] and link["href"]
    ]

    if len(urls) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Dohvaćeno {len(urls)} datoteka cjenika.")

    return urls


def clean_sifra(value: Any) -> Any:
    """
    Čišćenje šifre proizvoda trgovačkog lanca Žabac.

    Args:
        value (str): Vrijednost stupca 'Artikl' (šifra proizvoda) iz datoteke cijena.

    Returns:
        str: Očišćeni string.
    """
    if re.fullmatch(r"^0,$", str(value)):
        value = "0"
    return value
