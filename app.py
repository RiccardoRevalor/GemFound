import datetime, os, re, hashlib, random
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import user_dao, rac_dao, don_dao
from user_model import User
from werkzeug.security import generate_password_hash, check_password_hash

# crea applicazione flask
app = Flask(__name__)
app.secret_key = 'chiave sessioni'  # Chiave segreta per le sessioni
app.config['SECRET_KEY'] = 'questa è una chiave segreta'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

login_manager = LoginManager()
login_manager.init_app(app)

result = None

def updatePtf(rac):
  # aggiorna il valore del ptf se il TotaleRaccolto è maggiore del target
  ptfOld = user_dao.user_GetPtf(rac['UserID'])
  if not ptfOld: return False
  ptfOld = int(ptfOld['Ptf'])
  money = int(rac['TotaleRaccolto'])
  if money >= int(rac['Target']):
    ptfNew = ptfOld + money
    if ptfNew > ptfOld: user_dao.user_SetPtf(rac['UserID'], ptfNew)
    #rac_dao.RacSetSuccesso(rac['RacID'], 1)
  return True

def checkRacOpen(rac):
  # ritorna True se la raccolta risulta effettivamente aperta, False altrimenti
  # nel caso la raccolta sia chiusa ma ancora con Open = 1, la chiude (aggiorando il db) e aggiorna il ptf e ritorna False
  today = datetime.datetime.now()

  if rac['Open'] == 0: 

    # raccolte sperimentali, se bisogna attivarle ora fallo e ritorna True
    if datetime.datetime.strptime(rac['ActivationDate'] + " " + rac['ActivationTime'], '%Y-%m-%d %H:%M') <= today and datetime.datetime.strptime(rac['CloseDate'] + " " + rac['CloseTime'], '%Y-%m-%d %H:%M') > today:
      r = rac_dao.RacSetState(rac['RacID'], 1) # apri la raccolta nel db
      if not r:
        flash('Errore nel far attivare la Raccolta Fondi ' + rac['Title'] + '!')
        return redirect(url_for('index'))
      return True # EFFETTIVAMENTE aperta
    else:
      # raccolte gia chiuse, non fare nulla
      return False  # chiusa

  # qua si ha rac['Open'] == 1 
  if datetime.datetime.strptime(rac['CloseDate'] + " " + rac['CloseTime'], '%Y-%m-%d %H:%M') <= today:
    # raccolta scaduta ma ancora con Open = 1, da chiudere e vedere se ha raggiunto il target

    r = rac_dao.RacSetState(rac['RacID'], 0) # chiudi la raccolta nel db
    if not r:
      flash('Errore nel chiudere la Raccolta Fondi!')
      return redirect(url_for('index'))
    # aggiorna il valore del ptf se il TotaleRaccolto risulta maggiore del target
    if not updatePtf(rac):
      flash('Errore nel calcolare il Ptf!')
      return redirect(url_for('index'))
    
    return False # EFFETTIVAMENTE chiusa, ho messo Open = 0 e aggiornato il db ed il ptf
  
  return True # EFFETTIVAMENTE aperta
  

@app.route('/')
def index():
  
  # Carica tutte le entry contenenti Raccolte fondi attive dal db
  result = rac_dao.getAllRacs()
  if not result:
    flash("Non ci sono raccolte attive, per adesso.")
    return render_template('index3.html', raccolte_attive=[], mode = 1)
  

  # trasforma result in lista di dizionari così da essere manipolabile (sqlite3Row è solo read only)
  result = [dict(r) for r in result]

  #controlla le raccolte e mostra nella home solo quelle attive, ordinandole per data di attivazione
  today = datetime.datetime.now()
  for rac in result[:]: # usa lo slicing per evitare di modificare la lista mentre la stai iterando

    if not checkRacOpen(rac):
      result.remove(rac)

  # calcola quanto manca (in ore, minuti) alla chiusura di ogni raccolta non scartata 
  for rac in result:
    closeDate = rac['CloseDate']
    closeTime = rac['CloseTime']
    closeDateTime = datetime.datetime.strptime(closeDate + " " + closeTime, '%Y-%m-%d %H:%M')
    timeLeft = closeDateTime - today
    total_seconds = timeLeft.total_seconds()
    # Calcola il numero di giorni, ore e minuti
    days = total_seconds // (24 * 3600)
    hours = (total_seconds % (24 * 3600)) // 3600
    minutes = (total_seconds % 3600) // 60

    # Scrivi il tempo rimanente come valore: x giorni, y ore, z minuti
    rac['tempoRimanente'] = f"{int(days)} giorni, {int(hours)} ore, {int(minutes)} minuti"


  # ordina la raccolte rimanenti in modo da avere quelle che chiudono prima in cima
  result = sorted(result, key=lambda k: datetime.datetime.strptime(k['CloseDate'] + " " + k['CloseTime'], '%Y-%m-%d %H:%M'))

  return render_template('index3.html', raccolte_attive=result, mode = 1)

#pagina per mostrare le raccolte passate
#esse sono ordinate mettendo prima quelle che hanno raggiunto il target
@app.route('/raccoltepassate')
def raccoltepassate():
  result = rac_dao.getAllRacs()
  if not result:
    flash("Non ci sono raccolte, per adesso.")
    return render_template('index3.html', raccolte_attive=[], mode = 0)
  
  # trasforma result in lista di dizionari così da essere manipolabile (sqlite3Row è solo read only)
  result = [dict(r) for r in result]  
  # Filtra le raccolte chiuse
  today = datetime.datetime.now()

  for rac in result[:]:
    if checkRacOpen(rac): # se la raccolta è ancora aperta, la elimina da result  
      result.remove(rac)

    # CHECK PER RACCOlTE CHE SI ATTIVANO NEL FUTURO (raccolte sperimentali)
    # vedi se la data di attivazione è nel futuro, se si rimuovi la raccolta da result, non devi mostrarla
    if datetime.datetime.strptime(rac['ActivationDate'] + " " + rac['ActivationTime'], '%Y-%m-%d %H:%M') > today and datetime.datetime.strptime(rac['CloseDate'] + " " + rac['CloseTime'], '%Y-%m-%d %H:%M') > today:
      #flash('Raccolta Fondi ' + rac['Title'] + ' si attiverà nel futuro!')
      result.remove(rac)


  for rac in result:
      rapporto = int(rac['TotaleRaccolto']) / int(rac['Target'])
      if rapporto >= 1:
          rac['Raggiunto'] = 1
      else:
          rac['Raggiunto'] = 0

  # Ordina le raccolte mostrando prima quelle che hanno raggiunto il target, e tra questi in ordine di data di chiusura più recente
  # Poi quelle che non l'hanno raggiunto, e tra questi in ordine di data di chiusura più recente
  result = sorted(result, key=lambda k: (k['Raggiunto'], datetime.datetime.strptime(k['CloseDate'] + " " + k['CloseTime'], '%Y-%m-%d %H:%M')), reverse=True)
  return render_template('index3.html', raccolte_attive=result, mode = 0)





# VECCHIA PAGINA DI REGISTRAZIONE - LA NUOVA E CON I MODALI
@app.route('/signup')
def signup():
  return render_template('signup.html')

# REGISTRAZIONE - METODO POST
@app.route('/signup2', methods=['POST'])
def signup2():

  new_user_from_form = request.form.to_dict()
  
  
  if new_user_from_form ['name'] == '':
    flash('Il campo Nome non deve essere vuoto')
    return redirect(url_for('index'))

  if new_user_from_form ['surname'] == '':
    flash('Il campo Cognome non deve essere vuoto')
    return redirect(url_for('index'))

  if new_user_from_form ['mail'] == '':
    flash('Il campo Mail non deve essere vuoto')
    return redirect(url_for('index'))

  if new_user_from_form ['password'] == '':
    flash('Il campo Password non deve essere vuoto')
    return redirect(url_for('index'))
  
  if new_user_from_form ['nickname'] == new_user_from_form ['mail']:
    flash('Non puoi usare la tua mail come nickname, o viceversa')
    return redirect(url_for('index'))

  if len(new_user_from_form ['nickname']) > 10:
    flash('Il nickname non deve essere più lungo di 10 caratteri')
    return redirect(url_for('index'))
  
  # verifica che il nick non sia già preso
  if user_dao.get_user_by_nickname(new_user_from_form ['nickname']):
    flash('Nickname già in uso. Se hai già un account, clicca su "Accedi" in alto a destra.', 'danger')
    return redirect(url_for('index'))
  
  # verifica che la mail non sia già presa
  if user_dao.get_user_by_mail(new_user_from_form ['mail']):
    flash('Mail già in uso. Se hai già un account, clicca su "Accedi" in alto a destra.', 'danger')
    return redirect(url_for('index'))
  
  new_user_from_form ['password'] = generate_password_hash(new_user_from_form ['password'])
  
  success = user_dao.create_user(new_user_from_form)

  if success:
    flash('Utente creato con successo, ora puoi accedere cliccando sul bottone "Accedi" in alto a destra!', 'success')
    return redirect(url_for('index'))
  else:
    flash('Spiacenti, si è verificato un errore nella creazione dell\'utente. Riprovare in un secondo momento.')

  return redirect(url_for('index'))

# VECCHIA FINESTRA DI LOGIN - ORA CON I MODALI
@app.route('/signin')
def signin():
  return render_template('signin.html')

# LOGIN - METODO POST
@app.route('/signin2', methods=['POST'])
def login():

  utente_form = request.form.to_dict()
  loginCredential = utente_form['loginName']

# prima cerca l'utente per mail, se non lo trova cerca per nickname
  utente_db = user_dao.get_user_by_mail(loginCredential)
  
  if not utente_db:
    utente_db = user_dao.get_user_by_nickname(loginCredential)

  # se l'utente non esiste o la password non è corretta genera errore
  if not utente_db or not check_password_hash(utente_db['Password'], utente_form['password']):
    flash("L'utente o la password non sono corretti.", 'danger')
    return redirect(url_for('index')) #prima era: sign_in ma ora h fatto il login col modale di bootstrap
  else:
    
  
    new = User(UserID=utente_db['UserID'], Nome=utente_db['Nome'], Cognome=utente_db['Cognome'], UserMail=utente_db['UserMail'], Password=utente_db['Password'], UserNickName=utente_db['UserNickName'], Ptf=utente_db['Ptf'] )
    login_user(new, True)
    flash(f'Ben ritrovato, {utente_db["Nome"]} {utente_db["Cognome"]}!', 'success')
    #print("User logged in: ", current_user.id, current_user.name, current_user.surname, current_user.mail, current_user.password, current_user.nickname)
    return redirect(url_for('index'))
  
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo')
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
  db_user = user_dao.get_user_by_id(user_id)

  utente = User(UserID=db_user['UserID'],
  Nome=db_user['Nome'],
  Cognome=db_user['Cognome'],
  UserMail=db_user['UserMail'],
  Password=db_user['Password'],
  UserNickName=db_user['UserNickName'],
  Ptf=db_user['Ptf'])

  return utente 

@app.route('/newraccolta')
@login_required
def newraccolta():
  return render_template('newraccolta.html', update = False)

def hash_file_name(user_id, upload_date):
    random_number = random.randint(0, 9999)  
    data_to_hash = f"{user_id}-{upload_date}-{random_number}"
    hash_object = hashlib.sha256(data_to_hash.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex

@app.route('/crearaccolta', methods=['POST'])
@login_required
def crearaccolta():
  raccolta = request.form.to_dict()

  
  if raccolta['title'] == '':
    flash('Il titolo non deve essere vuoto!')
    return redirect(url_for('newraccolta'))
  if len(raccolta['title']) > 30:
    flash('Il titolo deve avere al massimo 30 caratteri!')
    return redirect(url_for('newraccolta'))
  if not raccolta['target'].isdecimal():
    flash('Il target deve essere un numero!')
    return redirect(url_for('newraccolta'))
  t = int(raccolta['target'])
  if (t <= 0):
    flash('Il target deve essere maggiore di 0!')
    return redirect(url_for('newraccolta'))
  if (t > 1000000):
    flash('Il target deve essere minore o uguale a 1 mln!')
    return redirect(url_for('newraccolta'))
  if not raccolta['min'].isdecimal():
    flash('La donazione minima deve essere un numero!')
    return redirect(url_for('newraccolta'))
  if not raccolta['max'].isdecimal():
    flash('La donazione massima deve essere un numero!')
    return redirect(url_for('newraccolta'))
  
  dmin = int(raccolta['min'])
  dmax = int(raccolta['max'])
  if (dmin <= 0 or dmax <= 0):
    flash('La donazione minima e massima non possono essere minori o uguali a 0!')
    return redirect(url_for('newraccolta'))
  if dmin > dmax:
    flash('La donazione minima non deve essere maggiore della donazione massima!')
    return redirect(url_for('newraccolta'))
  if (dmin > t or dmax > t):
    flash('La donazione minima e massima non possono essere maggiori del target!')
    return redirect(url_for('newraccolta'))
  if not raccolta['type'] in ['0', '1']:
    flash('Il tipo di raccolta non risulta valido!')
    return redirect(url_for('newraccolta'))
  
  dataPattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}'

  today = datetime.datetime.now()
  if not 'attiva_subito' in raccolta.keys():
    if not re.match(dataPattern, raccolta['activation']):
      flash('Errore nella data di attivazione!')
      return redirect(url_for('newraccolta'))
    startDate = raccolta['activation']
    sdatestr = startDate.replace('T', ' ')
    sdate = datetime.datetime.strptime(sdatestr, '%Y-%m-%d %H:%M')
    if sdate < today:
      flash('La data di attivazione della Raccolta Fondi non può essere nel passato!')
      return redirect(url_for('newraccolta'))
  else:
    if raccolta['attiva_subito'] == 'on': 
      sdate = today
    else:
      flash('Errore nella data di attivazione!')
      return redirect(url_for('newraccolta'))
    
  if raccolta['type'] == '0':
    # raccolta normale 
    if not re.match(dataPattern, raccolta['close']):
      flash('Errore nella data di chiusura!')
      return redirect(url_for('newraccolta'))
    endDate = raccolta['close']
    edatestr = endDate.replace('T', ' ')
    edate = datetime.datetime.strptime(edatestr, '%Y-%m-%d %H:%M')
    # controllo che la data di chiusura non sia troppo lontana da quella di apertura (max 14 giorni)
    if edate - sdate > datetime.timedelta(days=14):
      flash('La data di chiusura della Raccolta Fondi non può distare più di 14 giorni da quella di apertura!')
      return redirect(url_for('newraccolta'))
  else:
    # raccolta lampo, aggiungi 5 minuti alla data di attivazione
    edate = sdate + datetime.timedelta(minutes=5)
  
  if edate <= sdate:
    flash('La data di chiusura della Raccolta Fondi non può essere prima della data di attivazione, o coincidere con essa!')
    return redirect(url_for('newraccolta'))
  if edate <= today:
    flash('La data di chiusura della Raccolta Fondi non può essere nel passato, o coincidere con adesso!')
    return redirect(url_for('newraccolta'))
  if raccolta['description'] == '':
    flash('La descrizione non può essere vuota!')
    return redirect(url_for('newraccolta'))
  if len(raccolta['description']) > 300:
    flash('La descrizione non può essere più lunga di 300 caratteri!')
    return redirect(url_for('newraccolta'))

  # controllo errori andato a buon fine

    

  # esempio: {'title': 'titolo', 'description': 'desc', 'target': '1000', 'activation': '2024-02-14T17:04', 'close': '2024-02-16T17:00', 'min': '1', 'max': '2', 'type': '0'}
  newRacDict = {}
  newRacDict['UserID'] = current_user.id
  newRacDict['Successo'] = 0
  if 'attiva_subito' in raccolta.keys():
    if raccolta['attiva_subito'] == 'on':
      newRacDict['Open'] = 1
    else:
      newRacDict['Open'] = 0
  else:
    newRacDict['Open'] = 0 # raccolta non attiva subito, si attiverà nel futuro
  newRacDict['TotaleRaccolto'] = 0
  newRacDict['Target'] = t
  newRacDict['Title'] = raccolta['title']
  newRacDict['Description'] = raccolta['description']
  newRacDict['ActivationDate'] = sdate.strftime('%Y-%m-%d')
  newRacDict['ActivationTime'] = sdate.strftime('%H:%M')
  newRacDict['CloseDate'] = edate.strftime('%Y-%m-%d')
  newRacDict['CloseTime'] = edate.strftime('%H:%M')
  newRacDict['Min'] = dmin
  newRacDict['Max'] = dmax
  newRacDict['Type'] = int(raccolta['type'])

  accepted_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
  if 'img' in request.files:
    if request.files['img'].filename != '':
      image_file = request.files['img']
      file_extension = os.path.splitext(image_file.filename)[1]
      if not file_extension.lower() in accepted_extensions:
        flash("L'estensione del file (" + file_extension + ") non risulta valida.")
        return redirect(url_for('newraccolta'))
      # calcola hash per il nome del file che sarà salvato sul server
      n_hash = hash_file_name(current_user.id, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
      newfilename = n_hash + file_extension
      image_file.save('./static/' + newfilename) # salva img sul server, cartella static
      newRacDict['Img'] = newfilename # nel db salva solo l'url della img
    else: 
      newRacDict['Img'] = '0'
  else:
    newRacDict['Img'] = '0' 
  #print(newRacDict) 

  res = rac_dao.createRac(newRacDict)
  if not res:
    flash('Errore nella creazione della Raccolta Fondi! Si prega di riprovare più tardi.')
    return redirect(url_for('newraccolta'))
  flash('Raccolta Fondi creata con successo! Puoi visualizzarla in "Le tue raccolte"')

  
  return redirect(url_for('index'))

@app.route('/mieraccolte')
@login_required
def mieraccolte():
  racs = rac_dao.getRacsByUserID(current_user.id)
  if len(racs) == 0:
    flash('Non hai ancora creato nessuna Raccolta Fondi!')
    return redirect(url_for('index'))
  for rac in racs: checkRacOpen(rac) #aggiorna raccolte e in caso aggiorna ptf
  ptfValue = user_dao.user_GetPtf(current_user.id) # prendi il valore del ptf dell'utente aggiornato dopo aver fatto il check
  return render_template('mieraccolte.html', raccolte=racs, ptfValue=ptfValue['Ptf'], ricerca=False, keyword='')


@app.route('/raccolta/<int:id>')
def raccolta(id):
  rac = rac_dao.getRacByID(id)
  dons = don_dao.getDonationsByRacID(id) # possono non esserci donazioni
  nd = 0
  if dons: nd = len(dons)
  if not rac:
    flash('Raccolta Fondi non trovata!')
    return redirect(url_for('index'))
  user = user_dao.get_user_by_id(rac['UserID'])
  if not user:
    flash('Utente creatore della Raccolta non trovato!')
    return redirect(url_for('index'))
  nickname = user['UserNickName']

  sperimentale=0 # se è una raccolta sperimentale che si attiva nel futuro
  rag = 0 # se è stata raggiunto l'obiettivo
  today = datetime.datetime.now()
  if not checkRacOpen(rac):
    # raccolte sperimentali che si attivano nel futuro
    if datetime.datetime.strptime(rac['ActivationDate'] + " " + rac['ActivationTime'], '%Y-%m-%d %H:%M') > today and datetime.datetime.strptime(rac['CloseDate'] + " " + rac['CloseTime'], '%Y-%m-%d %H:%M') > today:
      sperimentale = 1
    else:
      # se la raccolta fondi è chiusa, vedi se è stato raggiunto il target
      rapporto = int(rac['TotaleRaccolto']) / int(rac['Target'])
      if rapporto >= 1: rag = 1
  return render_template('single2.html', raccolta=rac, nickname=nickname, donazioni=dons, nd= nd, raggiunto = rag, sperimentale = sperimentale)

@app.route('/modificaraccolta/<int:id>')
@login_required
def modificaraccolta(id):
  rac = rac_dao.getRacByID(id)
  if not rac:
    flash('Raccolta Fondi non esistente oppure eliminata in precedenza!')
    return redirect(url_for('mieraccolte'))
  
  if rac['UserID'] != current_user.id:
    flash('Nessuna raccolta di questo tipo è associata al tuo account!')
    return redirect(url_for('mieraccolte'))
  
  # verifica che Raccolta non sia chiusa

  if rac['Open'] == 0:
    flash('Non puoi modificare una Raccolta Fondi chiusa!')
    return redirect(url_for('mieraccolte'))
  
  # fai il check se la raccolta è effettivamente ancora aperta, sennò settala come chiusa e aggiorna il ptf
  today = datetime.datetime.now()
  if not checkRacOpen(rac):
    if datetime.datetime.strptime(rac['CloseDate'] + " " + rac['CloseTime'], '%Y-%m-%d %H:%M') <= today:
      flash('Non puoi modificare una Raccolta Fondi chiusa! Chiusa il ' + rac['CloseDate'] + " alle " + rac['CloseTime'] + '.')
    else: flash('Non puoi modificare una Raccolta Fondi non aperta! Aprirà il ' + rac['ActivationDate'] + " alle " + rac['ActivationTime'] + '.')
    return redirect(url_for('mieraccolte'))
  
  return render_template('newraccolta.html', raccolta=rac, update = True)

@app.route('/modificaraccolta2/<int:id>', methods=['POST'])
@login_required
def modificaraccolta2(id):
  raccolta = request.form.to_dict() # raccolta modificata
  rac = rac_dao.getRacByID(id) # raccolta salvata nel db

  
  
  if not rac:
    flash('Raccolta Fondi non esistente oppure eliminata in precedenza!')
    return redirect(url_for('mieraccolte'))
  if rac['UserID'] != current_user.id:
    flash('Non puoi modificare una Raccolta Fondi che non hai creato tu!')
    return redirect(url_for('mieraccolte'))
  
  
  # TI CALCOLI SE LA RAC è ANCORA OPEN, SENNO NON LA PUOI PIù MODIFICARE
  today = datetime.datetime.now()
  if not checkRacOpen(rac):
    if datetime.datetime.strptime(rac['CloseDate'] + " " + rac['CloseTime'], '%Y-%m-%d %H:%M') <= today:
      flash('Non puoi modificare una Raccolta Fondi chiusa! Chiusa il ' + rac['CloseDate'] + " alle " + rac['CloseTime'] + '.')
    else: flash('Non puoi modificare una Raccolta Fondi non aperta! Aprirà il ' + rac['ActivationDate'] + " alle " + rac['ActivationTime'] + '.')
    return redirect(url_for('mieraccolte'))
  


  

  # fine controllo: Rac è OPEN
  # SE RAC è OPEN CONTROLLA CHE I CAMP IMMESSI NEL FORM DI MODIFICA SIANO OK
  if raccolta['title'] == '':
    flash('Il titolo non può essere vuoto!')
    return redirect(url_for('modificaraccolta', id=id))
  if len(raccolta['title']) > 30:
    flash('Il titolo deve avere al massimo 30 caratteri!')
    return redirect(url_for('modificaraccolta', id=id))
  if not raccolta['target'].isdecimal():
    flash('Il target deve essere un numero!')
    return redirect(url_for('modificaraccolta', id=id))
  t = int(raccolta['target'])
  if (t <= 0):
    flash('Il target deve essere maggiore di 0!')
    return redirect(url_for('modificaraccolta', id=id))
  if (t > 1000000):
    flash('Il target deve essere minore o uguale a 1 mln!')
    return redirect(url_for('modificaraccolta', id=id))
  if not raccolta['min'].isdecimal():
    flash('La donazione minima deve essere un numero!')
    return redirect(url_for('modificaraccolta', id=id))
  if not raccolta['max'].isdecimal():
    flash('La donazione massima deve essere un numero!')
    return redirect(url_for('modificaraccolta', id=id))
  
  dmin = int(raccolta['min'])
  dmax = int(raccolta['max'])
  if (dmin <= 0 or dmax <= 0):
    flash('La donazione minima e massima non possono essere minori o uguali a 0!')
    return redirect(url_for('modificaraccolta', id=id))
  if dmin > dmax:
    flash('La donazione minima non può essere maggiore della donazione massima!')
    return redirect(url_for('modificaraccolta', id=id))
  if (dmin > t or dmax > t):
    flash('La donazione minima e massima  non possono essere maggiori del target!')
    return redirect(url_for('modificaraccolta', id=id))
  if not raccolta['type'] in ['0', '1']:
    flash('Il tipo di raccolta non è valido!')
    return redirect(url_for('modificaraccolta', id=id))
  if raccolta['description'] == '':
    flash('La descrizione non può essere vuota!')
    return redirect(url_for('modificaraccolta', id=id))
  if len(raccolta['description']) > 300:
    flash('La descrizione non può essere più lunga di 300 caratteri!')
    return redirect(url_for('modificaraccolta', id=id))
  
  newRacDict = {}
  #CASI:
  #1) RAC è LAMPO, RACCOLTA MODIFICATA è LAMPO -> NON TOCCARE LE DATE
  #2) RAC è LAMPO, RACCOLTA MODIFICATA è NORMALE -> MODIFICARE LE CLOSEDATE, CLOSETIME A PATTO CHE LA LAMPO NON SIA GIA' SCADUTA
  #3) RAC è NORMALE, RACCOLTA MODIFICATA è LAMPO -> MODIFICARE LE CLOSEDATE, CLOSETIME A PATTO CHE LA NORMALE NON SIA GIA' SCADUTA E NON SONO PASSATI PIU' DI 5 MIN DA DATA DI ATTIVAZIONE
  #4) RAC è NORMALE, RACCOLTA MODIFICATA è NORMALE -> MODIFICARE LE CLOSEDATE, SE SONO DIVERSE DA QUELLE DI RAC
  
  #devi verificare, nel caso di una raccolta di tipo normale, che la data di chiusura disti da quella di apertura massimo 14 giorni

  # la data di attivazione la prendi dal Db tanto non la puoi modificare
  startDatefromDB = rac['ActivationDate'] + " " + rac['ActivationTime']
  sdate = datetime.datetime.strptime(startDatefromDB, '%Y-%m-%d %H:%M')
  
  dataPattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}'

  # prenditi la nuova endDate 
  if raccolta['type'] == '0':
    # raccolta normale 
    if not re.match(dataPattern, raccolta['close']):
      flash('Errore nella data di chiusura!')
      return redirect(url_for('modificaraccolta', id=id))
    endDate = raccolta['close']
    edatestr = endDate.replace('T', ' ')
    edate = datetime.datetime.strptime(edatestr, '%Y-%m-%d %H:%M')
    if edate < today:
      flash('La data di chiusura della Raccolta Fondi non può essere nel passato!')
      return redirect(url_for('modificaraccolta', id=id))
    
    if edate - sdate > datetime.timedelta(days=14):
      flash('La data di chiusura della Raccolta Fondi non può distare più di 14 giorni da quella di apertura!')
      return redirect(url_for('modificaraccolta', id=id))
  else:
    # raccolta lampo, aggiungi 5 minuti alla data di attivazione
    edate = rac['ActivationDate'] + " " + rac['ActivationTime']
    edate = datetime.datetime.strptime(edate, '%Y-%m-%d %H:%M')
    edate = edate + datetime.timedelta(minutes=5)
  
  # MODIFICA DEL TIPO DI RACCOLTA
  if rac['type'] == 1 and raccolta['type'] == "0":
    # da lampo a normale
    newRacDict['Type'] = 0
  elif rac['type'] == 0 and raccolta['type'] == "1":
    # da normale a lampo
    # controlla che puoi trasformarla in lampo
    # se la data di chiusura è minore di quella attuale, non puoi
    # nel senso, se sono passati più di 5 minuti da quando la raccolta normale si è attivata, essa non può diventare lampo
    if edate <= today:
      flash('Non puoi trasformare questa Raccolta Fondi normale in una Raccolta Fondi lampo siccome i 5 minuti sarebbero scaduti!')
      return redirect(url_for('modificaraccolta', id=id))
    
    newRacDict['Type'] = 1
  elif rac['type'] == 0 and raccolta['type'] == "0":
    newRacDict['Type'] = 0 # rimane normale
  else: newRacDict['Type'] = 1 # rimane lampo

  newRacDict['RacID'] = rac['RacID']
  newRacDict['UserID'] = rac['UserID']
  newRacDict['Successo'] = rac['Successo']
  newRacDict['Open'] = rac['Open']
  newRacDict['TotaleRaccolto'] = rac['TotaleRaccolto']
  newRacDict['Target'] = t
  newRacDict['Title'] = raccolta['title']
  newRacDict['Description'] = raccolta['description']
  newRacDict['ActivationDate'] = rac['ActivationDate']
  newRacDict['ActivationTime'] = rac['ActivationTime']
  newRacDict['CloseDate'] = edate.strftime('%Y-%m-%d')
  newRacDict['CloseTime'] = edate.strftime('%H:%M')
  newRacDict['Min'] = dmin
  newRacDict['Max'] = dmax

  accepted_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
  if 'img' in request.files:

    if request.files['img'].filename != '':
      image_file_old = rac['Img']
      image_file = request.files['img']
      file_extension = os.path.splitext(image_file.filename)[1]
      if not file_extension.lower() in accepted_extensions:
        flash("L'estensione del file (" + file_extension + ") non risulta valida.")
        return redirect(url_for('modificaraccolta', id=id))
      #n = str(current_user.id) + "-" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + "-" + image_file.filename
      # calcola hash per il nome del file che sarà salvato sul server
      nhash = hash_file_name(current_user.id, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
      newfilename = nhash + file_extension
      image_file.save('./static/' + newfilename) # salva img sul server, cartella static
      oldpath = './static/' + image_file_old
      if os.path.exists(oldpath) and oldpath != './static/default.jpg' and oldpath != './static/premium.png': os.remove(oldpath) # cancella img vecchia dal server, se esiste
      newRacDict['Img'] = newfilename 
    else: 
      newRacDict['Img'] = rac['Img'] # l'immagine non è ne modificata ne cancellata
  else:
    newRacDict['Img'] = rac['Img'] # l'immagine non è ne modificata ne cancellata

  if 'deleteImg' in raccolta.keys():
      if raccolta['deleteImg'] == 'on':
        # elimina img vecchia dal server, se esiste
        image_file_old = rac['Img']
        oldpath = './static/' + image_file_old
        if os.path.exists(oldpath) and oldpath != './static/default.jpg' and oldpath != './static/premium.png': os.remove(oldpath) # cancella img vecchia dal server, se esiste
        newRacDict['Img'] = "0"
      
  
  #flash("Raccolta fondi: " + rac['Title'] + "cambiamenti: " + str(newRacDict))
  res = rac_dao.updateRac(newRacDict)
  if not res:
    flash('Errore nella modifica della Raccolta Fondi!')
    return redirect(url_for('mieraccolte'))
  flash('Raccolta Fondi modificata con successo: ' + raccolta['title'])
  return redirect(url_for('mieraccolte'))
    

@app.route('/deleteraccolta/<int:id>')
@login_required
def deleteraccolta(id):
  rac = rac_dao.getRacByID(id)
  if not rac:
    flash('Raccolta Fondi non esistente oppure eliminata in precedenza!')
    return redirect(url_for('mieraccolte'))
  if rac['UserID'] != current_user.id:
    flash('Raccolta Fondi non trovata tra le tue Raccolte.')
    return redirect(url_for('mieraccolte'))
  
  # non puoi eliminare una rac chiusa
  today = datetime.datetime.now()
  if not checkRacOpen(rac):
    if datetime.datetime.strptime(rac['CloseDate'] + " " + rac['CloseTime'], '%Y-%m-%d %H:%M') <= today:
      flash('Non puoi eliminare una Raccolta Fondi chiusa! Chiusa il ' + rac['CloseDate'] + " alle " + rac['CloseTime'] + '.')
    else: flash('Non puoi eliminare una Raccolta Fondi non aperta! Aprirà il ' + rac['ActivationDate'] + " alle " + rac['ActivationTime'] + '.')
    return redirect(url_for('mieraccolte'))

  res = rac_dao.deleteRac(id)
  if not res:
    flash('Errore nell\'eliminazione della Raccolta Fondi!')
    return redirect(url_for('mieraccolte'))
  
  # elimina img dal server, se esiste
  if rac['Img'] != '0':
    image_file = rac['Img']
    path = './static/' + image_file
    if os.path.exists(path) and path != './static/default.jpg' and path != './static/premium.png': os.remove(path) # cancella img dal server, se esiste

  flash('Raccolta Fondi eliminata con successo: ' + rac['Title'])
  return redirect(url_for('mieraccolte'))

@app.route('/donazione/<int:id>')
def donazione(id):
  rac = rac_dao.getRacByID(id)
  if not rac:
    flash('Raccolta Fondi non trovata!')
    return redirect(url_for('index'))
  
  # non puoi donare ad una raccolta chiusa
  if not checkRacOpen(rac):
    flash('Raccolta Fondi Chiusa! Impossibile donare.')
    return redirect(url_for('index'))
  
  return render_template('donazione.html', raccolta=rac)


@app.route('/donazione2/<int:id>', methods=['POST'])
def donazione2(id):
  rac = rac_dao.getRacByID(id)
  if not rac:
    flash('Raccolta Fondi non trovata! Impossibile donare')
    return redirect(url_for('index'))
  
  # non puoi donare ad una raccolta chiusa
  if not checkRacOpen(rac):
    flash('Raccolta Fondi Chiusa! Impossibile donare')
    return redirect(url_for('index'))
  
  today = datetime.datetime.now()
  donazione = request.form.to_dict()

  #print(donazione)

  newDonDict = {}
  newDonDict['RacID'] = id
  newDonDict['UserID'] = -1 # donazione da parte di un utente non registrato, valore di default

  if not donazione['importo'].isdecimal():
    flash('L\'importo deve essere un numero!')
    return redirect(url_for('donazione', id=id))
  importo = int(donazione['importo'])
  if importo <= 0:
    flash('L\'importo deve essere maggiore di 0!')
    return redirect(url_for('donazione', id=id))
  if importo < rac['Min'] or importo > rac['Max']:
    flash('L\'importo deve essere compreso tra ' + str(rac['Min']) + ' e ' + str(rac['Max']) + '!')
    return redirect(url_for('donazione', id=id))
  totale = rac['TotaleRaccolto'] + importo
  
  nomeVisualizato = ''
  if 'usenick' in donazione.keys():
    if current_user.is_authenticated:
      if donazione['usenick'] == 'on': 
        nomeVisualizato = current_user.nickname
        newDonDict['UserID'] = current_user.id # donazione da parte di un utente registrato che ha scelto di usare il proprio nickname e rivendica la donazione
      else: 
        flash('Devi effettuare l\'accesso per poter usare il tuo nickname!')
        return redirect(url_for('donazione', id=id))
    else:
      flash('Devi effettuare l\'accesso per poter usare il tuo nickname!')
      return redirect(url_for('donazione', id=id))
  elif 'anonimo' in donazione.keys():
    if donazione['anonimo'] == 'on': nomeVisualizato = "Anonimo"
  else: 
    nVname = donazione['firstName']
    nVsurname = donazione['lastName']
    if (nVname == '' or nVsurname == ''):
      flash('Il nome e il cognome non possono essere vuoti!')
      return redirect(url_for('donazione', id=id))
    nomeVisualizato = nVname + " " + nVsurname
  
  if (nomeVisualizato == ''): 
    flash('Errore nel nome visualizzato!')
    return redirect(url_for('donazione', id=id))
  
  cmt = donazione['commento']
  if len(cmt) > 100:
    flash('Il commento non deve superare i 100 caratteri!')
    return redirect(url_for('donazione', id=id))
  
  newDonDict['NomeVisualizzato'] = nomeVisualizato
  newDonDict['Importo'] = importo
  newDonDict['Data'] = today.strftime('%Y-%m-%d %H:%M')
  newDonDict['Commento'] = cmt

  # fai la donazione
  res0 = don_dao.sendDonation(newDonDict) #res0 rappresenta il numTransazione se donazione va a buon fine, altrimenti None
  if res0 == None:
    flash('Errore nella donazione!')
    return redirect(url_for('donazione', id=id))
  
  # aggiorna il totale della raccolta
  res1 = rac_dao.updateTotaleRaccolto(id, totale)
  if not res1:
    # fai il roll-back eliminando anche la donazione dalla tabella Donazioni
    don_dao.deleteDonation(res0)
    flash('Errore nella donazione!')
    return redirect(url_for('donazione', id=id))
  flash('Donazione effettuata con successo! Grazie per aver contribuito alla Raccolta Fondi: ' + rac['Title'])
  return redirect(url_for('index'))

@app.route('/account/<int:id>')
@login_required
def account(id):
  if id != current_user.id:
    flash('Non puoi accedere a questa pagina!')
    return redirect(url_for('index'))

  # prendi tutte le raccolte associate all'utente
  # prendi tutte le donazioni associate a quelle raccolte
  # calcola il ptf
  racs = rac_dao.getRacsByUserID(id)
  if not racs:
    flash('Non hai ancora creato nessuna Raccolta Fondi!')
    return redirect(url_for('index'))
  
  for rac in racs: checkRacOpen(rac) # aggiorna raccolte e in caso aggiorna ptf

  user = user_dao.get_user_by_id(id) # prendi valore ptf aggiornato dopo il check sulle raccolte
  # devi prendere tutte le donazioni associate a queste raccolte
  dons = []
  for rac in racs:
    d = don_dao.getDonationsByRacID(rac['RacID'])
    if d:
      for don in d:
        don = dict(don)
        don['RacTitle'] = rac['Title']
        dons.append(don)
  if not dons:
    flash('Non hai ancora ricevuto nessuna donazione!')
  
  #ordina le donazioni in modo da mostrare le ultime in cima 
  dons = sorted(dons, key=lambda k: datetime.datetime.strptime(k['Data'], '%Y-%m-%d %H:%M'), reverse=True)
  return render_template('myaccount.html', donazioni=dons, raccolte=racs, ptfValue = user['Ptf'])

@app.route('/readComment/<int:id>')
@login_required
def readComment(id):
  don = don_dao.getDonationsbynumTransazione(id)
  if not don:
    flash('Donazione non trovata!')
    return redirect(url_for('index'))
  rac = rac_dao.getRacByID(don['RacID'])
  if not rac:
    flash("Raccolta non trovata!")
    return redirect(url_for('index'))
  if rac['UserID'] != current_user.id:
    flash("Commento non trovato!")
    return redirect(url_for('account',id=current_user.id))
  if don['Commento'] == '':
    flash('Nessun commento associato a questa donazione!')
    return redirect(url_for('account',id=current_user.id))
  return render_template('viewdonation.html', donazione=don)

@app.route('/search_raccolte')
@login_required
def search_raccolte():
    keyword = request.args.get('ricercaRaccolta')
    if not keyword:
      flash("Nessuna chiave di ricerca!")
      return redirect(url_for('mieraccolte'))
    if keyword == '':
      flash("La chiave di ricerca non deve essere vuota!")
      return redirect(url_for('mieraccolte'))
    if len(keyword) > 30:
      flash("La chiave di ricerca deve avere al massimo 30 caratteri!")
      return redirect(url_for('mieraccolte'))
    
    racsAlike = rac_dao.getRacsByTitle(keyword, current_user.id)
    if not racsAlike:
      flash("Nessuna raccolta trovata!")
      return redirect(url_for('mieraccolte'))
    
    for rac in racsAlike: checkRacOpen(rac)
    ptfValue = user_dao.user_GetPtf(current_user.id) 

    return render_template('mieraccolte.html', raccolte=racsAlike, ptfValue=ptfValue['Ptf'], ricerca=True, keyword=keyword)
    
  