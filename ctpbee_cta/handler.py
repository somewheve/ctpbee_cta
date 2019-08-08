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
//        ┃　　　┃   Datetime: 2019/7/10 下午5:11  ---> 无知即是罪恶
//        ┃　　　┗━━━━━━━━━┓
//        ┃　　　　　　　    ┣┓
//        ┃　　　　         ┏┛
//        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
//          ┃ ┫ ┫   ┃ ┫ ┫
//          ┗━┻━┛   ┗━┻━┛
//
"""
from copy import copy

from ctpbee.constant import Direction, Offset, EVENT_LOG, ContractData, OrderType, OrderRequest, EVENT_TICK, \
    EVENT_ORDER, EVENT_TRADE, EVENT_POSITION
from ctpbee.event_engine import Event

from ctpbee_cta.covert import OffsetConverter
from ctpbee_cta.help import round_to
from ctpbee_cta.constant import STOPORDER_PREFIX, StopOrder, StopOrderStatus, EVENT_CTA_STOPORDER


class Handler:
    """  单策略实现  """

    def __init__(self, cta, symbol):
        self.cta = cta
        self.symbol = symbol
        self.event_engine = cta.app.event_engine
        self.orderid_strategy_map = {}
        self.strategy_orderid_map = {}
        self.offset_converter = OffsetConverter(cta.app)
        self.stop_order_count = 0
        self.stop_orders = {}

    def export_log(self, log):
        event = Event(EVENT_LOG, log)
        self.cta.app.event_engine.put(event)

    def send_order(self, direction: Direction, offset: Offset, price: float, volume: float, stop: bool, lock: bool):
        """ 提供外层访问的API """
        contract = self.cta.app.recorder.get_contract(self.symbol)
        if not contract:
            self.export_log(f"委托失败，找不到合约：{self.symbol}")
            return ""
        # Round order price and volume to nearest incremental value
        price = round_to(price, contract.pricetick)
        volume = round_to(volume, contract.min_volume)
        if stop:
            if contract.stop_supported:
                return self.send_server_stop_order(contract, direction, offset, price, volume, lock)
            else:
                return self.send_local_stop_order(direction, offset, price, volume, lock)
        else:
            return self.send_limit_order(contract, direction, offset, price, volume, lock)

    def send_limit_order(
            self,
            contract: ContractData,
            direction: Direction,
            offset: Offset,
            price: float,
            volume: float,
            lock: bool
    ):
        """
        Send a limit order to server.
        """
        return self.send_server_order(
            contract,
            direction,
            offset,
            price,
            volume,
            OrderType.LIMIT,
            lock
        )

    def send_server_stop_order(self, contract: ContractData, direction: Direction, offset: Offset, price: float,
                               volume: float, lock: bool):
        """
        Send a stop order to server.

        Should only be used if stop order supported
        on the trading server.
        """
        return self.send_server_order(
            contract,
            direction,
            offset,
            price,
            volume,
            OrderType.STOP,
            lock
        )

    def send_server_order(
            self,
            contract: ContractData,
            direction: Direction,
            offset: Offset,
            price: float,
            volume: float,
            type: OrderType,
            lock: bool
    ):
        """
        Send a new order to server.
        """
        # Create request and send order.
        original_req = OrderRequest(
            symbol=contract.symbol,
            exchange=contract.exchange,
            direction=direction,
            offset=offset,
            type=type,
            price=price,
            volume=volume,
        )

        # Convert with offset converter
        req_list = self.offset_converter.convert_order_request(original_req, lock)

        # Send Orders
        vt_orderids = []
        for req in req_list:
            vt_orderid = self.cta.app.send_order(
                req, contract.gateway_name)
            vt_orderids.append(vt_orderid)
            self.offset_converter.update_order_request(req, vt_orderid)

            # Save relationship between orderid and strategy.
            self.orderid_strategy_map[vt_orderid] = self.cta
            self.strategy_orderid_map[self.cta.cta_name].add(vt_orderid)
        return vt_orderids

    def send_local_stop_order(
            self,
            direction: Direction,
            offset: Offset,
            price: float,
            volume: float,
            lock: bool
    ):
        """
        Create a new local stop order.
        """
        self.stop_order_count += 1
        stop_orderid = f"{STOPORDER_PREFIX}.{self.stop_order_count}"

        stop_order = StopOrder(
            vt_symbol=self.symbol,
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            stop_orderid=stop_orderid,
            strategy_name=self.cta.cta_name,
            lock=lock
        )
        self.stop_orders[stop_orderid] = stop_order

        vt_orderids = self.strategy_orderid_map[self.cta.cta_name]
        vt_orderids.add(stop_orderid)

        ##todo  触发停止单回调函数
        #  self.call_strategy_func(strategy, strategy.on_stop_order, stop_order)
        self.put_stop_order_event(stop_order)

        return stop_orderid

    def put_stop_order_event(self, stop_order: StopOrder):
        """
        Put an event to update stop order status.
        """
        event = Event(EVENT_CTA_STOPORDER, stop_order)
        self.event_engine.put(event)

    def cancel_server_order(self, vt_orderid: str):
        """
        Cancel existing order by vt_orderid.
        """
        order = self.cta.app.recorder.get_order(vt_orderid)
        if not order:
            self.export_log(f"撤单失败，找不到委托{vt_orderid}, {self.cta.cta_name}", )
            return
        # 快速创建OrderReq
        req = order.create_cancel_request()

        self.cta.app.cancel_order(req)

    def cancel_local_stop_order(self, stop_orderid: str):
        """
        Cancel a local stop order.
        """
        stop_order = self.stop_orders.get(stop_orderid, None)
        if not stop_order:
            return

        # Remove from relation map.
        self.stop_orders.pop(stop_orderid)

        vt_orderids = self.strategy_orderid_map[self.cta.cta_name]
        if stop_orderid in vt_orderids:
            vt_orderids.remove(stop_orderid)

        # Change stop order status to cancelled and update to strategy.
        stop_order.status = StopOrderStatus.CANCELLED

        # todo :  本地停止单回调函数
        # self.call_strategy_func(strategy, strategy.on_stop_order, stop_order)
        self.put_stop_order_event(stop_order)

    def cancel_order(self, vt_orderid: str):
        """
        """
        if vt_orderid.startswith(STOPORDER_PREFIX):
            self.cancel_local_stop_order(vt_orderid)
        else:
            self.cancel_server_order(vt_orderid)

    def cancel_all(self):
        """
        Cancel all active orders of a strategy.
        """
        vt_orderids = self.strategy_orderid_map[self.cta.cta_name]
        if not vt_orderids:
            return

        for vt_orderid in copy(vt_orderids):
            self.cancel_order(vt_orderid)
