import socket
import sys
import argparse

from src.client.utils.email_util import send_email


def client(host='127.0.0.1', port=8000):
    s = socket.socket()
    try:
        s.connect((host, port))
    except:
        send_email(
            subject='Unable to connect to trade server',
            body='Unable to connect to trade server'
        )
        s.close()
        sys.exit()

    try:
        message = input('Enter Command > ')
        while message != 'q':
            s.sendall(message.encode(encoding='UTF-8'))
            data = s.recv(1024).decode(encoding='UTF-8')
            print(data)
            if data == '1':
                send_email(
                    subject='Trade Server Error {}'.format(data),
                    body='Trade server returned with error code {}'
                )
            message = input('Enter Command > ')
    except KeyboardInterrupt:
        s.close()
        sys.exit()

    s.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the trading client.')
    parser.add_argument('--server_address', type=str, default='127.0.0.1:8000', help='Specify address of server to connect to.')

    args = parser.parse_args()
    host, port = args.server_address.split(':')

    client(host=host, port=int(port))
