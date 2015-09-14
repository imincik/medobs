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
Run following commands in source code directory to create development project:
```
$ export PYTHONPATH=$(pwd)
$ mkdir dev
$ django-admin.py startproject --template=medobs/conf/project_template devproj dev
$ cd dev
$ export DJANGO_SETTINGS_MODULE=devproj.settings
$ python ./manage.py migrate
```

Create superuser account
```
$ python ./manage.py createsuperuser --username admin --email admin@dev.io
```

Create offices and generate reservations
```
$ python ./manage.py loaddata ../medobs/reservations/fixtures/offices.json
$ python ./manage.py medobstemplates "First Office" "08:00" "16:00" 15
$ python ./manage.py medobstemplates "Second Office" "08:00" "16:00" 15
$ python ./manage.py medobsgen
```

Start development server
```
$ python ./manage.py runserver
```
