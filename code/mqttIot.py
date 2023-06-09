"""
MQTT客户端抽象类
"""
import _thread
from queue import Queue
from umqtt import MQTTClient


class MqttIot(object):

    def __init__(self, *args, **kwargs):
        """init umqtt.MQTTClient instance.
        args:
            client_id - 客户端 ID，字符串类型，具有唯一性。
            server - 服务端地址，字符串类型，可以是 IP 或者域名。
        kwargs:
            port - 服务器端口（可选），整数类型，默认为1883，请注意，MQTT over SSL/TLS的默认端口是8883。
            user - （可选) 在服务器上注册的用户名，字符串类型。
            password - （可选) 在服务器上注册的密码，字符串类型。
            keepalive - （可选）客户端的keepalive超时值，整数类型，默认为0。
            ssl - （可选）是否使能 SSL/TLS 支持，布尔值类型。
            ssl_params - （可选）SSL/TLS 参数，字符串类型。
            reconn - （可选）控制是否使用内部重连的标志，布尔值类型，默认开启为True。
            version - （可选）选择使用mqtt版本，整数类型，version=3开启MQTTv3.1，默认version=4开启MQTTv3.1.1。
            clean_session - 布尔值类型，可选参数，一个决定客户端类型的布尔值。 如果为True，那么代理将在其断开连接时删除有关此客户端的所有信息。
                如果为False，则客户端是持久客户端，当客户端断开连接时，订阅信息和排队消息将被保留。默认为True。
            qos - MQTT消息服务质量（默认0，可选择0或1）.
                整数类型 0：发送者只发送一次消息，不进行重试 1：发送者最少发送一次消息，确保消息到达Broker。
        """
        self.clean_session = kwargs.get('clean_session', True)
        self.qos = kwargs.get('qos', 0)
        self.subscribe_hooks = {}
        self.queue = Queue()

        self.cli = MQTTClient(*args, **kwargs)
        self.cli.set_callback(self.__callback)

    def __callback(self, topic, data):
        self.queue.put((topic, data))

    def init(self):
        try:
            self.cli.connect(clean_session=self.clean_session)
            for topic in self.subscribe_hooks.keys():
                self.cli.subscribe(topic, qos=self.qos)
        except Exception as e:
            self.cli.close()
            raise e

        _thread.start_new_thread(self.listen, ())

    def disconnect(self):
        self.cli.disconnect()

    def close(self):
        self.cli.close()

    def is_stat_ok(self):
        return self.cli.get_mqttsta() == 0

    def listen(self):
        while True:
            self.cli.wait_msg()

    def subscribe(self, topic):
        """decorator for subscribe topic."""
        def wrapper(fn):
            self.subscribe_hooks.setdefault(topic, fn)
            return fn
        return wrapper

    def publish(self, topic):
        """decorator for publish topic."""
        def wrapper(fn):
            def handler(*args, **kwargs):
                data = fn(*args, **kwargs)
                self.cli.publish(topic, data, qos=self.qos)
            return handler
        return wrapper

    def run_forever(self):
        try:
            self.init()
        except Exception as e:
            raise Exception('cloud init error, with message: {}'.format(str(e)))

        while True:
            topic, data = self.queue.get()
            handler = self.subscribe_hooks.get(topic.decode(), None)
            if handler is None:
                continue
            _thread.start_new_thread(handler, (data, ))
