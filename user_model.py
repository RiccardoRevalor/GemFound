from flask_login import UserMixin

class User(UserMixin):
  def __init__(self, UserID, Nome, Cognome, UserMail, Password, UserNickName, Ptf):
    self.id = UserID
    self.name = Nome
    self.surname = Cognome
    self.mail = UserMail
    self.password = Password
    self.nickname = UserNickName
    self.ptf = Ptf