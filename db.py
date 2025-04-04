# db.py

import pyodbc


def get_connection():
    return pyodbc.connect("DSN=LI-STARROCKS", autocommit=True)


# Adiciona SET lc_time_names = 'pt_BR' para garantir que os dias da semana sejam retornados em português no fetch_one e no fetch_all
def fetch_one(query: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None


def fetch_row(query: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row if row else None


def fetch_all(query: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results
