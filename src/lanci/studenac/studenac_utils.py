import logging
import re
from typing import Optional, Tuple

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_zip_link(datum_cijena: str) -> str | None:
    """
    Dohvaćanje URL-a zip datoteke za proslijeđeni datum cijena
    trgovačkog lanca Studenac.

    Args:
        datum_cijena (str): Datum objave cijena.

    Returns:
        str | None: URL datoteke ili None ako ne postoji za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nije pronađena zip datoteka za proslijeđeni datum.
    """
    # YYYY-mm-dd format datuma
    split_datum_cijena = datum_cijena.split(".")
    file_datum_cijena = (
        f"{split_datum_cijena[2]}-{split_datum_cijena[1]}-{split_datum_cijena[0]}"
    )

    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.STUDENAC, datum_cijena), "html.parser"
    )
    links = soup.find_all("a", href=True)

    url = None

    for link in links:
        if file_datum_cijena in link["href"] and link["href"].endswith(".zip"):
            url = link["href"]

    if not url:
        warn_msg = f"Nije pronađena zip datoteka za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Pronađena zip datoteka {url} za datum {datum_cijena}.")

    return url


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik-Adresni_dio_GRAD-DucanID-Broj pohrane-Godina-Mjesec-Dan-Vrijeme
    Primjer: SUPERMARKET-Bijela_uvala_5_FUNTANA-T598-143-2025-10-04-07-00-16-011151

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '-100-135-2025-09-26-06-56-50-093226'
    throwaway_pattern = r"-(T\d{3}|\d{4})-(\d+)-(\d+)-.*"
    throwaway_match = re.search(throwaway_pattern, filename)
    print(throwaway_match)
    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'SUPERMARKET-Bijela_uvala_5_FUNTANA'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['SUPERMARKET-Bijela', 'uvala', '5', 'FUNTANA']
    data_parts = data_part.split("_")

    # ['SUPERMARKET', 'Bijela']
    remove_oblik = data_parts[0].split("-")

    # ['Bijela', 'uvala', '5', 'FUNTANA']
    data_parts.pop(0)
    data_parts.insert(0, remove_oblik[1])

    # Grad se pronalazi tako da potraga kreće sa desna na lijevo
    # Pravila za grad: samo slova, nema 'bb' i dužina > 1
    # Dok se pronađe dio koji više ne pripada gradu, sve ostalo je adresa
    city_parts = []
    city_start_index = None

    for i in range(len(data_parts) - 1, -1, -1):
        part = data_parts[i]

        # Provjera da li je ovaj 'dio' dio grada
        if part.isalpha() and part not in ["bb", "BB"] and len(part) > 1:
            city_parts.insert(0, part)
            city_start_index = i
        else:
            # Došli do dijela koji nije dio grada (znamenka, alphanumeric, bb/BB, ili jedno slovo)
            # Prekid skupljanja dijelova grada
            break

    # Razdvajanje u adresu i grad
    if city_start_index is not None:
        address_parts = data_parts[:city_start_index]
    else:
        # Nije pronađen valjani grad
        address_parts = data_parts

    if not city_parts:
        return None, None

    city = " ".join(city_parts)
    address = " ".join(address_parts).upper()

    return address, city
