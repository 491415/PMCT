import decimal
import logging
import math
import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Any, Dict, List, Optional

from environs import env
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Custom tipovi podataka
PositiveInt = Annotated[int, Field(gt=0, description="Must be a positive integer")]
ProductCode = Annotated[
    Optional[str], Field(max_length=50, pattern=r"^[A-Za-z0-9\-_\.]+$")
]
NazivProizvoda = Annotated[str, Field(min_length=1, max_length=200)]


class CijenaDTO(BaseModel):
    """
    Pydantic model za podatke o parsiranim cijenama iz datoteka trgovačkih lanaca.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        strict=False,
        extra="forbid",
        validate_default=True,
        str_strip_whitespace=True,
    )

    # Required polja
    pmda_id: PositiveInt = Field(description="ID datoteke iz koje se čitaju cijene")
    naziv_proizv: NazivProizvoda = Field(description="Naziv proizvoda")

    # Optional polja
    sifra_proizv: ProductCode = Field(default=None, description="Šifra proizvoda")
    marka_proizv: Optional[str] = Field(
        default=None, max_length=50, description="Marka proizvoda"
    )
    neto_kolicina: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Neto količina",
        examples=["0.13 l", "0.13 kg"],
    )
    jedinica_mjere: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Jedinica mjere",
        examples=["ko", "kg", "l"],
    )
    cijena_mpc: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Maloprodajna cijena proizvoda",
    )
    cijena_jed_mjere: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Cijena jedinice mjere",
    )
    cijena_posebna: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Cijena posebna (akcijska)",
    )
    cijena_posebna_flag: Optional[bool] = Field(
        default=False,
        description="Flag koji označava da li postoji posebna (akcijska) cijena",
    )
    cijena_najniza_30: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Najniža cijena u posljednjih 30 dana",
    )
    cijena_sidrena: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Sidrena cijena sa određenim datumom",
    )
    barkod: Optional[str] = Field(
        default=None, max_length=50, description="Barkod proizovda"
    )
    kategorija: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Kategorija proizvoda",
        examples=["HRANA", "ELEKTRONIKA"],
    )
    datum: Optional[str] = Field(
        default=None, max_length=10, description="Datum cijena"
    )

    @field_validator("naziv_proizv", mode="before")
    @classmethod
    def validate_naziv_proizv(cls, value: str) -> str:
        """
        Validacija i čišćenje polja naziv_proizv.

        Args:
            value(str): Naziv proizvoda.

        Returns:
             str: Validiran i očišćen naziv_proizv.

        Raises:
            ValueError: Ako je naziv_proizv prazan/ne postoji.
        """
        if not value or (isinstance(value, str) and not value.strip()):
            error_msg = "Naziv proizvoda je obavezan i ne smije biti prazan."
            logging.error(error_msg)
            raise ValueError(error_msg)

        if isinstance(value, str):
            pattern = r"^[^A-Ža-ž0-9\'].*?(?=[A-Ža-ž0-9\'])"
            value = value.strip()
            # Za slučajeve kada unutar naziva proizvoda postoji više od jednog whitespacea
            value = re.sub(r"\s+", " ", value)
            value = re.sub(pattern, "", value)

        return value.upper()

    @field_validator(
        "sifra_proizv",
        "marka_proizv",
        "neto_kolicina",
        "jedinica_mjere",
        "kategorija",
        mode="before",
    )
    @classmethod
    def validate_optional_str_fields(cls, value: Optional[str]) -> Optional[str]:
        """
        Validacija i čišćenje polja sifra_proizv, marka_proizv, neto_kolicina, jedinica_mjere i kategorija.

        Args:
            value(Optional[str]): Šifra proizvoda/Marka proizvoda/Neto količina/Jedinica mjere/Kategorija.

        Returns:
             Optional[str]: Validiran i očišćen sifra_proizv, marka_proizv, neto_kolicina, jedinica_mjere i kategorija ili None.
        """
        if (
            value is None
            or (isinstance(value, str) and not value.strip())
            or value in ["nan", "0", "#", "NaN", "None", "NONE", "none"]
        ):
            return None

        if isinstance(value, str):
            value = value.strip().upper()

        return value

    @field_validator("sifra_proizv", mode="before")
    @classmethod
    def validate_sifra_proizv(cls, value: Optional[str]) -> Optional[str]:
        """
        Validacija i čišćenje polja sifra_proizv.
        Kod KONZUM-a, šifre proizvoda imaju '.0' kao završetak pa je ovo potrebno.

        Args:
            value(Optional[str]): Šifra proizvoda.

        Returns:
             Optional[str]: Validirana i očišćena šifra proizvoda.
        """
        if isinstance(value, str):
            if value[-2:] == ".0":
                value = value[:-2]

        return value

    @field_validator("neto_kolicina", mode="before")
    @classmethod
    def validate_neto_kolicina(cls, value: Optional[str]) -> Optional[str]:
        """
        Validacija i čišćenje polja neto_kolicina.
        Kod NTL-a, neto_kolicina pocinje sa ',' pa treba dodati 0 ispred.

        Args:
            value(Optional[str]): Neto količina.

        Returns:
            Optional[str]: Validirana i očišćena neto količina.
        """
        if value and value.startswith(","):
            value = f"0{value}"

        return value

    @field_validator("barkod", mode="before")
    @classmethod
    def validate_barkod(cls, value: Optional[str]) -> Optional[str]:
        """
        Validacija i čišćenje polja barkod.

        Args:
            value(Optional[str]): Barkod proizvoda.

        Returns:
             Optional[str]: Validiran i očišćen barkod ili None.
        """
        if (
            value is None
            or (isinstance(value, str) and not value.strip())
            or value == "nan"
        ):
            return None

        if isinstance(value, str):
            value = value.strip()

        # Ovaj uvjet je potreban jer BOSO ima barkod '1234567891234.0'
        if value[-2:] == ".0":
            # logging.warning(f'Barkod ne smije sadržavati sadržavati ".", dobiveno: {value}')
            value = value[:-2]

        if not re.match(r"^[0-9]+$", value):
            # logging.warning(f'Barkod smije sadržavati samo znamenke, dobiveno: {value}')
            return None

        if len(value) < 8 or len(value) > 13:
            # logging.warning(f'Barkod mora imati između 8 i 13 znamenki, dobiveno: {value}')
            return None

        return value

    @field_validator("datum", mode="before")
    @classmethod
    def validate_datum(cls, value: str) -> Optional[str]:
        """
        Validacija polja datum.

        Args:
            value(str): Datum cijena.

        Returns:
             Optional[str]: Validiran datum.

        """
        if value is None:
            return None

        if isinstance(value, str):
            if not value.strip():
                return None

        datum_cij = datetime.strptime(value, env("DATE_FORMAT"))
        trenutni_datum = datetime.strptime(
            datetime.now().strftime(env("DATE_FORMAT")), env("DATE_FORMAT")
        )
        if datum_cij > trenutni_datum:
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

    @field_validator(
        "cijena_mpc",
        "cijena_jed_mjere",
        "cijena_posebna",
        "cijena_najniza_30",
        "cijena_sidrena",
        mode="before",
    )
    @classmethod
    def validate_cijene(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        """
        Validacija polja cijena_mpc, cijena_jed_mjere, cijena_posebna,
        cijena_najniza_30, cijena_sidrena.

        Args:
            value (Optional[Decimal]): cijena_mpc/cijena_jed_mjere/cijena_posebna/cijena_najniza_30/cijena_sidrena

        Returns:
            Optional[Decimal]: Zaokružena cijena na 2 decimale.

        Raises:
            ValueError: Ako cijena nije decimalni broj.
        """
        if (
            value is None
            or value == ""
            or (isinstance(value, float) and math.isnan(value))
        ):
            return None
        if isinstance(value, str):
            value = value.replace(",", ".").strip()

        # DM ima cijenu sa -
        if str(value)[0] == "-":
            value = Decimal(str(value)[1:])

        try:
            return Decimal(str(value)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            error_msg = (
                f"Greška prilikom validacije cijene {value} (type: {type(value)}): {e}"
            )
            logging.error(error_msg)
            return None

    def to_dict(self):
        return {
            "pmda_id": self.pmda_id,
            "naziv_proizv": self.naziv_proizv,
            "sifra_proizv": self.sifra_proizv,
            "marka_proizv": self.marka_proizv,
            "neto_kolicina": self.neto_kolicina,
            "jedinica_mjere": self.jedinica_mjere,
            "cijena_mpc": self.cijena_mpc,
            "cijena_jed_mjere": self.cijena_jed_mjere,
            "cijena_posebna": self.cijena_posebna,
            "cijena_posebna_flag": self.cijena_posebna_flag,
            "cijena_najniza_30": self.cijena_najniza_30,
            "cijena_sidrena": self.cijena_sidrena,
            "barkod": self.barkod,
            "kategorija": self.kategorija,
            "datum": self.datum,
        }

    @staticmethod
    def as_dict(dto_list: List["CijenaDTO"]) -> List[Dict[str, Any]]:
        """
        Konverzija liste CijenaDTO u listu dictonarya koristeći Pydantic model_dump
        za serijalizaciju svakog objekta.

        Args:
            dto_list (List[CijenaDTO]): Lista CijenaDTO objekata za konverziju.

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
        return f"CijenaDTO (pmda_id={self.pmda_id}, naziv_proizv={self.naziv_proizv}"

    def __repr__(self) -> str:
        """
        Detaljana reprezentacija objekta za debugging.

        Returns:
            str: Potpuna reprezentacija objekta sa svim poljima.
        """
        return (
            f"CijenaDTO (pmda_id={self.pmda_id}, naziv_proizv={self.naziv_proizv}, "
            f"sifra_proizv={self.sifra_proizv}, marka_proizv={self.marka_proizv}, "
            f"neto_kolicina={self.neto_kolicina}, jedinica_mjere={self.jedinica_mjere}, "
            f"cijena_mpc={self.cijena_mpc}, cijena_jed_mjere={self.cijena_jed_mjere}, "
            f"cijena_posebna={self.cijena_posebna}, cijena_posebna_flag={self.cijena_posebna_flag}, "
            f"cijena_najniza_30={self.cijena_najniza_30}, cijena_sidrena={self.cijena_sidrena}, "
            f"barkod={self.barkod}, kategorija={self.kategorija}, datum={self.datum}"
        )
