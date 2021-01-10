# Write your code here
import random
import sqlite3
conn = sqlite3.connect('./card.s3db')


class DB:
    cur = conn.cursor()

    @staticmethod
    def __drop_table():
        cur = conn.cursor()
        query = 'drop table card;'
        cur.execute(query)
        conn.commit()

    @staticmethod
    def __select_one(query: str, params: tuple) -> tuple:
        cur = conn.cursor()
        try:
            cur.execute(query, params)
        except sqlite3.IntegrityError as e:
            print('sqlite error: ', e.args[0])
        res = cur.fetchone()
        conn.commit()
        if not res:
            res = None
        return res

    @staticmethod
    def __update_field(query: str, params: tuple) -> bool:
        cur = conn.cursor()
        try:
            cur.execute(query, params)
        except sqlite3.IntegrityError as e:
            print('sqlite error: ', e.args[0])
            return False
        else:
            conn.commit()
            return True

    @staticmethod
    def __create_table():
        cur = conn.cursor()
        query = 'create table if not exists card (' \
                'id INTEGER PRIMARY KEY AUTOINCREMENT,' \
                'number TEXT,' \
                'pin TEXT,' \
                'balance INTEGER DEFAULT 0' \
                ');'
        try:
            cur.execute(query)
        except sqlite3.IntegrityError as e:
            print('sqlite error: ', e.args[0])
        conn.commit()

    def startup(self):
        # self.__drop_table()
        self.__create_table()

    def validate_card_exists(self, number: str) -> bool:
        query = 'select * from card where number = ?'
        res = self.__select_one(query, (number,))
        if res:
            return True
        else:
            return False

    @staticmethod
    def insert_card(number: str, pin: str):
        cur = conn.cursor()
        query = 'insert into card("number", "pin") values(?, ?)'
        #query = f'insert into card ("number", "pin") values (\'{number}\', \'{pin}\')'
        # print(query, (number, pin))
        try:
            cur.execute(query, (number, pin))
        except sqlite3.IntegrityError as e:
            print('sqlite error: ', e.args[0])
        conn.commit()
        # for row in self.cur.execute('SELECT * FROM card'):
        #     print('currently_available:', row)

    def retrieve_pin(self, number: str) -> str:
        query = 'select pin from card where number = ?'
        return self.__select_one(query, (number,))

    def retrieve_account_balance(self, number: str):
        query = 'select balance from card where number = ?'
        return self.__select_one(query, (number,))[0]

    def add_income(self, number: str, amount: int) -> bool:
        cur_bal_q = 'select balance from card where number = ?'
        balance = self.__select_one(cur_bal_q, (number,))[0]
        new_balance = balance + amount
        query = 'update card set balance = ? where number = ?'
        return self.__update_field(query, (new_balance, number))


    def transfer(self, sender: str, receiver: str, amount: int) -> bool:
        balance_query = 'select balance from card where number = ?'
        balance_receiver = self.__select_one(balance_query, (receiver,))[0]
        balance_sender = self.__select_one(balance_query, (sender,))[0]

        new_balance_sender = balance_sender - amount
        new_balance_receiver = balance_receiver + amount
        query = 'update card set balance = ? where number = ?'
        sender_done = self.__update_field(query, (new_balance_sender, sender))
        receiver_done = self.__update_field(query, (new_balance_receiver, receiver))
        if sender_done and receiver_done:
            return True
        else:
            return False

    @staticmethod
    def remove_account(number: str) -> bool:
        cur = conn.cursor()
        query = 'delete from card where number = ?'
        try:
            cur.execute(query, (number,))
        except sqlite3.IntegrityError as e:
            print('sqlite error: ', e.args[0])
            return False
        else:
            conn.commit()
            return True


DB().startup()
START = '1. Create an account \n' \
        '2. Log into account \n' \
        '0. Exit'
LOGGED_IN = '1. Balance \n' \
            '2. Add income \n' \
            '3. Do transfer \n' \
            '4. Close account \n' \
            '5. Log out \n' \
            '0. Exit'

cards = dict()


def generate_random_number(digits: int) -> str:
    rand = ''
    i = 0
    while i < digits:
        rand += str(random.randrange(0, 9))
        i += 1
    return rand


class CreateAccount:
    @staticmethod
    def __generate_luhn(card: str) -> str:
        identifier = card[:-1]
        luhn_data = [int(i) for i in identifier]
        for key, value in enumerate(luhn_data):
            if key % 2 == 0:
                val = value * 2
                if val > 9:
                    val = val - 9
                luhn_data[key] = val
        if sum(luhn_data) % 10 == 0:
            mod = 0
        else:
            mod = 10 - sum(luhn_data) % 10

        return identifier + str(mod)

    def __generate_new_card_number(self):
        parts = {
            'bank': '4',
            'iin': '00000',
            'customer_account_number': generate_random_number(9),
            'checksum': '3'
        }
        card = ''.join([parts[i] for i in parts])
        card = self.__generate_luhn(card)
        setattr(self, 'card_id', card)

    def __generate_pin_number(self):
        i = 0
        pin = generate_random_number(4)
        if len(pin) != 4:
            exit('fatal error: pincode not at correct length')
        setattr(self, 'pin', pin)

    def validate_luhn(self, card_number: str) -> bool:
        if card_number == self.__generate_luhn(card_number):
            return True
        else:
            return False

    def get_new_account(self):
        self.__generate_new_card_number()
        self.__generate_pin_number()

        # CARDS[getattr(self, 'card_id')] = getattr(self, 'pin')

        # return getattr(self, 'pin')
        global cards
        # cards[getattr(self, 'card_id')] = getattr(self, 'pin')
        # print(getattr(self, 'card_id'), getattr(self, 'pin'))
        DB().insert_card(getattr(self, 'card_id'), getattr(self, 'pin'))
        return \
            {
                'card_id': getattr(self, 'card_id'),
                'pin': getattr(self, 'pin')
            }


class Account(CreateAccount):
    def __init__(self):
        card_id = None
        pin = None


def logged_in(number: str):
    print(LOGGED_IN)
    while True:
        res = input()
        if res == '0':
            log_out()
        elif res == '1':
            res = DB().retrieve_account_balance(number)
            print(f'\nBalance: {res}\n')
            print(LOGGED_IN)
        elif res == '2':
            print("Enter income:")
            income = int(input())
            res = DB().add_income(number, income)
            if res:
                print("Income was added!\n")
            else:
                print("Error while adding income!\n")
        elif res == '3':
            print("Transfer")
            print("Enter card number:")
            new_number = input()
            if new_number == number:
                print("You can't transfer money to the same account!")
                print(LOGGED_IN)
            elif not Account().validate_luhn(new_number):
                print("Probably you made a mistake in the card number. Please try again!")
                print(LOGGED_IN)
            elif not DB().validate_card_exists(new_number):
                print('Such a card does not exist.')
                print(LOGGED_IN)
            else:
                print('Enter how much money you want to transfer: ')
                amount = int(input())
                enough_balance = DB().retrieve_account_balance(number)
                if amount > enough_balance:
                    print('Not enough money!')
                    print(LOGGED_IN)
                else:
                    res = DB().transfer(number, new_number, amount)
                    if res:
                        print("Success!")
                    else:
                        print("Something went wrong")
        elif res == '4':
            res = DB().remove_account(number)
            if res:
                print("The account has been closed!")
            else:
                print('Something went wrong')

        elif res == '5':
            log_out()
            break
        else:
            print('invalid input!')
            break


def _exit():
    print('Bye!')
    exit()


def log_out():
    print('\nYou have succesfully logged out!\n')
    exit()


def startprogram():
    print(START)
    a = Account()
    while True:
        res = input()
        if res == '0':
            _exit()
        elif res == '1':
            client = a.get_new_account()
            print('\nYour card has been created')
            print(f'Your card number: \n{client["card_id"]}')
            print(f'Your card pin: \n{client["pin"]}\n')
            print(START)
        elif res == '2':
            print('\nEnter your card number:')
            card_number = input()
            print('Enter your PIN:')
            pin = input()
            _pin = DB().retrieve_pin(card_number)
            if pin and _pin and pin == _pin[0]:
                print("\nYou have successfully logged in!\n")
                logged_in(card_number)
                break
            else:
                print("\nWrong card number or PIN!")
                print(START)
        else:
            print('invalid input!')
            break


startprogram()