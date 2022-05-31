import MySQLdb
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()

# PORT for MYSQL
PORT = int(os.getenv("PORT"))
# Either Absolute path to dir, relative path, or nothing
DIRPATH = os.getenv("DIRPATH")
DB = os.getenv("MYSQL_DB")

class User:
    '''
    CRUD operations for User
    '''
    def __init__(self):
        # create connection
        self.conn = MySQLdb.connect(host="127.0.0.1", port=PORT, user="root", database=DB)
    
    def create_user(self, user):
        '''
        Create a new user
        '''
        try:
            # create a cursor
            cur = self.conn.cursor()
            # execute the query
            cur.execute(
                "INSERT INTO account(Id, Name, Email, Password, accountType) VALUES(%s, %s, %s, %s, %s)", 
                (user['id'], user['name'], user['email'], generate_password_hash(user['password'], method='sha256'), user['account_type'])
            )
            # commit to DB
            self.conn.commit()
            # close the cursor
            cur.close()
            # close connection
            self.conn.close()
            return {'message': 'User created successfully'}
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500
        
    def check_user(self, email):
        '''
        Check if a user has already exists
        '''
        try:
            # create a cursor
            cur = self.conn.cursor()
            # execute the query
            cur.execute("SELECT * FROM account WHERE email = %s", (email,))
            # commit to DB
            self.conn.commit()
            # close the cursor
            cur.close()
            # close connection
            self.conn.close()
            return cur.fetchone()
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500
        
    def verify_user(self, user):
        '''
        Verify if input user match with DB user
        '''
        try:
            # create a cursor
            cur = self.conn.cursor()
            # execute the query
            cur.execute("SELECT * FROM account WHERE email = %s", (email,))
            # commit to DB
            self.conn.commit()
            # close the cursor
            cur.close()
            # close connection
            self.conn.close()
            return cur.fetchone()
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500
        
    def update_user(self, user):
        '''
        Update a user
        '''
        try:
            # create a cursor
            cur = self.conn.cursor()
            # execute the query
            cur.execute("UPDATE account SET name = %s, email = %s, password = %s WHERE email = %s", (user['name'], user['email'], user['password'], user['email']))
            # commit to DB
            self.conn.commit()
            # close the cursor
            cur.close()
            # close connection
            self.conn.close()
            return {'message': 'User updated successfully'}
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500
        
    def delete_user(self, email):
        '''
        Delete a user
        '''
        try:
            # create a cursor
            cur = self.conn.cursor()
            # execute the query
            cur.execute("DELETE FROM users WHERE email = %s", (email))
            # commit to DB
            self.conn.commit()
            # close the cursor
            cur.close()
            # close connection
            self.conn.close()
            return {'message': 'User deleted successfully'}
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500