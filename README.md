1. Install flask
2. Create a docker image of mysql
3. docker exec -it nameOfTheImage /bin/bash - to access mysql
4. SELECT user,host from mysql.user;
5. UPDATE mysql.user set host='%' where user='root'
6. Flush privileges;
7. Create a db | table and etc.
