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
//        ┃　　　┃   Datetime: 2019/7/10 下午6:41  ---> 无知即是罪恶
//        ┃　　　┗━━━━━━━━━┓
//        ┃　　　　　　　    ┣┓
//        ┃　　　　         ┏┛
//        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
//          ┃ ┫ ┫   ┃ ┫ ┫
//          ┗━┻━┛   ┗━┻━┛
//
"""

from ctpbee_cta.strategy.double_ma import DoubleMaStrategy
from ctpbee import CtpBee


def go_ahead():
    app = CtpBee("hello wh", __name__)
    app.config.from_json("config.json")
    double_ma = DoubleMaStrategy(app=app,cta_symbol="ag1902.SHFE", name="double_ma")
    app.start()
    app.subscribe("ag1912")


if __name__ == '__main__':

    go_ahead()

