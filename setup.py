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
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    setup_requires=[
        'setuptools_scm',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'coverage',
        'flake8',
        'bandit',
        'mypy',
        'safety',
    ],
    scripts=glob('bin/*'),
    license='ISC',
)
