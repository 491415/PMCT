import logging
from io import BytesIO, StringIO
from pathlib import Path

import chardet
import pandas as pd
from pandas import DataFrame

from src.models.TrgovackiLanci import TrgLanci


def _fix_croatian_characters(text: str) -> str:
    """
    Zamjena heksadecimalnih znakova sa odgovarajućim hrvatskim diakriticima.

    Args:
        text (str): Tekst iz datoteke sa cijenama trgovačkog lanca.

    Returns:
        str: Ispravljen tekst.
    """
    if pd.isna(text) or not isinstance(text, str):
        return text

    replacements = {
        # Windows-1252 mapiranje hrvatskih diakritika
        "\x8a": "š",
        "\x8c": "ć",
        "\x8e": "ž",
        "\x9a": "š",
        "\x9c": "ć",
        "\x9e": "ž",
        "\x90": "đ",
        "\xc8": "č",
        "\xc6": "ć",
        "\xd0": "đ",
        "\xe6": "ć",
        "\xe8": "č",
        "Ù": "Č",
        "¹": "š",
        "¾": "ž",
        "©": "š",
        "®": "ž",
    }

    fixed_text = text

    for hexa, hrv in replacements.items():
        fixed_text = fixed_text.replace(hexa, hrv)

    return fixed_text


def _fix_croatian_csv(
    input_file: str,
    separator: str,
    encoding: str,
    file_name: str,
    output_file: str = None,
    **pandas_kwargs,
) -> DataFrame:
    """
    Čitanje csv datoteke sa krivim encodingom i ispravljanje hrvatskih diakritika.

    Args:
        input_file (str): Datoteka u kojoj se ispravljaju hrvatski znakovi.
        separator (str): Separator da file koji se sprema na disk ima isti separator kao
                         i izvorni file.
        encoding (str): Encoding datoteke koja se ispravlja.
        output_file (str): Lokacija/naziv ispravljene datoteke. Default = None

    Returns:
        DataFrame: Podaci iz konvertirane datoteke.
    """
    if output_file is None:
        output_file = input_file.replace(".csv", "_fixed.csv")

    logging.info(f"Čitanje {file_name} sa encodingom: {encoding}")

    df = pd.read_csv(input_file, encoding=encoding, **pandas_kwargs)

    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = df[column].apply(_fix_croatian_characters)

    # Ispravljanje naziva stupaca
    df.columns = [_fix_croatian_characters(col) for col in df.columns]

    df.to_csv(output_file, sep=separator, encoding="utf-8", index=False)

    return df


def change_file_encoding(
    url: str | BytesIO | StringIO | Path,
    datum_cijena: str,
    file_name: str,
    lanac: TrgLanci,
) -> DataFrame:
    """
    Konverzija u UTF-8 encoding datoteke.

    Args:
        url (str | BytesIO | StringIO): URL datoteke koja se preuzima i konvertira
                                        ili BytesIO za datoteke iz zip foldera
                                        ili StringIO za Spar
                                        ili Path za datoteke spremljene lokalno.
        datum_cijena (str): Datum objave cijena.
        file_name (str): Naziv datoteke.
        lanac (TrgLanci): Naziv trgovačkog lanca.

    Returns:
        DataFrame: Podaci iz konvertirane csv datoteke.
    """
    try:
        df = _fix_croatian_csv(
            url,
            separator=lanac.separator,
            output_file=rf"C:\Cijene\{datum_cijena}\{lanac.name if lanac != TrgLanci.TRGOVINA_KRK else lanac.name.replace('_', ' ')}\{file_name}",
            encoding="windows-1252",  # ili 'windows-1250'
            file_name=file_name,
            sep=lanac.separator,
            header=0,
            na_values=[""],
            skipinitialspace=True,
            on_bad_lines="warn",
        )

        logging.info("Konverzija na utf-8 uspješna!")
        logging.info(100 * "-")

        return df
    except Exception as e:
        logging.error(f"Dogodila se greška prilikom promjene encodinga: {e}")
        raise


def detect_local_file_encoding(file_path: Path) -> str:
    """
    Dohvaća se encoding sa datoteke koja se nalazi na lokalnom disku.

    Args:
        file_path (Path): Path datoteke sa lokalnog diska.

    Returns:
        str: Encoding datoteke.
    """
    logging.info(f"Dohvaćam encoding datoteke {file_path}...")

    with open(file_path, "rb") as file:  # Open in binary mode
        raw_data = file.read()
        result = chardet.detect(raw_data)

        logging.info(
            f"Encoding datoteke je {result['encoding']} sa {result['confidence']} confidenca."
        )
        logging.info(100 * "-")

        return result["encoding"]
