import os, sys
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

requirements = [
    'Django>=1.11',
    'djangorestframework',
    'Pillow>=4.2.1',
    'schema>=0.6.7',
]

if sys.version_info[0] == 2:
    requirements.append('django-model-changes==0.15')
else:
    requirements.append('django-model-changes-py3==0.14.1')

try:
    import django
    if django.VERSION[0] >= 3 and django.VERSION[1] < 1:
        pass
    else:
        requirements.append('jsonfield')
except ImportError:
    if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
        requirements[0] = 'Django>=3.1'
    else:
        requirements.append('jsonfield')

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
