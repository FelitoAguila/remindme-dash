from datetime import datetime, timedelta
import pandas as pd
from config import Config
from pymongo import MongoClient

# Inicializar MongoDB client
client = MongoClient(Config.MONGO_URI)
db = client['RemindMe-test']
collection = db['reminders']


# Helper function to convert timestamp to string
def timestamp_to_string(ts):
    if isinstance(ts, int):
        # Assume seconds, convert to datetime and format
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return ts


# Fetch data from MongoDB and return DataFrame
def get_reminders_data(collection, start_date, end_date):
    """
    Busca en Mongo los datos de uso de la funcionalidad de remind me
    Retorna todos los documentos de la base en el rango dado con los campos
    El dataframe de salida tiene las columnas
    user_id: nro de teléfono del usuario
    date_time (str de la forma yyyy-mm-dd): fecha de creación del recordatorio
    sentAt (str de la forma yyyy-mm-dd): fecha de envío del recordatorio, si no se envió None
    status (str): sent si el recordatorio se envió, not_sent si no se envió
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

    match_stage = {"$match": {"date_time": 
                            {"$gte": start.strftime('%Y-%m-%dT00:00:00.000-04:00'),
                            "$lt": end.strftime('%Y-%m-%dT00:00:00.000-04:00')}}}
    
    # Un solo proyecto que incluya todos los campos necesarios
    project_stage = {
        "$project": {
            "user_id": 1,
            "date_time": { "$substr": ["$date_time", 0, 10] },
            "sentAt": { "$ifNull": [{ "$substr": ["$sentAt", 0, 10] }, None] },
            "status": { "$ifNull": ["$status", "not_sent"] },
            "_id": 0
        }
    }
    pipeline = [match_stage, project_stage]

    data = list(collection.aggregate(pipeline))
    return pd.DataFrame(data)

# Metric functions
def get_daily_users(df):
    """Users creating reminders per day."""
    if df.empty:
        return pd.DataFrame({"date_time": [], "count": []})
    daily_users = df.groupby('date_time')['user_id'].nunique().reset_index(name='count')
    return daily_users

def get_monthly_users(df):
    """Users creating reminders per month."""
    if df.empty:
        return pd.DataFrame({"mes": [], "count": []})
    df['mes'] = pd.to_datetime(df['date_time']).dt.to_period('M').astype(str)
    df_month = df.groupby('mes')['user_id'].nunique().reset_index(name="count")
    return df_month

def get_daily_reminds_created(df):
    """Reminders created per day."""
    if df.empty:
        return pd.DataFrame({"date_time": [], "count": []})
    # Group by date_created and count
    daily_counts = df.groupby('date_time').size().reset_index(name='count')
    return daily_counts.sort_values('date_time').reset_index(drop=True)

def get_monthly_reminds_created(df):
    """Reminders created per month."""
    if df.empty:
        return pd.DataFrame({"month": [], "count": []})
    # Convert date_time to datetime and extract month
    df['month'] = pd.to_datetime(df['date_time'], errors='coerce').dt.strftime('%Y-%m')
    # Group by month and count
    monthly_counts = df.groupby('month').size().reset_index(name='count')
    return monthly_counts.sort_values('month').reset_index(drop=True)

def get_daily_reminds_sent(df):
    if df.empty:
        return pd.DataFrame({"date_time": [], "count": []})
    sent_date = df[df['status'] == "sent"]
    daily_sent = sent_date.groupby('date_time').size().reset_index(name='count')
    return daily_sent

def get_monthly_reminds_sent(df):
    """Return DataFrame with month and count of status == 'sent' per month."""
    if df.empty:
        return pd.DataFrame({"month": [], "count": []})
    # Filter for status == 'sent'
    sent_date = df[df['status'] == 'sent']
    # Convert date_time to datetime and extract month
    sent_date['month'] = pd.to_datetime(sent_date['date_time'], errors='coerce').dt.strftime('%Y-%m')
    # Group by month and count
    monthly_sent = sent_date.groupby('month').size().reset_index(name='count')
    return monthly_sent

def calculate_metrics(start_date, end_date):
    """Calcula todas las métricas para el rango de fechas dado."""
    data = get_reminders_data(collection, start_date, end_date)
    
    if data.empty:
        return {
            "total_users": 0,
            "total_reminds_created": 0,
            "total_reminds_sent": 0,
            "average_daily_users": 0,
            "average_monthly_users": 0,
            "per_user_reminds_created": 0,
            "per_user_reminds_sent": 0,
            "daily_users": pd.DataFrame({"date_time": [], "count": []}),
            "monthly_users": pd.DataFrame({"mes": [], "count": []}),
            "daily_reminds_created": pd.DataFrame({"date_time": [], "count": []}),
            "monthly_reminds_created": pd.DataFrame({"month": [], "count": []}),
            "daily_reminds_sent": pd.DataFrame({"date_time": [], "count": []}),
            "monthly_reminds_sent": pd.DataFrame({"month": [], "count": []}),
            "average_daily_reminds_created": 0,
            "average_daily_reminds_sent": 0,
            "average_per_user_daily_reminds_created": 0,
            "average_per_user_daily_reminds_sent": 0,
            "average_monthly_reminds_created": 0,
            "average_monthly_reminds_sent": 0,
            "average_per_user_monthly_reminds_created": 0,
            "average_per_user_monthly_reminds_sent": 0
        }
    
    # Calcular métricas
    daily_users = get_daily_users(data)
    monthly_users = get_monthly_users(data)
    daily_reminds_created = get_daily_reminds_created(data)
    monthly_reminds_created = get_monthly_reminds_created(data)
    daily_reminds_sent = get_daily_reminds_sent(data)
    monthly_reminds_sent = get_monthly_reminds_sent(data)

    # Totales
    total_users = data['user_id'].nunique()
    total_reminds_created = len(data)
    total_reminds_sent = data[data['status'] == 'sent'].shape[0]

    # Estadísticas de usuarios
    average_daily_users = daily_users['count'].mean() if not daily_users.empty else 0
    average_monthly_users = monthly_users['count'].mean() if not monthly_users.empty else 0
    per_user_reminds_created = total_reminds_created / total_users if total_users > 0 else 0
    per_user_reminds_sent = total_reminds_sent / total_users if total_users > 0 else 0

    # Estadísticas diarias
    average_daily_reminds_created = daily_reminds_created['count'].mean() if not daily_reminds_created.empty else 0
    average_daily_reminds_sent = daily_reminds_sent['count'].mean() if not daily_reminds_sent.empty else 0
    average_per_user_daily_reminds_created = average_daily_reminds_created / total_users if total_users > 0 else 0
    average_per_user_daily_reminds_sent = average_daily_reminds_sent / total_users if total_users > 0 else 0

    # Estadísticas mensuales
    average_monthly_reminds_created = monthly_reminds_created['count'].mean() if not monthly_reminds_created.empty else 0
    average_monthly_reminds_sent = monthly_reminds_sent['count'].mean() if not monthly_reminds_sent.empty else 0
    average_per_user_monthly_reminds_created = average_monthly_reminds_created / total_users if total_users > 0 else 0
    average_per_user_monthly_reminds_sent = average_monthly_reminds_sent / total_users if total_users > 0 else 0

    return {
        "total_users": total_users,
        "total_reminds_created": total_reminds_created,
        "total_reminds_sent": total_reminds_sent,
        "average_daily_users": average_daily_users,
        "average_monthly_users": average_monthly_users,
        "per_user_reminds_created": per_user_reminds_created,
        "per_user_reminds_sent": per_user_reminds_sent,
        "daily_users": daily_users,
        "monthly_users": monthly_users,
        "daily_reminds_created": daily_reminds_created,
        "monthly_reminds_created": monthly_reminds_created,
        "daily_reminds_sent": daily_reminds_sent,
        "monthly_reminds_sent": monthly_reminds_sent,
        "average_daily_reminds_created": average_daily_reminds_created,
        "average_daily_reminds_sent": average_daily_reminds_sent,
        "average_per_user_daily_reminds_created": average_per_user_daily_reminds_created,
        "average_per_user_daily_reminds_sent": average_per_user_daily_reminds_sent,
        "average_monthly_reminds_created": average_monthly_reminds_created,
        "average_monthly_reminds_sent": average_monthly_reminds_sent,
        "average_per_user_monthly_reminds_created": average_per_user_monthly_reminds_created,
        "average_per_user_monthly_reminds_sent": average_per_user_monthly_reminds_sent
    }
