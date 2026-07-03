# ChurnSense - Bank Customer Churn Prediction

ChurnSense is a Flask-based machine learning web application that predicts whether a bank customer is likely to churn. The app uses a trained classification model, engineered customer features, and a polished web interface for interactive predictions.

## Features

- Customer churn prediction from a browser form
- Flask JSON API endpoint for inference
- Pre-trained Random Forest model artifacts
- Feature engineering aligned with the training notebook
- Render-ready deployment configuration
- Health check endpoint for deployment monitoring

## Project Structure

```text
churn_modelling_project/
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── static/
│   │   ├── script.js
│   │   └── style.css
│   └── templates/
│       └── index.html
├── data/
│   └── churn_modelling_raw_data.csv
├── models/
│   ├── best_model_classifier.pkl
│   ├── best_model_name.pkl
│   ├── feature_columns.pkl
│   ├── scaler.pkl
│   └── smote.pkl
├── notebooks/
│   └── training.ipynb
├── .gitignore
├── LICENSE
├── Procfile
├── README.md
├── requirements.txt
```

## Model Information

- Task: binary customer churn classification
- Main model: Random Forest classifier
- Evaluation metrics exposed in the app:
  - Accuracy: 95.77%
  - ROC-AUC: 95.13%
- Model artifacts:
  - `models/best_model_classifier.pkl`: trained classifier
  - `models/feature_columns.pkl`: ordered training feature columns
  - `models/scaler.pkl`: scaler used by non-tree models
  - `models/best_model_name.pkl`: selected model name
  - `models/smote.pkl`: training resampling artifact

## Installation

```bash
cd churn_modelling_project
pip install -r requirements.txt
```

On macOS/Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Run Locally

```bash
python app/app.py
```

Open:

```text
http://127.0.0.1:5000
```

