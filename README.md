<p align="center"> ======================= > COMPLAINT MANAGEMENT SYSTEM < ======================= </P>
  
### DESCRIPTION:
-----------
A secure, web-based platform that allows users to seamlessly submit and track 
issues, while providing an administrative dashboard for authorized staff to view, 
filter, update, and effectively resolve these complaints. 

This Web-app is built with Enterprise-Grade security features including 
parameterized queries against SQL Injection, CSRF protection, XSS sanitization, 
and Werkzeug password hashing.

### Features:
-----------
* **User Portal:** Submit issues with categories, urgency levels, and receive unique tracking IDs (`CM_XXXXXXXX`).
* **Live Tracking:** Track complaint status in real time.
* **Admin Dashboard:** Secure login with hashed credentials, search filters, pagination, and status management.
* **Security Controls:** CSRF protection, secure cookie handling, strict input sanitation, and environment-based configuration.

### TECH STACK:
-----------
* **Frontend:** HTML5, CSS3 (Flexbox), Jinja2 Templating
* **Backend:** Python3, Flask
* **Database:** MySQL (mysql-connector-python, Flask-Mysqldb)
* **Security:** Flask-WTF, Werkzeug.security, python "secret" module

### INSTALLATION & SETUP
--------------------
1. Clone the Repository
   ```
   git clone [https://github.com/swayan-basu/complaint-management-system.git](https://github.com/swayan-basu/complaint-management-system.git)
   cd complaint-management-system
   ```
2. Setup python virtual enviroment:
   ```
   python3 -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   pip install Flask Flask-MySQLdb mysql-connector-python Flask-WTF Werkzeug

4. Setup local MySQL database:
   Login to your mysql server as root:
   ```
   mysql -u root -p
   ```
   Run the following SQL commands to create your local database user and grant permissions;
   ```
   CREATE DATABASE complaint_db;
   CREATE USER 'cms_user'@'localhost' IDENTIFIED BY 'YourSecurePassword123';
   GRANT ALL PRIVILEGES ON complaint_db.* TO 'cms_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```
5. Configure your.env file:
   ```
   cp .env.example .env
   ```
   Open the .env file and fill in your actual local database username, password and custom flask secret keys:
   ```
   DB_HOST=localhost
   DB_USER=cms_user
   DB_PASSWORD=YourSecurePassword123
   DB_NAME=complaint_db
   secret_key=your_super_secret_flask_key
   admin_username=admin
   admin_password=your_secure_admin_password
   cookie_secure=0
   ```
6. Running the Application:
   Start the Flask server:
   ```
   python cms.py
   ```
   Open your browser and navigate to http://0.0.0.0:5000

### RUNNING THE APPLICATION
-----------------------
1. Navigate to the complaint-management-system directory in your terminal.
2. Run the cms.py file:
 python cms.py or python3 cms.py
3. The server will start on http://127.0.0.1:5000/

### USAGE GUIDE:
-----------
1. User Portal (http://127.0.0.1:5000):
  - Users can fill out the form to submit a new complaint.
  - After submission, a unique tracking ID (e.g., CM_12345678) is generated.
  - Users can use the "Track your issue" widget to check the live status.
    
<img width="1223" height="924" alt="cms-customer" src="https://github.com/user-attachments/assets/f204a23e-3abe-477b-90c9-86dc19117f50" />

2. Admin Dashboard (http://127.0.0.1:5000/admin):
  - To access the dashboard, navigate to the login page.
  - Default Admin Credentials:
    Username: admin
    Password: admin123
  - Admins can view list of complaints records, filter by Category, Status, or Priority, 
    search by ID, and update ticket statuses.
    
<img width="1214" height="943" alt="cms-admin" src="https://github.com/user-attachments/assets/d94bcf7e-5aae-4685-a72a-961e3b6746df" />

<br>
<p align="center"> ====><====END OF THE PAGE====><==== </p>
