from core.connectors.base import BaseConnector
from core.schemas.messages import ScrapeResult
import logging
from typing import Dict, Any

import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import asyncio


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
