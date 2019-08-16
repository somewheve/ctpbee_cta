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
from ctpbee.constant import EVENT_LOG
from ctpbee.event_engine import Event

from ctpbee_cta.handler import Handler


class CtaCore:
    def __init__(self, cta_name, app: CtpBee, symbol):
        self.app = app
        self.cta_name = cta_name

        # 核心处理器 --> 调度发单等等
        self.core_handler = Handler(cta=self, local_symbol=symbol)

    @property
    def pos(self):
        """ 返回持仓数量 """
        return len(self.app.recorder.positions)

    def push_bar(self, bar):
        """ 推送bar """
        event = Event(EVENT_BAR, bar)
        self.app.event_engine.put(event)

    def export_log(self, log):
        """ 输出日志信息 """
        event = Event(EVENT_LOG, log)
        self.app.event_engine.put(event)

    def buy(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        开仓 多头
        """
        return self.core_handler.send_order(Direction.LONG, Offset.OPEN, price, volume, stop, lock)

    def sell(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """ 平空头 """
        return self.core_handler.send_order(Direction.SHORT, Offset.CLOSE, price, volume, stop, lock)

    def short(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
         开仓 空头
        """
        return self.core_handler.send_order(Direction.SHORT, Offset.OPEN, price, volume, stop, lock)

    def cover(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        平 多头
        """
        return self.core_handler.send_order(Direction.LONG, Offset.CLOSE, price, volume, stop, lock)
