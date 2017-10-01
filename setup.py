from glob import glob
from setuptools import setup


setup(
    name='rpn',
    description='RPN calculator',
    url='https://github.com/pilona/RPN',
    version='0.2',
    install_requires=[
        'regex',
    ],
    author='Alex Pilon',
    author_email='alp@alexpilon.ca',
    packages=['rpn'],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    setup_requires=[
        # run pytest, coverage and checks when running python setup.py test.
        'pytest-runner',
        'pytest-cov',
        'pytest-flakes',
    ],
    tests_require=[
        'pytest',
        'coverage',
    ],
    scripts=glob('bin/*'),
)
