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
//        ┃　　　┃   Datetime: 2019/7/7 上午11:58  ---> 无知即是罪恶
//        ┃　　　┗━━━━━━━━━┓
//        ┃　　　　　　　    ┣┓
//        ┃　　　　         ┏┛
//        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
//          ┃ ┫ ┫   ┃ ┫ ┫
//          ┗━┻━┛   ┗━┻━┛
//
"""

from ctpbee import CtpbeeApi
from ctpbee.constant import (
    TickData,
    BarData,
    TradeData,
    OrderData,
    AccountData, PositionData, LogData, ContractData)

from ctpbee_cta.constant import EVENT_CTA_STOPORDER
from ctpbee_cta.constant import StopOrder
from ctpbee_cta.cta import CtaCore
from ctpbee_cta.indicator import ArrayManager


class DoubleMaStrategy(CtpbeeApi):
    author = "open_source"
    name = "double ma"

    fast_window = 10
    slow_window = 20

    fast_ma0 = 0.0
    fast_ma1 = 0.0

    slow_ma0 = 0.0
    slow_ma1 = 0.0

    parameters = ["fast_window", "slow_window"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, name, app, cta_symbol):
        """"""

        super().__init__(extension_name=name, app=app)
        self.cta_symbol = cta_symbol
        self.cta_core = CtaCore(cta_name=self.name, app=self.app, symbol=self.cta_symbol)
        self.am = ArrayManager()

        # 注册停止单事件
        self.app.event_engine.register(EVENT_CTA_STOPORDER, self.on_stop_order)

    def start(self):
        self.cta_core.export_log("策略初始化")
        self.load_bar(10)

    def on_account(self, account: AccountData) -> None:
        pass

    def on_position(self, position: PositionData) -> None:
        pass

    def on_log(self, log: LogData):
        print(log)

    def on_contract(self, contract: ContractData):

        if contract.local_symbol == self.cta_symbol:
            self.cta_core.export_log("成功订阅相关行情")
            self.app.subscribe(self.cta_symbol)

    def load_bar(self, count):
        """ Accourding to your own data"""

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.cta_core.export_log("策略启动")

    def on_tick(self, tick: TickData):
        """
        处理tick
        """
        pass

    def on_bar(self, bar: BarData):
        """
        处理bar
        """
        # 初始化load
        if bar.interval == 1:
            am = self.am
            am.update_bar(bar)
            if not am.inited:
                return

            fast_ma = am.sma(self.fast_window, array=True)
            self.fast_ma0 = fast_ma[-1]
            self.fast_ma1 = fast_ma[-2]

            slow_ma = am.sma(self.slow_window, array=True)
            self.slow_ma0 = slow_ma[-1]
            self.slow_ma1 = slow_ma[-2]

            cross_over = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 < self.slow_ma1
            cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 > self.slow_ma1

            if cross_over:
                if self.cta_core.pos == 0:
                    self.cta_core.buy(bar.close_price, 1)
                elif self.cta_core.pos < 0:
                    self.cta_core.cover(bar.close_price, 1)
                    self.cta_core.buy(bar.close_price, 1)

            elif cross_below:
                if self.cta_core.pos == 0:
                    self.cta_core.short(bar.close_price, 1)
                elif self.cta_core.pos > 0:
                    self.cta_core.sell(bar.close_price, 1)
                    self.cta_core.short(bar.close_price, 1)

    def on_shared(self, shared):
        pass

    def on_order(self, order: OrderData):
        """
        处理order事件
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        更新成交单事件
        """

    def on_stop_order(self, stop_order: StopOrder):
        """

        """
        pass
