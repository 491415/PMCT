import logging
import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova datoteka cijena trgovačkog lanca Trgocentar.

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
        get_data_from_source(TrgLanci.TRGOCENTAR, datum_cijena), "html.parser"
    )
    links = soup.find_all("a", href=True)

    urls = [
        link["href"]
        for link in links
        if file_datum_cijena in link["href"] and link["href"]
    ]

    full_urls = []

    for i in urls:
        full_urls.append(f"{TrgLanci.TRGOCENTAR.cijene_url}/{i}")

    if len(full_urls) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Dohvaćeno {len(full_urls)} datoteka cjenika.")

    return full_urls


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik_Adresni_dio_Grad_DucanID_Broj pohrane_DatumVrijeme
    Primjer: SUPERMARKET_103_BRIGADE_8_ZABOK_P080_144_041020250744

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '_P080_144_041020250744'
    throwaway_pattern = r"_(P\d{3})_(\d+)_(\d+)"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'SUPERMARKET_103_BRIGADE_8_ZABOK'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['SUPERMARKET', '103', 'BRIGADE', '8', 'ZABOK']
    data_parts = data_part.split("_")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # ['103', 'BRIGADE', '8', 'ZABOK']
    parts = data_parts[1:]

    # Grad se pronalazi tako da potraga kreće sa desna na lijevo
    # Pravila za grad: samo slova, nema 'bb' i dužina > 1
    # Dok se pronađe dio koji više ne pripada gradu, sve ostalo je adresa
    city_parts = []
    city_start_index = None

    for i in range(len(parts) - 1, -1, -1):
        part = parts[i]

        # Provjera da li je ovaj 'dio' dio grada
        if part.isalpha() and part not in ["bb", "BB", "VRANKOVEC"] and len(part) > 1:
            city_parts.insert(0, part)
            city_start_index = i
        else:
            # Došli do dijela koji nije dio grada (znamenka, alphanumeric, bb/BB, ili jedno slovo)
            # Prekid skupljanja dijelova grada
            break

    # Razdvajanje u adresu i grad
    if city_start_index is not None:
        address_parts = parts[:city_start_index]
    else:
        # Nije pronađen valjani grad
        address_parts = parts

    if not city_parts:
        return None, None

    city = " ".join(city_parts)
    address = " ".join(address_parts).upper()

    return address, city
