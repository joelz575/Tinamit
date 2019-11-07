import socket
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("p")


def create_client_socket(sockname):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((socket.gethostname(), int(sockname)))
        while True:
            msg = s.recv(100).decode('utf8')
            print(msg)
            cmd, txt = msg.split(':', maxsplit=1)
            if cmd.upper() == 'OBT':
                print('OBT')
                if txt.strip() in ['Lluvia', 'Bosques']:
                    s.sendall(b'[1]')
                else:
                    s.sendall(b"[1,2,3]")

            elif cmd.upper() == "MAND":
                print('MAND')
                if txt.strip() in ['Lluvia', 'Bosques']:
                    name, val = txt.split(':', maxsplit=1)
                    if len(val) > 1:
                        s.sendall(bytes("Esta valor no es possibile para " + name, "utf-8"))
                        print("Esta valor no es possibile para " + name)
                    else:
                        s.sendall(bytes(name + " updated to " + val, "utf-8"))
                        print(name + " actualizado a " + val)
                else:
                    name, val = txt.split(':', maxsplit=1)
                    s.sendall(bytes(name + " actualizado a " + val, "utf-8"))
                    print(name + " actualizado a " + val)

            elif cmd.upper() == "CORR":
                print("CORR")
                s.sendall(bytes("Un paso de simulaccion se corre", "utf-8"))

            elif cmd.upper() == 'FIN':
                break
            else:
                raise ValueError(cmd)

if __name__ == '__main__':
    port = vars(parser.parse_args())['p']
    print(port)
    create_client_socket(port)
