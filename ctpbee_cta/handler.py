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

from ctpbee.constant import Direction, Offset, EVENT_LOG, ContractData, OrderType, OrderRequest
from ctpbee.event_engine import Event

from ctpbee_cta.constant import STOPORDER_PREFIX, StopOrder, StopOrderStatus, EVENT_CTA_STOPORDER
from ctpbee_cta.covert import OffsetConverter
from ctpbee_cta.help import round_to


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
        发送停止单到服务器
        如果交易服务器支持停止单才能够进行使用
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
        发送新的单子给服务器
        """
        # 创建新的order_req.
        original_req = OrderRequest(
            symbol=contract.symbol,
            exchange=contract.exchange,
            direction=direction,
            offset=offset,
            type=type,
            price=price,
            volume=volume,
        )

        # 通过本地持仓携带的转换请求功能 --> 详情见ctpbee下面的data_handle/local_position.py
        req_list = self.cta.app.recorder.position_manager.get(contract.local_symbol).convert_order_request(original_req,
                                                                                                           lock)
        # 发单
        local_orderids = []
        for req in req_list:
            local_orderid = self.cta.app.send_order(
                req, contract.gateway_name)
            local_orderids.append(local_orderid)
            self.cta.app.recorder.position_manager.get(contract.local_symbol)._update_order_request(req, local_orderid)

            # Save relationship between orderid and strategy.
            self.orderid_strategy_map[local_orderid] = self.cta
            self.strategy_orderid_map[self.cta.cta_name].add(local_orderid)
        return local_orderids

    def send_local_stop_order(
            self,
            direction: Direction,
            offset: Offset,
            price: float,
            volume: float,
            lock: bool
    ):
        """
        发送本地停止单
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

        local_orderids = self.strategy_orderid_map[self.cta.cta_name]
        local_orderids.add(stop_orderid)

        ##todo  触发停止单回调函数.... 猜测是将停止单送入到一个监测器,然后等条件触发立即执行
        self.put_stop_order_event(stop_order)

        return stop_orderid

    def put_stop_order_event(self, stop_order: StopOrder):
        """
        推送事件到停止单处理函数更新
        """
        event = Event(EVENT_CTA_STOPORDER, stop_order)
        self.event_engine.put(event)

    def cancel_server_order(self, local_orderid: str):
        """
        通过local_orderid来撤掉服务器的停止单
        """
        order = self.cta.app.recorder.get_order(local_orderid)
        if not order:
            self.export_log(f"撤单失败，找不到委托{local_orderid}, {self.cta.cta_name}", )
            return
        # 快速创建OrderReq
        req = order._create_cancel_request()
        self.cta.app.cancel_order(req)

    def cancel_local_stop_order(self, stop_orderid: str):
        """
        撤掉本地的停止单
        """
        stop_order = self.stop_orders.get(stop_orderid, None)
        if not stop_order:
            return

        # 移除关系
        self.stop_orders.pop(stop_orderid)

        local_orderids = self.strategy_orderid_map[self.cta.cta_name]
        if stop_orderid in local_orderids:
            local_orderids.remove(stop_orderid)

        # 更新停止单的状态
        stop_order.status = StopOrderStatus.CANCELLED
        # 推送到处理函数
        self.put_stop_order_event(stop_order)

    def cancel_order(self, local_orderid: str):
        """
        撤单
        """
        if local_orderid.startswith(STOPORDER_PREFIX):
            self.cancel_local_stop_order(local_orderid)
        else:
            self.cancel_server_order(local_orderid)

    def cancel_all(self):
        """
        撤掉全部单子
        """
        vt_orderids = self.strategy_orderid_map[self.cta.cta_name]
        if not vt_orderids:
            return

        for vt_orderid in copy(vt_orderids):
            self.cancel_order(vt_orderid)
