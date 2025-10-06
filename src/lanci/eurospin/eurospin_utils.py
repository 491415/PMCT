import logging

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_zip_link(datum_cijena: str) -> str | None:
    """
    Dohvaćanje URL-a zip datoteke za proslijeđeni datum cijena
    trgovačkog lanca Eurospin.

    Args:
        datum_cijena (str): Datum objave cijena.

    Returns:
        str | None: URL datoteke ili None ako ne postoji za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nije pronađena zip datoteka za proslijeđeni datum.
    """
    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.EUROSPIN, datum_cijena), "html.parser"
    )
    option_tags = soup.find_all("option")

    url = None

    for option in option_tags:
        value = option.get("value", "")
        if datum_cijena in value:
            url = value

    if not url:
        error_msg = f"Nije pronađena zip datoteka za datum {datum_cijena}"
        logging.warning(error_msg)
        raise RuntimeError(error_msg)

    logging.info(f"Pronađena zip datoteka {url} za datum {datum_cijena}.")

    return url


def clean_naziv(value: str) -> str:
    """
    Čišćenje naziv proizvoda trgovačkog lanca Eurospin.

    Args:
        value (str): Vrijednost stupca 'NAZIV_PROIZVODA' iz datoteke cijena.

    Returns:
        str: Očišćeni string.
    """
    if "9VAKAĆA".lower() in value.lower():
        value = "ŽVAKAĆA GUM.OR.CARE 3*23,8G 71,4G"
    if "KASIICA KUKUR.,RI?A" in value:
        value = "KASIICA KUKUR.,RIŽA,TAPI. BIO 200G"
    if "OMEKŠIVA?" in value:
        value = "GEL KAPS.RUBLJE 5U1 OMEKŠIVAČ 20KOM"
    return value
