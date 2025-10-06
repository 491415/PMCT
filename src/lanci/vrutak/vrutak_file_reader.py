import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import List

import pandas as pd
from data_utils import remove_decimals, to_decimal
from db_utils import (
    get_datoteka_id_and_status,
    get_pravilo_id,
    get_prodajni_objekt_id,
    get_tl_id,
    insert_cijene_into_db,
    insert_datoteka_into_db,
    update_datoteka_status,
)
from lxml import etree

from src.database.db_connection import OracleDBConn
from src.models.TrgovackiLanci import TrgLanci
from src.schemas.CijenaDTO import CijenaDTO
from src.schemas.DatotekaDTO import DatotekaDTO, StatusEnum
from src.utils.file_encoding import detect_local_file_encoding

datum_cijena = ""
lanac = TrgLanci.VRUTAK
db = OracleDBConn(lanac.name, run_file=__file__)
db.connect()

inserted_rows = 0

path = Path(rf"C:/Cijene/{datum_cijena}/{lanac.name}")

for file_path in path.iterdir():
    cijene_dto: List[CijenaDTO] = []
    datoteke_dto: List[DatotekaDTO] = []

    if file_path.is_file():
        file_name, ext = os.path.splitext(file_path.name)

        try:
            logging.info(f"Parsiram datoteku {file_name}...")
            encoding = detect_local_file_encoding(file_path)
            logging.info(100 * "-")

            oblik = file_name.split("-")[1]
            pmtl_id = get_tl_id(db, lanac)
            pmpr_id = get_pravilo_id(db, pmtl_id)
            ducan_id = file_name.split("-")[3]
            pmpo_id = get_prodajni_objekt_id(db, pmtl_id, ducan_id)

            dat_dto = DatotekaDTO(
                pmpr_id=pmpr_id,
                pmpo_id=pmpo_id,
                dat_naziv=file_name,
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

            parser = etree.XMLParser(recover=True)
            root = etree.parse(file_path, parser=parser)

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
            update_datoteka_status(db, pmpo_id, file_name, datum_cijena)
        except Exception as e:
            logging.error(f"Dogodila se greška za {file_name}: {e}")
            raise

logging.info(100 * "-")
logging.info(f"Ukupno zapisano redaka: {inserted_rows}")
db.close()
db.get_script_execution_time()
