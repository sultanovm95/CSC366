1. Install flask
2. Create a docker image of mysql
3. docker exec -it nameOfTheImage /bin/bash - to access mysql
4. SELECT user,host from mysql.user;
5. UPDATE mysql.user set host='%' where user='root'
6. Flush privileges;
7. Create a db | table and etc.

---

Directories:
```
./data/    - contains the injest data from an excel file (massaging of excel file needed)
./datadir/ - mysql datadirectory for docker contain and/or mysql local installation
./scripts/ - contains the scripts to execute any single function
./src/     - source code of file
```