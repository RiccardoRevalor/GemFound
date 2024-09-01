import sqlite3
db = 'db/db1.db'

def sendDonation(donation):
    #RacID è l'id della raccolta a cui si vuole donare
    #donation è la donazione, è struttura come un dizionario con: NomeVisualizzato (può anche essere Anonimo), Importo, Commento (opzionale) 
    #la donation è generata dal form di donazione e gestita dalla funzione che si occupa del POST
    #la funzione del POST richiama questa funzione passandogli i parametri
    #la funzione si occupa di aggiungere la donazione al database
    #la funzione ritorna True se la donazione è stata aggiunta correttamente, False altrimenti
    result = None
    sql = 'INSERT INTO Donazioni(RacID, NomeVisualizzato, Importo, Commento, UserID, Data) VALUES (?,?,?,?,?,?)'
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    try:
        cursor.execute(sql, (donation['RacID'], donation['NomeVisualizzato'], donation['Importo'], donation['Commento'], donation['UserID'], donation['Data']))
        connection.commit()
        result = cursor.lastrowid  # Ottieni l'ID dell'ultima riga inserita
    except Exception as e:
        print('Error', str(e))
        connection.rollback()
        result = None
        
    
    cursor.close()
    connection.close()
    return result

def deleteDonation(donation_id):
    # donation_id è l'id della donazione che si desidera eliminare
    # La funzione si occupa di eliminare la donazione dal database
    # Ritorna True se la donazione è stata eliminata correttamente, False altrimenti
    result = False
    sql = 'DELETE FROM Donazioni WHERE numTransazione = ?'
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, (donation_id,))
        connection.commit()
        result = True
    except Exception as e:
        print('Error:', str(e))
        connection.rollback()
        result = False

    cursor.close()
    connection.close()
    return result


def getDonationsByRacID(id):
    #id è l'id della raccolta di cui si vogliono le donazioni
    #la funzione ritorna tutte le donazioni relative a quella raccolta
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    donations = cursor.execute('SELECT * FROM Donazioni WHERE RacID = ?', (id,)).fetchall()

    cursor.close()
    connection.close()
    
    return donations

def getDonationsByUserID(id):
    #id è l'id dell'utente di cui si vogliono le donazioni
    #la funzione ritorna tutte le donazioni relative a quell'utente
    #non è necessario essre iscritti per fare le donazioni, quindi la funzione può non ritornare nulla
    #una donazione dove non c'è un utente associato ha UserID = -1
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    donations = cursor.execute('SELECT * FROM Donazioni WHERE UserID = ?', (id,)).fetchall()

    cursor.close()
    connection.close()
    
    #fai il check, se donations è vuoto ritorna None
    if len(donations) == 0:
        return None
    return donations

def getDonationsbynumTransazione(numTransazione):
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    donation = cursor.execute('SELECT * FROM Donazioni WHERE numTransazione = ?', (numTransazione,)).fetchone()

    cursor.close()
    connection.close()

    return donation



