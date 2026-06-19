"""CART, Random Forest e importancia de variables."""

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

from config import MODELO_CART, MODELO_RF, RECOMENDACIONES
from preparar_datos import FEATURES_ML


def entrenar_cart(X: pd.DataFrame, y: pd.Series) -> tuple[DecisionTreeClassifier, LabelEncoder]:
    le = LabelEncoder()
    le.fit(RECOMENDACIONES)
    y_num = le.transform(y)
    modelo = DecisionTreeClassifier(max_depth=6, random_state=42, class_weight="balanced")
    modelo.fit(X, y_num)
    return modelo, le


def entrenar_rf(X: pd.DataFrame, y: pd.Series) -> tuple[RandomForestClassifier, LabelEncoder]:
    le = LabelEncoder()
    le.fit(RECOMENDACIONES)
    y_num = le.transform(y)
    modelo = RandomForestClassifier(
        n_estimators=100, max_depth=8, random_state=42, class_weight="balanced", n_jobs=-1
    )
    modelo.fit(X, y_num)
    return modelo, le


def predecir_cart(modelo: DecisionTreeClassifier, le: LabelEncoder, X: pd.DataFrame) -> str:
    idx = int(modelo.predict(X)[0])
    return le.inverse_transform([idx])[0]


def predecir_rf(modelo: RandomForestClassifier, le: LabelEncoder, X: pd.DataFrame) -> str:
    idx = int(modelo.predict(X)[0])
    return le.inverse_transform([idx])[0]


def importancia_rf(modelo: RandomForestClassifier) -> pd.DataFrame:
    imp = modelo.feature_importances_
    return (
        pd.DataFrame({"variable": FEATURES_ML, "importancia": imp})
        .sort_values("importancia", ascending=False)
        .reset_index(drop=True)
    )


def guardar_modelos(cart, le_cart, rf, le_rf) -> None:
    joblib.dump({"modelo": cart, "encoder": le_cart, "features": FEATURES_ML}, MODELO_CART)
    joblib.dump({"modelo": rf, "encoder": le_rf, "features": FEATURES_ML}, MODELO_RF)


def cargar_cart() -> tuple[DecisionTreeClassifier, LabelEncoder]:
    pkg = joblib.load(MODELO_CART)
    return pkg["modelo"], pkg["encoder"]


def cargar_rf() -> tuple[RandomForestClassifier, LabelEncoder]:
    pkg = joblib.load(MODELO_RF)
    return pkg["modelo"], pkg["encoder"]


def evaluar(modelo, le: LabelEncoder, X_test, y_test) -> float:
    y_pred = le.inverse_transform(modelo.predict(X_test))
    return accuracy_score(y_test, y_pred)
