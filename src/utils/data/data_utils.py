import decimal
import logging
import math
import os
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from pandas import DataFrame

from src.models.TrgovackiLanci import TrgLanci


def read_data_file(lanac: TrgLanci, file_path: Path) -> Optional[DataFrame]:
    """
    Čitanje datoteke sa cijenama sa lokalnog diska.

    Args:
        lanac (TrgLanci): Trgovački lanac.
        file_path (Path): Putanja datoteke sa lokalnog diska.

    Returns:
        Optional[DataFrame]: DataFrame sa podacima ili None ako nema podataka.

    Raises:
         FileNotFoundError: Ako datoteka nije pronađena.
         EmptyDataError: Ako je datoteka prazna ili nema validne podatke.
         ParserError: Ako se dogodila greška prilikom parsiranja (krivi delimiter ili format datoteke).
         UnicodeDecodeError: Ako je greška u encodingu.
         MemoryError: Ako je datoteka prevelika za učitavanje.
    """
    try:
        if not os.access(file_path, os.R_OK):
            logging.error(f"Nema prava za čitanje datoteke: {file_path}.")
            return None

        if not os.path.exists(file_path):
            logging.error(f"Datoteka {file_path} ne postoji.")
            raise FileNotFoundError(f"Datoteka {file_path} ne postoji.")

        if not str(file_path).lower().endswith(".csv"):
            logging.warning(f"Datoteka {file_path} nema ekstenziju .csv.")

        df = pd.read_csv(
            file_path,
            sep=lanac.separator,
            header=0,
            encoding="utf-8",
            na_values=[""],
            skipinitialspace=True,
            on_bad_lines="warn",
        )

        return df
    except FileNotFoundError:
        logging.error(f"Datoteka {file_path} nije pronađena!")
        return None
    except pd.errors.EmptyDataError:
        logging.error(f"Datoteka {file_path} je prazna ili nema validne podatke!")
        return None
    except pd.errors.ParserError as e:
        logging.error(
            f"Greška prilikom parsiranja {file_path}. Provjeriti delimiter ili format datoteke: {e}"
        )
        return None
    except UnicodeDecodeError as e:
        logging.error(f"Greška u encodingu za {file_path}: {e}")
        return None
    except MemoryError:
        logging.error(
            f"Datoteka {file_path} je prevelika za učitavanje u memoriju (koristiti chunksize)! "
        )
        return None
    except Exception as e:
        logging.error(f"Dogodila se greška: {e}")
        return None


def remove_decimals(value: Any) -> Any:
    """
    Provjerava da li cijena ima više od 2 decimalna mjesta, ako ima,
    postavlja na 2 decimalna mjesta.

    Args:
        value (Any): Vrijednost pročitana iz datoteke (stupci koji sadrže cijene).

    Returns:
        Any: Vrijednost nakon provjere.
    """
    if str(value) != "nan":
        value_str = str(value).strip()

        if "." not in value_str:
            return value_str
        else:
            if len(value_str.split(".")) > 2:
                return value
            integer_part, decimal_part = value_str.split(".")
            decimal_part = decimal_part[:2]

        return f"{integer_part}.{decimal_part.ljust(2, '0')}"
    return value


def to_decimal(value: Any) -> Any:
    """
    Konverzija vrijednosti u decimalni broj sa dva decimalna mjesta.

    Args:
        value (Any): Vrijednost pročitana iz datoteke (stupci koji sadrže cijene).

    Returns:
        Decimal: U ovisnosti o proslijeđenoj vrijednosti: 0 ili decimalni broj
    """
    try:
        if (
            value is None
            or value == ""
            or (isinstance(value, float) and math.isnan(value))
        ):
            return Decimal("0")
        if isinstance(value, str):
            value = value.replace(",", ".")
            if value == "":
                return Decimal("0")
        return Decimal(str(value)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError, decimal.InvalidOperation):
        # Ovo je zakomentirano jer ima jako puno non numeric vrijednosti pa da ne guši log file.
        # logging.warning(f'Neispravna numerička vrijednost: {value} (type: {type(value)}), koristim 0.')
        return Decimal("0")


def add_leading_zero(value: Any) -> Any:
    """
    Dodavanje 0 ispred cijene manje od 1.
    Pojedini trgovački lanci stavljaju cijenu kao ',99'.

    Args:
        value (Any):  Vrijednost pročitana iz datoteke (stupci koji sadrže cijene).

    Returns:
        Any: Vrijednost nakon dodavanja 0 ako je potrebno.
    """
    if str(value)[0] == ",":
        return f"0{str(value)}"
    return value


def create_folders(file_path: str) -> None:
    """
    Kreiranje foldera za datoteke ako ne postoji na lokalnom disku.

    Args:
        file_path (str): Putanja na disku gdje se spremaju datoteke.
    """
    try:
        if not os.path.exists(file_path):
            os.makedirs(file_path)
    except Exception as e:
        logging.error(
            f"Dogodila se greška prilikom kreiranja foldera: {file_path}: {e}"
        )
