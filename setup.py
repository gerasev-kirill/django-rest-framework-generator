import os, sys
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

requirements = [
    'Django>=1.11',
    'djangorestframework>=3.14.0',
    'Pillow>=4.2.1',
    'schema>=0.6.7',
    'jsonfield>=3.1.0'
]

if sys.version_info >= (3,8,0):
    requirements[0] = 'Django>=3.1'

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
    install_requires=requirements,
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
