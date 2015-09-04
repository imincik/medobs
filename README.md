MEDOBS - Simple medical reservation system
==========================================

Users actions
-------------
### Unauthorized user (patient)
 - select date and time of visit reservation and apply for reservation

### Authorized user (nurse etc.)
 - same as unauthorized user
 - can see reservations status
 - can see the patient name
 - can make "authorized only" reservation
 - can hold free reservation for future use
 - can unhold reservation
 - can cancel reservation
 - can print simple and detailed list of reservations for selected day


Development
-----------
Run following commands in source code root directory:
```
$ export PYTHONPATH=$(pwd)
$ mkdir dev
$ django-admin.py startproject --template=medobs/conf/project_template devproj dev
$ cd dev
$ export DJANGO_SETTINGS_MODULE=devproj.settings
$ python ./manage.py syncdb
$ python ./manage.py runserver
```
