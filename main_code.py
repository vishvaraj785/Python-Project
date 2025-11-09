import streamlit as st
import mysql.connector
from datetime import date, datetime
import pandas as pd

class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Suraj@536",
            database="Employee_Payroll_System"
        )
        self.cursor = self.connection.cursor()


    def create_tables(self):
        self.cursor.execute("""
        create table if not exists Employee_Data(
            ID BIGINT AUTO_INCREMENT PRIMARY KEY,
            Name varchar(255),
            Designation varchar(255),
            Age int,
            Salary float,
            Address varchar(255),
            Joining_date Date,
            Password int
        )""")
        try:
            self.cursor.execute("ALTER TABLE Employee_Data AUTO_INCREMENT = 2410303500")
        except Exception:
            pass

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Applications(
            Application_ID INT AUTO_INCREMENT PRIMARY KEY,
            Employee_ID BIGINT,
            Application_Type VARCHAR(255),
            Description TEXT,
            Status VARCHAR(50) DEFAULT 'Pending',
            Remarks TEXT,
            Applied_Date DATE,
            Applied_Time TIME,
            FOREIGN KEY (Employee_ID) REFERENCES Employee_Data(ID)
        )""")
        try:
            self.cursor.execute("ALTER TABLE Applications AUTO_INCREMENT = 1000")
        except Exception:
            pass

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Attendance(
            Attendance_ID INT AUTO_INCREMENT PRIMARY KEY,
            Employee_ID BIGINT,
            Attendance_Date DATE,
            Attendance_Time TIME,
            Status VARCHAR(50),
            FOREIGN KEY (Employee_ID) REFERENCES Employee_Data(ID)
        )""")

        self.cursor.execute("""
        create table if not exists About_Admin(
            Admin_ID varchar(255),
            Password varchar(255)
        )""")

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()



class Employee:
    def __init__(self, db, Employee_ID_Password):
        self.db = db
        self.cursor = db.cursor
        self.Employee_ID_Password = Employee_ID_Password

    def apply_application(self, emp_id, app_type, desc):
        applied_date = date.today()
        applied_time = datetime.now().time()
        ap = """INSERT INTO Applications(Employee_ID, Application_Type, Description, Applied_Date, Applied_Time)
                VALUES (%s, %s, %s, %s, %s)"""
        data = (emp_id, app_type, desc, applied_date, applied_time)
        self.cursor.execute(ap, data)
        self.db.commit()

    def mark_attendance(self, emp_id):
        today = date.today()
        self.cursor.execute("SELECT * FROM Attendance WHERE Employee_ID=%s AND Attendance_Date=%s", (emp_id, today))
        already = self.cursor.fetchone()
        if already:
            return False
        else:
            now = datetime.now()
            status = "Present"
            date_str = today.strftime("%Y-%m-%d")      
            time_str = now.strftime("%H:%M:%S") 
            self.cursor.execute("INSERT INTO Attendance(Employee_ID, Attendance_Date, Attendance_Time, Status) VALUES (%s, %s, %s, %s)", (emp_id, today, now.time(), status))
            self.db.commit()
            return True

    def view_attendance(self, emp_id):
        self.cursor.execute("SELECT Attendance_Date, Attendance_Time, Status FROM Attendance WHERE Employee_ID=%s ORDER BY Attendance_Date DESC", (emp_id,))
        data = self.cursor.fetchall()
        return data

    def Taking_Employee_data(self, name, designation, age, salary, address, joining_date, password):
        self.cursor.execute("""
            INSERT INTO Employee_Data(Name, Designation, Age, Salary, Address, Joining_date, Password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, designation, age, salary, address, joining_date, password))
        self.db.commit()
        self.cursor.execute("SELECT ID FROM Employee_Data WHERE Name = %s ORDER BY ID DESC LIMIT 1", (name,))
        id1 = self.cursor.fetchone()[0]
        self.Employee_ID_Password[id1] = password
        return id1

    def Calculate_Salary(self, emp_id):
        self.cursor.execute("select Salary from Employee_Data where ID = (%s)", (emp_id,))
        result = self.cursor.fetchone()
        if result is not None:
            base_salary = result[0]
            hra = 0.2 * base_salary
            da = 0.1 * base_salary
            gross_salary = base_salary + hra + da
            tax = 0.1 * gross_salary
            net_salary = gross_salary - tax
            return {
                'Base Salary': base_salary,
                'HRA': hra,
                'DA': da,
                'Gross Salary': gross_salary,
                'Tax Deducted': tax,
                'Net Salary': net_salary
            }
        else:
            return None

    def Change_Pass_Emp(self, id1, old_pass, new_pass):
        if id1 in self.Employee_ID_Password and self.Employee_ID_Password[id1] == old_pass:
            self.cursor.execute("update Employee_Data set Password =(%s) where ID = (%s)", (new_pass, id1))
            self.db.commit()
            self.Employee_ID_Password[id1] = new_pass
            return True
        return False

    def View_Details(self, id1):
        self.cursor.execute("select * from Employee_Data where ID = (%s)", (id1,))
        result = self.cursor.fetchone()
        return result

    def view_applications_status(self, emp_id):
        self.cursor.execute("SELECT Application_ID, Application_Type, Status, Remarks FROM Applications WHERE Employee_ID=%s", (emp_id,))
        apps = self.cursor.fetchall()
        return apps


class Admin:
    def __init__(self, db, Admin_ID_Password, Employee_ID_Password):
        self.db = db
        self.cursor = db.cursor
        self.Admin_ID_Password = Admin_ID_Password
        self.Employee_ID_Password = Employee_ID_Password
        self.emp = Employee(db, Employee_ID_Password)

    def registerAdmin(self, admin_login_id, admin_login_pass, new_admin_id, new_admin_pass):
        
        if admin_login_id in self.Admin_ID_Password and self.Admin_ID_Password[admin_login_id] == admin_login_pass:
            self.cursor.execute("insert into About_Admin(Admin_ID, Password) values (%s,%s)", (new_admin_id, new_admin_pass))
            self.db.commit()
            self.Admin_ID_Password[new_admin_id] = new_admin_pass
            return True
        return False

    def view_all_applications(self):
        self.cursor.execute("""SELECT A.Application_ID, E.Name, A.Application_Type, A.Description, A.Status, A.Remarks 
                          FROM Applications A JOIN Employee_Data E ON A.Employee_ID = E.ID""")
        apps = self.cursor.fetchall()
        return apps

    def update_application_status(self, app_id, decision, remarks):
        status = "Approved" if decision == 'A' else "Rejected"
        self.cursor.execute("UPDATE Applications SET Status=%s, Remarks=%s WHERE Application_ID=%s", (status, remarks, app_id))
        self.db.commit()
        return True

   
    def add_employee(self, name, designation, age, salary, address, joining_date, password):
        return self.emp.Taking_Employee_data(name, designation, age, salary, address, joining_date, password)

    def delete_employee(self, del_id):
        self.cursor.execute("delete from Employee_Data where ID = (%s)", (del_id,))
        self.db.commit()

    def update_employee(self, upd_id, name, designation, age, salary, address, joining_date):
        self.cursor.execute("""
                update Employee_Data set Name=(%s), Designation=(%s), Age=(%s), Salary=(%s), Address=(%s), Joining_date=(%s) where ID = (%s)
            """, (name, designation, age, salary, address, joining_date, upd_id))
        self.db.commit()

    def view_employees(self):
        self.cursor.execute("select * from Employee_Data")
        result = self.cursor.fetchall()
        return result

    def view_salary_report(self):
        self.cursor.execute("select ID, Designation, Name, Salary from Employee_Data")
        result = self.cursor.fetchall()
        return result




st.set_page_config(page_title="Employee Payroll System", layout="centered")

st.markdown("""
<style>
.header {
  background: linear-gradient(90deg,#4b6cb7,#182848);
  padding: 18px;
  border-radius: 12px;
  color: white;
  text-align: center;
}
.card {
  background: linear-gradient(180deg, #ffffffaa, #ffffff55);
  padding: 12px;
  border-radius: 10px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><h1>Employee Payroll System</h1></div>', unsafe_allow_html=True)
st.write("\n")


@st.cache_resource
def get_db():
    return Database()

if 'db' not in st.session_state:
    st.session_state.db = get_db()
    st.session_state.db.create_tables()

    cur = st.session_state.db.cursor
    cur.execute("select Admin_ID, Password from About_Admin")
    result = cur.fetchall()
    st.session_state.Admin_ID_Password = dict(result)
    cur.execute("select ID, Password from Employee_Data")
    result1 = cur.fetchall()
    st.session_state.Employee_ID_Password = dict(result1)


def refresh_credentials():
    cur = st.session_state.db.cursor
    cur.execute("select Admin_ID, Password from About_Admin")
    st.session_state.Admin_ID_Password = dict(cur.fetchall())
    cur.execute("select ID, Password from Employee_Data")
    st.session_state.Employee_ID_Password = dict(cur.fetchall())


emp_logic = Employee(st.session_state.db, st.session_state.Employee_ID_Password)
admin_logic = Admin(st.session_state.db, st.session_state.Admin_ID_Password, st.session_state.Employee_ID_Password)


col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("1. Register", key="register"):
        st.session_state.page = 'register'
with col2:
    if st.button("2. Admin Login", key="admin_login"):
        st.session_state.page = 'admin_login'
with col3:
    if st.button("3. Employee Login", key="emp_login"):
        st.session_state.page = 'emp_login'
with col4:
    if st.button("0. Exit", key="exit"):
        st.session_state.page = 'exit'

if 'page' not in st.session_state:
    st.session_state.page = None

st.write("---")



def page_register():
    st.subheader("Register")
    reg_type = st.radio("Register as:", ("Admin (requires existing admin)", "Employee"))
    if reg_type.startswith("Admin"):
        st.info("To register a new admin you must provide an existing admin's credentials first.")
        with st.form("register_admin_form"):
            login_admin_id = st.text_input("Existing Admin ID")
            login_admin_pass = st.text_input("Existing Admin Password", type='password')
            new_admin_id = st.text_input("New Admin ID")
            new_admin_pass = st.text_input("New Admin Password", type='password')
            submitted = st.form_submit_button("Register Admin")
        if submitted:
            ok = admin_logic.registerAdmin(login_admin_id, login_admin_pass, new_admin_id, new_admin_pass)
            if ok:
                st.success("New admin created successfully")
                refresh_credentials()
            else:
                st.error("Failed to create admin. Check existing admin credentials.")
    else:
        st.info("Register a new Employee (password must be integer as in original system)")
        with st.form("register_emp_form"):
            name = st.text_input("Name")
            password = st.text_input("Password (integer)")
            submitted = st.form_submit_button("Register Employee")
        if submitted:
            try:
                pa = int(password)
                st.session_state.db.cursor.execute("insert into Employee_Data(Name, Password) values (%s,%s)", (name, pa))
                st.session_state.db.commit()
                st.session_state.db.cursor.execute("select ID from Employee_Data where Name = %s order by ID desc limit 1", (name,))
                re = st.session_state.db.cursor.fetchone()[0]
                st.session_state.Employee_ID_Password[re] = pa
                st.success(f"Employee Registered. ID: {re}")
                refresh_credentials()
            except ValueError:
                st.error("Password must be an integer")


def page_admin_login():
    st.subheader("Admin Login")
    with st.form("admin_login_form"):
        admin_id = st.text_input("Admin ID")
        admin_pass = st.text_input("Password", type='password')
        submitted = st.form_submit_button("Login")
    if submitted:
        if admin_id in st.session_state.Admin_ID_Password and st.session_state.Admin_ID_Password[admin_id] == admin_pass:
            st.session_state.admin_logged_in = admin_id
            st.session_state.page = 'admin_panel'
            

        else:
            st.error("Admin ID Not Found or Wrong Password")


def page_admin_panel():
    st.subheader(f"Admin Panel — {st.session_state.get('admin_logged_in')}")
    menu = st.selectbox("Choose operation:", ["Select",
        "Add Employee",
        "Delete Employee",
        "Update Employee",
        "View Employees",
        "Calculate Salary",
        "View Salary Report",
        "View Applications",
        "Update Application Status",
        "Logout"
    ])
    if menu == "Select":
        pass

    elif menu == "Add Employee":
        with st.form("add_emp_form"):
            name = st.text_input("Name")
            designation = st.text_input("Designation")
            age = st.number_input("Age", min_value=18, max_value=80, step=1)
            salary = st.number_input("Salary", min_value=0, step=100)
            address = st.text_input("Address")
            joining_date = st.date_input("Joining Date")
            password = st.text_input("Password (integer)")
            submitted = st.form_submit_button("Add Employee")
        if submitted:
            try:
                pwd = int(password)
                emp_id = admin_logic.add_employee(name, designation, int(age), int(salary), address, joining_date, pwd)
                st.success(f"Employee added with ID: {emp_id}")
                refresh_credentials()
            except ValueError:
                st.error("Password must be an integer")

    elif menu == "Delete Employee":
        del_id = st.text_input("Enter Employee ID to delete")
        if st.button("Delete"):
            try:
                admin_logic.delete_employee(int(del_id))
                st.success("Employee Deleted")
                refresh_credentials()
            except Exception as e:
                st.error(f"Error: {e}")

    elif menu == "Update Employee":
        upd_id = st.text_input("Enter Employee ID to update")
        if st.button("Load Employee") and upd_id:
            try:
                cur = st.session_state.db.cursor
                cur.execute("select * from Employee_Data where ID=%s", (int(upd_id),))
                row = cur.fetchone()
                if row:
                    with st.form("update_emp_form"):
                        name = st.text_input("Name", value=row[1])
                        designation = st.text_input("Designation", value=row[2])
                        age = st.number_input("Age", value=row[3])
                        salary = st.number_input("Salary", value=row[4])
                        address = st.text_input("Address", value=row[5])
                        joining_date = st.date_input("Joining Date", value=row[6])
                        submitted = st.form_submit_button("Update Employee")
                    if submitted:
                        admin_logic.update_employee(int(upd_id), name, designation, int(age), int(salary), address, joining_date)
                        st.success("Employee Updated Successfully ! ")
                        refresh_credentials()
                else:
                    st.error("Employee not found")
            except Exception as e:
                st.error(f"Error: {e}")

    elif menu == "View Employees":
        rows = admin_logic.view_employees()
        if not rows:
            st.info("No employees yet")
        else:
            
            df = pd.DataFrame(rows, columns=['ID','Name','Designation','Age','Salary','Address','Joining_date','Password'])
            st.dataframe(df)

    elif menu == "Calculate Salary":
        emp_id = st.text_input("Enter Employee ID to calculate salary")
        if st.button("Calculate"):
            try:
                res = emp_logic.Calculate_Salary(int(emp_id))
                if res:
                    for k,v in res.items():
                        st.write(f"**{k}:** {v}")
                else:
                    st.error("Employee ID not found")
            except Exception as e:
                st.error(f"Error: {e}")

    elif menu == "View Salary Report":
        rows = admin_logic.view_salary_report()
        
        if rows:
            df = pd.DataFrame(rows, columns=['ID','Designation','Name','Salary'])
            st.dataframe(df)
        else:
            st.info("No data")

    elif menu == "View Applications":
        apps = admin_logic.view_all_applications()
        if not apps:
            st.info("No applications found")
        else:
            
            df = pd.DataFrame(apps, columns=['Application_ID','Employee_Name','Type','Description','Status','Remarks'])
            st.dataframe(df)

    elif menu == "Update Application Status":
        with st.form("update_app_form"):
            app_id = st.number_input("Application ID", step=1)
            decision = st.selectbox("Decision", ("Approve (A)", "Reject (R)"))
            remarks = st.text_area("Remarks")
            submitted = st.form_submit_button("Update")
        if submitted:
            code = 'A' if decision.startswith('Approve') else 'R'
            admin_logic.update_application_status(int(app_id), code, remarks)
            st.success("Application updated")

    elif menu == "Logout":
        st.session_state.pop('admin_logged_in', None)
        st.session_state.page = None
        st.session_state.page = 'admin_panel'



def page_employee_login():
    st.subheader("Employee Login")
    with st.form("employee_login_form"):
        emp_id = st.text_input("Employee ID")
        emp_pass = st.text_input("Password (integer)", type='password')
        submitted = st.form_submit_button("Login")
    if submitted:
        try:
            id_int = int(emp_id)
            if id_int in st.session_state.Employee_ID_Password and st.session_state.Employee_ID_Password[id_int] == int(emp_pass):
                st.session_state.emp_logged_in = id_int
                st.session_state.page = 'emp_panel'
                

            else:
                st.error("Employee ID Not Found or Wrong Password")
        except ValueError:
            st.error("Employee ID and Password should be integers")


def page_employee_panel():
    st.subheader(f"Employee Panel — ID {st.session_state.get('emp_logged_in')}")
    choice = st.selectbox("Choose:", [
        "View Personal Details",
        "View Salary Report",
        "Change Password",
        "Apply for leave/Application",
        "View Applications",
        "Mark Attendance",
        "View Attendance",
        "Logout"
    ])
    emp_id = st.session_state.get('emp_logged_in')

    if choice == "View Personal Details":
        row = emp_logic.View_Details(emp_id)
        if row:
            st.write(f"**ID:** {row[0]}")
            st.write(f"**Name:** {row[1]}")
            st.write(f"**Designation:** {row[2]}")
            st.write(f"**Age:** {row[3]}")
            st.write(f"**Salary:** {row[4]}")
            st.write(f"**Address:** {row[5]}")
            st.write(f"**Joining Date:** {row[6]}")
            st.write(f"**Password:** {row[7]}")
        else:
            st.error("Employee ID not found")

    elif choice == "View Salary Report":
        res = emp_logic.Calculate_Salary(emp_id)
        if res:
            for k,v in res.items():
                st.write(f"**{k}:** {v}")
        else:
            st.error("Employee ID not found")

    elif choice == "Change Password":
        with st.form("change_pass_form"):
            old = st.text_input("Old Password", type='password')
            new = st.text_input("New Password (integer)", type='password')
            submitted = st.form_submit_button("Change Password")
        if submitted:
            try:
                ok = emp_logic.Change_Pass_Emp(emp_id, int(old), int(new))
                if ok:
                    st.success("Password Updated Successfully")
                    refresh_credentials()
                else:
                    st.error("Wrong old password")
            except ValueError:
                st.error("Passwords must be integers")

    elif choice == "Apply for leave/Application":
        with st.form("apply_form"):
            app_type = st.selectbox("Application Type", ("Leave", "Other"))
            desc = st.text_area("Description")
            submitted = st.form_submit_button("Submit Application")
        if submitted:
            emp_logic.apply_application(emp_id, app_type, desc)
            st.success("Application submitted successfully")

    elif choice == "View Applications":
        apps = emp_logic.view_applications_status(emp_id)
        if not apps:
            st.info("No applications found")
        else:
            
            df = pd.DataFrame(apps, columns=['Application_ID','Type','Status','Remarks'])
            st.dataframe(df)

    elif choice == "Mark Attendance":
        if st.button("Mark Attendance"):
            ok = emp_logic.mark_attendance(emp_id)
            if ok:
                st.success("Attendance marked successfully")
            else:
                st.warning("Attendance already marked for today")

    elif choice == "View Attendance":
        data = emp_logic.view_attendance(emp_id)
        if not data:
            st.info("No attendance record found")
        else:
            
            df = pd.DataFrame(data, columns=['Date','Time','Status'])
            st.dataframe(df)

    elif choice == "Logout":
        st.session_state.pop('emp_logged_in', None)
        st.session_state.page = None
        st.session_state.page = 'emp_panel'




if st.session_state.page == 'register':
    page_register()
elif st.session_state.page == 'admin_login':
    page_admin_login()
elif st.session_state.page == 'admin_panel':

    if st.session_state.get('admin_logged_in'):
        page_admin_panel()
    else:
        st.warning("Please login as admin first")
        page_admin_login()
elif st.session_state.page == 'emp_login':
    page_employee_login()
elif st.session_state.page == 'emp_panel':
    if st.session_state.get('emp_logged_in'):
        page_employee_panel()
    else:
        st.warning("Please login as employee first")
        page_employee_login()
elif st.session_state.page == 'exit':
    st.balloons()
    st.success("Thank you for using Employee Payroll System. You can close this tab.")
else:
    st.info("Choose an option from above to get started.")


