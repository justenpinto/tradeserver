import socket
import sys
import argparse


def client(host='127.0.0.1', port=8000):
    # TODO: add email to user when trading system does not respond or gives error
    s = socket.socket()
    s.connect((host, port))

    try:
        message = input('Enter Command > ')
        while message != 'q':
            s.sendall(message.encode(encoding='UTF-8'))
            data = s.recv(1024).decode(encoding='UTF-8')
            print(data)
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
