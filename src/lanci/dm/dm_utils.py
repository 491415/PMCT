import logging
from typing import Any

import requests
from requests import HTTPError
from web_utils import get_data_from_source

from src.models.TrgovackiLanci import TrgLanci


def remove_euro_sign(value: Any) -> Any:
    """
    Briše znak '€' iz stupaca sa cijenama.
    DM u stupcima sa cijenama ima i znak '€' pa ga je potrebno maknuti.

    Args:
        value (Any): Vrijednost pročitana iz datoteke (stupci koji sadrže cijene).

    Returns:
        Any: Vrijednost nakon brisanja ako sadrži '€'.
    """
    if "€" in str(value):
        return str(value)[:-1].strip()
    return value


def clean_marka(value: Any) -> Any:
    """
    Ispravak znaka 'È' u 'Č'.
    DM ima marku proizvoda koja umjesto 'Č' ima 'È' (ÈISTO POLIT.)

    Args:
        value (Any): Vrijednost pročitana iz datoteke (stupac 'marka').

    Returns:
         Any: Ispravljena vrijednost marke proizvoda.
    """
    if "ISTO POLIT." in value:
        value = "ČISTO POLIT."
    return value


def _format_file_date(datum_cijena: str) -> str:
    """
    Formatiranje datuma cijena u format 1.1.2000.
    DM u nazivima svojih datoteka nema format 01.01.2000, već se 0 briše.

    Args:
        datum_cijena (str): Datum za koji se preuzima datoteka sa cijenama.

    Returns:
        str: Formatirani datum.
    """
    file_datum = datum_cijena.split(".")
    file_datum = (
        f"{file_datum[0].replace('0', '') if file_datum[0][0] == '0' else file_datum[0]}."
        f"{file_datum[1].replace('0', '') if file_datum[1][0] == '0' else file_datum[1]}."
        f"{file_datum[2]}"
    )

    return file_datum


def get_file_link(datum_cijena: str) -> str:
    """
    Dohvaćanje linka datoteke DM-a sa njihove web-stranice.

    Args:
        datum_cijena (str): Datum cijena za koji se dohvaća link.

    Returns:
        str: Link za preuzimanje datoteke

    Raises:
        RuntimeError: Ako nije pronađena datoteka za proslijeđeni datum.
    """
    json = get_data_from_source(TrgLanci.DM, datum_cijena)

    target_link = None
    for item in json.get("mainData", []):
        if item.get("type") == "CMDownload":
            headline = item.get("data", {}).get("headline", "")
            if _format_file_date(datum_cijena) in headline:
                target_link = item.get("data", {}).get("linkTarget")

    if target_link:
        full_url = (
            "https://content.services.dmtech.com/rootpage-dm-shop-hr-hr" + target_link
        )
        logging.info(f"Nađen link datoteke za datum {datum_cijena}: {full_url}")
        logging.info(100 * "-")

        return full_url
    else:
        warn_msg = f"Nije pronađena datoteka za datum {datum_cijena}"
        logging.warning(warn_msg)
        raise RuntimeError(warn_msg)


def download_and_save_excel_from_url(
    full_url: str, file_name: str, file_path: str
) -> None:
    """
    Preuzimanje i spremanje DM xlsx datoteke sa cijenama na lokalni disk.

    Args:
        full_url (str): URL datoteke za preuzimanje.
        file_name (str): Naziv datoteke.
        file_path (str): Lokacija gdje se sprema datoteka na lokalnom disku.

    Raises:
        HTTPError: Ako se dogodi HTTP greška.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream",
    }

    try:
        logging.info(f"Preuzimanje i spremanje datoteke sa URL-a: {full_url}")

        response = requests.get(full_url, headers=headers)
        response.raise_for_status()

        with open(rf"{file_path}\{file_name}", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Dogodio se HTTP Error: {e}"
        logging.error(error_msg)
        raise HTTPError(error_msg) from e
    except Exception as e:
        logging.error(
            f"Dogodila se greška prilikom preuzimanja i spremanja DM xlsx datoteke: {e}"
        )
        raise
