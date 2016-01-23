MEDOBS - Simple reservation system
==================================

Development
-----------
Create Python virtualenv
```
$ mkvirtualenv medobs
$ pip install -r ./requirements.txt
```

Run following commands in source code directory to create development project:
```
$ unset DJANGO_SETTINGS_MODULE
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
$ python ./manage.py medobstemplates "First Office" "08:00" "16:00" 30
$ python ./manage.py medobstemplates "Second Office" "08:00" "16:00" 30
$ python ./manage.py medobsgen
```

Start development server
```
$ python ./manage.py runserver
```
