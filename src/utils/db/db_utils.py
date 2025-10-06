import logging
from typing import List

from environs import env

from src.database.db_connection import OracleDBConn
from src.models.TrgovackiLanci import TrgLanci
from src.schemas.CijenaDTO import CijenaDTO
from src.schemas.DatotekaDTO import DatotekaDTO
from src.schemas.ProdajniObjektDTO import ProdajniObjektDTO


def get_tl_id(db: OracleDBConn, lanac: TrgLanci) -> int | None:
    """
    Dohvaćanje ID-a trgovačkog lanca prema proslijeđenom trgovačkom lancu.

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        lanac (TrgLanci): Trgovački lanac.

    Returns:
        int | None: ID trgovačkog lanca ili None ako ga nije moguće pronaći.

    Raises:
        ValueError: Ako se dogodi greška prilikom dohvata ID-a trgovačkog lanca.
    """
    try:
        if lanac == TrgLanci.TRGOVINA_KRK:
            pmtl_id = db.execute_query(
                env("GET_ID_TL"),
                params={"naziv": lanac.name.replace("_", " ").upper()},
            )
        elif lanac == TrgLanci.ZABAC:
            pmtl_id = db.execute_query(
                env("GET_ID_TL"),
                params={"naziv": lanac.name.replace("Z", "Ž").upper()},
            )
        else:
            pmtl_id = db.execute_query(
                env("GET_ID_TL"), params={"naziv": lanac.name.upper()}
            )

        if not pmtl_id:
            logging.warning(
                f"Nije moguće pronaći ID trgovačkog lanca {lanac.name.upper()}!"
            )
            raise
        else:
            pmtl_id = pmtl_id[0][0]

        return pmtl_id
    except Exception as e:
        error_msg = f"Dogodila se greška prilikom dohvaćanja ID-a trgovačkog lanca {lanac.name.upper()}: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg) from e


def get_pravilo_id(db: OracleDBConn, pmtl_id: int) -> int | None:
    """
    Dohvaćanje pravila za trgovački lanac prema proslijeđenom ID-u trgovačkog lanca.

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        pmtl_id (int): ID trgovačkog lanca.

    Returns:
        int | None: ID pravila trgovačkog lanca ili None ako ga nije moguće pronaći.

    Raises:
        ValueError: Ako se dogodi greška prilikom dohvata ID-a pravila za trgovački lanac.
    """
    try:
        pmpr_id = db.execute_query(
            env("GET_PRAVILO_ZA_TL"), params={"pmtl_id": pmtl_id}
        )

        if not pmpr_id:
            logging.warning(
                f"Nije moguće pronaći ID pravila za ID trgovačkog lanca {pmtl_id}!"
            )
            pmpr_id = None
        else:
            pmpr_id = pmpr_id[0][0]

        return pmpr_id
    except Exception as e:
        error_msg = f"Dogodila se greška prilikom dohvaćanja ID-a pravila za trgovački lanac {pmtl_id}: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg) from e


def get_id_naselja(db: OracleDBConn, naziv_naselja: str) -> int:
    """
    Dohvaćanje ID-a naselja za proslijeđeni naziv naselja.

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        naziv_naselja (str): Naziv naselja.

    Returns:
        int: ID naselja.

    Raises:
        ValueError: Ako nije moguće pronaći ID naselja.
    """
    pmna_id = db.execute_query(
        env("GET_ID_NASELJA"), params={"naziv": f"{naziv_naselja}"}
    )

    if not pmna_id:
        error_msg = f"Nije moguće pronaći ID naselja {naziv_naselja}!"
        logging.error(error_msg)
        raise ValueError(error_msg)

    return pmna_id[0][0]


def get_prodajni_objekt_id(db: OracleDBConn, pmtl_id: int, ducan_id: str) -> int:
    """
    Dohvaćanje ID-a prodajnog objekta za proslijeđeni ID trgovačkog lanca i šifru prodajnog objekta.

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        pmtl_id (int): ID trgovačkog lanca.
        ducan_id (int): Šifra prodajnog objekta.

    Returns:
        int: ID prodajnog objekta.

    Raises:
        ValueError: Ako se dogodi greška prilikom dohvata ID-a prodajnog objekta.
    """
    try:
        pmpo_id = db.execute_query(
            env("GET_PRODAJNI_OBJEKT_ID"),
            params={"pmtl_id": pmtl_id, "ducan_id": ducan_id},
        )

        if not pmpo_id:
            logging.warning(
                f"Nije moguće pronaći ID prodajnog objekta {ducan_id} i ID-a trgovačkog lanca {pmtl_id}!"
            )
            pmpo_id = None
        else:
            pmpo_id = pmpo_id[0][0]

        return pmpo_id
    except Exception as e:
        error_msg = f"Dogodila se greška prilikom dohvaćanja ID-a prodajnog objekta {ducan_id} i ID-a trgovačkog lanca {pmtl_id}: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg) from e


def insert_new_prodajni_objekt(db: OracleDBConn, po_dto: ProdajniObjektDTO) -> None:
    """
    Zapisivanje podataka o prodajnom objektu (pogledati DatotekaProdajniObjektDTO objekt).

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        po_dto (ProdajniObjektDTO): Popunjeni DTO objekt sa podacima prodajnom objektu.

    Raises:
        RuntimeError: Ako se dogodi greška prilikom zapisivanja podataka u bazu.
    """
    try:
        db.execute_query(env("INSERT_PRODAJNI_OBJEKT"), params=po_dto.model_dump())
    except Exception as e:
        error_msg = f"Greška prilikom zapisivanja prodajnog objekta: {e}"
        logging.error(error_msg)
        raise RuntimeError(error_msg) from e


def insert_datoteka_into_db(db: OracleDBConn, datoteka_dto: DatotekaDTO) -> None:
    """
    Zapisivanje podataka o datoteci sa cijenama (pogledati DatotekaDTO objekt).

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        datoteka_dto (DatotekaDTO): Popunjeni DTO objekt sa podacima o datoteci sa cijenama.

    Raises:
        RuntimeError: Ako se dogodi greška prilikom zapisivanja podataka u bazu.
    """
    try:
        db.execute_query(env("INSERT_DATOTEKE"), params=datoteka_dto.model_dump())
    except Exception as e:
        error_msg = f"Greška prilikom zapisivanja datoteke: {e}"
        logging.error(error_msg)
        raise RuntimeError(error_msg) from e


def get_datoteka_id_and_status(
    db: OracleDBConn, pmpo_id: int, datum_cijena: str
) -> tuple[int | None, int | None]:
    """
    Doohvaćanje ID-a i statusa datoteke prema ID-u prodajnog objekta i datumu objave cijena.

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        pmpo_id (int): ID prodajnog objekta.
        datum_cijena (str): Datum objave cijena.

    Returns:
        tuple[int | None, int | None]: ID i status datoteke ili None

    Raises:
        ValueError: Ako je došlo do greške prilikom dohvata ID-a i statusa datoteke
        za prodajni objekt i datum objave cijena.
    """
    pmda_id = None
    dat_status = None

    try:
        result = db.execute_query(
            env("GET_ID_STATUS_DATOTEKE"),
            params={"pmpo_id": pmpo_id, "datum_objave": datum_cijena},
        )

        if not result:
            logging.warning(
                f"Nije moguće pronaći ID datoteke za pmpo_id {pmpo_id} i datum objave {datum_cijena}!"
            )
        else:
            pmda_id = result[0][0]
            dat_status = result[0][1]

        return pmda_id, dat_status
    except Exception as e:
        error_msg = f"Došlo je do greške prilikom dohvata ID-a i statusa datoteke za prodajni objekt {pmpo_id}: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg) from e


def insert_cijene_into_db(db: OracleDBConn, cijene_dto: List[CijenaDTO]) -> int:
    """
    Zapisivanje podataka o cijenama u bazu podataka prema proslijeđenoj listi CijenaDTO objekata.

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        cijene_dto (List[CijenaDTO]): lista DTO objekata sa podacima o cijenama.

    Returns:
        int: Broj zapisanih redaka u bazu podataka.

    Raises:
        ValueError: Ako je došlo do greške prilikom zapisivanja cijena u bazu podataka.
    """
    inserted_rows = 0

    try:
        inserted_rows += db.execute_many(
            env("INSERT_CJENICI"), params_list=CijenaDTO.as_dict(cijene_dto)
        )
    except Exception as e:
        error_msg = f"Dogodila se greška prilikom zapisivanja cijena: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg) from e

    return inserted_rows


def update_datoteka_status(
    db: OracleDBConn, pmpo_id: int, file_name: str, datum_cijena: str
) -> None:
    """
    Ažuriranje statusa datoteke nakon zapisivanja podataka o cijenama.

    Args:
        db (OracleDBConn): Konekcija na bazu podataka.
        pmpo_id (int): ID prodajnog objekta.
        file_name (str): Naziv datoteke.
        datum_cijena (str): Datum objave cijena.

    Raises:
        ValueError: Ako je došlo do greške prilikom ažuriranja statusa datoteke.
    """
    try:
        updated_rows = db.execute_query(
            env("UPDATE_STATUS_DATOTEKE"),
            params={
                "pmpo_id": pmpo_id,
                "naziv_datoteke": file_name,
                "datum_objave": datum_cijena,
            },
        )
        logging.info(f"Uspješno ažurirano {updated_rows} datoteka.")
        logging.info(100 * "-")
    except Exception as e:
        error_msg = f"Dogodila se greška prilikom ažuriranja statusa datoteke: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg) from e
