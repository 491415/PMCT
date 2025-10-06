import logging
import os
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from environs import env


class Logger:
    """
    Custom Logger klasa za logiranje sa console i file outputom.
    """

    # Dovoljno ovdje pročitati i koristi se kroz cijeli projekt
    env.read_env()

    def __init__(
        self,
        datum: str,
        run_file: str,
        trgovacki_lanac: str,
        dir_name: str = env("LOG_DIR_NAME"),
    ) -> None:
        """
        Inicijalizacija Logger klase sa podacima o datumu, fileu i trgovačkom lancu.

        Args:
            datum (str): Datum na koji se skripta pokreće.
            run_file (str): File (skripta) koja se pokreće.
            trgovacki_lanac (str): Naziv trgovačkog lanca.
            dir_name (str): Naziv direktorija u koji se log fileovi spremaju (default: Log).
        """
        self.datum: str = datum
        self.app_name: str = env("APP_NAME")
        # Ovdje se sprema u varijablu samo naziv skripte (skripta.py), inače __file__
        # zapisuje putanju skripte ( C:/../../../skripta.py)
        self.run_file: str = os.path.basename(run_file)
        self.trgovacki_lanac: str = trgovacki_lanac
        self.dir_name: str = dir_name
        self.work_dir: Path = Path.cwd()
        self.log_file_path: Optional[Path] = None
        self.start_time: Optional[float] = None

        self._start_logging()

    @staticmethod
    def _validate_inputs(
        self, datum: date, run_file: str, trgovacki_lanac: str, dir_name: str
    ) -> None:
        """
        Validacija input parametara.

        Args:
            datum (date): Datum za validaciju.
            run_file (str): File path za validaciju.
            trgovacki_lanac (str): Naziv trgovačkog lanca za validaciju.
            dir_name (str): Direktorij naziv za validaciju.

        Raises:
            ValueError: Ako neki od parametara nije valjan.
        """
        if not datum or not isinstance(datum, date):
            raise ValueError("Datum mora biti date objekt.")

        if not run_file or not isinstance(run_file, str):
            raise ValueError("run_file mora biti non-empty string.")

        if not trgovacki_lanac or not isinstance(trgovacki_lanac, str):
            raise ValueError("trgovacki_lanac mora biti non-empty string.")

        if not dir_name or not isinstance(dir_name, str):
            raise ValueError("dir_name mora biti non-empty string.")

    def _create_log_directory(self) -> Path:
        """
        Kreira log direktorij ako ne postoji.

        Returns:
            Path: Putanja do log direktorija.

        Raises:
            OSError: Ako kreiranje direktorija nije uspješno.
        """
        log_dir = self.work_dir / self.dir_name

        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            return log_dir
        except OSError as e:
            error_msg = f"Nije moguće kreirati log direktorij '{log_dir}': {str(e)}"
            raise OSError(error_msg) from e

    def _generate_log_filename(self) -> str:
        """
        Generira naziv log filea na osnovu trenutnog vremena i trgovačkog lanca.

        Returns:
            str: Generirani naziv log filea.
        """
        timestamp = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")

        return f"{self.app_name}_{timestamp}_{self.trgovacki_lanac}.log"

    def _init_logging(self) -> None:
        """
        Konfiguracija logging sistema sa file i console handlerima.

        Postavlja osnovne logging postavke, kreira log direktorij i file,
        i konfigurira formatiranje log poruka.
        """
        try:
            log_dir = self._create_log_directory()
            filename = self._generate_log_filename()
            self.log_file_path = log_dir / filename

            # Brisanje postojećih handlera za izbjegavanje duplića
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            logging.basicConfig(
                format="%(asctime)s %(levelname)s: %(message)s",
                level=logging.INFO,
                datefmt="%d.%m.%Y %H:%M:%S",
                handlers=[
                    logging.FileHandler(self.log_file_path, encoding="utf-8"),
                    logging.StreamHandler(),
                ],
                force=True,
            )

        except Exception as e:
            # Fallback na console-only ako file logiranje ne uspije
            logging.basicConfig(
                format="%(asctime)s %(levelname)s: %(message)s",
                level=logging.INFO,
                datefmt="%d.%m.%Y %H:%M:%S",
                handlers=[logging.StreamHandler()],
                force=True,
            )
            logging.warning(
                f"Nije moguće kreirati log file, koristi se samo console logging: {str(e)}"
            )

    def _start_logging(self) -> None:
        """
        Inicijalizacija logiranja i zapisivanje početka izvršavanja skripte.

        Postavlja logging konfiguraciju i zapisuje početne informacije
        o pokretanju skripte sa timestamp-om.
        """
        self._init_logging()
        self.start_time = time.time()

        start_datetime = datetime.fromtimestamp(self.start_time)
        formatted_start = start_datetime.strftime("%d.%m.%Y %H:%M:%S")

        logging.info("-" * 100)
        logging.info(f"Skripta {self.run_file} pokrenuta {formatted_start}.")
        logging.info("-" * 100)

    def script_exec_time(self) -> None:
        """
        Računa i ispisuje ukupno vrijeme izvršavanja skripte.

        Raises:
            RuntimeError: Ako start_time nije postavljen.
        """
        if self.start_time is None:
            error_msg = "Logger nije inicijaliziran - start_time nije postavljen!"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        end = time.time()
        ukupno = end - self.start_time
        formatted_time = f"{ukupno:.2f} sec."

        logging.info("-" * 100)
        logging.info(f"Ukupno vrijeme izvršavanja: {formatted_time}")
        logging.info(
            f'Skripta {self.run_file} završena {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
        )
        logging.info("-" * 100)

    def __str__(self) -> str:
        """
        String reprezentacija Logger objekta.

        Returns:
            str: String opisujući logger konfiguraciju.
        """
        return f"Logger(script='{self.run_file}', lanac='{self.trgovacki_lanac}', app='{self.app_name}')"

    def __repr__(self) -> str:
        """
        Detaljana reprezentacija Logger objekta.

        Returns:
            str: Detaljnan opis Logger objekta.
        """
        return (
            f"Logger(datum={self.datum}, run_file='{self.run_file}', "
            f"trgovacki_lanac='{self.trgovacki_lanac}', dir_name='{self.dir_name}', "
            f"log_file='{self.log_file_path}')"
        )
