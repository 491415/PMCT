import logging
import time

import chardet
import requests

from src.models.TrgovackiLanci import TrgLanci


def _check_website_availability(trg_lanac: TrgLanci) -> bool:
    """
    Provjera da li je web-stranica sa cijenama trgovačkog lanca dostupna.

    Args:
        trg_lanac (str): Trgovački lanac na čiju se web-stranicu pokušava spojiti.

    Returns:
        bool: True ako je web-stranica dostupna ili False ako je nedostupna nakon maksimalnog broja pokušaja.
    """
    timeout = 30
    retries = 120

    for attempt in range(retries):
        try:
            logging.info(
                f"Provjera dostupnosti web-stranice {trg_lanac.cijene_url}: {attempt + 1}/{retries}..."
            )
            response = requests.Session().get(trg_lanac.cijene_url, timeout=timeout)

            if response.status_code == 200:
                logging.info(f"Stranica trgovačkog lanca {trg_lanac.name} je dostupna.")
                logging.info("-" * 100)
                return True
            elif response.status_code == 503:
                logging.info(
                    f"Stranica trgovačkog lanca {trg_lanac.name} je privremeno nedostupna."
                )
                time.sleep(5)
                continue
            else:
                logging.warning(
                    f"Stranica trgovačkog lanca {trg_lanac.name} je nedostupna: {response.status_code}."
                )
                logging.info("-" * 100)

        except requests.exceptions.Timeout:
            logging.warning(f"Timeout: {attempt + 1}...")
        except requests.exceptions.ConnectionError:
            logging.warning(f"Greška u konekciji: {attempt + 1}...")
        except requests.exceptions.RequestException as e:
            logging.error(f"Greška u zahtjevu: {e}...")

        if attempt < retries - 1:
            wait_time = 2**attempt
            logging.info(
                f"Čekam {wait_time} sekundi prije ponovnog pokušaja spajanja..."
            )
            time.sleep(wait_time)

    logging.error("Web-stranica nije dostupna nakon maksimalnog broja pokušaja!")
    return False


def get_data_from_source(trg_lanac: TrgLanci, datum: str) -> str | None:
    """
    Preuzimanje HTML-a web-stranice sa cijenama. Ako je trgovački lanac DM, vraća json.

    Args:
        trg_lanac (str): Trgovački lanac sa čije se web-stranice preuzima HTML.
        datum (str): Datum za koji se preuzimaju cijene.

    Returns:
        str | None: HTML u obliku string ili None ako nema podataka za proslijeđeni datum.
    """
    logging.info(
        f"Preuzimanje datoteka cijena za trgovački lanac {trg_lanac.name} i datum {datum}."
    )
    logging.info(100 * "-")

    with requests.get(trg_lanac.cijene_url) as response:
        _check_website_availability(trg_lanac)
    try:
        if trg_lanac == TrgLanci.DM or trg_lanac == TrgLanci.KAUFLAND:
            return response.json()
        return response.text
    except Exception as e:
        logging.warning(
            f"Nema dostupnih datoteka na stranici trgovačkog lanca {trg_lanac.name} za datum {datum}. ({e})"
        )
        return None


def find_encoding(full_url: str) -> str:
    """
    Dohvaća se encoding sa URL-a datoteke koji se koristi prilikom parsiranja iste.

    Args:
        full_url (str): URL datoteke.

    Returns:
        str: Encoding datoteke.
    """
    logging.info(f"Dohvaćam encoding datoteke {full_url}...")

    detected = chardet.detect(requests.get(full_url).content)
    confidence = detected["confidence"]

    logging.info(
        f"Encoding datoteke je {detected['encoding']} sa {confidence} confidenca."
    )
    logging.info(100 * "-")

    return detected["encoding"]
