import logging
import re
from typing import Any, List, Optional, Tuple
from urllib.parse import quote, urljoin

from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def get_all_files(datum_cijena: str) -> List[str]:
    """
    Dohvaćanje svih URL-ova za preuzimanje datoteka cijena trgovačkog
    lanca Kaufland.

    Args:
        datum_cijena (str): Datum objavljivanja cijena.

    Returns:
        List[str]: Lista URL-ova sa datotekama cijena za proslijeđeni datum.

    Raises:
        RuntimeError: Ako nisu pronađene datoteke za proslijeđeni datum.
    """
    file_datum_cijena = datum_cijena.replace(".", "")

    data = get_data_from_source(TrgLanci.KAUFLAND, datum_cijena)

    urls = []
    for item in data:
        if "path" in item:
            encoded_path = quote(item["path"])
            full_url = urljoin(TrgLanci.KAUFLAND.base_url, encoded_path)
            urls.append(full_url)

    today_urls = [url for url in urls if file_datum_cijena in url]

    if len(today_urls) == 0:
        warn_msg = f"Nisu pronađene datoteke za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)

    logging.info(f"Dohvaćeno {len(today_urls)} datoteka cjenika.")

    return today_urls


def remove_strings_in_sidrena_cijena(value: Any) -> Any:
    """
    Brisanje stringa 'MPC' iz stupca sidrene cijene trgovačkog lanca Kaufland.

    Args:
        value (Any): Vrijednost stupca sidrene cijene iz datoteke cijena.

    Returns:
         Any: Očišćena vrijednost sidrene cijene.
    """
    if str(value) == "MPC4.7.25":
        return "4.49"
    if "MPC" in str(value):
        split_value = value.split("=")
        return split_value[1][:-1]
    return value


def extract_address_city(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Izvlačenje podataka o adresi i gradu iz naziva datoteke.

    Format: Oblik_Adresni_Dio_Grad_DucanID_Datum_Vrijeme
    Primjer: Hipermarket_Jurja_Zakna_3_Pula_2630_30092025_7-30

    Args:
        filename (str): Naziv datoteke.

    Returns:
        Tuple[Optional[str], Optional[str]]: Vrijednost adresa i grada ili
        None ako je postoje.
    """
    # Ovdje se pronalazi dio iza naziva grada koji nije potreban i odbacuje se
    # '_2630_30092025_7-30'
    throwaway_pattern = r"_(\d+)_(\d+)_(\d{1,2}-\d+)"
    throwaway_match = re.search(throwaway_pattern, filename)

    if not throwaway_match:
        return None, None

    # Sve ispred dijela koji se odbacuje
    # 'Hipermarket_Jurja_Zakna_3_Pula'
    data_part = filename[: throwaway_match.start()]

    # Split u listu dijelova
    # ['Hipermarket', 'Jurja', 'Zakna', '3', 'Pula']
    data_parts = data_part.split("_")

    # Briše oblik prodajnog objekta (uvijek prvi u nazivu datoteke)
    # ['Jurja', 'Zakna', '3', 'Pula']
    parts = data_parts[1:]

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
