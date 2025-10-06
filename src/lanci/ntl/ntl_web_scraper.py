import logging
from datetime import datetime
from decimal import Decimal
from typing import List
from urllib.parse import unquote

from data_utils import create_folders, remove_decimals, to_decimal
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
from environs import env
from web_utils import find_encoding

from src.database.db_connection import OracleDBConn
from src.lanci.ntl.ntl_utils import (
    clean_naziv,
    get_all_files_current_date,
)
from src.models.TrgovackiLanci import TrgLanci
from src.schemas.CijenaDTO import CijenaDTO
from src.schemas.DatotekaDTO import DatotekaDTO, StatusEnum
from src.schemas.ProdajniObjektDTO import ProdajniObjektDTO, ProdajniObjektOblikEnum
from src.utils.file_encoding import change_file_encoding

# Promijeniti ovdje datum kada se dohvaćaju datoteke iz prošlosti i
# metodu ispod koja dohvaća datoteke
datum_cijena = datetime.now().strftime(env("DATE_FORMAT"))
lanac = TrgLanci.NTL
file_path = rf"C:\Cijene\{datum_cijena}\{lanac.name}"
create_folders(file_path)
db = OracleDBConn(lanac.name, run_file=__file__)
db.connect()

inserted_rows = 0

urls = get_all_files_current_date()
# Za datoteke u prošlosti
# urls = get_all_files_past_date(datum_cijena)

for url in urls:
    logging.info(f"Dohvaćam i parsiram datoteku {url}...")
    encoding = find_encoding(url)

    file_name = unquote(url.split("/")[-1])
    file_name_no_ext = file_name[:-4]  # Briše .csv iz naziva datoteke

    try:
        if encoding != "utf-8":
            df = change_file_encoding(url, datum_cijena, file_name, lanac)

            pmtl_id = get_tl_id(db, lanac)
            pmpr_id = get_pravilo_id(db, pmtl_id)
            ducan_id = file_name.split("_")[-6]
            pmpo_id = get_prodajni_objekt_id(db, pmtl_id, ducan_id)

            if not pmpo_id:
                po_dto = ProdajniObjektDTO(
                    pmtl_id=pmtl_id,
                    pmna_id=get_id_naselja(db, file_name.split("_")[2].title()),
                    adresa=file_name.split("_")[1].upper(),
                    oblik=ProdajniObjektOblikEnum.check_value(
                        file_name.split("_")[0].upper()
                    ).value,
                    oznaka=ducan_id,
                    datum_od=datum_cijena,
                )
                insert_new_prodajni_objekt(db, po_dto)
                pmpo_id = get_prodajni_objekt_id(db, pmtl_id, ducan_id)

            dat_dto = DatotekaDTO(
                pmpr_id=pmpr_id,
                pmpo_id=pmpo_id,
                dat_naziv=file_name_no_ext,
                dat_format=lanac.file_ext,
                status=StatusEnum.INIT,
                broj_pohrane=file_name.split("_")[4],
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
            df["Naziv proizvoda"] = df["Naziv proizvoda"].apply(clean_naziv)

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
                        cijena_posebna=Decimal(row.iloc[7]),
                        cijena_najniza_30=Decimal(row.iloc[8]),
                        cijena_sidrena=Decimal(row.iloc[9]),
                        barkod=str(row.iloc[10]),
                        kategorija=str(row.iloc[11]),
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
