from distutils.core import setup

setup(
    name='bbx_ninja',  # How you named your package folder (MyLib)
    packages=['bbx_ninja'],  # Chose the same as "name"
    version='0.0.4',  # Start with a small number and increase it with every change you make
    license='MIT',  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description='bbx repo to make my life easier.',  # Give a short description about your library
    author='Kunpeng GUO',  # Type in your name
    author_email='kunpeng.guo@univ-st-etienne.fr',  # Type in your E-Mail
    url='https://github.com/gabinguo/',  # Provide either the link to your github or to your website
    download_url='https://github.com/gabinguo/bbx/releases/download/v0.0.4/bbx_ninja_v0.0.4.tar.gz',
    keywords=['scripts', 'anything', 'python'],  # Keywords that define your package best
    install_requires=[
        "tqdm",
        "SPARQLWrapper",
        "rich",
        "requests"
    ],
    python_requires=">=3.6.0",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',  # Define that your audience are developers
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        'License :: OSI Approved :: MIT License',  # Again, pick a license
        'Programming Language :: Python :: 3',  # Specify which pyhton versions that you want to support
    ],
)
