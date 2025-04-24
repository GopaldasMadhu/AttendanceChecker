from selenium import webdriver
from selenium.webdriver.edge.service import Service
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pywhatkit as kit
from datetime import datetime

# Set the path to msedgedriver.exe
EDGE_DRIVER_PATH = r"C:\Users\DELL\PycharmProjects\Attendance\msedgedriver.exe"

# Initialize Edge WebDriver
service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service)

# Your College Website URL
LOGIN_URL = "http://202.160.160.58:8080/evarsityla/usermanager/loginManager/youLogin.jsp"

# Get today's date in DD-MM-YYYY format
today_date = datetime.today().strftime("%d-%m-%Y")
hour = None

try:
    # Step 1: Open College Website and Login
    driver.get(LOGIN_URL)
    time.sleep(2)  # Wait for page to load

    # Find Username & Password Fields and Enter Credentials
    user_id_field = driver.find_element(By.NAME, "login")
    password_field = driver.find_element(By.NAME, "passwd")

    # Enter values manually
    user_id_field.send_keys(input("Enter YourID: "))
    password_field.send_keys(input("Enter your passwd: "))


    # Submit login
    password_field.send_keys(Keys.RETURN)
    time.sleep(2)

    # Step 2: Navigate to Attendance Page
    driver.find_element(By.LINK_TEXT, "Attendance Abstract").click()
    time.sleep(2)

    # Step 3: Click on Absent Count
    driver.find_element(By.ID, "cmdGo").click()
    time.sleep(2)

    # Step 4: Select Program, Semester, Section, and Hour
    driver.find_element(By.XPATH, "//td[@class='dynaColorTR1']/font").click()
    time.sleep(2)

    driver.find_element(By.XPATH, "//td[@class='dynaColorTR2']/font").click()
    time.sleep(2)
    # Click on "2nd Hour" from Section A
    try:
        hour = int(input("Enter the hour: "))
        xpath_expression = f'//td[contains(@onclick, "funGetStudentdetails(1784,{hour})")]'
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_expression))
        )
        element.click()


        # Switch to new tab if it opens
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])


    except Exception as e:
        print("Error clicking the 2nd Hour link:", e)
        driver.quit()
        exit()

    # Extract absent students' data
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "table1"))
        )

        rows = table.find_elements(By.TAG_NAME, "tr")

        absent_index = 2  # Hardcoded Absent Column Index
        absent_count = 0
        absent_students = []

        for row in rows[1:]:  # Skip header row
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) > absent_index:
                absent_col = cells[absent_index]

                # Check if student is absent
                if "✔️" in absent_col.text or absent_col.find_elements(By.TAG_NAME, "img"):
                    student_name = cells[0].text.strip()
                    register_no = cells[1].text.strip()

                    absent_count += 1  # ✅ Increment only once per student
                    absent_students.append(f"{register_no.ljust(15)} {student_name}")

        # Prepare WhatsApp Message with Proper Formatting
        header = " Roll No                   Name\n" + "-" * 45  # Table header

        formatted_students = "\n".join(absent_students)
        #session_type = "Morning Classes" if hour == 2 else "Afternoon Classes" if hour == 5 else "Classes"
        if hour in (1, 2, 3):
            session_type = "Morning Classes"
        elif hour in (4, 5, 6):
            session_type = "Afternoon Classes"
        else:
            session_type = "Classes"
        message = (
            f"Dear parents,\nThe following students were absent from Today's ({today_date}) {session_type}:\n\n"
            f"{header}\n{formatted_students}\n\n"
            "Kindly ensure regular attendance to avoid any academic impact and 75% of attendance Mandatory.\n\n"
            "Thank you,\nHOD DESK"
        )

        # WhatsApp Group ID (Find from WhatsApp group URL)
        GROUP_ID = "Ewts7wJODiY5Es3N6S4I00"  # Replace with actual group ID
        # GROUP_ID = "FSDhZVYl73Z4hWaXPuLUXe" # absent test group

        # Send message to WhatsApp Group
        kit.sendwhatmsg_to_group_instantly(GROUP_ID, message)
        print("Message sent to WhatsApp group successfully!")

    except Exception as e:
        print("Error reading absent students' data:", e)

finally:
    driver.quit()