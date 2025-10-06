from enum import Enum
from typing import List

from src.schemas.DatotekaDTO import DatotekaFormatEnum


class TrgLanci(Enum):
    """
    Enum sa listom trgovačkih lanaca sa pripadajućim URL-ovima i separatorima (lanci koji dostavljaju .csv datoteke).
    """

    BOSO = (
        "https://www.boso.hr",
        "https://www.boso.hr/cjenik",
        DatotekaFormatEnum.CSV,
        [
            "MPC",
            "cijena za jedinicu mjere",
            "MPC za vrijeme posebnog oblika prodaje",
            "Najniža cijena u poslj. 30 dana",
            "sidrena cijena na 2.5.2025",
        ],
        ";",
    )

    DM = (
        "https://www.dm.hr",
        "https://content.services.dmtech.com/rootpage-dm-shop-hr-hr/novo/promocije/nove-oznake-cijena-i-vazeci-cjenik-u-dm-u-2906632",
        DatotekaFormatEnum.XLSX,
        [
            "MPC",
            "cijena za jedinicu mjere",
            "MPC za vrijeme posebnog oblika prodaje (Rasprodaja proizvoda koji izlaze iz asortimana)",
            "Najniža cijena u posljednjih 30 dana prije rasprodaje",
            "sidrena cijena na 2.5.2025. ili na datum ulistanja",
        ],
        "",
    )

    EUROSPIN = (
        "https://www.eurospin.hr",
        "https://www.eurospin.hr/cjenik",
        DatotekaFormatEnum.CSV,
        [
            "MALOPROD.CIJENA(EUR)",
            "CIJENA_ZA_JEDINICU_MJERE",
            "MPC_POSEB.OBLIK_PROD",
            "NAJNIŽA_MPC_U_30DANA",
            "SIDRENA_CIJENA",
        ],
        ";",
    )

    KAUFLAND = (
        "https://www.kaufland.hr",
        "https://www.kaufland.hr/akcije-novosti/popis-mpc.assetSearch.id=assetList_1599847924.json",
        DatotekaFormatEnum.CSV,
        [
            "maloprod.cijena(EUR)",
            "cijena jed.mj.(EUR)",
            "MPC poseb.oblik prod",
            "Najniža MPC u 30dana",
            "Sidrena cijena",
        ],
        "\t",
    )

    KONZUM = (
        "https://www.konzum.hr",
        "https://www.konzum.hr/cjenici",
        DatotekaFormatEnum.CSV,
        [
            "MALOPRODAJNA CIJENA",
            "CIJENA ZA JEDINICU MJERE",
            "MPC ZA VRIJEME POSEBNOG OBLIKA PRODAJE",
            "NAJNIŽA CIJENA U POSLJEDNIH 30 DANA",
            "SIDRENA CIJENA NA 2.5.2025",
        ],
        ",",
    )

    KTC = (
        "https://www.ktc.hr",
        "https://www.ktc.hr/cjenici",
        DatotekaFormatEnum.CSV,
        [
            "Maloprodajna cijena",
            "Cijena za jedinicu mjere",
            "Najniža cijena u posljednjih 30 dana",
            "MPC za vrijeme posebnog oblika prodaje",
        ],
        ";",
    )

    LIDL = (
        "https://tvrtka.lidl.hr",
        "https://tvrtka.lidl.hr/cijene",
        DatotekaFormatEnum.CSV,
        [
            "MALOPRODAJNA_CIJENA",
            "CIJENA_ZA_JEDINICU_MJERE",
            "MPC_ZA_VRIJEME_POSEBNOG_OBLIKA_PRODAJE",
            "NAJNIZA_CIJENA_U_POSLJ._30_DANA",
            "Sidrena_cijena_na_02.05.2025",
        ],
        ",",
    )

    METRO = (
        "https://www.metro-cc.hr",
        "https://metrocjenik.com.hr",
        DatotekaFormatEnum.CSV,
        [
            "MPS",
            "CIJENA_PO_MJERI",
            "POSEBNA_PRODAJA",
            "NAJNIZA_30_DANA",
            "SIDRENA_02_05",
        ],
        ",",
    )

    NTL = (
        "https://ntl.hr",
        "https://ntl.hr/cjenik",
        DatotekaFormatEnum.CSV,
        [
            "Maloprodajna cijena",
            "Cijena za jedinicu mjere",
            "MPC za vrijeme posebnog oblika prodaje",
            "Najniža cijena u poslj.30 dana",
            "Sidrena cijena na 2.5.2025",
        ],
        ";",
    )

    PLODINE = (
        "https://www.plodine.hr",
        "https://www.plodine.hr/info-o-cijenama",
        DatotekaFormatEnum.CSV,
        [
            "Maloprodajna cijena",
            "Cijena po JM",
            "MPC za vrijeme posebnog oblika prodaje",
            "Najniza cijena u poslj. 30 dana",
            "Sidrena cijena na 2.5.2025",
        ],
        ";",
    )

    RIBOLA = (
        "https://ribola.hr",
        "https://ribola.hr/ribola-cjenici",
        DatotekaFormatEnum.XML,
        [
            "MaloprodajnaCijena",
            "CijenaPoJedinici",
            "MaloprodajnaCijenaAkcija",
            "NajnizaCijena",
            "SidrenaCijena",
        ],
        "",
    )

    SPAR = (
        "https://www.spar.hr",
        "https://www.spar.hr/usluge/cjenici",
        DatotekaFormatEnum.CSV,
        [
            "MPC (EUR)",
            "cijena za jedinicu mjere (EUR)",
            "MPC za vrijeme posebnog oblika prodaje (EUR)",
            "Najniža cijena u posljednjih 30 dana (EUR)",
            "sidrena cijena na 2.5.2025. (EUR)",
        ],
        ";",
    )

    STUDENAC = (
        "https://www.studenac.hr",
        "https://www.studenac.hr/popis-maloprodajnih-cijena",
        DatotekaFormatEnum.XML,
        [
            "MaloprodajnaCijena",
            "CijenaPoJedinici",
            "MaloprodajnaCijenaAkcija",
            "NajnizaCijena",
            "SidrenaCijena",
        ],
        "",
    )

    TOMMY = (
        "https://www.tommy.hr",
        "https://www.tommy.hr/objava-cjenika",
        DatotekaFormatEnum.CSV,
        ["MPC", "MPC_POSEBNA_PRODAJA", "CIJENA_PO_JM", "MPC_NAJNIZA_30", "MPC_020525"],
        ",",
    )

    TRGOCENTAR = (
        "https://trgocentar.com",
        "https://trgocentar.com/Trgovine-cjenik",
        DatotekaFormatEnum.XML,
        ["mpc", "c_jmj", "mpc_pop", "c_najniza_30", "c_020525"],
        "",
    )

    TRGOVINA_KRK = (
        "https://trgovina-krk.hr",
        "https://trgovina-krk.hr/objava-cjenika",
        DatotekaFormatEnum.CSV,
        [
            "Maloprodajna cijena",
            "Cijena za jedinicu mjere",
            "MPC za vrijeme posebnog oblika prodaje",
            "Najniža cijena u poslj.30 dana",
            "Sidrena cijena na 2.5.2025",
        ],
        ";",
    )

    VRUTAK = (
        "https://www.vrutak.hr",
        "https://www.vrutak.hr/cjenik-svih-artikala",
        DatotekaFormatEnum.XML,
        [],
        "",
    )

    ZABAC = (
        "https://zabacfoodoutlet.hr",
        "https://zabacfoodoutlet.hr/cjenik",
        DatotekaFormatEnum.CSV,
        ["Mpc", "Najniža cijena u posljednjih 30 dana", "Sidrena cijena na 2.5.2025"],
        ",",
    )

    def __init__(
        self,
        base_url: str,
        cijene_url: str,
        file_ext: DatotekaFormatEnum,
        stupci_cijena: List[str],
        separator: str,
    ) -> None:
        """
        Inicijalizacija Enum klase sa podacima o pojedinom trgovačkom lancu.

        Args:
            base_url (str): Glavna stranica trgovačkog lanca.
            cijene_url (str): Stranica cijena trgovačkog lanca (kod nekih je u json obliku).
            file_ext (DatotekaFormatEnum): Ekstenzija datoteka cijena.
            stupci_cijena (List[str]): Stupci/tagovi cijena u datotekama cijena.
            separator (str): Separator csv datoteka.
        """
        self.base_url = base_url
        self.cijene_url = cijene_url
        self.file_ext = file_ext
        self.stupci_cijena = stupci_cijena
        self.separator = separator

    def __str__(self) -> str:
        """
        Enum ime kao string.
        """
        return self.name

    def __repr__(self) -> str:
        """
        Detaljan prikaz za debugging.
        """
        return (
            f"TrgLanci.{self.name}: base={self.base_url}, cijene={self.cijene_url}, file_ext={self.file_ext}, "
            f"separator={self.separator}"
        )
