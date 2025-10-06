import logging
import re
from datetime import datetime
from enum import Enum, IntEnum
from typing import Annotated, Any, Dict, List, Optional

from environs import env
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StatusEnum(IntEnum):
    """
    Enumeracija za polje statusa datoteke.
    """

    INIT = 0
    SPREMLJENO_U_BAZI = 1
    GRESKA_PRILIKOM_OBRADE = 9


class DatotekaFormatEnum(str, Enum):
    """
    Enumeracija za format datoteke koji se prihvaćaju za datoteke.
    """

    CSV = "CSV"
    XLSX = "XLSX"
    XML = "XML"
    ZIP = "ZIP"


# Custom tipovi podataka
PositiveInt = Annotated[int, Field(gt=0, description="Mora biti pozitivan broj")]
NonEmptyStr = Annotated[
    str, Field(min_length=1, description="Ne smije biti prazan string")
]


# noinspection PyNestedDecorators
class DatotekaDTO(BaseModel):
    """
    Pydantic model za podatke o datoteci sa cijenama.
    """

    model_config = ConfigDict(
        # Validacija podataka tokom dodjeljivanja vrijednosti
        validate_assignment=True,
        # Korištenje enum vrijednosti kod serijalizacije,
        # koristi 0, a ne INIT (primjer iz StatusEnum klase)
        use_enum_values=True,
        # Bolji type safety, npr. ('123' neće biti prihvaćen kao int),
        # ne dozvoljava type coercion (automatska konverzija iz jednog data typea u drugi)
        strict=True,
        # Zabranjuje dodatna polja
        extra="forbid",
        # Validacija default vrijednosti prema constraintovima polja
        validate_default=True,
        # Custom serialization
        ser_json_bytes="utf8",
        # Frozen model (nakon kreacije nije moguće mijenjanje)
        frozen=True,
        # Čišćenje whitespace iz stringova (na početku i na kraju stringa)
        str_strip_whitespace=True,
    )

    # Required polja
    pmpr_id: PositiveInt = Field(description="ID pravila za preuzimanje datoteke")
    pmpo_id: PositiveInt = Field(description="ID prodajnog objekta trgovačkog lanca")
    dat_naziv: NonEmptyStr = Field(
        max_length=4000, description="Naziv učitane datoteke"
    )
    dat_format: DatotekaFormatEnum = Field(description="Format učitane datoteke")
    status: StatusEnum = Field(description="Status preuzimanja datoteke")
    datum_objave: NonEmptyStr = Field(
        max_length=10, description="Datum objave datoteke"
    )

    # Optional polja
    dat_naziv_zip: Optional[str] = Field(
        min_length=1,
        default=None,
        description="Naziv zip datoteke u kojoj se isporučuju cijene (Eurospin, Lidl, Plodine, Studenac) - opcionalno",
    )
    broj_pohrane: Optional[str] = Field(
        min_length=1,
        default=None,
        pattern=r"^[A-Za-z0-9\-_]+$",
        description="Broj pohrane - opcionalno",
    )

    @field_validator("dat_naziv", mode="before")
    @classmethod
    def validate_dat_naziv(cls, value: str) -> str:
        """
        Validacija i čišćenje naziv datoteke. Ne smije bit prazan i ne smije sadržavati
        ne podržane znakove (<,>,:,",/,\\,|,?,*). Također čisti whitespace iz naziva datoteke

        Args:
            value(str): Naziv datoteke.

        Returns:
            str: Validirani naziv datoteke.

        Raises:
            ValueError: Ako je naziv datoteke prazan ili sadrži nepodržane znakove.
        """
        if isinstance(value, str):
            value = value.strip()

        if not value:
            error_msg = "Naziv datoteke ne smije biti prazan!"
            logging.error(error_msg)
            raise ValueError(error_msg)

        if re.search(r'[<>:"/\\|?*]', value):
            error_msg = "Naziv datoteke sadrži ne podržane znakove!"
            logging.error(error_msg)
            raise ValueError(error_msg)

        return value

    @field_validator("datum_objave")
    @classmethod
    def validator_datum_od(cls, value: str) -> str:
        """
        Validacija da li je datum_od u formatu dd.mm.YYYY. i da li je veći
        od trenutnog datuma.

        Args:
            value(str): Datum.

        Returns:
            str: Validirani datum da je u formatu dd.mm.YYYY i da je manji ili jednak od trenutnog datuma.

        Raise:
            ValueError: Ako datum nije u formatu dd.mm.YYYY ili ako je veći od trenutnog datuma.
        """
        datum_dat = datetime.strptime(value, env("DATE_FORMAT"))
        trenutni_datum = datetime.strptime(
            datetime.now().strftime(env("DATE_FORMAT")), env("DATE_FORMAT")
        )
        if datum_dat > trenutni_datum:
            error_msg = "Datum ne smije biti veći od trenutnog datuma"
            logging.error(error_msg)
            raise ValueError(error_msg)

        try:
            datetime.strptime(value, env("DATE_FORMAT"))
            return value
        except ValueError as e:
            error_msg = "Datum od mora biti u formatu dd.mm.YYYY!"
            logging.error(error_msg)
            raise ValueError(error_msg) from e

    @staticmethod
    def as_dict(dto_list: List["DatotekaDTO"]) -> List[Dict[str, Any]]:
        """
        Konverzija liste DatotekaDTO u listu dictonarya koristeći Pydantic model_dump.

        Args:
            dto_list(List['DatotekaDTO']): Lista DatotekaDTO objekata za konverziju.

        Returns:
            List[Dict[str, Any]]: Lista dictionarya koji sadrže DatotekaDTO polja kao vrijednosti.
        """
        return [dto.model_dump() for dto in dto_list]

    def __str__(self) -> str:
        """
        String reprezentacija objekta za logging i debugging.

        Returns:
             str: Kratki opis objekta sa ključnim informacijama.
        """
        return f"DatotekaDTO (id={self.pmpr_id}-{self.pmpo_id}, naziv_datoteke={self.dat_naziv}, status={self.status.name})"

    def __repr__(self) -> str:
        """
        Detaljana reprezentacija objekta za debugging.

        Returns:
            str: Potpuna reprezentacija objekta sa svim poljima.
        """
        return (
            f"DatotekaDTO (pmpr_id={self.pmpr_id}, pmpo_id={self.pmpo_id}, "
            f"dat_format={self.dat_format}, dat_naziv_zip={self.dat_naziv_zip}, "
            f"dat_naziv={self.dat_naziv}, status={self.status.name}), "
            f"datum_objave={self.datum_objave}, broj_pohrane={self.broj_pohrane}"
        )
