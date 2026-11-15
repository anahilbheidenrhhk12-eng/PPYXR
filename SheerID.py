import time
import asyncio
from datetime import date, timedelta
import threading
import os
import db
import pickle
import random
import string
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from browser import get_driver, Proxy_Test
from selenium.webdriver.common.action_chains import ActionChains
import sys
from selenium.webdriver.support.ui import Select
import requests 
from GetPDFdoc import GetPDFfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import BadRequest

from Edx import Proxies, proxy_locks, proxies_initialized, proxy_lock_obj, ensure_proxies, get_any_available_proxy

# --- NON-BLOCKING ASYNC ELEMENT WAITER ---
async def async_wait_for_element(driver, selector, by=By.XPATH, timeout=10, condition="visible"):
    """Non-blocking wait for DOM elements using asyncio.sleep."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            elements = driver.find_elements(by, selector)
            if elements:
                elem = elements[0]
                if condition == "visible" and elem.is_displayed():
                    return elem
                elif condition == "clickable" and elem.is_displayed() and elem.is_enabled():
                    return elem
                elif condition == "presence":
                    return elem
        except Exception:
            pass
        await asyncio.sleep(0.4)
    raise TimeoutException(f"Element '{selector}' ({by}) not found within {timeout}s")


def IsTextVisible(driver, search_string):
    try:
        visible_text = driver.find_element(By.TAG_NAME, "body").text
        return search_string in visible_text
    except Exception as e:
        print(f"[-] Error scanning text: {e}")
        return False


async def human_scroll_to_center(driver, element, do_check_scroll=False):
    """Smoothly scrolls an element to the middle of the screen using native wheel events."""
    delta_y = driver.execute_script("""
        var rect = arguments[0].getBoundingClientRect();
        var elementCenter = rect.top + (rect.height / 2);
        var viewportCenter = window.innerHeight / 2;
        return Math.round(elementCenter - viewportCenter);
    """, element)

    target_scroll = delta_y + random.randint(-35, 35)

    if abs(target_scroll) > 50:
        remaining = target_scroll
        while abs(remaining) > 0:
            step_size = random.randint(140, 260)
            step = remaining if abs(remaining) <= step_size else (step_size if remaining > 0 else -step_size)

            actions = ActionChains(driver)
            actions.scroll_by_amount(0, int(step)).perform()
            remaining -= step
            await asyncio.sleep(random.uniform(0.12, 0.30))

        await asyncio.sleep(random.uniform(0.3, 0.5))

    if do_check_scroll:
        check_amount = random.randint(80, 140)
        ActionChains(driver).scroll_by_amount(0, check_amount).perform()
        await asyncio.sleep(random.uniform(0.4, 0.7))
        ActionChains(driver).scroll_by_amount(0, -check_amount).perform()
        await asyncio.sleep(random.uniform(0.4, 0.8))


async def human_move_to_element(driver, element):
    await human_scroll_to_center(driver, element)

    action = ActionChains(driver)
    width = element.size['width']
    height = element.size['height']
    
    max_x = int(width / 2) - 2
    max_y = int(height / 2) - 2
    
    x_offset = random.randint(-max_x, max_x) if max_x > 0 else 0
    y_offset = random.randint(-max_y, max_y) if max_y > 0 else 0
    
    action.move_to_element_with_offset(element, x_offset, y_offset)
    action.pause(random.uniform(0.1, 0.4))
    action.perform()


async def Human_Insert(driver, PATH, Data, check_after=False):
    input_field = await async_wait_for_element(driver, PATH, timeout=10, condition="visible")
    
    await human_move_to_element(driver, input_field)

    actions = ActionChains(driver)
    actions.move_to_element(input_field)
    actions.pause(random.uniform(0.4, 1.4))
    actions.click()
    actions.perform()
    
    await asyncio.sleep(random.uniform(0.3, 0.6))
    input_field.clear()
    
    await asyncio.sleep(random.uniform(0.5, 1.8)) 
    
    data_length = len(Data)
    middle_pause_index = random.randint(data_length // 4, (data_length * 3) // 4) if data_length > 3 else -1

    for index, char in enumerate(Data):
        if index == middle_pause_index:
            await asyncio.sleep(random.uniform(0.7, 1.4))
        
        if char == '@':
            await asyncio.sleep(random.uniform(0.6, 1.1))
        elif not char.isalnum():
            await asyncio.sleep(random.uniform(0.15, 0.35))
            
        input_field.send_keys(char)
        await asyncio.sleep(random.uniform(0.05, 0.20)) 

    await asyncio.sleep(random.uniform(0.6, 1.2))

    if check_after:
        check_dist = random.randint(100, 150)
        ActionChains(driver).scroll_by_amount(0, check_dist).perform()
        await asyncio.sleep(random.uniform(0.5, 0.8))
        ActionChains(driver).scroll_by_amount(0, -check_dist).perform()
        await asyncio.sleep(random.uniform(0.6, 1.0))


async def HumanClick(driver, PATH):
    button = await async_wait_for_element(driver, PATH, timeout=10, condition="clickable")

    await human_move_to_element(driver, button)

    actions = ActionChains(driver)
    actions.move_to_element(button)
    actions.pause(random.uniform(0.5, 1.5))
    actions.click()
    actions.perform()

    await asyncio.sleep(random.uniform(1.5, 3.5))


async def Upload_Document(driver, PDF_DOC, SHEER_ID_LINK):
    FILE_INPUT_XPATH = "//input[@type='file' and contains(@accept, '.pdf')]"
    
    for attempt in range(3):
        file_inputs = driver.find_elements(By.XPATH, FILE_INPUT_XPATH)
        if file_inputs:
            break
        await asyncio.sleep(3)
    
    if file_inputs:
        print("  [ + ] PDF Document Insertion Input Field FOUND 🟢\n")
        file_input = file_inputs[0]
        absolute_file_path = os.path.abspath(PDF_DOC)
        file_input.send_keys(absolute_file_path)
        print("  [ + ] File attached successfully without opening the OS popup 🟢")
    else:
        print("  ⛔ File input element not found.")
        return "error"

    SUBMIT_DOC_XPATH = "//button[contains(@id, 'sid-submit-doc-upload') or .//span[normalize-space(text())='Submit']]"
    submit_doc_buttons = driver.find_elements(By.XPATH, SUBMIT_DOC_XPATH)

    if submit_doc_buttons:
        submit_button = submit_doc_buttons[0]
        is_disabled = submit_button.get_attribute("aria-disabled")
        
        if is_disabled == "false":
            await HumanClick(driver, SUBMIT_DOC_XPATH)
            print("  [ + ] Document 'Submit' button clicked successfully 🟢")
            return "success"
        else:
            print("  ⛔ Submit button is present but disabled. Ensure the document was attached properly.")
            return "error"
    else:
        print("  ⛔ Document 'Submit' button not found, skipping.")
        return "error"


EMAIL = "ramie132321zaba@gmail.com"
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

TARGET_MONTH = random.choice(MONTHS).capitalize()
TARGET_DAY = str(random.randint(1, 28))
TARGET_YEAR = str(random.randint(2002, 2006))

async def SheerID(update: Update, context: ContextTypes.DEFAULT_TYPE):
    SHEER_ID_LINK = update.message.text.strip()
    
    user = update.effective_user
    username = f"@{user.username}" if user.username else str(user.id)
    full_name = "Unknown"
    driver = None
    current_proxy = None

    try:
        if not SHEER_ID_LINK.startswith("http"):
            text = (
                "⚠️ <b>Invalid Link!</b>\n\n"
                "Please enter a valid URL (starting with https://):"
            )
            keyboard = [[InlineKeyboardButton("🚫 Cancel", callback_data="dash_back", style="danger")]]
            return await update.message.reply_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode=ParseMode.HTML
            )

        context.user_data.pop('waiting_for_sheerid_link', None)
        
        # 1. Initialize Proxy Environment
        if not proxies_initialized:
            sent_message = await update.message.reply_text(
                '<tg-emoji emoji-id="5287292843763713628">🚀</tg-emoji>   <b>Checking Proxies   <tg-emoji emoji-id="5287292843763713628">🚀</tg-emoji></b>\n\n<i><tg-emoji emoji-id="5976614478928679990">🚀</tg-emoji> Testing working proxies, please wait...</i>',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Testing Proxies...", callback_data="noop", style="primary", icon_custom_emoji_id="5427181942934088912")]]),
                parse_mode=ParseMode.HTML
            )
            
            if not await ensure_proxies():
                await sent_message.edit_text('<tg-emoji emoji-id="5846210329700217522">🚀</tg-emoji> No working proxies found!', parse_mode=ParseMode.HTML)
                raise Exception("No working proxies found!")
        else:
            sent_message = await update.message.reply_text(
                '<tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji> <b>Processing Your Link</b>\n━━━━━━━━━━━━━━━━━━\n<i>Opening SheerID Link...</i>',
                parse_mode=ParseMode.HTML
            )

        text = (
            f'<tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji> <b>Processing Your Link</b> <tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>\n'
            f'━━━━━━━━━━━━━━━━━━\n'
            f'<tg-emoji emoji-id="5379742233853451967">🚀</tg-emoji> <b>Opening The SheerID Link:</b> \n\n'
        )
        keyboard = [[InlineKeyboardButton(" Processing Link", callback_data="dash_back", style="primary", icon_custom_emoji_id="5427181942934088912")]]
        
        await sent_message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

        current_proxy = await get_any_available_proxy()
        print(f"  [ Initial ]  Proxy=>{current_proxy}")
        
        # Non-blocking browser startup & navigation
        driver = await asyncio.to_thread(get_driver, proxy=current_proxy)

        await asyncio.to_thread(driver.get, "https://youtube.com/")
        await asyncio.to_thread(driver.switch_to.new_window, 'tab')

        print("  [ + ] Opening SheerID Link \n")
        await asyncio.to_thread(driver.get, SHEER_ID_LINK)

        FOUND = False
        for attempt in range(5):
            if IsTextVisible(driver, "Verify your student status"):
                print("  [ + ] SheerID Link Verified Working !\n")
                FOUND = True
                await sent_message.edit_text(
                    f'<tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>  <b>Processing Your Link</b>  <tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>\n'
                    f'━━━━━━━━━━━━━━━━━━\n'
                    f'<tg-emoji emoji-id="5379742233853451967">🚀</tg-emoji> <b>Opened The SheerID Link Successfully.</b> \n\n',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Processing Link...", callback_data="noop", style="success", icon_custom_emoji_id="5427181942934088912")]]),
                    parse_mode=ParseMode.HTML
                )                
                break
            await asyncio.sleep(3)

        if not FOUND:
            raise Exception("SheerID Link Failed")

        await asyncio.to_thread(db.insert_sheerid_request, username, "Unknown", SHEER_ID_LINK)
        
        lang_input = await async_wait_for_element(driver, "changeLanguageSelector-input", by=By.ID, timeout=10, condition="presence")
        current_language = lang_input.get_attribute("value")

        if current_language != "English":
            print(f"  [ + ] Current language is '{current_language}'. Changing to English...")
            
            toggle_button = await async_wait_for_element(driver, "changeLanguageSelector-toggle-button", by=By.ID, timeout=5, condition="clickable")
            driver.execute_script("arguments[0].click();", toggle_button)
            
            await sent_message.edit_text(
                f'<tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>  <b>Processing Your Link</b>  <tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>\n'
                f'━━━━━━━━━━━━━━━━━━\n'
                f'<tg-emoji emoji-id="5192670896006897974">🚀</tg-emoji> <b>Inserting SheerID DATA .</b> \n\n',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Processing Link...", callback_data="noop", style="success", icon_custom_emoji_id="5427181942934088912")]]),
                parse_mode=ParseMode.HTML
            )
            
            ENGLISH_OPTION_XPATH = "//div[@id='changeLanguageSelector-menu']//*[normalize-space(text())='English']"
            english_option = await async_wait_for_element(driver, ENGLISH_OPTION_XPATH, timeout=5, condition="clickable")
            
            driver.execute_script("arguments[0].click();", english_option)
            print("  [ + ] Language successfully changed to English 🟢")
        else:
            print("  [ + ] Language is already set to English. No action needed 🟢")

        await asyncio.sleep(3)

        COUNTRY_INPUT_XPATH = "//input[@id='sid-country']"
        await Human_Insert(driver, COUNTRY_INPUT_XPATH, "Morocco")
        
        MOROCCO_OPTION_XPATH = "//div[@id='sid-country-menu']//*[normalize-space(text())='Morocco']"
        morocco_option = await async_wait_for_element(driver, MOROCCO_OPTION_XPATH, timeout=5, condition="clickable")
        driver.execute_script("arguments[0].click();", morocco_option)
        print("  [ + ] Morocco typed and selected successfully 🟢")

        school_input_xpath = "//input[@id='sid-college-name']"
        school_inputs = driver.find_elements(By.XPATH, school_input_xpath)

        if school_inputs:
            await Human_Insert(driver, school_input_xpath, "1337")
            SCHOOL_OPTION_XPATH = "//div[@id='sid-org-list-menu']//div[@role='option'][.//span[contains(text(), 'مدرسة 1337')] and .//span[contains(text(), 'خريبكة')]]"
            
            try:
                target_school_option = await async_wait_for_element(driver, SCHOOL_OPTION_XPATH, timeout=8, condition="clickable")
                driver.execute_script("arguments[0].click();", target_school_option)
                print("  [ + ] 1337 Campus selected successfully 🟢")
            except TimeoutException:
                print("  ⛔ The specific 1337 Khouribga option never appeared in the dropdown.")
                raise Exception("error message")
        else:
            print("  ⛔ School input field not found, skipping.")
            raise Exception("error message")

        from GetPDFdoc import load_users 
        f_names, l_names = load_users()

        FIRST_NAME = random.choice(f_names)
        LAST_NAME = random.choice(l_names)
        full_name = f'{FIRST_NAME} {LAST_NAME}'

        print(f"\n  - - - - - Data - - - - - \n\n  FirstName : {FIRST_NAME} ; LastName : {LAST_NAME}\n")

        FIRST_NAME_INPUT_XPATH = "//input[@id='sid-first-name']"
        first_name_inputs = driver.find_elements(By.XPATH, FIRST_NAME_INPUT_XPATH)
        if first_name_inputs:
            await Human_Insert(driver, FIRST_NAME_INPUT_XPATH, FIRST_NAME)
        else:
            print("  ⛔ First name input field not found, skipping.")
            raise Exception("error message")

        LAST_NAME_INUT_XPATH = "//input[@id='sid-last-name']"
        last_name_inputs = driver.find_elements(By.XPATH, LAST_NAME_INUT_XPATH)
        if last_name_inputs:
            await Human_Insert(driver, LAST_NAME_INUT_XPATH, LAST_NAME)
        else:
            print("  ⛔ Last name input field not found, skipping.")
            raise Exception("error message")

        # Birthdate Month
        month_inputs = driver.find_elements(By.XPATH, "//input[@id='sid-birthdate__month']")
        if month_inputs:
            await Human_Insert(driver, "//input[@id='sid-birthdate__month']", TARGET_MONTH)
            month_option_xpath = f"//div[@id='sid-birthdate__month-menu']//*[normalize-space(text())='{TARGET_MONTH}']"
            try:
                month_option = await async_wait_for_element(driver, month_option_xpath, timeout=5, condition="clickable")
                driver.execute_script("arguments[0].click();", month_option)
                print(f"  - Month '{TARGET_MONTH}' selected successfully.")
            except TimeoutException:
                print(f"  ⛔ The month option '{TARGET_MONTH}' never appeared in the dropdown menu.")
                raise Exception("error message")
        else:
            print("  ⛔ Birthdate month input not found, skipping.")
            raise Exception("error message")

        # Birthdate Day
        day_inputs = driver.find_elements(By.XPATH, "//input[@id='sid-birthdate-day']")
        if day_inputs:
            await Human_Insert(driver, "//input[@id='sid-birthdate-day']", TARGET_DAY)
            print(f"  - Day '{TARGET_DAY}' filled.")
        else:
            print("  ⛔ Birthdate day input not found, skipping.")
            raise Exception("error message")

        # Birthdate Year
        year_inputs = driver.find_elements(By.XPATH, "//input[@id='sid-birthdate-year']")
        if year_inputs:
            await Human_Insert(driver, "//input[@id='sid-birthdate-year']", TARGET_YEAR)
            print(f"  - Year '{TARGET_YEAR}' filled.")
        else:
            print("  ⛔ Birthdate year input not found, skipping.")
            raise Exception("error message")

        # Email
        email_inputs = driver.find_elements(By.XPATH, "//input[@id='sid-email']")
        if email_inputs:
            await Human_Insert(driver, "//input[@id='sid-email']", EMAIL, check_after=True)
        else:
            print("  ⛔ Email input not found, skipping.")
            raise Exception("error message")

        SUBMIT_XPATH = "//button[@id='sid-submit-wrapper__collect-info']"
        submit_buttons = driver.find_elements(By.XPATH, SUBMIT_XPATH)

        if submit_buttons:
            submit_button = submit_buttons[0]
            is_disabled = submit_button.get_attribute("aria-disabled")
            
            if is_disabled == "false":
                await HumanClick(driver, SUBMIT_XPATH)
                print("  [ + ] Submit button clicked successfully 🟢")
                PDF_DOC_Process = asyncio.create_task(asyncio.to_thread(GetPDFfile, FIRST_NAME, LAST_NAME))
                await sent_message.edit_text(
                    f'<tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>  <b>Processing Your Link</b>  <tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>\n'
                    f'━━━━━━━━━━━━━━━━━━\n'
                    f'<tg-emoji emoji-id="5192670896006897974">🚀</tg-emoji> <b>Submitted Document.</b> \n\n',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Processing Link...", callback_data="noop", style="success", icon_custom_emoji_id="5427181942934088912")]]),
                    parse_mode=ParseMode.HTML
                )
            else:
                if IsTextVisible(driver, "Unable to confirm you are human"):
                    print("  [ + ] Detected as BOT !\n")
                    raise Exception("Unable to Confirm you are human")
                else:
                    print("  ⛔ Submit button found but disabled.")
                    raise Exception("error message")
        else:
            print("  ⛔ Submit button not found, skipping.")
            raise Exception("error message")

        ORIGIN_TAB = driver.current_window_handle
        
        for attempts in range(3):
            if IsTextVisible(driver, "Verify using your school credentials") or IsTextVisible(driver, "Upload proof of enrollment"):
                print("  [ + ] DATA INSERTION PHASE PASSED 🟢\n")
                await sent_message.edit_text(
                    f'<tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>  <b>Processing Your Link</b>  <tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>\n'
                    f'━━━━━━━━━━━━━━━━━━\n'
                    f'<tg-emoji emoji-id="5382026293166489702">🚀</tg-emoji> <b>SheerID DATA Insertion Successful.</b> \n\n',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Processing Link...", callback_data="noop", style="success", icon_custom_emoji_id="5427181942934088912")]]),
                    parse_mode=ParseMode.HTML
                )
                break
            if IsTextVisible(driver, "We couldn't continue your verification"):
                print("  [ + ] DATA INSERTION PHASE FAILED ⛔\n")
                raise Exception("  [ + ] Send New link")
            await asyncio.sleep(3)

        if not IsTextVisible(driver, "Upload proof of enrollment"):
            SIGNIN_TO_YOURSCHOLL = "//button[@id='sid-submit-btn-sso']"
            sso_buttons = driver.find_elements(By.XPATH, SIGNIN_TO_YOURSCHOLL)
            if sso_buttons:
                await HumanClick(driver, SIGNIN_TO_YOURSCHOLL)
                print("  [ + ] SSO 'Sign in to your school' button clicked successfully 🟢")
            else:
                print("  ⛔ SSO 'Sign in' button not found, skipping.")
                raise Exception("error message")

            driver.switch_to.window(ORIGIN_TAB)
            print("  [ + ] SWITCHED BACK TO ORIGIN TAB 🔙")

        UPLOAD_XPATH = "//button[contains(@class, 'sid-sso-pending-submit-btn') or .//span[normalize-space(text())='Upload Proof of Enrollment']]"
        flag = 0
        while flag < 3:
            upload_buttons = driver.find_elements(By.XPATH, UPLOAD_XPATH)
            if upload_buttons:
                await HumanClick(driver, UPLOAD_XPATH)
                print("  [ + ] 'Upload Proof of Enrollment' button clicked successfully 🟢")
            else:
                print("  [ + ] 'Upload Proof of Enrollment' button not found, Checking Other Button.")
                FILE_INPUT_XPATH = "//input[@type='file' and contains(@accept, '.pdf')]"    
                file_inputs = driver.find_elements(By.XPATH, FILE_INPUT_XPATH)
                if file_inputs:
                    print("  [ + ] Jumping Directly to Next Button !")
                    break
                await asyncio.sleep(3)
            flag += 1

        if IsTextVisible(driver, "Upload proof of enrollment"):
            print("  [ + ] 🟢 FOUND Upload Proof of Enrollment : PAGE [📃]\n")
        else:
            print("  ⛔ ERROR Upload Proof of Enrollment : PAGE [📃]\n")
            raise Exception("error message")

        PDF_DOC = await PDF_DOC_Process
        await Upload_Document(driver, PDF_DOC, SHEER_ID_LINK)

        flag = 0
        while flag < 5:
            if IsTextVisible(driver, "Your document was uploaded successfully and is being reviewed."):
                print("  [ + ] Document Uploaded Successfully 🎉!\n")
                await sent_message.edit_text(
                    f'<tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>  <b>Processing Your Link</b>  <tg-emoji emoji-id="5215522595922779944">🚀</tg-emoji>\n'
                    f'━━━━━━━━━━━━━━━━━━\n'
                    f'<tg-emoji emoji-id="5368694620190416501">🚀</tg-emoji> <b>Document Uploaded Successfully <tg-emoji emoji-id="5368694620190416501">🚀</tg-emoji></b> \n\n',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Processing Link...", callback_data="noop", style="success", icon_custom_emoji_id="5427181942934088912")]]),
                    parse_mode=ParseMode.HTML
                )
                break
            else:
                await asyncio.sleep(5)
            flag += 1 

        print("  [ + ] Checking Verification Status 🔍\n")
        flag = 0
        upload_retry_count = 0

        while flag < 24:
            if IsTextVisible(driver, "Congrats, you've been verified"):
                await asyncio.to_thread(db.update_sheerid_status, SHEER_ID_LINK, "verified")
                print("  [ + ] LL777WWWWAAAAA 🎉🎉🎉\n\n")
                await sent_message.edit_text(
                    f'<tg-emoji emoji-id="6206378324273403309">🚀</tg-emoji>  <b>SUCCESSFUL VERIFICATION</b>  <tg-emoji emoji-id="6206378324273403309">🚀</tg-emoji>\n'
                    f'━━━━━━━━━━━━━━━━━━\n'
                    f'<tg-emoji emoji-id="5368694620190416501">🚀</tg-emoji> <b>Verified as Student Successfully.</b> \n\n',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Processing Link...", callback_data="noop", style="success", icon_custom_emoji_id="5427181942934088912")]]),
                    parse_mode=ParseMode.HTML
                )
                break

            elif IsTextVisible(driver, "We were unable to confirm your eligibility") or IsTextVisible(driver, "We couldn't continue your verification"):
                if upload_retry_count < 3:
                    upload_retry_count += 1
                    print(f"  [ + ] Unable to Confirm Eligibility. Retrying Upload ({upload_retry_count}/3) 🔄️\n")
                    
                    await asyncio.to_thread(driver.refresh)
                    await asyncio.sleep(4)
                    
                    status = await Upload_Document(driver, PDF_DOC, SHEER_ID_LINK)
                    if status == "success":
                        flag = 0
                        continue
                    else:
                        print("  ⛔ Retry upload failed to find the elements.")
                
                await asyncio.to_thread(db.update_sheerid_status, SHEER_ID_LINK, "rejected")
                print("  [ + ] Status Verification Rejected (Max Retries Reached) ⛔\n")
                await sent_message.edit_text(
                    f'<tg-emoji emoji-id="6206378324273403309">🚀</tg-emoji>  <b>VERIFICATION REJECTED</b>  <tg-emoji emoji-id="6206378324273403309">🚀</tg-emoji>\n'
                    f'━━━━━━━━━━━━━━━━━━\n'
                    f'<tg-emoji emoji-id="5368694620190416501">🚀</tg-emoji> <b>Your Verification as Student Rejected :)</b> \n\n',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Processing Link...", callback_data="noop", style="success", icon_custom_emoji_id="5427181942934088912")]]),
                    parse_mode=ParseMode.HTML
                )
                break

            else:
                await asyncio.sleep(5)
                flag += 1

    except Exception as e:
        if "Send New link" in str(e):
            await sent_message.edit_text(
                f'<tg-emoji emoji-id="5255955667155434143">🚀</tg-emoji>  <b>SheerID Verification Failed</b>  <tg-emoji emoji-id="5255955667155434143">🚀</tg-emoji>\n'
                f'━━━━━━━━━━━━━━━━━━\n'
                f'<tg-emoji emoji-id="5226886710020820160">🚀</tg-emoji> <b>Get a New Link and Try again Later\n- Contact the Admin if the Problem Persists!</b> \n\n',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(" Back To Menu", callback_data="SheerID", style="danger", icon_custom_emoji_id="5226886710020820160")]]),
                parse_mode=ParseMode.HTML
            )
        elif "SheerID Link Failed" in str(e):
            print("  [ + ] SheerID Link Failed\n")
            await sent_message.edit_text(
                f'<tg-emoji emoji-id="5255955667155434143">🚀</tg-emoji>  <b>SheerID Link Not Working</b>  <tg-emoji emoji-id="5255955667155434143">🚀</tg-emoji>\n'
                f'━━━━━━━━━━━━━━━━━━\n'
                f'<tg-emoji emoji-id="5226886710020820160">🚀</tg-emoji> <b>Check the SheerID Link and Try again Later\n- Contact the Admin if the Problem Persists!</b> \n\n',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(" Back To Menu", callback_data="SheerID", style="danger", icon_custom_emoji_id="5226886710020820160")]]),
                parse_mode=ParseMode.HTML
            )
        else:
            print(f"{e}")
            await sent_message.edit_text(
                f'<tg-emoji emoji-id="5255955667155434143">🚀</tg-emoji>  <b>VERIFICATION FAILED</b>  <tg-emoji emoji-id="5255955667155434143">🚀</tg-emoji>\n'
                f'━━━━━━━━━━━━━━━━━━\n'
                f'<tg-emoji emoji-id="5976614478928679990">🚀</tg-emoji> <b>Try again Later \n- Contact the Admin if the Problem Persists!</b> \n\n',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(" Back To Menu", callback_data="SheerID", style="danger", icon_custom_emoji_id="5226886710020820160")]]),
                parse_mode=ParseMode.HTML
            )

        if driver:
            os.makedirs('./SheerLogs', exist_ok=True)
            screenshot_name = full_name if full_name != "Unknown" else username
            try:
                driver.save_screenshot(f'./SheerLogs/{screenshot_name}.png')
            except Exception:
                pass

    finally:
        if driver:
            try:
                await asyncio.to_thread(driver.quit)
            except Exception:
                pass
        if current_proxy and current_proxy in proxy_locks:
            try:
                proxy_locks[current_proxy].release()
            except Exception:
                pass
            

async def SheerID_Entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    clear_waiting_states(context)
    
    # Activate the waiting status
    context.user_data['waiting_for_sheerid_link'] = True
    
    text = (
        '<tg-emoji emoji-id="5938195768832692153">✅</tg-emoji> <b>GOOGLE STUDENT VERIFICATION (GEMINI PRO 1-YEAR)</b> <tg-emoji emoji-id="5420321583082271289">✅</tg-emoji>\n\n'
       ' <tg-emoji emoji-id="5922693616953725714">✅</tg-emoji> Steps:\n'
        '<tg-emoji emoji-id="5794164805065514131">✅</tg-emoji> Use a <b>US IP/VPN</b> <tg-emoji emoji-id="5447410659077661506">✅</tg-emoji>.\n'
        '<tg-emoji emoji-id="5794085322400733645">✅</tg-emoji> Open https://one.google.com/ai-student.\n'
        '<tg-emoji emoji-id="5794280000383358988">✅</tg-emoji> Select the 1-year student Pro plan and click Verify until the SheerID form appears.\n'
        '<tg-emoji emoji-id="5794241397217304511">✅</tg-emoji> Copy the complete URL from your browser address bar.\n'
        '<tg-emoji emoji-id="5793985348446984682">✅</tg-emoji> Send <b>1–3 URLs</b>, one per line, directly in this chat!\n\n'

        '<tg-emoji emoji-id="5271604874419647061">✅</tg-emoji> <b>Required format:</b>\n'
        '<code>https://services.sheerid.com/verify/...</code>'
    )
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="dash_back", style="danger")]]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

