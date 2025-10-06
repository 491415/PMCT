import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def _get_files_url(datum_cijena: str) -> str:
    """
    Dohvaćanje URL-a sa datotekama cijena za proslijeđeni datum
    trgovačkog lanca Ribola.

    Args:
         datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        str: URL za proslijeđeni datum.

    Raises:
        ValueError: Ako ne postoji link za proslijeđeni datum.
    """
    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.RIBOLA, datum_cijena), "html.parser"
    )

    for a in soup.find_all("a", href=True):
        if f"?date={datum_cijena}" in a["href"]:
            url = urljoin(TrgLanci.RIBOLA.cijene_url, a["href"])
            logging.info(f"Pronađen URL za datum {datum_cijena}: {url}")
            return url

    warn_msg = f"Nije pronađen URL za datum {datum_cijena}"
    logging.warning(warn_msg)
    raise ValueError(warn_msg)


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih datoteka za proslijeđeni datum objave cijena.

    Args:
        datum_cijena (str): Datum objave cijena.

    Returns:
        List[str]: Lista datoteka za proslijeđeni datum objave cijena.
    """
    url = _get_files_url(datum_cijena)

    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    xml_links = list(
        {
            f'{TrgLanci.RIBOLA.cijene_url}/{a["href"]}'
            for a in soup.find_all("a", href=True)
            if a["href"].endswith(".xml")
        }
    )

    logging.info(f"Pronađeno {len(xml_links)} datoteka za preuzimanje")

    return xml_links


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik-Adresni_Dio_Grad-DucanID-Broj pohrane-Datum-Vrijeme
    Primjer: HIPERMARKET-Cesta_dr._Franje_Tuđmana_7_Kastel_Sucurac-100-135-2025-09-26-06-56-50-093226

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '-100-135-2025-09-26-06-56-50-093226'
    throwaway_pattern = r"-(\d+)-(\d+)-(\d+)-.*"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'HIPERMARKET-Cesta_dr._Franje_Tuđmana_7_Kastel_Sucurac'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['HIPERMARKET-Cesta', 'dr.', 'Franje', 'Tuđmana', '7', 'Kastel', 'Sucurac']
    data_parts = data_part.split("_")
    # ['HIPERMARKET', 'Cesta']
    remove_oblik = data_parts[0].split("-")
    # ['Cesta', 'dr.', 'Franje', 'Tuđmana', '7', 'Kastel', 'Sucurac']
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
        if (
            part.isalpha()
            and part not in ["bb", "BB", "Medena", "rata"]
            and len(part) > 1
        ):
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
