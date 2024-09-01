import sqlite3
db = 'db/db1.db'

def getAllRacs():
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    racs = cursor.execute('SELECT * FROM Raccolte').fetchall()
    cursor.close()
    connection.close()
    return racs



def createRac(rac):
    result = False
    sql = 'INSERT INTO Raccolte (UserID, Successo, Open, TotaleRaccolto, Target, Title, Description, ActivationDate, ActivationTime, CloseDate, CloseTime, Min, Max, Type, Img) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute(sql, (rac['UserID'],rac['Successo'],rac['Open'],rac['TotaleRaccolto'],
                             rac['Target'],rac['Title'],rac['Description'],rac['ActivationDate'],rac['ActivationTime'],rac['CloseDate'],
                             rac['CloseTime'],rac['Min'],rac['Max'],rac['Type'], rac['Img']))
        connection.commit()
        result = True
    except Exception as e:
        print('Error', str(e))
        connection.rollback()
        result = False
        
    
    cursor.close()
    connection.close()
    return result

def getRacByID(id):
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    rac = cursor.execute('SELECT * FROM Raccolte WHERE RacID = ?', (id,)).fetchone()

    cursor.close()
    connection.close()
    
    return rac

def getRacsByUserID(id):
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    racs = cursor.execute('SELECT * FROM Raccolte WHERE UserID = ?', (id,)).fetchall()

    cursor.close()
    connection.close()
    
    return racs

def getRacsByTitle(title_query, user_id):
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    # Normalizza la query di ricerca in minuscolo
    title_query = title_query.lower()
    # Utilizza il carattere jolly % per cercare tutte le raccolte che contengono la query di ricerca nel titolo
    racs = cursor.execute('SELECT * FROM Raccolte WHERE LOWER(Title) LIKE ? AND UserID = ?', ('%' + title_query + '%', user_id)).fetchall()

    cursor.close()
    connection.close()
    
    return racs





def getRacsByState(state):
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    racs = cursor.execute('SELECT * FROM Raccolte WHERE Open = ?', (state,)).fetchall()

    cursor.close()
    connection.close()
    
    return racs

def updateRac(rac):
    result = False
    sql = 'UPDATE Raccolte SET UserID = ?, Successo = ?, Open = ?, TotaleRaccolto = ?, Target = ?, Title = ?, Description = ?, ActivationDate = ?, ActivationTime = ?, CloseDate = ?, CloseTime = ?, Min = ?, Max = ?, Type = ?, Img = ? WHERE RacID = ?'
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute(sql, (rac['UserID'],rac['Successo'],rac['Open'],rac['TotaleRaccolto'],
                             rac['Target'],rac['Title'],rac['Description'],rac['ActivationDate'],rac['ActivationTime'],rac['CloseDate'],
                             rac['CloseTime'],rac['Min'],rac['Max'],rac['Type'], rac['Img'], rac['RacID']))
        connection.commit()
        result = True
    except Exception as e:
        print('Error', str(e))
        connection.rollback()
        result = False
        
    
    cursor.close()
    connection.close()
    return result

def RacSetState(id, state):
    result = False
    sql = 'UPDATE Raccolte SET Open = ? WHERE RacID = ?'
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute(sql, (state, id))
        connection.commit()
        result = True
    except Exception as e:
        print('Error', str(e))
        connection.rollback()
        result = False
        
    
    cursor.close()
    connection.close()
    return result

def deleteRac(id):
    result = False
    sql = 'DELETE FROM Raccolte WHERE RacID = ?'
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute(sql, (id,))
        connection.commit()
        result = True
    except Exception as e:
        print('Error', str(e))
        connection.rollback()
        result = False
        
    
    cursor.close()
    connection.close()
    return result

def updateTotaleRaccolto(id, totaleRaccolto):
    result = False
    sql = 'UPDATE Raccolte SET TotaleRaccolto = ? WHERE RacID = ?'
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute(sql, (totaleRaccolto, id))
        connection.commit()
        result = True
    except Exception as e:
        print('Error', str(e))
        connection.rollback()
        result = False
        
    
    cursor.close()
    connection.close()
    return result
