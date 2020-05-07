"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if login == client.login:
                        self.transport.write(
                            f"Логин {login} занят, попробуйте другой".encode()
                        )
                        self.transport.close()
                        break
                else:
                    self.send_history()
                    self.login = login
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        self.server.history.append(format_string)
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        total_messages = len(self.server.history)
        if total_messages > 10:
            last_history = (message for message in self.server.history[-10:])
        else:
            last_history = self.server.history
        history = "\n".join(last_history)
        self.transport.write(
            history.encode()
        )

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")

class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
