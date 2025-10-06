import logging
import re
from datetime import datetime
from typing import Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup
from environs import env

from src.models.TrgovackiLanci import TrgLanci


def _get_all_pages(datum_cijena: str) -> int:
    """
    Dohvaća broj stranica cjenika sa Konzumove stranice (https://www.konzum.hr/cjenici) za proslijeđeni datum.

    Args:
        datum_cijena (str): Datum za koji se preuzimaju datoteke sa cijenama.

    Returns:
        int: Broj podstranica liste datoteka.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    logging.info(f"Dohvaćam broj stranica cjenika za datum {datum_cijena}...")

    file_datum_cijena = datetime.strptime(datum_cijena, env("DATE_FORMAT")).strftime(
        env("FILE_DATE")
    )

    response = requests.get(f"{TrgLanci.KONZUM.cijene_url}?date={file_datum_cijena}")

    if response.status_code == 200:
        # Parsiraj HTML sa BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        # Dohvati sve 'ul' tagove unutar html-a sa klasom 'pagination'
        ul = soup.find_all("ul", class_="pagination")
        if len(ul) == 0:
            warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
            logging.warning(warn_msg)
            raise RuntimeError(warn_msg)
        # Pronađi sve 'a' tagove unutar 'li' tagova koja sadrže klasu 'page-item'
        anchors = ul[0].select("li.page-item a")
        # Dohvati broj stranica sa predzadnjeg elementa liste (jer zadnji element je gumb za next page)
        num_pages = anchors[-2].text

        logging.info(f"Broj stranica cjenika za datum {datum_cijena} je {num_pages}.")

        return int(num_pages)
    else:
        logging.error(
            f"{TrgLanci.KONZUM.cijene_url} je trenutno nedostupan. Code: {response.status_code}"
        )
        exit()


def get_all_files(datum_cijena: str) -> Set[str]:
    """
    Dohvaća sve URL-ove datoteka za preuzimanje za proslijeđeni datum objave cijena.

    Args:
        datum_cijena (str): Datum za koji se preuzimaju datoteke sa cijenama.

    Returns:
         List[set]: Lista datoteka cijena.
    """
    logging.info(f"Dohvaćam sve datoteke cjenika za {TrgLanci.KONZUM.name}...")

    file_datum_cijena = datetime.strptime(datum_cijena, env("DATE_FORMAT")).strftime(
        env("FILE_DATE")
    )
    files = []

    for page in range(1, _get_all_pages(datum_cijena) + 1):
        page_url = f"{TrgLanci.KONZUM.cijene_url}?date={file_datum_cijena}&page={page}"
        res = requests.get(page_url)
        pattern = r'href="(/cjenici/download\?[^"]+)"'
        matches = re.findall(pattern, res.text)
        files.extend(matches)

    full_urls = [f"{TrgLanci.KONZUM.base_url}{url}" for url in files]

    logging.info(f"Dohvaćeno {len(set(full_urls))} datoteka cjenika.")

    return set(full_urls)


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik,Adresa Poštanski broj Grad,DucanID,Broj pohrane,Datum, Vrijeme
    Primjer: HIPERMARKET,BJELOVARSKA 48B 10360 SESVETE,0201,25805,26.09.2025, 05-21

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # ',0201,25805,26.09.2025, 05-21'
    throwaway_pattern = r",(\d+),(\d+),.*"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'HIPERMARKET,BJELOVARSKA 48B 10360 SESVETE'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['HIPERMARKET', 'BJELOVARSKA 48B 10360 SESVETE']
    data_parts = data_part.split(",")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # ['BJELOVARSKA 48B 10360 SESVETE']
    parts = data_parts[1:]

    # Novi pattern za pronalazak podataka
    # ^(.+?) - pronalazi adresu
    # \s+(\d{5}) - pronalazi poštanski broj
    # \s+(.+)$ - pronalazi grad (sve nakon poštanskog broja)
    data_pattern = r"^(.+?)\s+(\d{5})\s+(.+)"

    match = re.search(data_pattern, parts[0].strip())

    if match:
        address = match.group(1).upper()  # Adresa
        city = match.group(3).title()  # Grad

        return address, city

    return None, None
