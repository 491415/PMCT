import logging
from datetime import datetime
from decimal import Decimal
from typing import List
from urllib.parse import unquote

import pandas as pd
import requests
from data_utils import create_folders, remove_decimals, to_decimal
from db_utils import (
    get_datoteka_id_and_status,
    get_pravilo_id,
    get_prodajni_objekt_id,
    get_tl_id,
    insert_cijene_into_db,
    insert_datoteka_into_db,
    update_datoteka_status,
)
from environs import env
from lxml import etree

from src.database.db_connection import OracleDBConn
from src.lanci.vrutak.vrutak_utils import get_all_files
from src.models.TrgovackiLanci import TrgLanci
from src.schemas.CijenaDTO import CijenaDTO
from src.schemas.DatotekaDTO import DatotekaDTO, StatusEnum

datum_cijena = datetime.now().strftime(env("DATE_FORMAT"))
lanac = TrgLanci.VRUTAK
file_path = rf"C:\Cijene\{datum_cijena}\{lanac.name}"
create_folders(file_path)
db = OracleDBConn(lanac.name, run_file=__file__)
db.connect()

inserted_rows = 0

for url in get_all_files(datum_cijena):
    file_name = unquote(url.split("/")[-1])
    file_name_no_ext = file_name[:-4]  # Briše .xml iz naziva datoteke

    logging.info(f"Dohvaćam i parsiram datoteku {file_name}...")

    ducan_id = file_name.split("-")[3]

    try:
        response = requests.get(url)

        with open(rf"{file_path}\{file_name}", "wb") as file:
            file.write(response.content)

        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(response.content, parser=parser)

        oblik = file_name.split("-")[1]

        products_data = []

        for item in root.findall("item"):
            if oblik == "supermarket":
                product_data = {
                    "naziv": item.find("naziv").text,
                    "sifra": item.find("sifra").text,
                    "marka": item.find("marka").text,
                    "nettokolicina": item.find("nettokolicina").text,
                    "mjera": item.find("mjera").text,
                    "mpcijena": item.find("mpcijena").text,
                    "mpcijenamjera": item.find("mpcijenamjera").text,
                    "barkod": item.find("barkod").text,
                    "kategorija": item.find("kategorija").text,
                }

                products_data.append(product_data)

            if oblik == "hipermarket":
                product_data = {
                    "naziv": item.find("naziv").text,
                    "sifra": item.find("sifra").text,
                    "marka": item.find("marka").text,
                    "nettokolicina": item.find("nettokolicina").text,
                    "mjera": item.find("mjera").text,
                    "mpcijena": item.find("mpcijena").text,
                    "mpcijenamjera": item.find("mpcijenamjera").text,
                    "mpcijenasidrena": item.find("mpcijenasidrena").text,
                    "mpcijenasidrenadatum": item.find("mpcijenasidrenadatum").text,
                    "barkod": item.find("barkod").text,
                    "kategorija": item.find("kategorija").text,
                }

                products_data.append(product_data)

        df = pd.DataFrame(products_data)

        metro_cijene = ["mpcijena", "mpcijenamjera"]

        if oblik == "hipermarket":
            metro_cijene.append("mpcijenasidrena")

        for col in metro_cijene:
            if col in df.columns:
                df[col] = df[col].apply(remove_decimals)
                df[col] = df[col].apply(to_decimal)

        pmtl_id = get_tl_id(db, lanac)
        pmpr_id = get_pravilo_id(db, pmtl_id)
        pmpo_id = get_prodajni_objekt_id(db, pmtl_id, ducan_id)

        dat_dto = DatotekaDTO(
            pmpr_id=pmpr_id,
            pmpo_id=pmpo_id,
            dat_naziv=file_name_no_ext,
            dat_format=lanac.file_ext,
            status=StatusEnum.INIT,
            datum_objave=datum_cijena,
            broj_pohrane=file_name.split("-")[-3],
        )

        insert_datoteka_into_db(db, dat_dto)
        pmda_id, dat_status = get_datoteka_id_and_status(db, pmpo_id, datum_cijena)

        if dat_status == StatusEnum.SPREMLJENO_U_BAZI.value:
            logging.info(f"U bazi već postoje cijene za datoteku ID: {pmda_id}")
            logging.info(100 * "-")
            logging.info(100 * "-")
            continue

        cijene_dto: List[CijenaDTO] = []

        if df is not None:
            logging.info(f"Broj praznih ćelija po stupcu:\n{df.isna().sum()}")
            for _index, row in df.iterrows():
                if oblik == "supermarket":
                    cijene = CijenaDTO(
                        pmda_id=pmda_id,
                        naziv_proizv=str(row.iloc[0]),
                        sifra_proizv=str(row.iloc[1]),
                        marka_proizv=str(row.iloc[2]),
                        neto_kolicina=str(row.iloc[3]),
                        jedinica_mjere=str(row.iloc[4]),
                        cijena_mpc=Decimal(row.iloc[5]),
                        cijena_jed_mjere=Decimal(row.iloc[6]),
                        barkod=str(row.iloc[7]),
                        kategorija=str(row.iloc[8]),
                        datum=datum_cijena,
                    )

                    if cijene.cijena_posebna:
                        cijene.cijena_posebna_flag = True
                        cijene.cijena_mpc = cijene.cijena_posebna

                    cijene_dto.append(cijene)

                if oblik == "hipermarket":
                    cijene = CijenaDTO(
                        pmda_id=pmda_id,
                        naziv_proizv=str(row.iloc[0]),
                        sifra_proizv=str(row.iloc[1]),
                        marka_proizv=str(row.iloc[2]),
                        neto_kolicina=str(row.iloc[3]),
                        jedinica_mjere=str(row.iloc[4]),
                        cijena_mpc=Decimal(row.iloc[5]),
                        cijena_jed_mjere=Decimal(row.iloc[6]),
                        cijena_sidrena=Decimal(row.iloc[7]),
                        barkod=str(row.iloc[9]),
                        kategorija=str(row.iloc[10]),
                        datum=datum_cijena,
                    )

                    if cijene.cijena_posebna:
                        cijene.cijena_posebna_flag = True
                        cijene.cijena_mpc = cijene.cijena_posebna

                    cijene_dto.append(cijene)

        inserted_rows += insert_cijene_into_db(db, cijene_dto)
        update_datoteka_status(db, pmpo_id, file_name_no_ext, datum_cijena)
    except Exception as e:
        logging.error(f"Dogodila se greška za {file_name}: {e}")
        raise

logging.info(100 * "-")
logging.info(f"Ukupno zapisano redaka: {inserted_rows}")
db.close()
db.get_script_execution_time()
