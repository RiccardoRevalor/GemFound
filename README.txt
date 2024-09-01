RICCARDO REVALOR - s294468
IAW 2023/24

LINK DEPLOY PYTHONANYWHERE: http://rpix17.pythonanywhere.com/

DISPOSITIVO TARGET: PC (anche se l'ho testata su smartphone e il comportamento, grazie ad alcune media query da me aggiunte, è accettabile)

ISTRUZIONI SITO WEB "GEMFOUND" 

Gli utenti possono fare il login sia con il NickName sia con la mail, è uguale.

UTENTI ATTUALMENTE INSERITI:
NickName utenti: 			Mail utenti:					Password:
rpix17 				test@gmail.com					1234
utente2				utente2@gmail.com					1234
utente3				onlus@onlus.it					1234
utente4				test@outlook.com					1234


RACCOLTE ATTUALMENTE INSERITE:

Nome Raccolta:				Tipo			creata da			Note
Questa raccolta avrà successo			normale			rpix17			chiusa, obbiettivo raggiunto
Lampo che avrà successo			lampo			utente2			chiusa, obbiettivo raggiunto
Lampo senza successo			lampo			rpix17			chusa, obbiettivo NON raggiunto
normale senza successo			normale			utente3			chiusa, obbiettivo NON raggiunto
Fiat Doblò				normale			rpix17			aperta, chiude il 2024-02-25
Sport per tutti, adesso			normale			utente3			aperta, chiude il 2024-02-28
raccolta 1					normale			rpix17			aperta, chiude il 2024-02-29
nuovo Pc					normale			utente2			aperta, chiude il 2024-03-01


DESCRIZIONE PAGINE SITO WEB (FRONT-END)

1) Pagina HOME
è la pagina principale del sito, mostra (ad utenti registrati e non) le raccolte ancora attive (cioè con data di scadenza nel futuro), ordinate mostrando prima quelle che scadranno prima nel tempo.
Se si clicca sul riquadro di una raccolta si verrà reindirizzati alla pagina specifica dedicata ad essa.
TEMPLATE HTML: index3.html
STYLESHEET CSS: indexstyle.css, style.css (è lo stylesheet base usato nel tamplate base.html)

2) Pagina Raccolte Fondi passate
è la pagine dove vengono mostrate le raccolte donde chiuse, a cui non è più possibile donare. Vengono mostrate prima, ordinate così da mostrae prima quelle più recenti, le raccolte che hanno raggiunto/superato l'obbiettivo monetario richiesto.
Poi vengono mosttate, sempre ordinate così da mostrae prima quelle più recenti, le raccolte che non hanno raggiunto l'obbiettivo.
TEMPLATE HTML: index3.html
STYLESHEET CSS: indexstyle.css, style.css 
(sono gli stessi della Home)

3) Pagina Registrati
in principio era una pagina vera e propria, poi l'ho sostituita col Modale a comparsa di Bootstrap, il cui codice si trova in base.html

4) Pagina Accedi
in principio era una pagina vera e propria, poi l'ho sostituita col Modale a comparsa di Bootstrap, il cui codice si trova in base.html

4) Pagina Crea una Raccolta Fondi!
Se l'utente risulta autenticato, la pagina permette di creare e dettagliare una nuova Raccolta Fondi, definendone:
- Titolo (required)
- Descrizione (required)
- Target monetario (required)
- Data e ora di chiusura (se raccolta è normale)
- Tipo raccolta: normale oppure lampo (a scelta tra questi due)
- Minima donazione (required)
- Massima donazione (required)
- Immagine rappresentativa
è un form che effettua una richiesta POST.
TEMPLATE HTML: newraccolta.html
STYLESHEET CSS: style.css 


5) Pagina di modifica Raccolta Fondi 
è login required.
permette di modificare le caratteristiche di una raccolta. Ovviamente la data di attivazione non è modificabile.
Se una raccolta è chiusa non è più modifivabile nè eliminabile.
Una raccolta normale può diventare lampo solo se non sono ancora trascorsi 5 minuti dalla data di attivazione, sennò è troppo tardi.
Una lampo può diventare normale se è ovviamente ancora aperta.
Si può aggiungere/cambiare/rimuovere immagine rappresentativa.
è un form che effettua una richiesta POST.
TEMPLATE HTML: newraccolta.html
STYLESHEET CSS: style.css 
(stessi della pagina 4)

6) Pagina Le mie raccolte
è login_required.
Mostra in una tabella lo storico delle raccolte fondi create dall'utente, con la possibilità di eseguire azioni su di esse.
Mostra anche il valore attuale del portafoglio dell'utente (cioè dei soldi guadagnati da raccole chiuse e con obbiettivo raggiunto)
TEMPLATE HTML: mieraccolte.html
STYLESHEET CSS: tablestyle.css, style.css 

7) Pagina dell'account
è login_required
permette di visualizzare sia le donazioni ricevute per le proprie raccolte (mostrate in una tabela), sia info sul proprio account e sul valore del propriom portafoglio.
Cliccando sulla singola donazione si potrà leggere il commento associato per esteso.
TEMPLATE HTML: myaccount.html
STYLESHEET CSS: tablestyle.css, style.css 

8) Pagina della singola raccolta
permette di vedere in maniera dettagliata le info di una certa raccolta Fondi. Se aperta permette di donare tramite il pulsante "Dona ora".
 Se il creatore della raccolta è l'utente permette a quest'ultimo di visualizzare il gestore delle raccolte tramite il pulsate "Gestisci".
Vengono anche mostrate le donazioni (e il nome, cognome oppure il NickName del donatore, oppure ancora "Anonimo").
TEMPLATE HTML: single2.html
STYLESHEET CSS: singlestyle.css, style.css 

9) Pagina per fare una donazione
Permette di effettuare una donazione verso una raccolta aperta, immettendo:
- Importo donazione, che deve essere compreso tra Min e Max.
- Commento (opzionale)
- Indirizzo
- Codice Carta di Credito (max 16 cifre)
- Codice CVV Carta di Credito (3 cifre)
Ci sono tre opzioni:
a) Inserire Nome e Cognome
b) Rimanere Anonimo (verrà visualizzato "Anonimo" come donatore)
c) nel caso di utenti autenticati, inserire il proprio NickName (es rpix17, utente2 ecc) e "associare" la donazione al proprio profilo, cioè far sapere a tutti che siamo stati proprio noi come utenti a donare.
è un form che effettua una richiesta POST.
TEMPLATE HTML: donazione.html
STYLESHEET CSS: style.css 

## Technologies Used
- **HTML**
- **CSS**
- **JavaScript**
- **Python**
