#!/usr/bin/env python

from setuptools import setup, find_packages


# classifiers
classifiers = [
	'Development Status :: 4 - Beta',
	'Environment :: Web Environment',
	'Framework :: Django',
	'Intended Audience :: Healthcare Industry',
	'License :: OSI Approved :: GNU General Public License version 3.0 (GPLv3)',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
	'Topic :: Office/Business :: Scheduling',
]

exclude_from_packages = [
	'medobs.conf.project_template',
]


# requirements
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# setup
setup(name='medobs',
	version=".".join(map(str, __import__('medobs').VERSION)),
	description='MEDOBS reservation system',
	author='Peter Hyben, Marcel Dancak, Ivan Mincik',
	author_email='hugis@tag.sk, dancakm@gmail.com, ivan.mincik@gmail.com',
	url='https://github.com/imincik/medobs/',
	packages=find_packages(),
	include_package_data=True,
	classifiers=classifiers,
	install_requires=requirements
)

# vim: set ts=4 sts=4 sw=4 noet:
