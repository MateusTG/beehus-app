from core.connectors.base import BaseConnector
from core.schemas.messages import ScrapeResult
import logging
from typing import Dict, Any

import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, date
import asyncio

from core.utils.date_utils import get_previous_business_day

logger = logging.getLogger(__name__)

PAIR_RE = re.compile(r"(\d)\s*ou\s*(\d)")


class ItauOnshoreConnector(BaseConnector):
    @property
    def name(self):
        return "itau_onshore_login"


    # Helper log function (similar to tasks.py)
    def make_run_logger(self, logger, run):
        async def log(msg):
            logger.info(f"[Itau Onshore] {msg}")
            if run:
                timestamped_msg = f"[{datetime.now().time()}] {msg}"
                await run.update({"$push": {"logs": timestamped_msg}})
        return log


    # mapeia teclado digital de senha
    def build_digit_to_button_map(self, driver, timeout=50):
        wait = WebDriverWait(driver, timeout)
        
        container = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.it-auth-keyboard__digits"))
        )
        # pega apenas botões "normais" (exclui o de apagar)
        buttons = container.find_elements(
            By.CSS_SELECTOR, "button.it-auth-keyboard__digit:not(.it-auth-keyboard__digit--remove)"
        )

        digit_to_btn = {}
    
        for btn in buttons:
            label = btn.text.strip()
        
            m = PAIR_RE.search(label)
        
            if not m:
                continue
        
            d1, d2 = m.group(1), m.group(2)
        
            digit_to_btn[d1] = btn
            digit_to_btn[d2] = btn

        # valida se mapeou tudo (0-9)
        missing = [str(d) for d in range(10) if str(d) not in digit_to_btn]
    
        if missing:
            raise RuntimeError(f"Não consegui mapear estes dígitos no teclado: {missing}")

        return digit_to_btn

    # dias uteis
    def get_previous_business_day(self, ref_date = None, region = "BR", state = "SP", days = 1):
        return get_previous_business_day(ref_date, region, state, days)


    # funcao de scrape - navegado passo a passo
    async def scrape(self, driver, params: Dict[str, Any]) -> ScrapeResult:

        # Import models here to avoid circular imports if any, or ensuring context
        from core.models.mongo_models import Run
        from core.db import init_db

        # await init_db()
        run_id = params.get("run_id")
        run = None
        # Ensure DB is ready? tasks.py usually already init_db, but safe to ignore if already done
        run = await Run.get(run_id) if run_id else None

        # iniciando log de execucao
        log = self.make_run_logger(logger, run)

        logger.info(f"Starting Itau Login with params: {params}")

        # pegar agencia e conta
        agencia = params.get("agencia")
        conta = params.get("conta_corrente") or params.get("conta")

        # Support both 'user' (from legacy) and 'username' (from new UI)
        cpf_assessor = params.get("username") or params.get("user") # itau usa cpf como usuario
        password = params.get("password") or params.get("pass")
        
        # Validate credentials are present
        if not cpf_assessor or not password:
            error_msg = f"Missing credentials - username: {cpf_assessor is not None}, password: {password is not None}"
            logger.error(error_msg)
            await log(f"❌ {error_msg}")
            await log(f"📋 Available params: {list(params.keys())}")
            return ScrapeResult(
                run_id=run_id,
                success=False,
                error=error_msg
            )  

        # URL do Itau
        _url = "https://www.itau.com.br"

        try:
            # 1. Navegação
            await log(f"NAVIGATE: {_url}")
            driver.get(_url)
            
            wait = WebDriverWait(driver, 50)

            # 2. Preenchimento de campos Agencia e Conta
            await log("Waiting for agencia e conta input field...")
            button_id_field = wait.until(
                EC.any_of(
                    EC.element_to_be_clickable((By.ID, "open_modal_more_access")),
                    EC.element_to_be_clickable((By.ID, "open-modal-more-access-zoom")),
                )
            )
            button_id_field.click()
            await log("Clicked more access")

            agencia_id_field = driver.find_element(By.ID, "idl-more-access-input-agency")
            agencia_id_field.send_keys(agencia) 
            await log("Typed agencia")
            
            conta_id_field = driver.find_element(By.ID, "idl-more-access-input-account")
            conta_id_field.send_keys(conta)
            await log("Typed conta")

            # 3. Click Acessar
            await log("Clicking Sign In...")
            try:
                access_in_btn = driver.find_element(By.ID, "idl-more-access-submit-button")
                access_in_btn.click()

            except Exception:
                 # Fallback to type=submit if ID changes
                 await log("Fallback: Finding access button...")
                 access_in_btn = driver.find_element(By.CSS_SELECTOR, "button[type='button'][aria-label='Acessar']")
                 access_in_btn.click()
            
            await log("Clicked Access")

            # 3. Selecao de tipo usuario
            await log("Waiting for Assessores button...")
            try:
                nome_id_field = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[title='Selecionar Assessores'][role='button']"))
                )
            except Exception:
                nome_id_field = wait.until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "ASSESSORES"))
                )

            nome_id_field.click()
            await log("Clicked Name (Assessores)")

            # 4. Preenchimento de campos CPF
            # cpf
            await log("Preenchendo CPF...")
            cpf_id_field = wait.until(
                EC.element_to_be_clickable((By.ID, "cpf"))
            )
            cpf_id_field.send_keys(cpf_assessor)
            await log("Typed CPF")
            
            # <button _ngcontent-juu-c53="" class="it-button it-button--private" id="submitBtn" type="button" disabled="" customlinkanalytics="" openmodalonclickanalytics=""><!----> acessar </button>
            submit_btn = driver.find_element(By.ID, "submitBtn")
            submit_btn.click()
            await log("Clicked Submit")

            # senha - vai ter que achar botao correspondente no corpo do html e clicar
            await log("Preenchendo Senha...")
            wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.it-auth-keyboard__digits"))
            )

            digit_to_btn = self.build_digit_to_button_map(driver)

            for d in password:
                btn = digit_to_btn[d]
                wait.until(EC.element_to_be_clickable(btn))
                btn.click()
           
            continuar_btn = driver.find_element(By.ID, "submitBtn")
            continuar_btn.click()
            await log("Clicked Continuar")

            #####
            # Menu
            # <a href="javascript:;" aria-expanded="false" class="btn-nav btn-menu btn-menubg" tabindex="0"><span class="ico-header ico-header-menu icon-itaufonts_menu_hamburguer"></span>menu</a>
            menu_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn-nav.btn-menu.btn-menubg"))
            )
            ActionChains(driver).move_to_element(menu_btn).perform()
            await log("Hovered Menu")

            # Abre Menu
            # <li class=" ">
            #    <a onclick="GA.pushMegaMenu('investimentos','investimentos/posicaoDiaria');dispararEventoTagueamento('');toggleMenuGA4Event('2', 'posição diária', 'investimentos','homeCategoria');" data-op="feVpOPOaCl/BfhRY7cmrKq9VuTKSGqvdEangFQOHTws=;" href="javascript:;" tabindex="0">
            #        posição diária
            #    </a>    
            #    <span class="item-menu-novo">novo</span>                                      
            # </li>
            posicao_diaria = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(@onclick,\"posicaoDiaria\") or normalize-space()='posição diária']"
                ))
            )
            posicao_diaria.click()
            await log("Clicked Position Diaria")
            
            # Relatorio
            # <button _ngcontent-ng-c2437018688="" role="tab" type="button" class="ids-tabs__item ids-tabs__item--selected" id="ids-tabs-0-5" tabindex="0" aria-selected="true" aria-controls="ids-tabs-0-panel-5"><!----><span _ngcontent-ng-c2437018688="" class="ids-tabs__text">Relatórios</span><!----></button>
            relatorio_tab = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(@class,'ids-tabs__item')][.//span[normalize-space()='Relatórios']]"
                ))
            )
            relatorio_tab.click()
            await log("Clicked Relatorio Tab")
            
            # Data Posicao
            # <button _ngcontent-ng-c2437018688="" role="tab" type="button" class="ids-tabs__item ids-tabs__item--selected" id="ids-tabs-0-5" tabindex="0" aria-selected="true" aria-controls="ids-tabs-0-panel-5"><!----><span _ngcontent-ng-c2437018688="" class="ids-tabs__text">Relatórios</span><!----></button>
            data_posicao = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(@class,'ids-tabs__item')][.//span[normalize-space()='Data Posição']]"
                ))
            )
            data_posicao.click()
            await log("Clicked Data Posicao")
            
            # Data
            # <button _ngcontent-ng-c67500750="" class="btn-chip"> 07/01/2026 <ids-icon _ngcontent-ng-c67500750="" size="S" class="ids-icon ids-icon--small notranslate"><span aria-hidden="true">seta_cima_achatada</span></ids-icon><!----></button>
            data_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(@class,'btn-chip')][.//span[normalize-space()='Data Posição']]"
                ))
            )

            current_date_text = data_btn.text.strip()
            current_date = datetime.strptime(current_date_text, "%d/%m/%Y").date()

            expected_previous = get_previous_business_day(ref_date=datetime.today().date())

            if current_date != expected_previous:
                # Atualiza a data (ex.: abrindo o seletor e escolhendo o dia útil anterior)
                data_btn.click()
                expected_label = expected_previous.strftime("%d/%m/%Y")
                wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//button[contains(@class,'btn-chip')][contains(normalize-space(), '{expected_label}')]")
                    )
                ).click()
            else:
                data_btn.click()
            await log("Clicked Data")
            
            # confirmar
            # <button idsmainbutton="" _nghost-ng-c3171858074="" class="ids-main-button" tabindex="0"><span _ngcontent-ng-c3171858074="" class="ids-main-button__content">Confirmar</span><!----></button>
            confirmar_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(@class,'ids-main-button')][.//span[normalize-space()='Confirmar']]"
                ))
            )
            confirmar_btn.click()
            await log("Clicked Confirmar")
            
            # Formato Excel
            # <ids-form-selection><div class="ids-form-selection"><div class="ids-form-selection__input"><span class="ids-radio-button"><input type="radio" idsradiobutton="" name="undefined" value="2" aria-invalid="false" id="ids-radio-button-8" aria-labelledby="ids-radio-button-8-label" class="ids-radio-button__input"><i aria-hidden="true" class="ids-icon ids-icon--medium ids-radio-button__icon"></i></span></div><label class="ids-form-selection__label ids-label" for="ids-radio-button-8" id="ids-radio-button-8-label" aria-hidden="true"><span class="ids-label"> Excel </span></label></div></ids-form-selection>
            formato_excel = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//ids-form-selection//span[contains(@class,'ids-label')][.//span[normalize-space()='Excel']]"
                ))
            )
            formato_excel.click()
            await log("Clicked Formato Excel")
            
            # Botao "Baixar relatorio"
            # <button idsmainbutton="" _nghost-ng-c3171858074="" class="ids-main-button"><span _ngcontent-ng-c3171858074="" class="ids-main-button__content"> Baixar relatório <ids-icon class="ids-icon notranslate"><span aria-hidden="true">download_base</span></ids-icon></span><!----></button>
            download_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(@class,'ids-main-button')][.//span[normalize-space()='Baixar relatório']]"
                ))
            )
            download_btn.click()
            await log("Clicked Download")
            
            # Sair
            # <a onclick="GA.pushHeader('botaoSair');triggerGA4Event('click', 'header:sair');" data-op="fm7xOEMMTW4yb9LvLQQy2nI6Tfx4JaM1cDkBFLiOOQU=;" role="button" id="linkSairHeader" class="btn-nav" href="" tabindex="0" accesskey="S">
			#	<span class="ico-header ico-header-seguranca icon-itaufonts_full_seguranca"></span>sair
			# </a>
            sair_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(@class,'btn-nav')][.//span[normalize-space()='sair']]"
                ))
            )
            sair_btn.click()
            await log("Clicked Sair")

            # Confirmar
            # <a href="#" data-op="v2df1WXu4Zb/2n8VQdGYaRwz6SA0MjB+xqSyHX1zuBs=;" onclick="sair();" class="itau-button btn-fluxo margem-direita5 left"><span>sim</span></a>
            confirmar_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(@class,'itau-button')][.//span[normalize-space()='sim']]"
                ))
            )
            confirmar_btn.click()
            await log("Clicked Confirmar")
            #####
            



            # Aguarda o tempo solicitado
            await log("✅ Login Success! Sleeping for 120s for visual verification...")
            await asyncio.sleep(120)

            return ScrapeResult(
                run_id=run_id,
                success=True,
                data={"message": "Logged in successfully", "cpf": cpf_assessor}
            )

        except Exception as e:
            await log(f"❌ Erro durante o login Itau Onshore: {str(e)}\nAgencia:{agencia}\nConta:{conta}")
            
            # Capture Debug Screenshot
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"/app/artifacts/error_itauonshore_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                await log(f"📸 Screenshot salvo em: {screenshot_path}")
            except Exception as ss_e:
                await log(f"⚠️ Falha ao salvar screenshot: {ss_e}")
            
            # DEBUG: Wait for 2 minutes on error to allow visual inspection via VNC
            await log("⏸️ Pausando por 120s para inspeção visual (erro)...")
            await asyncio.sleep(120)
            
            return ScrapeResult(
                run_id=run_id,
                success=False,
                error=str(e)
            )
