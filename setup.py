# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
    name="serialj",
    version="0.2.16",
    author="Donatus Herre",
    author_email="donatus.herre@slub-dresden.de",
    description="Parse JSON serialized MARC and PICA data",
    license=open("LICENSE").read(),
    url="https://github.com/herreio/serialj",
    packages=["serialj"],
    install_requires=["python-dateutil"],
)
