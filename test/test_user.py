import os, sys, pytest
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from src import user

user_test = {
    'id': 98,
    'name': 'john doe',
    'email': 'johndoe@gmail.com',
    'password': 'pass123',
    'account_type': 'user'
}

# USER CRUD TESTS
def test_create_user():
    u = user.User()
    if u.check_user(user_test):
        u.delete_user(user_test)
        u.create_user(user_test)
        assert u.check_user(user_test) == True
    else:
        u.create_user(user_test)
        assert u.check_user(user_test) == True
    
def test_verify_user():
    u = user.User()
    assert u.verify_user(user_test) == True
    
def test_update_user():
    new_user = {
        'name' : 'jane doe',
        'email' : 'janedoe@yahoo.com',
        'password' : 'newpass123'
    }
    u = user.User()
    u.update_user(new_user, 'johndoe@gmail.com')
    assert u.check_user(new_user) == True
    
def test_delete_user():
    u = user.User()
    u.delete_user(user_test)
    assert u.check_user(user_test) == False
    