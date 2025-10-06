import logging
import re
from typing import List, Optional, Tuple

import requests


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova datoteka cijena trgovačkog lanca Spar.

    Args:
         datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista URL-ova datoteka cijena za proslijeđeni datum.

    Raises:
        RuntimeError: Ako stranica nije pronađena (404) ili ako nisu pronađene
                      datoteke za proslijeđeni datum.
    """
    # YYYYmmdd format datuma
    datum_cijena_split = datum_cijena.split(".")
    file_datum_cijena = (
        f"{datum_cijena_split[2]}{datum_cijena_split[1]}{datum_cijena_split[0]}"
    )

    response = requests.get(
        f"https://www.spar.hr/datoteke_cjenici/Cjenik{file_datum_cijena}.json"
    )

    if response.status_code == 404:
        error_msg = f"Nije pronađena .json datoteka za datum {datum_cijena}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    if response.status_code == 200:
        data = response.json()

    urls = [file["URL"] for file in data.get("files", [])]

    if len(urls) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Dohvaćeno {len(urls)} datoteka cjenika.")

    return urls


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik_Grad_Adresni_Dio_DucanID_Oznake_dućana_Broj pohrane_Datum_Vrijeme
    Primjer: hipermarket_donji_stupnik_gospodarska_ulica_5_8708_interspar_zg_emmez_stup_0148_20250926_0330

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # VAŽNO!!! Ne radi za gradove koji u nazivu imaju više od jedne riječi
    # Neda mi se s tim z........

    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '-100-135-2025-09-26-06-56-50-093226'
    throwaway_pattern = r"_(\d{4,5})_[a-zA-Z]+_[a-zA-Z]+_.*"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'hipermarket_donji_stupnik_gospodarska_ulica_5'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['hipermarket', 'donji', 'stupnik', 'gospodarska', 'ulica', '5']
    data_parts = data_part.split("_")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # ['donji', 'stupnik', 'gospodarska', 'ulica', '5']
    parts = data_parts[1:]

    city = parts[0].title()
    address = " ".join(parts[1:]).upper()

    return address, city
