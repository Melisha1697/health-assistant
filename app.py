import os
import sqlite3
import pickle
from hashlib import sha256
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config(page_title="Health Assistant", layout="wide", page_icon="🩺")

# Initialize cookies manager
cookies = EncryptedCookieManager(
    password=os.environ.get("COOKIE_PASSWORD", "a_secure_password")
)
if not cookies.ready():
    st.stop()

# Hashing passwords for security
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Database management without persistent connections
def execute_query(query, params=(), fetch=False):
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect("database/users.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    if fetch:
        results = cursor.fetchall()
        conn.close()
        return results
    conn.close()

# Initialize database with default admin user
def initialize_database():
    execute_query('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    try:
        execute_query('''
            INSERT INTO users (username, email, password, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@example.com', hash_password('admin123'), 1))
    except sqlite3.IntegrityError:
        pass  # Admin user already exists

# Check login state
def check_login():
    username = cookies.get("username")
    is_admin = cookies.get("is_admin") == "True"
    return username, is_admin

# Set login state
def set_login(username, is_admin):
    cookies["username"] = username
    cookies["is_admin"] = str(is_admin)
    cookies.save()

# Clear login state
def clear_login():
    cookies["username"] = ""
    cookies["is_admin"] = ""
    cookies.save()

# Load machine learning models
@st.cache_data
def load_models():
    working_dir = os.path.dirname(os.path.abspath(__file__))
    diabetes_model = pickle.load(open(f"{working_dir}/saved_models/diabetes_model.sav", "rb"))
    heart_disease_model = pickle.load(open(f"{working_dir}/saved_models/heart_disease_model.sav", "rb"))
    parkinsons_model = pickle.load(open(f"{working_dir}/saved_models/parkinsons_model.sav", "rb"))
    return diabetes_model, heart_disease_model, parkinsons_model

# Home Page
def homepage():
    st.markdown(
        """
        <style>
        .homepage-title {
            margin-top: -5rem;
            font-size: 3rem;
            color: #fff;
            font-weight: bold;
            text-align: center;
        }
        .homepage-subtitle {
            font-size: 1.5rem;
            color: #bbb;
            text-align: center;
            margin-bottom: 2rem;
        }
        </style>
        """, unsafe_allow_html=True
    )
    
    st.markdown("<div class='homepage-title'>Welcome to Health Assistant App 🩺</div>", unsafe_allow_html=True)
    st.markdown("<div class='homepage-subtitle'>Your reliable assistant for health predictions and management.</div>", unsafe_allow_html=True)
    
    st.image("https://raw.githubusercontent.com/Melisha1697/health-assistant/refs/heads/main/assets/health-assistant-banner.png", use_column_width=True)
    
    # Add a horizontal divider
    st.markdown("---")
    
    # Features section
    st.markdown(
        """
        ### Key Features
        - 🩺 **Predict Diseases**: Analyze the likelihood of Diabetes, Heart Disease, or Parkinson's Disease using advanced machine learning models.
        - 👥 **User Management**: Securely manage user accounts with admin functionality.
        - 🔒 **Secure Authentication**: Passwords are hashed for user security.
        
        #### Getting Started
        - Login to access predictions and dashboards.
        - Register if you're new to the platform.
        - Navigate using the sidebar menu to explore features.
        """,
        unsafe_allow_html=True,
    )

# Login Page
def login():
    st.title("Login")
    username_or_email = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username_or_email or not password:
            st.error("Please fill out both fields!")
        else:
            user = execute_query(
                "SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ?",
                (username_or_email, username_or_email, hash_password(password)),
                fetch=True
            )
            if user:
                st.success(f"Welcome, {user[0][1]}!")
                set_login(user[0][1], bool(user[0][4]))
                st.experimental_rerun()
            else:
                st.error("Invalid username/email or password.")

# Register Page
def register():
    st.title("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if not username or not email or not password or not confirm_password:
            st.error("All fields are required!")
        elif password != confirm_password:
            st.error("Passwords do not match!")
        else:
            try:
                execute_query(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, hash_password(password))
                )
                st.success("Registration successful! Redirecting to login...")
                st.experimental_rerun()
            except sqlite3.IntegrityError:
                st.error("Username or email already exists.")

# Admin Dashboard
def admin_dashboard():
    st.title("Admin Dashboard")
    st.subheader("Manage Users")

    users = execute_query("SELECT username, email FROM users", fetch=True)
    st.table(users)

    st.subheader("Edit or Delete Users")
    user_id = st.number_input("User ID", min_value=1, step=1)
    action = st.radio("Action", ["Edit", "Delete"], horizontal=True)

    if action == "Edit":
        new_username = st.text_input("New Username")
        new_email = st.text_input("New Email")
        new_password = st.text_input("New Password", type="password")
        new_is_admin = st.checkbox("Is Admin?", value=False)

        if st.button("Update User"):
            if not new_username or not new_email:
                st.error("Username and email cannot be empty!")
            elif new_password and len(new_password) < 6:
                st.error("Password must be at least 6 characters long!")
            else:
                try:
                    params = [new_username, new_email, int(new_is_admin), user_id]
                    query = "UPDATE users SET username = ?, email = ?, is_admin = ? WHERE id = ?"
                    if new_password:
                        query = "UPDATE users SET username = ?, email = ?, is_admin = ?, password = ? WHERE id = ?"
                        params.insert(3, hash_password(new_password))
                    execute_query(query, tuple(params))
                    st.success("User updated successfully!")
                    st.experimental_rerun()
                except sqlite3.IntegrityError:
                    st.error("Failed to update user. Username or email may already exist.")

    elif action == "Delete":
        if st.button("Delete User"):
            execute_query("DELETE FROM users WHERE id = ?", (user_id,))
            st.success("User deleted successfully!")
            st.experimental_rerun()

# Disease Prediction Dashboard
def disease_prediction_dashboard():
    st.title("Disease Prediction Dashboard")
    st.subheader(f"Welcome, {cookies.get('username', 'User')}")

    # Load models
    diabetes_model, heart_disease_model, parkinsons_model = load_models()

    # Sidebar menu for navigation
    selected = option_menu(
        "Prediction Options",
        ["Diabetes Prediction", "Heart Disease Prediction", "Parkinson's Prediction"],
        icons=["activity", "heart", "person"],
        menu_icon="stethoscope",
        default_index=0,
    )

    if selected == "Diabetes Prediction":
        st.subheader("Diabetes Prediction")
        col1, col2, col3 = st.columns(3)

        with col1:
            Pregnancies = st.number_input("Number of Pregnancies", min_value=0, step=1)
        with col2:
            Glucose = st.number_input("Glucose Level (mg/dL)", min_value=0.0, step=1.0)
        with col3:
            BloodPressure = st.number_input("Blood Pressure (mmHg)", min_value=0.0, step=1.0)
        with col1:
            SkinThickness = st.number_input("Skin Thickness (mm)", min_value=0.0, step=1.0)
        with col2:
            Insulin = st.number_input("Insulin Level (IU/mL)", min_value=0.0, step=1.0)
        with col3:
            BMI = st.number_input("BMI (kg/m²)", min_value=0.0, step=0.1)
        with col1:
            DiabetesPedigreeFunction = st.number_input("Diabetes Pedigree Function", min_value=0.0, step=0.01)
        with col2:
            Age = st.number_input("Age (years)", min_value=0, step=1)

        if st.button("Predict Diabetes"):
            try:
                input_data = [
                    Pregnancies, Glucose, BloodPressure, SkinThickness,
                    Insulin, BMI, DiabetesPedigreeFunction, Age
                ]
                result = diabetes_model.predict([input_data])[0]
                if result == 1:
                    st.success("The person is diabetic.")
                else:
                    st.success("The person is not diabetic.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    elif selected == "Heart Disease Prediction":
        st.subheader("Heart Disease Prediction")
        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.number_input("Age (years)", min_value=0, step=1)
        with col2:
            sex = st.selectbox("Gender", ["Male", "Female"])
            sex = 1 if sex == "Male" else 0
        with col3:
            cp = st.selectbox("Chest Pain Type", [
                "Typical Angina", "Atypical Angina", "Non-Anginal Pain", "Asymptomatic"
            ], index=3)
            cp = ["Typical Angina", "Atypical Angina", "Non-Anginal Pain", "Asymptomatic"].index(cp)

        with col1:
            trestbps = st.number_input("Resting Blood Pressure (mmHg)", min_value=0.0, step=1.0)
        with col2:
            chol = st.number_input("Cholesterol Level (mg/dL)", min_value=0.0, step=1.0)
        with col3:
            fbs = st.selectbox("Fasting Blood Sugar > 120 mg/dL?", ["No", "Yes"])
            fbs = 1 if fbs == "Yes" else 0

        with col1:
            restecg = st.selectbox("Resting ECG Results", ["Normal", "ST-T Wave Abnormality", "Left Ventricular Hypertrophy"])
            restecg = ["Normal", "ST-T Wave Abnormality", "Left Ventricular Hypertrophy"].index(restecg)
        with col2:
            thalach = st.number_input("Max Heart Rate Achieved", min_value=0.0, step=1.0)
        with col3:
            exang = st.selectbox("Exercise-Induced Angina", ["No", "Yes"])
            exang = 1 if exang == "Yes" else 0

        with col1:
            oldpeak = st.number_input("ST Depression Induced by Exercise", min_value=0.0, step=0.1)
        with col2:
            slope = st.selectbox("Slope of Peak Exercise ST Segment", ["Upsloping", "Flat", "Downsloping"])
            slope = ["Upsloping", "Flat", "Downsloping"].index(slope)
        with col3:
            ca = st.number_input("Number of Major Vessels Colored by Fluoroscopy", min_value=0, step=1)
        with col1:
            thal = st.selectbox("Thalassemia Type", ["Normal", "Fixed Defect", "Reversible Defect"])
            thal = ["Normal", "Fixed Defect", "Reversible Defect"].index(thal)

        if st.button("Predict Heart Disease"):
            try:
                input_data = [
                    age, sex, cp, trestbps, chol, fbs, restecg, thalach,
                    exang, oldpeak, slope, ca, thal
                ]
                result = heart_disease_model.predict([input_data])[0]
                if result == 1:
                    st.success("The person does not have heart disease.")
                else:
                    st.success("The person has heart disease.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    elif selected == "Parkinson's Prediction":
        st.subheader("Parkinson's Prediction")
        col1, col2, col3 = st.columns(3)

        with col1:
            fo = st.text_input("MDVP:Fo(Hz)", value="118.0")
            fhi = st.text_input("MDVP:Fhi(Hz)", value="160.0")
            flo = st.text_input("MDVP:Flo(Hz)", value="90.0")
            Jitter_percent = st.text_input("MDVP:Jitter(%)", value="0.010")
            Jitter_Abs = st.text_input("MDVP:Jitter(Abs)", value="0.005")
        with col2:
            RAP = st.text_input("MDVP:RAP", value="0.020")
            PPQ = st.text_input("MDVP:PPQ", value="0.015")
            DDP = st.text_input("Jitter:DDP", value="0.025")
            Shimmer = st.text_input("MDVP:Shimmer", value="0.040")
            Shimmer_dB = st.text_input("MDVP:Shimmer(dB)", value="0.130")
        with col3:
            APQ3 = st.text_input("Shimmer:APQ3", value="0.035")
            APQ5 = st.text_input("Shimmer:APQ5", value="0.040")
            APQ = st.text_input("MDVP:APQ", value="0.020")
            DDA = st.text_input("Shimmer:DDA", value="0.025")
            NHR = st.text_input("NHR", value="0.120")
        with col1:
            HNR = st.text_input("HNR", value="17.5")
            RPDE = st.text_input("RPDE", value="0.55")
            DFA = st.text_input("DFA", value="0.85")
        with col2:
            spread1 = st.text_input("Spread1", value="3.4")
            spread2 = st.text_input("Spread2", value="5.1")
            D2 = st.text_input("D2", value="2.30")
            PPE = st.text_input("PPE", value="0.78")

        if st.button("Predict Parkinson's Disease"):
            try:
                # Convert all inputs to floats
                input_data = [
                    float(fo), float(fhi), float(flo), float(Jitter_percent), float(Jitter_Abs),
                    float(RAP), float(PPQ), float(DDP), float(Shimmer), float(Shimmer_dB),
                    float(APQ3), float(APQ5), float(APQ), float(DDA), float(NHR),
                    float(HNR), float(RPDE), float(DFA), float(spread1), float(spread2),
                    float(D2), float(PPE)
                ]

                # Make prediction
                result = parkinsons_model.predict([input_data])[0]

                # Display result
                if result == 1:
                    st.success("The person has Parkinson's disease.")
                else:
                    st.success("The person does not have Parkinson's disease.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Sidebar Navigation
username, is_admin = check_login()
if username:
    with st.sidebar:
        if is_admin:
            selected = option_menu(
                "Main Menu",
                ["Dashboard", "Admin Dashboard", "Logout"],
                icons=["house", "tools", "box-arrow-right"],
                menu_icon="list",
                default_index=0,
            )
        else:
            selected = option_menu(
                "Main Menu",
                ["Dashboard", "Logout"],
                icons=["house", "box-arrow-right"],
                menu_icon="list",
                default_index=0,
            )
else:
    with st.sidebar:
        selected = option_menu(
            "Main Menu",
            ["Home", "Login", "Register"],
            icons=["house", "key", "plus-circle"],
            menu_icon="list",
            default_index=0,
        )

# Navigation Logic
if selected == "Home":
    homepage()
elif selected == "Login":
    login()
elif selected == "Register":
    register()
elif selected == "Dashboard" and username:
    disease_prediction_dashboard()
elif selected == "Admin Dashboard" and username and is_admin:
    admin_dashboard()
elif selected == "Logout":
    clear_login()
    st.success("Logged out successfully!")
    st.experimental_rerun()
else:
    st.warning("Please log in to access this page.")

# Initialize database on first run
initialize_database()
