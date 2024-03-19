import os
from datetime import datetime, timedelta
from tempfile import mkdtemp

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium_stealth import stealth


def init_webdriver():
    # Create Chromeoptions instance
    options = webdriver.ChromeOptions()
    service = webdriver.ChromeService("/opt/chromedriver")

    # * For local dev
    # TODO impl dev environment
    # service = webdriver.ChromeService("./chromedriver.exe")

    options.binary_location = '/opt/chrome/chrome'
    options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1080")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")

    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

    options.add_argument(f'user-agent={user_agent}')
    options.add_argument('--allow-running-insecure-content')

    # Adding argument to disable the AutomationControlled flag
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Exclude the collection of enable-automation switches
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Turn-off userAutomationExtension
    options.add_experimental_option("useAutomationExtension", False)

    # Setting the driver path and requesting a page
    driver = webdriver.Chrome(options=options, service=service)

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    # Changing the property of the navigator value for webdriver to undefined
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


def day_to_offset(day: str) -> int:
    match day:
        case "Mon":
            return 6
        case "Tue":
            return 0
        case "Wed":
            return 1
        case "Thu":
            return 2
        case "Fri":
            return 3
        case "Sat":
            return 4
        case "Sun":
            return 5
        case _:
            # No day of week provided, default to saturday
            return 4


def handler(event, context):
    # Init
    driver = init_webdriver()
    driver.implicitly_wait(int(os.environ.get("WAIT_TIME")))

    # Login
    driver.get(os.environ.get("LOGIN_URL"))
    username = os.environ.get("USERNAME")
    user_input = driver.find_element(By.XPATH,
                                     "//input[@id='weblogin_username']")
    user_input.send_keys(username)
    password_input = driver.find_element(By.XPATH,
                                         "//input[@id='weblogin_password']")
    password_input.send_keys(os.environ.get("PASSWORD"))
    driver.find_element(By.XPATH,
                        "//button[@id='weblogin_buttonlogin']").submit()
    print("signing in as {}".format(username))

    # Use previous session if exists
    try:
        driver.find_element(
            By.XPATH,
            "//button[@id='loginresumesession_buttoncontinue']").click()
        print("using previous session")
    except NoSuchElementException:
        pass

    # Select desired golf course
    course_name = os.environ.get("COURSE_NAME")
    print("course: '{}'".format(course_name))
    match course_name:
        case "Jimmy Clay Golf Course":
            course_code = 1
        case "Roy Kizer Golf Course":
            course_code = 2
        case "Morris Williams Golf Course":
            course_code = 3
        case "Lions Municipal Golf Course":
            course_code = 4
        case "Hancock Golf Course":
            course_code = 5
        case _:
            driver.quit()
            return {
                'message': "unsupported golf course: {}".format(course_name)
            }

    # Wait until 9:00 am CST
    start_time = datetime.today().replace(hour=14,
                                          minute=0,
                                          second=0,
                                          microsecond=0)
    print("waiting until {}... ".format(datetime.now()))
    while True:
        if datetime.now() >= start_time:
            print("starting booking process...")
            break

    driver.get(os.environ.get("URL") + str(course_code))

    date_button = driver.find_element(By.XPATH,
                                      "//button[@id='begindate_vm_4_button']")
    ActionChains(driver).scroll_to_element(date_button).move_to_element(
        date_button).click().perform()

    # * Was having some trouble finding elements on modal
    modal = driver.find_element(By.XPATH, "//div[@role='dialog']")
    modal.find_element(
        By.XPATH,
        '//button[@id="begindate_vm_4_day_selection_button"]').click()
    dropdown = modal.find_element(
        By.XPATH,
        "//div[@class='combobox__dropdown dropdown dropdown--state-open']")

    # Select booking date, assuming today is Tuesday
    book_day = os.environ.get("BOOK_DAY")
    book_date = datetime.today() + timedelta(day_to_offset(book_day))
    print("booking date: '{}'".format(book_date.strftime('%m/%d/%Y')))

    dropdown.find_element(By.XPATH,
                          "//li[@title='{}']".format(book_date.day)).click()

    # ! Click done button
    # ! wasn't able to find this looking for "button" elements
    modal.find_element(
        By.XPATH, "/html/body/div[1]/div/div/div/b/font/b/font/font/font/form\
            /div[1]/div[1]/div[1]/div[3]/div[1]/div/div/button").click()

    # Select earliest desired time
    WANT_TIME = os.environ.get("WANT_TIME")  # ex: '10:00 am'
    time_input = driver.find_element(
        By.XPATH, "/html/body/div[1]/div/div/div/b/font/b/font/font/font\
            /form/div[1]/div[1]/div[1]/div[2]/div[1]/div/input")
    for _ in range(10):
        time_input.send_keys(Keys.BACK_SPACE)
    time_input.send_keys(WANT_TIME)

    # Update available tee times
    search_button = driver.find_element(
        By.XPATH, "//button[@id='grwebsearch_buttonsearch']")
    ActionChains(driver).scroll_to_element(search_button).move_to_element(
        search_button).click().perform()
    try:
        time_table = driver.find_element(
            By.XPATH, "//table[@id='grwebsearch_output_table']")
    except NoSuchElementException:
        no_results = driver.find_element(
            By.XPATH, "//div[@id='grwebsearch_noresultsmessage']/p").text

        assert "Your search did not return any matching results" in no_results

        msg = "no tee times found in search"
        print(msg)
        driver.quit()
        return {'message': msg}

    # Select earliest tee time
    try:
        add_to_cart_button = time_table.find_element(
            By.XPATH, "//tr[1]//a[@data-tooltip='Add To Cart']")
    except NoSuchElementException:
        msg = "no available tee times found"
        print(msg)
        driver.quit()
        return {'message': msg}
    ActionChains(driver).scroll_to_element(add_to_cart_button).move_to_element(
        add_to_cart_button).click().perform()

    # * Book time
    # driver.find_element(
    #     By.XPATH,
    #     "//button[@id='golfmemberselection_buttononeclicktofinish']").click()

    # Confirm checkout confirmation
    try:
        assert "Checkout Confirmation" in driver.title
    except AssertionError:
        # Used to make debugging faster
        driver.quit()
        msg = "did not find confirm text"
        print(msg)
        return {'message': msg}

    confirm_text = driver.find_element(
        By.XPATH, "//div[@id='webconfirmation_emailtext']")
    print("found confirm text")
    receipt_num = confirm_text.find_element(By.XPATH, "//h3").text
    print("found receipt number: {}".format(receipt_num))
    logout_button = driver.find_element(
        By.XPATH, "//a[@id='webconfirmation_buttonlogout']")
    print("found webconfirm logout")
    ActionChains(driver).scroll_to_element(logout_button).move_to_element(
        logout_button).click().perform()

    msg = "successfully booked tee time: receipt #{}".format(receipt_num)
    print(msg)
    driver.quit()
    print("closed driver")
    return {'message': msg}
