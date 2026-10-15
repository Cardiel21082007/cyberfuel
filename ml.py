import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest

def predecir_gasto(df):
    try:
        if df.empty or len(df) < 2: return None
        df_c = df.copy()
        df_c["fecha"] = pd.to_datetime(df_c["fecha"])
        df_m = df_c.groupby(df_c["fecha"].dt.to_period("M"))["custo"].sum().reset_index()
        if len(df_m) < 2: return None
        X = np.arange(len(df_m)).reshape(-1, 1)
        y = df_m["custo"].values
        return max(0, LinearRegression().fit(X, y).predict(np.array([[len(df_m)]]))[0])
    except:
        return None

def detectar_anomalia_ai(historial_df, nueva_carga):
    """
    Usa Machine Learning (Isolation Forest) para detectar cargas raras.
    historial_df: DataFrame con las últimas cargas del vehículo (al menos 10 idealmente).
    nueva_carga: Diccionario con {'litros': X, 'custo': Y, 'kilometraje': Z, 'hora': H}
    """
    try:
        if historial_df.empty or len(historial_df) < 8:
            return False # No hay suficiente data para aprender
        
        # Preparamos los datos históricos
        df = historial_df.copy()
        df['hora'] = pd.to_datetime(df['fecha'], format='mixed', errors='coerce').dt.hour
        df = df[['litros', 'custo', 'kilometraje', 'hora']].fillna(0)
        
        # Agregamos la nueva carga
        nuevo_punto = pd.DataFrame([nueva_carga])
        data = pd.concat([df, nuevo_punto], ignore_index=True)
        
        # Entrenamos el modelo de detección de anomalías
        # Contamination=0.05 significa que asumimos que el 5% de las cargas históricas son raras
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        iso_forest.fit(data)
        
        # Predecimos (1 = Normal, -1 = Anomalía)
        predicciones = iso_forest.predict(data)
        
        # Si el último punto (la nueva carga) es -1, ¡ES UNA ANOMALÍA AI!
        return predicciones[-1] == -1
        
    except Exception as e:
        print("Error AI Anomaly: " + str(e))
        return False