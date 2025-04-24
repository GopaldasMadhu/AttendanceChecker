from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pywhatkit as kit
from datetime import datetime

app = Flask(__name__)

EDGE_DRIVER_PATH = r"C:\Users\DELL\PycharmProjects\Attendance\msedgedriver.exe"
LOGIN_URL = "http://202.160.160.58:8080/evarsityla/usermanager/loginManager/youLogin.jsp"
program_subject_code_map = {
    "M.C.A.-Master of Computer Applications-Regulation 2024": 1784,
    "M.Sc.-Biotechnology-Regulation 2024": 1790,
    "M.Sc.-Organic Chemistry-Regulation 2024": 1789
}
global_hour = None
# Get today's date in DD-MM-YYYY format
today_date = datetime.today().strftime("%d-%m-%Y")


def check_attendance(user_id, password, program_name, semester_name, subject_code, hour):
    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service)
    driver.get(LOGIN_URL)
    try:
        wait = WebDriverWait(driver, 10)
        user_id_field = wait.until(EC.presence_of_element_located((By.NAME, "login")))
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "passwd")))

        user_id_field.send_keys(user_id)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(2)

        # Menu Tab
        menu_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='project-nav']/ul/li[2]/a")))
        menu_tab.click()
        time.sleep(2)

        # Academic
        academic_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='ui-accordion-tabMenu-header-1']")))
        academic_option.click()
        time.sleep(2)

        # Attendance Abstract
        attendance_abstract = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@title='Attendance Abstract']")))
        driver.execute_script("arguments[0].scrollIntoView();", attendance_abstract)
        time.sleep(1)
        attendance_abstract.click()
        time.sleep(2)

        # Absent Count
        driver.find_element(By.ID, "cmdGo").click()
        time.sleep(3)

        # 🔍 Select Program
        program_xpath = f"//tr[td/font[contains(text(), '{program_name}')]]"
        program_row = wait.until(EC.element_to_be_clickable((By.XPATH, program_xpath)))
        program_row.click()  # ✅ safer than JS execution
        time.sleep(2)

        # 💚 Click the Semester row
        semester_rows = driver.find_elements(By.XPATH, "//tr[starts-with(@onclick, 'funAjaxmethod')]")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "table2"))
        )
        for row in semester_rows:
            row.get_attribute("onclick")
            if f'{semester_name}' in row.text:
                driver.execute_script("arguments[0].click();", row)
                break
        time.sleep(3)

        # Construct the XPath using subject code and hour
        xpath_expression = f'//td[contains(@onclick, "funGetStudentdetails({subject_code},{hour})")]'
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_expression))
        )
        element.click()
        time.sleep(3)

        # If new tab opened
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])

        # ⏬ Wait and locate the student table
        table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "table1")))
        rows = table.find_elements(By.TAG_NAME, "tr")

        absent_index = 2
        absent_count = 0
        absent_students = []

        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > absent_index:
                absent_col = cells[absent_index]
                if "✔️" in absent_col.text or absent_col.find_elements(By.TAG_NAME, "img"):
                    student_name = cells[0].text.strip()
                    register_no = cells[1].text.strip()
                    absent_count += 1
                    absent_students.append(f"{register_no.ljust(15)} {student_name}")

        # Prepare WhatsApp Message with Proper Formatting
        header = " Roll No                   Name\n" + "-" * 45  # Table header

        formatted_students = "\n".join(absent_students)
        # session_type = "Morning Classes" if hour == 2 else "Afternoon Classes" if hour == 5 else "Classes"
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
        # group_id = "Ewts7wJODiY5Es3N6S4I00"  # Loyola Parents group ID
        # absent test group
        group_id = "FSDhZVYl73Z4hWaXPuLUXe"

        # Send message to WhatsApp Group
        kit.sendwhatmsg_to_group_instantly(group_id, message)
        print("Message sent to WhatsApp group successfully!")

        return {"status": "success", "message": "Attendance checked successfully!"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        driver.quit()


# ✅ Correctly placed route
@app.route('/')
def home():
    return render_template('index.html')


# ✅ Correctly placed route
@app.route('/check_attendance', methods=['POST'])
def get_attendance():
    user_id = request.form['user_id']
    password = request.form['password']
    program_name = request.form['program_name']
    semester_name = request.form['semester_name']
    subject_code = program_subject_code_map.get(program_name)
    if not subject_code:
        return jsonify({"status": "error", "message": f"Unknown program: {program_name}"})
    selected_hour = int(request.form['hour'])

    result = check_attendance(user_id, password, program_name, semester_name, subject_code, selected_hour)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
