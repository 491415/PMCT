import logging
from typing import List

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova datoteka cijena trgovačkog lanca Vrutak.

    Args:
         datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista URL-ova datoteka cijena za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    # YYYYmmdd format datuma
    split_datum_cijena = datum_cijena.split(".")
    file_datum_cijena = (
        f"{split_datum_cijena[2]}{split_datum_cijena[1]}{split_datum_cijena[0]}"
    )

    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.VRUTAK, datum_cijena), "html.parser"
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
