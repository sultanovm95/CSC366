import MySQLdb
import os, bcrypt
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Loads Enviroment Variables from .env file use command: 'touch .env' to create
load_dotenv()

# PORT for MYSQL
PORT = int(os.getenv("PORT"))
# Either Absolute path to dir, relative path, or nothing
DIRPATH = os.getenv("DIRPATH")
DB = os.getenv("MYSQL_DB")
HOST = os.getenv("MYSQL_HOST")
USER = os.getenv("MYSQL_USER")

class User:
    def __init__(self):
        # create salt
        self.salt = bcrypt.gensalt()
        
    '''
    CRUD operations for User
    '''
    def create_user(self, user):
        '''
        Create a new user
        '''
        try:
            conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, database=DB)
            # create a cursor
            cur = conn.cursor()
            # find max id and set new id for the user
            cur.execute('''
                        SELECT MAX(id)
                        FROM account''')
            max_id = cur.fetchone()
            id = 1
            if max_id:
                id = int(max_id[0]) + 1
            # hash password
            hashed_password = bcrypt.hashpw(user['password'].encode('utf-8'), self.salt)
            # execute the query
            cur.execute('''
                        INSERT INTO account(Id, Name, Email, Password, accountType) 
                        VALUES(%s, %s, %s, %s, %s)''', 
                        (id, user['name'], user['email'], hashed_password, user['account_type']))
            # commit to DB
            conn.commit()
            # close the cursor
            cur.close()
            # close connection
            conn.close()
            return id
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500
        
    def check_user(self, user):
        '''
        Check if a user has already exists
        '''
        try:
            conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, database=DB)
            # create a cursor
            cur = conn.cursor()
            # execute the query
            cur.execute('''
                        SELECT * 
                        FROM account 
                        WHERE email = %(email)s''', 
                        {'email': user['email']})
            # fetch the data
            record = cur.fetchone()
            # close the cursor
            cur.close()
            # close connection
            conn.close()
            if record:
                return True
            return False
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500
        
    def verify_user(self, user):
        '''
        Verify if input user match with DB user
        '''
        try:
            conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, database=DB)
            # create a cursor
            cur = conn.cursor(MySQLdb.cursors.DictCursor)
            # execute the query
            cur.execute('''
                        SELECT Id, password
                        FROM account 
                        WHERE email = %(email)s''', 
                        {'email': user['email']})
            # fetch the data
            account = cur.fetchone()
            print(account)
            if account:
                if bcrypt.checkpw(user['password'].encode('utf-8'), account["password"].encode('utf-8')):
                    return account["Id"]
            
            # close the cursor
            cur.close()
            # close connection
            conn.close()
            
            return -1            
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500
        
    def update_user(self, user, email):
        '''
        Update a user
        '''
        try:
            conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, database=DB)
            hashed_password = bcrypt.hashpw(user['password'].encode('utf-8'), self.salt)
            # create a cursor
            cur = conn.cursor()
            # execute the query
            cur.execute('''
                        UPDATE account 
                        SET name = %(name)s, email = %(email)s, password = %(pass)s 
                        WHERE email = %(existing_email)s''', 
                        {'name': user['name'], 'email': user['email'], 'pass': hashed_password, 'existing_email': email})
            # commit to DB
            conn.commit()
            # close the cursor
            cur.close()
            # close connection
            conn.close()
            return {'message': 'User updated successfully'}
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500
        
    def delete_user(self, user):
        '''
        Delete a user
        '''
        try:
            conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, database=DB)
            # create a cursor
            cur = conn.cursor()
            # execute the query
            cur.execute('''
                        DELETE FROM account 
                        WHERE email = %(email)s''', 
                        {'email': user['email']})
            # commit to DB
            conn.commit()
            # close the cursor
            cur.close()
            # close connection
            conn.close()
            return {'message': 'User deleted successfully'}
        except Exception as e:
            print(e)
            return {'message': 'Something went wrong'}, 500