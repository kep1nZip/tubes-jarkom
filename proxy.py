import socket
import threading

# SESUAIKAN DENGAN IP SERVER TEMANMU
SERVER_IP = "10.15.11.249" 
SERVER_PORT = 9999

def handle_client(client_socket):
    try:
        # 1. Terima request dari Client
        request = client_socket.recv(4096)
        if not request:
            return
        
        print(f"[PROXY] Menerima request dari Client:\n{request.decode(errors='ignore')}")

        # 2. Teruskan request ke Server (Device 3)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((SERVER_IP, SERVER_PORT))
        server_socket.sendall(request)

        # 3. Terima respon dari Server
        response = b""
        while True:
            data = server_socket.recv(4096)
            if not data:
                break
            response += data
        print(f"[PROXY] Menerima respon dari Server. Meneruskan ke Client...")

        # 4. Kembalikan respon ke Client
        client_socket.sendall(response)
        server_socket.close()

    except Exception as e:
        print(f"[ERROR] Proxy bermasalah: {e}")
    finally:
        client_socket.close()

def start_proxy():
    # Proxy listen di semua interface laptopmu sendiri
    PROXY_IP = "0.0.0.0"
    PROXY_PORT = 9090 # Gunakan port berbeda dari server, misal 9090

    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.bind((PROXY_IP, PROXY_PORT))
    proxy_server.listen(5)
    print(f"[*] Proxy berjalan di port {PROXY_PORT}, siap meneruskan ke Server {SERVER_IP}:{SERVER_PORT}")

    while True:
        client_sock, addr = proxy_server.accept()
        # Threading sesuai instruksi whiteboard
        thread = threading.Thread(target=handle_client, args=(client_sock,))
        thread.start()

if __name__ == "__main__":
    start_proxy()