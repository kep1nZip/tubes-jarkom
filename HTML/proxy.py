import socket
import threading
import os
from datetime import datetime

# ==========================================
# KONFIGURASI SESUAI KETENTUAN MODUL
# ==========================================
PROXY_HOST = '0.0.0.0'      # Bind ke semua IP interface agar Laptop Client bisa konek
PROXY_PORT = 9090 

# SESUAIKAN DENGAN IP LAPTOP WEB SERVER (DEVICE 3)
SERVER_IP = "10.105.163.249"  
SERVER_PORT = 8000          # PERBAIKAN: Disamakan dengan port TCP server.py

CACHE_DIR = "cache_storage"
TIMEOUT_LIMIT = 5.0         

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

cache_lock = threading.Lock()

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_cache_filename(url_path):
    clean_path = url_path.replace('/', '_').replace('\\', '_').strip('_')
    if clean_path == "" or clean_path == "_":
        clean_path = "index.html"
    return os.path.join(CACHE_DIR, f"cache_{clean_path}")

def load_local_error_page(status_code, fallback_text):
    possible_paths = [f"{status_code}.html", f"errors/{status_code}.html", f"pages/{status_code}.html"]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return f.read()
    return fallback_text.encode('utf-8')

def build_error_response(status_code, status_text, html_content):
    response = f"HTTP/1.1 {status_code} {status_text}\r\n"
    response += "Content-Type: text/html; charset=utf-8\r\n"
    response += f"Content-Length: {len(html_content)}\r\n"
    response += "Connection: close\r\n\r\n"
    return response.encode('utf-8') + html_content

def handle_client(client_socket, client_address):
    try:
        request_bytes = client_socket.recv(4096)
        if not request_bytes:
            return
        
        request_decode = request_bytes.decode('utf-8', errors='ignore')
        lines = request_decode.splitlines()
        if len(lines) < 1:
            return
            
        first_line = lines[0]
        parts = first_line.split(' ')
        
        if len(parts) < 2:
            return
            
        method = parts[0]
        url_path = parts[1]
        
        cache_file_path = get_cache_filename(url_path)
        
        # --- MEKANISME CACHE HIT ---
        with cache_lock:
            if method == 'GET' and os.path.exists(cache_file_path) and os.path.isfile(cache_file_path):
                with open(cache_file_path, 'rb') as f:
                    cached_response = f.read()
                
                client_socket.sendall(cached_response)
                print(f"[LOG PROXY] {get_timestamp()} | Client: {client_address[0]} -> Akses: {url_path} | Cache: HIT")
                return

        # --- MEKANISME CACHE MISS ---
        print(f"[LOG PROXY] {get_timestamp()} | Client: {client_address[0]} -> Akses: {url_path} | Cache: MISS")
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(TIMEOUT_LIMIT)
        
        try:
            server_socket.connect((SERVER_IP, SERVER_PORT))
        except (socket.timeout, socket.error):
            print(f"[WARNING PROXY] {get_timestamp()} | Server {SERVER_IP}:{SERVER_PORT} tidak merespon. Mengirim 504.")
            html_504 = load_local_error_page("504", "<h1>504 Gateway Timeout</h1>")
            error_response = build_error_response("504", "Gateway Timeout", html_504)
            client_socket.sendall(error_response)
            return

        server_socket.sendall(request_bytes)
        
        response_bytes = b""
        server_socket.settimeout(TIMEOUT_LIMIT)
        
        try:
            while True:
                data = server_socket.recv(4096)
                if not data:
                    break
                response_bytes += data
        except socket.timeout:
            print(f"[WARNING PROXY] {get_timestamp()} | Pembacaan data dari server timeout.")
            
        server_socket.close()

        if not response_bytes or not response_bytes.startswith(b"HTTP/"):
            print(f"[WARNING PROXY] {get_timestamp()} | Respon dari server tidak valid. Mengirim 502.")
            html_502 = load_local_error_page("502", "<h1>502 Bad Gateway</h1>")
            error_response = build_error_response("502", "Bad Gateway", html_502)
            client_socket.sendall(error_response)
            return

        # --- SIMPAN KE FILE CACHE LOKAL ---
        if b"200 OK" in response_bytes.split(b"\r\n")[0] and method == 'GET':
            with cache_lock:
                with open(cache_file_path, 'wb') as f:
                    f.write(response_bytes)
                print(f"[PROXY CACHE] Berhasil menyimpan berkas cache fisik: {cache_file_path}")

        client_socket.sendall(response_bytes)

    except Exception as e:
        print(f"[ERROR PROXY] Terjadi kegagalan penanganan client {client_address}: {e}")
    finally:
        client_socket.close()

def start_proxy():
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        proxy_socket.bind((PROXY_HOST, PROXY_PORT))
        proxy_socket.listen(30)
        print(f"[*] Proxy Server berjalan aktif di port {PROXY_PORT}")
        print(f"[*] Topologi Target Upstream Server -> {SERVER_IP}:{SERVER_PORT}\n")
        
        while True:
            client_sock, addr = proxy_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_sock, addr))
            thread.daemon = True
            thread.start()
    except Exception as e:
        print(f"[CRITICAL PROXY] Gagal menjalankan Proxy Server: {e}")
    finally:
        proxy_socket.close()

if __name__ == "__main__":
    try:
        start_proxy()
    except KeyboardInterrupt:
        print("\n[!] Mematikan Proxy Server secara aman...")