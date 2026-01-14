from dataclasses import dataclass
from selenium.webdriver.common.by import By

@dataclass(frozen=True)
class SeletorItauOnshore:
    MORE_ACCESS_BTN = (By.ID, "open_modal_more_access")
    MORE_ACCESS_BTN_ZOOM = (By.ID, "open-modal-more-access-zoom")

    AGENCY = (By.ID, "idl-more-access-input-agency")
    ACCOUNT = (By.ID, "idl-more-access-input-account")

    ASSESSORES_BTN = (By.CSS_SELECTOR, "a[title='Selecionar Assessores'][role='button']")

    CPF = (By.ID, "cpf")
    SUBMIT_BTN = (By.ID, "submitBtn")

    KEYBOARD = (By.CSS_SELECTOR, "div.it-auth-keyboard__digits")

    SUBMIT_MORE_ACCESS = (By.ID, "idl-more-access-submit-button")
    ACCESS_FALLBACK = (By.CSS_SELECTOR, "button[type='button'][aria-label='Acessar']")


    MENU = (By.CSS_SELECTOR, "a.btn-nav.btn-menu.btn-menubg")

    POSICAO_DIARIA = (By.XPATH, "//a[contains(@onclick,'posicaoDiaria') or normalize-space()='posição diária']")
    RELATORIOS_TAB = (By.XPATH, "//button[contains(@class,'ids-tabs__item')][.//span[normalize-space()='Relatórios']]")
    DATA_POSICAO_TAB = (By.XPATH, "//button[contains(@class,'ids-tabs__item')][.//span[normalize-space()='Data Posição']]")
    CONFIRMAR = (By.XPATH, "//button[contains(@class,'ids-main-button')][.//span[normalize-space()='Confirmar']]")
    EXCEL = (By.XPATH, "//ids-form-selection//span[contains(@class,'ids-label')][.//span[normalize-space()='Excel']]")
    BAIXAR = (By.XPATH, "//button[contains(@class,'ids-main-button')][.//span[contains(normalize-space(),'Baixar relatório')]]")

    SAIR = (By.ID, "linkSairHeader")
    SAIR_SIM = (By.XPATH, "//a[contains(@class,'itau-button')][.//span[normalize-space()='sim']]")
