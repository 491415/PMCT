import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import List

from data_utils import read_data_file, remove_decimals, to_decimal
from db_utils import (
    get_datoteka_id_and_status,
    get_id_naselja,
    get_pravilo_id,
    get_prodajni_objekt_id,
    get_tl_id,
    insert_cijene_into_db,
    insert_datoteka_into_db,
    insert_new_prodajni_objekt,
    update_datoteka_status,
)

from src.database.db_connection import OracleDBConn
from src.lanci.ktc.ktc_utils import extract_address_city
from src.models.TrgovackiLanci import TrgLanci
from src.schemas.CijenaDTO import CijenaDTO
from src.schemas.DatotekaDTO import DatotekaDTO, StatusEnum
from src.schemas.ProdajniObjektDTO import ProdajniObjektDTO, ProdajniObjektOblikEnum
from src.utils.file_encoding import change_file_encoding, detect_local_file_encoding

datum_cijena = ""
lanac = TrgLanci.KTC
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

            df = None

            if encoding != "utf-8":
                df = change_file_encoding(
                    file_path, datum_cijena, file_path.name, lanac
                )
            else:
                df = read_data_file(lanac, file_path)

            pmtl_id = get_tl_id(db, lanac)
            pmpr_id = get_pravilo_id(db, pmtl_id)
            ducan_id = file_name.split("-")[-4]
            pmpo_id = get_prodajni_objekt_id(db, pmtl_id, ducan_id)

            if not pmpo_id:
                adresa, naselje = extract_address_city(file_name)

                po_dto = ProdajniObjektDTO(
                    pmtl_id=pmtl_id,
                    pmna_id=get_id_naselja(db, naselje),
                    adresa=adresa,
                    oblik=ProdajniObjektOblikEnum.check_value(
                        file_name.split("-")[0].upper()
                    ).value,
                    oznaka=ducan_id,
                    datum_od=datum_cijena,
                )
                insert_new_prodajni_objekt(db, po_dto)
                pmpo_id = get_prodajni_objekt_id(db, pmtl_id, ducan_id)

            dat_dto = DatotekaDTO(
                pmpr_id=pmpr_id,
                pmpo_id=pmpo_id,
                dat_naziv=file_name,
                dat_format=lanac.file_ext,
                status=StatusEnum.INIT,
                datum_objave=datum_cijena,
            )

            insert_datoteka_into_db(db, dat_dto)
            pmda_id, dat_status = get_datoteka_id_and_status(db, pmpo_id, datum_cijena)

            if dat_status == StatusEnum.SPREMLJENO_U_BAZI.value:
                logging.info(f"U bazi već postoje cijene za datoteku ID: {pmda_id}")
                logging.info(100 * "-")
                logging.info(100 * "-")
                continue

            for col in lanac.stupci_cijena:
                if col in df.columns:
                    df[col] = df[col].apply(remove_decimals)
                    df[col] = df[col].apply(to_decimal)

            cijene_dto: List[CijenaDTO] = []

            if df is not None:
                logging.info(f"Broj praznih ćelija po stupcu:\n{df.isna().sum()}")
                for _index, row in df.iterrows():
                    cijene = CijenaDTO(
                        pmda_id=pmda_id,
                        naziv_proizv=str(row.iloc[0]),
                        sifra_proizv=str(row.iloc[1]),
                        marka_proizv=str(row.iloc[2]),
                        neto_kolicina=str(row.iloc[3]),
                        jedinica_mjere=str(row.iloc[4]),
                        cijena_mpc=Decimal(row.iloc[5]),
                        cijena_jed_mjere=Decimal(row.iloc[6]),
                        cijena_posebna=Decimal(row.iloc[10]),
                        cijena_najniza_30=Decimal(row.iloc[9]),
                        barkod=str(row.iloc[7]),
                        kategorija=str(row.iloc[8]),
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
