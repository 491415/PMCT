import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import quote, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova za preuzimanje datoteka cijena trgovačkog
    lanca KTC.


    Args:
         datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista URL-ova sa datotekama cijena za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    # YYYYmmdd format datuma
    datum_cijena_split = datum_cijena.split(".")
    file_datum_cijena = (
        f"{datum_cijena_split[2]}{datum_cijena_split[1]}{datum_cijena_split[0]}"
    )

    soup = BeautifulSoup(
        get_data_from_source(TrgLanci.KTC, datum_cijena), "html.parser"
    )

    poslovnica_urls = [
        urljoin(TrgLanci.KTC.base_url, a["href"])
        for a in soup.find_all("a", href=True)
        if a["href"].startswith("cjenici?poslovnica=")
    ]

    urls = []
    for pos_url in poslovnica_urls:
        try:
            res = requests.get(pos_url)
            sub_soup = BeautifulSoup(res.text, "html.parser")

            for a in sub_soup.find_all("a", href=True):
                href = a["href"]
                if href.endswith(".csv") and file_datum_cijena in href:
                    full_url = urljoin(pos_url, href)
                    parsed = urlparse(full_url)
                    encoded_url = urlunparse(
                        (parsed.scheme, parsed.netloc, quote(parsed.path), "", "", "")
                    )
                    urls.append(encoded_url)
        except Exception as e:
            logging.error(f"Dogodila se greška za {pos_url}: {e}")
            raise

    if len(urls) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Dohvaćeno {len(urls)} datoteka cjenika.")

    return urls


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik-Adresa Grad-DucanID-?-Datum-Vrijeme
    Primjer: TRGOVINA-BOBOVJE 52  C KRAPINA-PJ77-1-20250926-071002

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '-PJ77-1-20250926-071002'
    throwaway_pattern = r"-(PJ\w{2})-1-(\d+)-.*"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'TRGOVINA-BOBOVJE 52  C KRAPINA'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['TRGOVINA', 'BOBOVJE 52  C KRAPINA']
    data_parts = data_part.split("-")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # ['BOBOVJE 52  C KRAPINA']
    parts = data_parts[1:]
    # Split prema whitespaceu
    # ['BOBOVJE', '52', ' C', 'KRAPINA']
    parts = parts[0].split()

    # Grad se pronalazi tako da potraga kreće sa desna na lijevo
    # Pravila za grad: samo slova, nema 'bb' i dužina > 1
    # Dok se pronađe dio koji više ne pripada gradu, sve ostalo je adresa
    city_parts = []
    city_start_index = None

    for i in range(len(parts) - 1, -1, -1):
        part = parts[i]

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
        address_parts = parts[:city_start_index]
    else:
        # Nije pronađen valjani grad
        address_parts = parts

    if not city_parts:
        return None, None

    city = " ".join(city_parts)
    address = " ".join(address_parts).upper()

    return address, city
