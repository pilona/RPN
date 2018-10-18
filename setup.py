from glob import glob
from setuptools import setup


setup(
    name='rpn',
    use_scm_version=True,
    description='RPN calculator',
    url='https://github.com/pilona/RPN',
    install_requires=[
        'regex',
        'prompt_toolkit',
    ],
    author='Alex Pilon',
    author_email='alp@alexpilon.ca',
    packages=['rpn'],
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    setup_requires=[
        'setuptools_scm',
    ],
    #setup_requires=[
    #    # run pytest, coverage and checks when running python setup.py test.
    #    'pytest-runner',
    #    'pytest-cov',
    #    'pytest-flakes',
    #],
    tests_require=[
        'pytest',
        'coverage',
    ],
    scripts=glob('bin/*'),
    license='ISC',
)
