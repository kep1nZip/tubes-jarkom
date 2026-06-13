import socket
import threading
import os
from datetime import datetime

HOST = '0.0.0.0'         
TCP_PORT = 8000         
UDP_PORT = 9000         

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_content_type(filepath):
    if filepath.endswith('.html'):
        return 'text/html; charset=utf-8'
    elif filepath.endswith('.css'):
        return 'text/css; charset=utf-8'
    elif filepath.endswith('.png'):
        return 'image/png'
    elif filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
        return 'image/jpeg'
    elif filepath.endswith('.ico'):
        return 'image/x-icon'
    return 'application/octet-stream'

def log_request(ip, path, status_code):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[LOG SERVER] [{timestamp}] IP:{ip} | Request:{path} | Status:{status_code}")

def handle_tcp_client(client_socket, client_address):
    proxy_ip = client_address[0]
    filepath_requested = "/"
    try:
        request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
        if not request_data:
            return
        
        # PERBAIKAN: Menggunakan splitlines() agar kebal terhadap \r\n maupun \n
        lines = request_data.splitlines()
        if len(lines) == 0:
            raise ValueError("Empty HTTP Request")
            
        first_line = lines[0]
        parts = first_line.split(' ')
        
        if len(parts) < 2:
            raise ValueError("Malformed HTTP Request")
            
        method = parts[0]
        filename = parts[1]
        filepath_requested = filename

        if method != 'GET':
            raise NotImplementedError("Hanya mendukung metode GET")

        if filename == '/' or filename == '/index.html':
            filepath = os.path.join(BASE_DIR, 'index.html')
        else:
            filepath = os.path.join(BASE_DIR, filename.lstrip('/'))

        if os.path.exists(filepath) and os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
            
            content_type = get_content_type(filepath)
            
            response_header = "HTTP/1.1 200 OK\r\n"
            response_header += f"Content-Type: {content_type}\r\n"
            response_header += f"Content-Length: {len(content)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            response = response_header.encode('utf-8') + content
            status_code = 200
        else:
            status_code = 404
            path_404 = os.path.join(BASE_DIR, '404.html')
            
            if os.path.exists(path_404):
                with open(path_404, 'rb') as f:
                    error_content = f.read()
            else:
                error_content = b"<h1>404 Not Found</h1>"
                
            response_header = "HTTP/1.1 404 Not Found\r\n"
            response_header += "Content-Type: text/html; charset=utf-8\r\n"
            response_header += f"Content-Length: {len(error_content)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            response = response_header.encode('utf-8') + error_content

        client_socket.sendall(response)
        log_request(proxy_ip, filepath_requested, status_code)

    except Exception as e:
        status_code = 500
        print(f"[ERROR INTERNAL] {e}")
        path_500 = os.path.join(BASE_DIR, '500.html')
        
        if os.path.exists(path_500):
            with open(path_500, 'rb') as f:
                error_500_content = f.read()
        else:
            error_500_content = b"<h1>500 Internal Server Error</h1>"
            
        response_header = "HTTP/1.1 500 Internal Server Error\r\n"
        response_header += "Content-Type: text/html; charset=utf-8\r\n"
        response_header += f"Content-Length: {len(error_500_content)}\r\n"
        response_header += "Connection: close\r\n\r\n"
        
        try:
            response = response_header.encode('utf-8') + error_500_content
            client_socket.sendall(response)
        except:
            pass
        log_request(proxy_ip, filepath_requested, status_code)
        
    finally:
        client_socket.close()

def start_tcp_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((HOST, TCP_PORT))
    tcp_socket.listen(25) 
    print(f"[*] TCP HTTP Server aktif di port {TCP_PORT}...")
    
    while True:
        try:
            client_socket, client_address = tcp_socket.accept()
            thread = threading.Thread(target=handle_tcp_client, args=(client_socket, client_address))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"[TCP ACCEPT ERROR] {e}")

def start_udp_server():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((HOST, UDP_PORT))
    print(f"[*] UDP Echo Server aktif di port {UDP_PORT}...")
    
    while True:
        try:
            data, address = udp_socket.recvfrom(2048)
            if not data:
                continue
            udp_socket.sendto(data, address)
        except Exception as e:
            print(f"[UDP ERROR] {e}")

if __name__ == "__main__":
    print("=== STARTING HYBRID WEB SERVER ===")
    udp_thread = threading.Thread(target=start_udp_server)
    udp_thread.daemon = True
    udp_thread.start()
    start_tcp_server()