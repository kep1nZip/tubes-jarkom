import socket
import threading
import os

# Konfigurasi Server
# Ganti dengan '0.0.0.0' agar server bisa menerima koneksi dari IP luar (dari laptop Proxy)
HOST = '0.0.0.0'  
PORT = 9999

def handle_client(client_socket, client_address):
    print(f"[KONEKSI BARU] Terhubung dengan {client_address}")
    try:
        # Menerima request dari Proxy/Client (ukuran buffer 1024 bytes)
        request = client_socket.recv(1024).decode('utf-8')
        if not request:
            return
        
        print(f"[REQUEST DITERIMA]\n{request}")
        
        # Mengambil baris pertama dari HTTP request (misal: "GET / HTTP/1.1")
        first_line = request.split('\n')[0]
        filename = first_line.split(' ')[1]
        
        # Jika request ke root (/) atau langsung ke index.html
        if filename == '/' or filename == '/index.html':
            filepath = 'index.html'
        else:
            filepath = filename.lstrip('/')

        # Cek apakah file yang diminta ada
        if os.path.exists(filepath) and os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Membuat HTTP Response Sukses (200 OK)
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type: text/html\r\n"
            response += f"Content-Length: {len(content)}\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            response += content
        else:
            # Jika file tidak ditemukan (404 Not Found)
            not_found_content = "<h1>404 Not Found</h1>"
            response = "HTTP/1.1 404 Not Found\r\n"
            response += "Content-Type: text/html\r\n"
            response += f"Content-Length: {len(not_found_content)}\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            response += not_found_content

        # Kirim response balik ke Proxy/Client
        client_socket.sendall(response.encode('utf-8'))
        
    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan: {e}")
    finally:
        # Tutup koneksi socket untuk client ini
        client_socket.close()
        print(f"[KONEKSI DITUTUP] Selesai melayani {client_address}\n")

def start_server():
    # Inisialisasi TCP Socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Mengizinkan penggunaan kembali port yang sama jika server di-restart
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER BERJALAN] Menunggu koneksi di port {PORT}...")

    while True:
        # Menerima koneksi yang masuk
        client_socket, client_address = server.accept()
        
        # Membuat thread baru untuk menangani client tersebut (Multi-threading)
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()