import socket
import threading
import os

HOST = '0.0.0.0'  
PORT = 9999

def handle_client(client_socket, client_address):
    print(f"[KONEKSI BARU] Terhubung dengan {client_address}")
    try:
        request = client_socket.recv(1024).decode('utf-8')
        if not request:
            return
        
        print(f"[REQUEST DITERIMA]\n{request}")
        
        first_line = request.split('\n')[0]
        filename = first_line.split(' ')[1]

        if filename == '/' or filename == '/index.html':
            filepath = 'index.html'
        else:
            filepath = filename.lstrip('/')

        if os.path.exists(filepath) and os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type: text/html\r\n"
            response += f"Content-Length: {len(content)}\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            response += content
        else:
            not_found_content = "<h1>404 Not Found</h1>"
            response = "HTTP/1.1 404 Not Found\r\n"
            response += "Content-Type: text/html\r\n"
            response += f"Content-Length: {len(not_found_content)}\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            response += not_found_content

        client_socket.sendall(response.encode('utf-8'))
        
    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan: {e}")
    finally:
        client_socket.close()
        print(f"[KONEKSI DITUTUP] Selesai melayani {client_address}\n")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER BERJALAN] Menunggu koneksi di port {PORT}...")

    while True:
        client_socket, client_address = server.accept()

        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()