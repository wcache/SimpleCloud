
import ujson
from usr.mqttIot import MqttIot


cloud = MqttIot('txm_1682300809', 'mq.tongxinmao.com', port=18830)


@cloud.publish('/public/topic1')
def pub_test(name, age):
    data = ujson.dumps({
        'name': name,
        'age': age
    })

    return data


@cloud.subscribe('/public/topic2')
def sub_test(data):
    print('get data from cloud: ', data)
    pub_test('weiwei', 18)


if __name__ == '__main__':
    cloud.run_forever()
