import logging
import playwright_setup  # noqa: F401 — sets PLAYWRIGHT_BROWSERS_PATH before playwright loads

playwright_setup.ensure_playwright_chromium()

import asyncio

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger("automation")


class ExtensionError(Exception):
    pass


def _log_prefix(request_id: str | None) -> str:
    return f"request_id={request_id} " if request_id else ""


async def extend_pythonanywhere_webapp(
    username: str,
    password: str,
    *,
    request_id: str | None = None,
) -> dict:
    prefix = _log_prefix(request_id)

    if not username or not password:
        raise ValueError("username and password are required")

    logger.info("%sStarting extension job for username=%s", prefix, username)

    playwright_setup.ensure_playwright_chromium()
    logger.info("%sLaunching headless Chromium", prefix)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            logger.info("%sStep 1/6: Open login page", prefix)
            await page.goto(
                "https://www.pythonanywhere.com/login/",
                wait_until="domcontentloaded",
            )
            logger.info("%sLogin page loaded url=%s", prefix, page.url)

            logger.info("%sStep 2/6: Submit credentials", prefix)
            await page.locator("#id_auth-username").fill(username)
            await page.locator("#id_auth-password").fill(password)
            await page.locator("#id_next").click()
            await page.wait_for_load_state("domcontentloaded")
            logger.info("%sAfter login url=%s", prefix, page.url)

            if "/login" in page.url and await page.locator(".alert-error, .errorlist").count():
                logger.warning("%sLogin failed for username=%s", prefix, username)
                raise ExtensionError("Login failed. Check username and password.")

            logger.info("%sStep 3/6: Open Web apps section", prefix)
            await page.locator("#id_web_app_link").click()
            await page.wait_for_url(f"**/user/{username}/webapps/**", timeout=30_000)
            await page.wait_for_load_state("domcontentloaded")
            logger.info("%sWeb apps page loaded url=%s", prefix, page.url)

            logger.info("%sStep 4/6: Click extend (run until one month)", prefix)
            extend_button = page.locator('form[action$="/extend"] input.webapp_extend')
            await extend_button.wait_for(state="visible", timeout=15_000)
            await extend_button.click()
            await page.wait_for_load_state("domcontentloaded")
            logger.info("%sStep 5/6: Extension form submitted url=%s", prefix, page.url)

            final_url = page.url
            body_text = (await page.inner_text("body")).lower()
            if "extend" not in body_text and "month" not in body_text:
                if await page.locator(".alert-error").count():
                    msg = await page.locator(".alert-error").first.inner_text()
                    logger.warning("%sExtension error banner: %s", prefix, msg.strip())
                    raise ExtensionError(msg.strip() or "Extension failed.")

            logger.info(
                "%sStep 6/6: Extension submitted successfully for username=%s final_url=%s",
                prefix,
                username,
                final_url,
            )
            return {
                "message": "Extension submitted!",
                "username": username,
                "final_url": final_url,
            }
        except PlaywrightTimeoutError as exc:
            logger.error(
                "%sTimed out during automation at url=%s",
                prefix,
                page.url,
                exc_info=exc,
            )
            raise ExtensionError(
                "Timed out waiting for PythonAnywhere. "
                "Check credentials or whether the extend button is available."
            ) from exc
        except ExtensionError:
            raise
        except Exception as exc:
            logger.exception(
                "%sUnexpected automation error at url=%s",
                prefix,
                page.url,
            )
            raise
        finally:
            logger.info("%sClosing browser", prefix)
            await browser.close()


def run_extension(
    username: str,
    password: str,
    *,
    request_id: str | None = None,
) -> dict:
    return asyncio.run(
        extend_pythonanywhere_webapp(username, password, request_id=request_id)
    )
