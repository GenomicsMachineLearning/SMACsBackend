import pathlib
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "SMACs Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]

    # AWS
    AWS_REGION: str = "ap-southeast-2"

    # Data
    LR_DB_FILE: str = "connectome_cellchat_cellphone_celltalk.txt"
    LR_SUBDIR: str = "LRInteractions"
    GENES_SUBDIR: str = "Genes"

    # Hardcoded Feature Lists
    GENES_LIST: List[str] = ['Apoe', 'B2m', 'Ctsd', 'Grn', 'Apod', 'Cd44', 'Cfh',
                             'Efemp1', 'C1qa', 'Gdf15', 'Agt', 'Ntn4', 'Vegfa', 'Mmp2',
                             'H2-D1', 'H2-K1', 'Trf', 'Anxa2', 'Cst3', 'Anxa1', 'Bgn',
                             'C1qb', 'C4b', 'Cd84', 'Cp', 'Csf1', 'F13a1', 'Lgals1',
                             'Lgals3', 'Ly86', 'Penk', 'Serping1', 'Vwf', 'Sdc1',
                             'Ccl5', 'Cdh4', 'C3', 'Cd248', 'Dkk3', 'Entpd1', 'Pltp',
                             'Ptprc', 'Thy1', 'Tnfsf13b', 'Tnxb', 'Vcam1', 'Adm',
                             'Cd14', 'Icam1', 'Lair1', 'S100a4', 'S100a8', 'Slpi',
                             'Spn', 'Timp1', 'Ccl12', 'Ccn2', 'Lcn2', 'Ftl1', 'Vim',
                             'Itgb1', 'Il2rg', 'Eng', 'Cd63',
                             'Cd74', 'C3ar1', 'C5ar1', 'Cd53', 'Gpnmb', 'Itgal', 'Pirb',
                             'Tlr2', 'Tlr4', 'Cd36', 'Cd72', 'Csf3r', 'Gpc1', 'Itga4',
                             'Itgax', 'Lrp1', 'Cxcr4', 'Il4ra', 'Ramp3', 'Tnfrsf12a',
                             'Trem2', 'Tyrobp']

    LR_PAIRS_LIST: List[str] = ['Bgn_Tlr2', 'Timp1_Itgb1', 'Timp1_Lrp1', 'Lgals3_Itgb3',
                                'C1qa_Cd33', 'Icam1_Itgam', 'Icam1_Itgb2', 'Ccl5_Sdc4',
                                'Gnai2_C5ar1', 'Lgals3_Itgb1', 'C1qb_Cd33',
                                'Ccl5_Ccrl2', 'Vcam1_Itgb2', 'Lgals3_Mertk',
                                'Cd14_Tlr2', 'Cd14_Itgb2', 'Sema6d_Trem2', 'Hmgb1_Tlr1',
                                'Anxa2_Tlr2', 'Mrc1_Ptprc', 'Adam10_Gpnmb',
                                'Angptl2_Pirb', 'Cd14_Tlr4', 'Sema4d_Cd72',
                                'Icam1_Itgax', 'Hmgb1_Tlr2', 'Ccl4_Ccr5',
                                'Lcn2_Slc22a17', 'Plau_Itgb2', 'St6gal1_Cd22',
                                'Bsg_Spn']

    @property
    def DATA_STORAGE_PATH(self) -> pathlib.Path:
        if self.ENVIRONMENT == "production":
            return pathlib.Path("/mnt/data")
        return pathlib.Path("./data")

    @property
    def LR_DB_PATH(self) -> pathlib.Path:
        return self.DATA_STORAGE_PATH / self.LR_DB_FILE

    @property
    def LR_DIR(self) -> pathlib.Path:
        return self.DATA_STORAGE_PATH / self.LR_SUBDIR

    @property
    def GENES_DIR(self) -> pathlib.Path:
        return self.DATA_STORAGE_PATH / self.GENES_SUBDIR

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
