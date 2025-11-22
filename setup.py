from setuptools import setup, find_packages

setup(
    name='Mopidy-Yt-Cast',
    version='0.1.0',
    description='Mopidy extension for YouTube Cast (DIAL) support',
    author='Antigravity',
    author_email='antigravity@example.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 3.0',
        'Pykka >= 2.0',
    ],
    entry_points={
        'mopidy.ext': [
            'yt_cast = mopidy_yt_cast:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
