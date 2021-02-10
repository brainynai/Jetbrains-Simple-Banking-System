import random
import sqlite3

random.seed()


class Account:
    def __init__(self, accID=None, accNum=None, pin=None, balance=0):
        self.accID = accID
        self.accNum = Account.genAccNum() if accNum is None else accNum
        self.pin = Account.genPin() if pin is None else pin
        self.balance = balance

    def toTuple(self):
        return self.accID, self.accNum, self.pin, self.balance

    @staticmethod
    def genAccNum():
        with sqlite3.connect('card.s3db') as conn:
            cur = conn.cursor()
            cur.execute('select count(*) from card')
            accID = cur.fetchone()[0] + 1

        iin = '400000'
        custNum = str(accID).zfill(9)
        checksum = Account.genChecksum(iin + custNum)

        return iin + custNum + checksum

    @staticmethod
    def genPin():
        return str(random.randint(0, 9999)).zfill(4)

    @staticmethod
    def genChecksum(needsChecksumStr):
        numList = [int(i) for i in needsChecksumStr]

        for i, num in enumerate(numList):
            if (i + 1) % 2 == 1:
                numList[i] = num * 2

            if numList[i] > 9:
                numList[i] -= 9

        preSum = sum(numList)
        checkDigit = (10 - (preSum % 10)) % 10

        return str(checkDigit)

    @staticmethod
    def fromTuple(accTuple):
        accID = accTuple[0]
        accNum = accTuple[1]
        pin = accTuple[2]
        balance = accTuple[3]
        return Account(accID, accNum, pin, balance)



def menu(accLoggedIn=None):
    if accLoggedIn is None:
        choices = {"1": (createAccount, 'Create an account'),
                   "2": (logIO, 'Log into account'),
                   "0": (goodbye, 'Exit')}
    else:
        choices = {"1": (showBalance, 'Balance'),
                   "2": (deposit, 'Add income'),
                   "3": (transfer, 'Do transfer'),
                   "4": (closeAccount, 'Close account'),
                   "5": (logIO, 'Log out'),
                   "0": (goodbye, 'Exit')}

    for option in choices:
        print(f'{option}. {choices[option][1]}')

    choice = input()
    print('')
    accLoggedIn = choices[choice][0](accLoggedIn)

    return accLoggedIn


def createAccount(accLoggedIn=None):
    global cur
    global conn

    newAcc = Account()
    print('Your card has been created')
    print('Your card number:')
    print(newAcc.accNum)
    print('Your card PIN:')
    print(newAcc.pin)
    print('')

    #Account.accDict[newAcc.accNum] = newAcc

    cur.execute('select count(*) from card')
    accID = cur.fetchone()[0] + 1

    cur.execute('insert into card values (?, ?, ?, ?)', (accID, newAcc.accNum, newAcc.pin, 0))
    conn.commit()

    return None


def deposit(accLoggedIn=None):
    global cur
    global conn

    print('Enter income: ')
    income = int(input())
    accLoggedIn.balance += income

    cur.execute('update card set balance = ? where id = ?', (accLoggedIn.balance, accLoggedIn.accID))
    conn.commit()
    print('Income was added!\n')

    return accLoggedIn


def transfer(accLoggedIn=None):
    global cur
    global conn

    print('Enter card number:')
    recipient = input()

    if recipient == accLoggedIn.accNum:
        print("You can't transfer money to the same account!\n")
        return accLoggedIn

    if not Account.genChecksum(recipient[:-1]) == recipient[-1]:
        print("Probably you made a mistake in the card number. Please try again!\n")
        return accLoggedIn

    cur.execute('select * from card where number = ?', (recipient,))
    accounts = cur.fetchall()

    if len(accounts) == 0:
        print("Such a card does not exist.")
        return accLoggedIn

    recipientAcc = Account.fromTuple(accounts[0])

    print('Enter how much money you want to transfer:')
    transferAmount = int(input())

    if transferAmount > accLoggedIn.balance:
        print('Not enough money!\n')
        return accLoggedIn

    recipientAcc.balance += transferAmount
    accLoggedIn.balance -= transferAmount

    cur.execute('update card set balance = ? where id = ?', (recipientAcc.balance, recipientAcc.accID))
    conn.commit()
    cur.execute('update card set balance = ? where id = ?', (accLoggedIn.balance, accLoggedIn.accID))
    conn.commit()


    print('Success!\n')
    return accLoggedIn


def closeAccount(accLoggedIn=None):
    global conn
    global cur

    cur.execute('delete from card where id = ? ', (accLoggedIn.accID,))
    conn.commit()

    print('The account has been closed!\n')

    return None


def logIO(accLoggedIn=None):
    global conn
    global cur

    if accLoggedIn is None:
        print('Enter your card number:')
        accNum = input()
        print('Enter your PIN')
        pin = input()
        print('')

        cur.execute('select * from card where number = ?', (accNum,))
        accounts = cur.fetchall()

        if len(accounts) == 1:
            thisAccount = Account.fromTuple(accounts[0])
            if thisAccount.pin == pin:
                print('You have successfully logged in!\n')
                return thisAccount
            else:
                print('Wrong card number or PIN!\n')
        else:
            print('Wrong card number or PIN!\n')
    else:
        print('You have successfully logged out!\n')
        return None


def showBalance(accLoggedIn=None):
    print(f'Balance: {accLoggedIn.balance}\n')
    return accLoggedIn


def goodbye(accLoggedIn=None):
    print("Bye!")
    exit()


def initDB():
    conn = sqlite3.connect('card.s3db')
    cur = conn.cursor()

    cur.execute('drop table if exists card')
    conn.commit()

    cur.execute('create table if not exists card (id INTEGER, number text, pin text, balance INTEGER default 0)')
    conn.commit()

    return conn, cur


conn, cur = initDB()
accLoggedIn = None
#print(Account.genChecksum('300000397219650'))
while True:
    try:
        accLoggedIn = menu(accLoggedIn)
    except SystemExit:
        conn.close()
        break
