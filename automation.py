import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


class ExtensionError(Exception):
    pass


async def extend_pythonanywhere_webapp(username: str, password: str) -> dict:
    if not username or not password:
        raise ValueError("username and password are required")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(
                "https://www.pythonanywhere.com/login/",
                wait_until="domcontentloaded",
            )

            await page.locator("#id_auth-username").fill(username)
            await page.locator("#id_auth-password").fill(password)
            await page.locator("#id_next").click()
            await page.wait_for_load_state("domcontentloaded")

            if "/login" in page.url and await page.locator(".alert-error, .errorlist").count():
                raise ExtensionError("Login failed. Check username and password.")

            await page.locator("#id_web_app_link").click()
            await page.wait_for_url(f"**/user/{username}/webapps/**", timeout=30_000)
            await page.wait_for_load_state("domcontentloaded")

            extend_button = page.locator('form[action$="/extend"] input.webapp_extend')
            await extend_button.wait_for(state="visible", timeout=15_000)
            await extend_button.click()
            await page.wait_for_load_state("domcontentloaded")

            final_url = page.url
            body_text = (await page.inner_text("body")).lower()
            if "extend" not in body_text and "month" not in body_text:
                # Still treat as success if we reached webapps after click without error banner
                if await page.locator(".alert-error").count():
                    msg = await page.locator(".alert-error").first.inner_text()
                    raise ExtensionError(msg.strip() or "Extension failed.")

            return {
                "message": "Extension submitted!",
                "username": username,
                "final_url": final_url,
            }
        except PlaywrightTimeoutError as exc:
            raise ExtensionError(
                "Timed out waiting for PythonAnywhere. "
                "Check credentials or whether the extend button is available."
            ) from exc
        finally:
            await browser.close()


def run_extension(username: str, password: str) -> dict:
    return asyncio.run(extend_pythonanywhere_webapp(username, password))
