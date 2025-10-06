import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import oracledb
from environs import env

from src.logger.Logger import Logger


class OracleDBConn:
    """
    Oracle DB connection manager sa logiranjem.

    Sadrži metode za spajanje na Oracle DB, izvršavanje upita i
    kontroliranje konekcije sa error handlingom i logiranjem.
    """

    def __init__(
        self,
        trgovacki_lanac: str,
        run_file: str = __file__,
        datum: str = str(datetime.now()),
        dir_name: str = env("LOG_DIR_NAME"),
    ) -> None:
        """
        Inicijalizacija Oracle DB konekcije sa logiranjem.

        Args:
            trgovacki_lanac (str): Naziv trgovačkog lanca.
            run_file (str): Ime skripte koja se izvršava (default: trenutna skripta).
            datum (str): Datum za log file (default: trenutni datum).
            dir_name (str): Direktorij u koji se spremaju log fileovi (default: env('LOG_DIR_NAME')).
        """
        self.username: str = env("DB_USERNAME")
        self.password: str = env("DB_PASSWORD")
        self.dsn: str = env("DB_HOST")
        self.connection: Optional[oracledb.Connection] = None
        self.cursor: Optional[oracledb.Cursor] = None
        self.is_connected: bool = False
        # Inicijalizacija Logger klase
        self.logger: Logger = Logger(
            datum=datum,
            run_file=run_file,
            trgovacki_lanac=trgovacki_lanac,
            dir_name=dir_name,
        )

    def connect(self) -> None:
        """
        Kreiranje konekcije na Oracle DB.

        Uspostavlja konekciju sa Oracle DB koristeći podatke iz .env datoteke
        i postavlja cursor za izvršavanje upita.
        """
        if self.is_connected:
            logging.warning("Konekcija već postoji!")
            return

        try:
            logging.info("-" * 100)
            logging.info(f"Spajanje na bazu podataka: {self.dsn}...")

            self.connection = oracledb.connect(
                user=self.username, password=self.password, dsn=self.dsn
            )

            self.cursor = self.connection.cursor()
            # Ovo je potrebno za produkcijsku bazu jer se inače dobije 'ORA 01843:not a valid month' greška
            self.cursor.execute(env("ALTER_SESSION_DATE_FORMAT"))
            self.is_connected = True

            logging.info("Uspješno spajanje na bazu podataka!")
            logging.info("-" * 100)
        except oracledb.Error as e:
            self.is_connected = False
            error_msg = f"Spajanje na bazu podataka nije uspjelo (DB): {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise
        except Exception as e:
            self.is_connected = False
            error_msg = f"Greška prilikom spajanja: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise

    def close(self) -> None:
        """
        Prekidanje konekcije na bazu podataka i zatvaranje cursora.

        Raises:
            oracledb.Error: Ako zatvaranje konekcije nije uspjelo.
            Exception: Za ostale greške tokom zatvaranja.
        """
        if not self.is_connected:
            logging.warning("Konekcija nije aktivna!")
            return

        try:
            if self.cursor:
                self.cursor.close()
                logging.info("Cursor baze podataka zatvoren.")
            if self.connection:
                self.connection.close()
                logging.info("Konekcija s bazom podataka prekinuta.")
        except oracledb.Error as e:
            error_msg = (
                f"Greška prilikom zatvaranja konekcije s bazom podataka (DB): {str(e)}"
            )
            logging.error(error_msg, exc_info=True)
            raise
        except Exception as e:
            error_msg = (
                f"Greška prilikom zatvaranja konekcije s bazom podataka: {str(e)}"
            )
            logging.error(error_msg, exc_info=True)
            raise
        finally:
            self.cursor = None
            self.connection = None
            self.is_connected = False

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[List[Any], int, None]:
        """
        Izvršavanje SQL upita i vraćanje rezultata.

        Args:
            query (str): SQL upit za izvršiti.
            params (Optional[Dict[str, Any]]): Parametri za parametrizirane upite.

        Returns:
            Union[List[Any], int, None]: Rezultati upita (ako postoje).

        Raises:
            RuntimeError: Ako konekcija nije aktivna.
            oracledb.Error: Za Oracle DB greške.
            Exception: Za ostale greške tokom izvršavanja.
        """
        if not self.is_connected or not self.connection or not self.cursor:
            error_msg = "Konekcija s bazom podataka ne postoji!"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            logging.info(f"Izvršavanje upita: {query} za parametre {params}")
            logging.info("-" * 100)

            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            query_type = query.strip().upper()

            if query_type.startswith("SELECT"):
                results = self.cursor.fetchall()
                if results is None:
                    results = []

                logging.info(
                    f"Upit uspješno izvršen, dohvaćeno {len(results)} redaka - {results}"
                )
                logging.info("-" * 100)

                return results
            elif query_type.startswith(("UPDATE", "INSERT", "DELETE")):
                affected_rows = self.cursor.rowcount
                self.connection.commit()

                operation = query_type.split()[0].lower()
                operation_msg = {
                    "update": "ažurirano",
                    "insert": "zapisano",
                    "delete": "obrisano",
                }.get(operation, "zahvaćeno")

                logging.info(
                    f"Upit uspješno izvršen, {operation_msg} {affected_rows} redaka."
                )
                logging.info("-" * 100)

                return affected_rows
            else:
                self.connection.commit()

                logging.info("Upit uspješno izvršen i potvrđen.")
                logging.info("-" * 100)

                return []
        except oracledb.Error as e:
            if "ORA-00001" in str(e):
                warning_msg = f"Preskačem podatke {params} jer već postoji u bazi!"
                logging.warning(f"{warning_msg}\n{e}")
                return 0
            else:
                error_msg = f"Izvršavanje upita nije uspjelo (DB): {str(e)}"
                logging.error(error_msg, exc_info=True)
                self.connection.rollback()
                raise
        except Exception as e:
            error_msg = f"Greška prilikom izvršavanja upita: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.connection.rollback()
            raise

    def execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """
        Izvršavanje batch upita sa dictionary listom parametara.

        Args:
            query (str): SQL upit za izvršiti.
            params_list (List[Dict[str, Any]]): Lista dictionarya sa parametrima.

        Returns:
            int: Broj zapisanih redaka

        Raises:
            RuntimeError: Ako konekcija nije aktivna.
            oracledb.Error: Za Oracle DB greške.
            Exception: Za ostale greške tokom izvršavanja.
        """
        if not self.is_connected or not self.connection or not self.cursor:
            error_msg = "Konekcija s bazom podataka ne postoji!"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        if not params_list:
            logging.warning("Prazna lista parametara za execute_many!")
            return 0

        try:
            logging.info(
                f"Izvršavanje višestrukog upita: {query} s {len(params_list)} parametara..."
            )
            logging.info("-" * 100)

            self.cursor.executemany(query, params_list)
            self.connection.commit()
            affected_rows = self.cursor.rowcount

            logging.info(
                f"Višestruki upit uspješno izvršen, zapisano {affected_rows} redaka."
            )
            logging.info("-" * 100)

            return affected_rows
        except oracledb.Error as e:
            error_msg = f"Izvršavanje batch upita nije uspjelo: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.connection.rollback()
            raise
        except Exception as e:
            error_msg = f"Greška prilikom batch izvršavanja upita: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.connection.rollback()
            raise

    def is_connection_active(self) -> bool:
        """
        Provjera da li je konekcija aktivna.

        Returns:
            bool: True ako je konekcija aktivna, inače False.
        """
        return self.is_connected and self.connection is not None

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Dohvaća informacije o trenutnoj konekciji.

        Returns:
            Dict[str, Any]: Dictionary sa informacijama o konekciji.
        """
        return {
            "is_active": self.is_connection_active(),
            "dsn": self.dsn,
            "username": self.username,
            "connection_object": self.connection is not None,
            "cursor_object": self.cursor is not None,
        }

    def get_script_execution_time(self) -> None:
        """
        Dohvaćanje trajanja izvršavanja skripte iz loggera.
        """
        try:
            self.logger.script_exec_time()
        except Exception as e:
            logging.warning(f"Nije moguće dohvatiti vrijeme izvršavanja: {str(e)}")
            return None

    def __del__(self) -> None:
        """
        Destruktor koji osigurava zatvaranje konekcije.

        Automatski zatvara konekciju kada se objekt briše iz memorije.
        """
        if self.is_connected:
            try:
                self.close()
            except Exception as e:
                logging.warning(
                    f"Greška prilikom automatskog zatvaranja konekcije: {str(e)}"
                )

    def __str__(self) -> str:
        """
        String reprezentacija objekta.

        Returns:
            str: Kratak opis objekta sa statusom konekcije.
        """
        status = "connected" if self.is_connection_active() else "disconnected"
        return f"OracleDBConn(dsn={self.dsn}, status={status})"

    def __repr__(self) -> str:
        """
        Detaljana reprezentacija objekta za debugging.

        Returns:
            str: Potpuna reprezentacija objekta.
        """
        return (
            f'OracleDBConn(dsn="{self.dsn}", username="{self.username}", '
            f"is_connected={self.is_connected})"
        )
