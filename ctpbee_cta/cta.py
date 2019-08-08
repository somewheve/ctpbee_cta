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
//        ┃　　　┃   Datetime: 2019/7/10 下午5:09  ---> 无知即是罪恶
//        ┃　　　┗━━━━━━━━━┓
//        ┃　　　　　　　    ┣┓
//        ┃　　　　         ┏┛
//        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
//          ┃ ┫ ┫   ┃ ┫ ┫
//          ┗━┻━┛   ┗━┻━┛
//
"""
from ctpbee import CtpBee
from ctpbee.constant import Direction, Offset, EVENT_BAR
from ctpbee_cta.handler import Handler
from ctpbee.constant import EVENT_LOG
from ctpbee.event_engine import Event


class Cta:
    def __init__(self, cta_name, app: CtpBee, symbol):
        self.app = app
        self.cta_name = cta_name
        ## 核心处理器  --> 调度发单等等
        self.core_handler = Handler(cta=self, symbol=symbol)

    @property
    def pos(self):
        """ 返回持仓数量 """
        return len(self.app.recorder.positions)

    def push_bar(self, bar):
        event = Event(EVENT_BAR, bar)
        self.app.event_engine.put(event)

    def export_log(self, log):
        event = Event(EVENT_LOG, log)
        self.app.event_engine.put(event)

    def buy(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send buy order to open a long position.
        """
        return self.core_handler.send_order(Direction.LONG, Offset.OPEN, price, volume, stop, lock)

    def sell(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send sell order to close a long position.
        """
        return self.core_handler.send_order(Direction.SHORT, Offset.CLOSE, price, volume, stop, lock)

    def short(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send short order to open as short position.
        """
        return self.core_handler.send_order(Direction.SHORT, Offset.OPEN, price, volume, stop, lock)

    def cover(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send cover order to close a short position.
        """
        return self.core_handler.send_order(Direction.LONG, Offset.CLOSE, price, volume, stop, lock)
