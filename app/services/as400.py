from flask import current_app


def lookup_account(account: str) -> dict:
    """Return AS400 lookup fields for an 8-digit account.

    When AS400_ENABLED=false, this returns mock data so the app can be used locally.
    The route that calls this function already validates the 8-character numeric mask.
    """
    if not current_app.config["AS400_ENABLED"]:
        return {
            "account": account,
            "name": f"CLIENTE {account}",
            "address1": "MORADA 1 MOCK",
            "address2": "MORADA 2 MOCK",
            "zip": "0000-000",
            "city": "LISBOA",
            "no_values_from_odbc": "ODBC MOCK",
        }

    import pyodbc

    conn_str = (
        f"DSN={current_app.config['AS400_DSN']};"
        f"UID={current_app.config['AS400_UID']};"
        f"PWD={current_app.config['AS400_PWD']}"
    )
    client_table = current_app.config["AS400_CLIENT_TABLE"]
    bic_table = current_app.config["AS400_BIC_TABLE"]

    sql_client = f"""
        SELECT clinom, CLIADR1, CLIADR2, CLICODPOS, CLIVILLE
        FROM {client_table}
        WHERE CLICOMPTE = ?
    """
    sql_bic = f"""
        SELECT BICVCLI
        FROM {bic_table}
        WHERE BICCPTCLI = ?
    """
    print("AS400 DSN:", current_app.config["AS400_DSN"])
    print("AS400 UID:", current_app.config["AS400_UID"])
    print("AS400 enabled:", current_app.config["AS400_ENABLED"])

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        row = cursor.execute(sql_client, account).fetchone()
        bic = cursor.execute(sql_bic, account).fetchone()

    if not row:
        return {}

    return {
        "account": account,
        "name": (row[0] or "").upper(),
        "address1": (row[1] or "").upper(),
        "address2": (row[2] or "").upper(),
        "zip": row[3] or "",
        "city": (row[4] or "").upper(),
        "no_values_from_odbc": bic[0] if bic else "",
    }
