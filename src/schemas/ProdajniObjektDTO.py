import logging
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional

from environs import env
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProdajniObjektOblikEnum(str, Enum):
    """
    Enumeracija za oblik prodajnog objekta.
    """

    CASH = "CASH AND CARRY PRODAVAONICA"
    DISKONT = "DISKONTNA PRODAVAONICA"
    HIPER = "HIPERMARKET"
    MINI = "MINIMARKET"
    PRODAJNO_SKLADISTE = "PRODAJNO SKLADIŠTE CASH AND CARRY"
    SJEDISTE = "SJEDIŠTE"
    SKLADISTE = "SKLADIŠTE ZA TRGOVANJE ROBOM NA VELIKO I MALO"
    SUPER = "SUPERMARKET"
    TRGOVINA = "TRGOVINA"

    @classmethod
    def check_value(cls, oblik: str) -> Optional["ProdajniObjektOblikEnum"]:
        """
        Provjerava da li postoji proslijeđeni oblik na popisu Enum vrijednosti.
        Ako postoji, vrati ProdajniObjektOblikEnum objekt.

        Args:
            oblik (str): Oblik prodajnog objekta proslijeđen iz naziva datoteke.

        Returns:
            Optional["ProdajniObjektOblikEnum"]: ProdajniObjektOblikEnum objekt
                                                 ili None ako ne postoji.
        """
        try:
            return cls(oblik)
        except ValueError:
            return None


# Custom tipovi podataka
PositiveInt = Annotated[int, Field(gt=0, description="Mora biti pozitivan broj")]
NonEmptyStr = Annotated[
    str, Field(min_length=1, description="Ne smije biti prazan string")
]


# noinspection PyNestedDecorators
class ProdajniObjektDTO(BaseModel):
    """
    Pydantic model za podatke o prodajnom objektu.

    Ovaj model predstavlja strukutru podataka za prodajni objekt trgovačkog lanca
    sa automatskom validacijom i serijalizacijom.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        strict=True,
        extra="forbid",
        validate_default=True,
        ser_json_bytes="utf8",
        frozen=True,
        str_strip_whitespace=True,
    )

    pmtl_id: PositiveInt = Field(
        description="ID trgovačkog lanca kojem prodajni objekt pripada"
    )
    pmna_id: PositiveInt = Field(description="ID naselja")
    adresa: NonEmptyStr = Field(description="Adresa prodajnog objekta")
    oblik: NonEmptyStr = Field(description="Oblik prodajnog objekta")
    oznaka: NonEmptyStr = Field(
        description="Oznaka/šifra prodajnog objekta trgovačkog lanca"
    )
    datum_od: NonEmptyStr = Field(
        max_length=10,
        description="Datum od kad tl počinje objavljivati svoje podatke za prodajni objekt",
    )

    @field_validator("datum_od")
    @classmethod
    def validator_datum_od(cls, value: str) -> str:
        """
        Validacija formata i vrijednosti datum_od polja.

        Provjerava da li je datum u ispravnom formatu (dd.mm.YYYY) i da li je
        manji ili jednak trenutnom datumu.

        Args:
            value (str): Datum string za validaciju.

        Returns:
            str: Validirani datum u formatu dd.mm.YYYY.

        Raise:
            ValueError: Ako datum nije u formatu dd.mm.YYYY ili ako je veći od trenutnog datuma.
        """
        datum_po = datetime.strptime(value, env("DATE_FORMAT"))
        trenutni_datum = datetime.strptime(
            datetime.now().strftime(env("DATE_FORMAT")), env("DATE_FORMAT")
        )
        if datum_po > trenutni_datum:
            error_msg = f"Datum {datum_po} ne smije biti veći od trenutnog datuma {trenutni_datum}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        try:
            datetime.strptime(value, env("DATE_FORMAT"))
            return value
        except ValueError as e:
            error_msg = f"Datum {value} mora biti u formatu dd.mm.YYYY!"
            logging.error(error_msg)
            raise ValueError(error_msg) from e

    @staticmethod
    def as_dict(dto_list: List["ProdajniObjektDTO"]) -> List[Dict[str, Any]]:
        """
        Konverzija liste ProdajniObjektDTO u listu dictonarya koristeći Pydantic model_dump
        za serijalizaciju svakog objekta.

        Args:
            dto_list (List[ProdajniObjektDTO]): Lista ProdajniObjektDTO objekata za konverziju.

        Returns:
            List[Dict[str, Any]]: Lista dictionarya objekata koji predstavljaju serijalizirane DTO objekte.
        """
        if not dto_list:
            return []

        return [dto.model_dump() for dto in dto_list]

    def __str__(self) -> str:
        """
        String reprezentacija objekta za logging i debugging.

        Returns:
            str: Kratki opis objekta sa ključnim informacijama.
        """
        return (
            f"ProdajniObjektDTO(id={self.pmtl_id}-{self.pmna_id}, "
            f'adresa="{self.adresa}", oblik={self.oblik.name})'
        )

    def __repr__(self) -> str:
        """
        Detaljana reprezentacija objekta za debugging.

        Returns:
            str: Potpuna reprezentacija objekta sa svim poljima.
        """
        return (
            f"ProdajniObjektDTO(pmtl_id={self.pmtl_id}, pmna_id={self.pmna_id}, "
            f'adresa="{self.adresa}", oblik={self.oblik.name}, '
            f'oznaka="{self.oznaka}", datum_od="{self.datum_od}")'
        )
