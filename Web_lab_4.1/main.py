from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pathlib
import urllib.parse
import mimetypes
import json
import socket
import threading

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static(pr_url.path)
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            post_data = self.rfile.read(content_length).decode()
            sock.sendto(post_data.encode(), ('localhost', 5000))

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self, path):
        self.send_response(200)
        mt = mimetypes.guess_type(path)

        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open('.' + path, 'rb') as file:
            self.wfile.write(file.read()) 

def sock():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('localhost', 5000))

        while True:
            data, addr = sock.recvfrom(2048)
            decoded_data = data.decode()
            parsed_data = urllib.parse.parse_qs(decoded_data)
            message_data = { 'username': parsed_data.get('username', [''])[0], 'message': parsed_data.get('message', [''])[0] }
        
            time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            with open('storage/data.json', 'r+') as file:
                json_data = json.load(file)
                json_data[time_now] = message_data
                file.seek(0)
                json.dump(json_data, file, indent=2)



def run_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run():
    server_thread = threading.Thread(target=run_server)
    socket_thread = threading.Thread(target=sock)
    
    server_thread.start()
    socket_thread.start()
    
    server_thread.join()
    socket_thread.join()

if __name__ == '__main__':
    run()
