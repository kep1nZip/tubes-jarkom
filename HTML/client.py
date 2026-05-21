import socket
import threading
import time

PROXY_IP = "10.15.11.54" 
PROXY_PORT = 9090

def send_single_request(request_id=1):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        start_time = time.time()

        client_socket.connect((PROXY_IP, PROXY_PORT))
        
        http_request = "GET /index.html HTTP/1.1\r\n"
        http_request += f"Host: {PROXY_IP}\r\n"
        http_request += "Connection: close\r\n\r\n"
        
        client_socket.sendall(http_request.encode())
        
        response = b""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            response += data
            
        end_time = time.time()
        delay = (end_time - start_time) * 1000 
        
        print(f"[REQ {request_id}] Berhasil menerima respon dalam {delay:.2f} ms")
        
    except Exception as e:
        print(f"[REQ {request_id}] Gagal terhubung ke Proxy: {e}")
    finally:
        client_socket.close()

def send_multi_request(total_requests):
    print(f"[*] Memulai pengiriman {total_requests} request secara simultan...")
    threads = []
    
    for i in range(total_requests):
        t = threading.Thread(target=send_single_request, args=(i+1,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    print("[*] Semua multi-request selesai dikirim.")

if __name__ == "__main__":
    while True:
        print("\n=== MENU CLIENT ===")
        print("1. Kirim Single Request")
        print("2. Kirim Multi-Request (Simultan)")
        print("3. Keluar")
        pilihan = input("Pilih menu (1/2/3): ")
        
        if pilihan == "1":
            send_single_request()
        elif pilihan == "2":
            jumlah = int(input("Masukkan jumlah request: "))
            send_multi_request(jumlah)
        elif pilihan == "3":
            print("Keluar dari program.")
            break
        else:
            print("Pilihan tidak valid!")