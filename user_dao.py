import sqlite3
db = 'db/db1.db'

def get_user_by_id(id):

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM Utenti WHERE UserID = ?'
    cursor.execute(sql, (id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def get_user_by_mail(mail):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM Utenti WHERE UserMail = ?'
    cursor.execute(sql, (mail,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user

def get_user_by_nickname(nickname):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM Utenti WHERE UserNickName = ?'
    cursor.execute(sql, (nickname,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user

def create_user(nuovo_utente):
    query = 'INSERT INTO Utenti(UserNickName, Password, UserMail, Nome, Cognome, Ptf) VALUES (?,?,?,?,?,?)'

    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    success = False

    try:
        cursor.execute(query, (nuovo_utente['nickname'],nuovo_utente['password'],nuovo_utente['mail'], nuovo_utente['name'], nuovo_utente['surname'], 0))
        connection.commit()
        success = True
    except Exception as e:
        print('Error', str(e))
        connection.rollback()
        success = False

    cursor.close()
    connection.close()

    return success

def user_GetPtf(id):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT Ptf FROM Utenti WHERE UserID = ?'
    cursor.execute(sql, (id,))
    ptf = cursor.fetchone()

    cursor.close()
    conn.close()

    return ptf #ritorna il ptf dell'utente

def user_SetPtf(id, ptf):
    success = False
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'UPDATE Utenti SET Ptf = ? WHERE UserID = ?'

    try:
        cursor.execute(sql, (ptf, id))
        conn.commit()
        success = True
    except Exception as e:
        print('Error', str(e))
        conn.rollback()
        success = False


    cursor.close()
    conn.close()

    return success 

# funzione che ritorna tutti gli utenti
def get_all_users():
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sql = 'SELECT * FROM Utenti'
    cursor.execute(sql)
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return users