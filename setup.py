import os, six
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

if six.PY2:
    dmc_module = 'django-model-changes==0.15'
else:
    dmc_module = 'django-model-changes-py3==0.14.1'

setup(
    name='django-rest-framework-generator',
    version='0.6.0',
    packages=['drfs'],
    include_package_data=True,
    license='BSD License',
    description='Models, Serializers, Views generator for DRF',
    long_description=README,
    author='Gerasev Kirill',
    author_email='gerasev.kirill@gmail.com',
    install_requires=[
        'Django>=1.11',
        'djangorestframework',
        'Pillow>=4.2.1',
        'jsonfield',
        dmc_module
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
