# config.py

# General Settings
GENERAL_SETTINGS = {
    "log_level": "DEBUG",  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "data_path": "./Data_store/",
    "strategy_path": "./strategies/",
    "results_path": "./results/",
}

# API Credentials
APIS = {
    "MEXC": {
        "key": "mx0vglXeTwvCQz4l1c",
        "pass": "8640fe5750a7403a84020a5e5bea8243",
    },
}

# Email Notifications (Optional)
EMAIL_NOTIFICATIONS = {
    "enabled": False,
    "smtp_server": "smtp.example.com",
    "port": 587,
    "email": "your_email@example.com",
    "password": "your_email_password",
}