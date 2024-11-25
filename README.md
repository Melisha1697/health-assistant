# Health Assistant: Multiple Disease Prediction System 🧑‍⚕️
This is a Streamlit-based web application that allows users to predict the likelihood of three different health conditions using Machine Learning models:

- Diabetes Prediction
- Heart Disease Prediction
- Parkinson's Disease Prediction

The application takes user input for specific medical parameters and predicts the likelihood of the disease using pre-trained ML models.

### 🔑 Features
- Diabetes Prediction: Based on parameters like pregnancies, glucose level, BMI, age, etc.
- Heart Disease Prediction: Considers factors like cholesterol, resting blood pressure, and heart rate.
- Parkinson's Disease Prediction: Uses features derived from voice data, such as jitter, shimmer, and others.
- Interactive User Interface: Built with Streamlit for easy navigation.
- Pre-trained Models: Predictions are made using ML models trained offline and loaded during runtime.


### 🛠️ Technologies Used
- Python: Core language for building the app and models.
- Streamlit: Framework for building the interactive web UI.
- scikit-learn: Library for training and deploying ML models.
- SQLite: Lightweight database for user management.
- pickle: For saving and loading pre-trained models.
- Streamlit-Cookies-Manager: For secure session management.