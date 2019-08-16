"""
Notice : 神兽保佑 ，测试一次通过
//      
//      ┏┛ ┻━━━━━┛ ┻┓
//      ┃　　　　　　 ┃
//      ┃　　　━　　　┃
//      ┃　┳┛　  ┗┳　┃
//      ┃　　　　　　 ┃
//      ┃　　　┻　　　┃
//      ┃　　　　　　 ┃
//      ┗━┓　　　┏━━━┛
//        ┃　　　┃   Author: somewheve
//        ┃　　　┃   Datetime: 2019/7/7 上午11:07  ---> 无知即是罪恶
//        ┃　　　┗━━━━━━━━━┓
//        ┃　　　　　　　    ┣┓
//        ┃　　　　         ┏┛
//        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
//          ┃ ┫ ┫   ┃ ┫ ┫
//          ┗━┻━┛   ┗━┻━┛
//
"""

import platform
from setuptools import Extension, setup

ext_modules = []

pkgs = ['ctpbee_cta', 'ctpbee_cta.strategy']
install_requires = ['ctpbee', "dataclasses"]
setup(
    name='ctpbee_cta',
    version='0.10',
    description="ctpbee cta strategy support",
    author='somewheve',
    author_email='somewheve@gmail.com',
    url='https://github.com/somewheve/ctpbee_cta',
    license="MIT",
    packages=pkgs,
    install_requires=install_requires,
    platforms=["Windows", "Linux", "Mac OS-X"],
    package_dir={'ctpbee': 'ctpbee'},
    package_data={'ctpbee': ['api/ctp/*', ]},
    ext_modules=ext_modules,
    classifiers=[
        'Development Status :: 3 - test',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ]
)
