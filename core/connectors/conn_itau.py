from core.connectors.base import BaseConnector
from core.schemas.messages import ScrapeResult
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class JPMorganConnector(BaseConnector):
    @property
    def name(self):
        return "jpmorgan_login"

    async def scrape(self, driver, params: Dict[str, Any]) -> ScrapeResult:
        logger.info(f"Starting Itau Login with params: {params}")
        
        run_id = params.get("run_id")

        # pegar agencia e conta
        agencia = params.get("agencia")
        conta = params.get("conta")

        # Support both 'user' (from legacy) and 'username' (from new UI)
        user = params.get("username") or params.get("user")
        password = params.get("password")
        


        # Import models here to avoid circular imports if any, or ensuring context
        from core.models.mongo_models import Run
        from core.db import init_db
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from datetime import datetime
        import asyncio

        # Helper log function (similar to tasks.py)
        run = None
        if run_id:
            # Ensure DB is ready? tasks.py usually already init_db, but safe to ignore if already done
            run = await Run.get(run_id)

        async def log(msg):
            logger.info(f"[JPMorgan] {msg}")
            if run:
                run.logs.append(f"[{datetime.now().time()}] {msg}")
                await run.save()

        _url = "https://secure.chase.com/web/auth/?treatment=jpo#/logon/logon/chaseOnline"

        try:
            # 1. Navegação
            await log(f"NAVIGATE: {_url}")
            driver.get(_url)
            
            # 2. Preenchimento de campos
            # id de agencia = "idl-more-access-input-agency"
            # id de conta corrente = "idl-more-access-input-account"
            # <a role="button" href="javascript:selecionarAssessor();" title="Selecionar Assessores" class="itau-button btn-fluxo margem-direita10 margem-baixo10" tabindex="0">ASSESSORES</a>

            # cpf
            # <input _ngcontent-juu-c92="" formcontrolname="cpf" type="tel" id="cpf" autocorrect="off" autocapitalize="off" autocomplete="off" mask="000.000.000-00" required="" class="it-auth-id__input ng-pristine ng-invalid ng-touched">
            # <button _ngcontent-juu-c53="" class="it-button it-button--private" id="submitBtn" type="button" disabled="" customlinkanalytics="" openmodalonclickanalytics=""><!----> acessar </button>

            # senha - vai ter que achar botao correspondente no corpo do html e clicar
            # <input _ngcontent-mds-c86="" id="digital-password" type="password" readonly="" required="" class="it-password-keyboard__input">
            # <div _ngcontent-mds-c85="" class="it-auth-keyboard__digits"><span _ngcontent-mds-c85="" id="feedbackButton" aria-live="assertive" class="it-auth-keyboard__digit--hidden"></span><button _ngcontent-mds-c85="" class="it-auth-keyboard__digit" aria-hidden="false"> 0 ou 9 </button><button _ngcontent-mds-c85="" class="it-auth-keyboard__digit" aria-hidden="false"> 8 ou 3 </button><button _ngcontent-mds-c85="" class="it-auth-keyboard__digit" aria-hidden="false"> 7 ou 5 </button><button _ngcontent-mds-c85="" class="it-auth-keyboard__digit" aria-hidden="false"> 4 ou 6 </button><button _ngcontent-mds-c85="" class="it-auth-keyboard__digit" aria-hidden="false"> 1 ou 2 </button><!----><button _ngcontent-mds-c85="" data-testid="clearButton" aria-label="apagar todo o campo de senha eletrônica" class="it-auth-keyboard__digit it-auth-keyboard__digit--remove" aria-hidden="false"></button></div>

            await log("Waiting for user input field...")
            user_id_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "userId-input-field-input"))
            )
            user_id_field.send_keys(user)
            await log("Typed username")
            
            password_field = driver.find_element(By.ID, "password-input-field-input")
            password_field.send_keys(password)
            await log("Typed password")

            # 3. Click Sign In
            await log("Clicking Sign In...")
            try:
                sign_in_btn = driver.find_element(By.ID, "signin-button")
                sign_in_btn.click()
            except Exception:
                 # Fallback to type=submit if ID changes
                 await log("Fallback: Finding submit button...")
                 sign_in_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                 sign_in_btn.click()
            
            await log("Clicked Sign In")
            
            # Aguarda o tempo solicitado
            await log("✅ Login Success! Sleeping for 120s for visual verification...")
            await asyncio.sleep(120)

            return ScrapeResult(
                run_id=run_id,
                success=True,
                data={"message": "Logged in successfully", "user": user}
            )

        except Exception as e:
            await log(f"❌ Erro durante o login JPMorgan: {str(e)}")
            
            # Capture Debug Screenshot
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"/app/artifacts/error_jpmorgan_{timestamp}.png"
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
