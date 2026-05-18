import socket
import threading
import time

# Konfigurasi: Masukkan IP dan Port milik Device 2 (Proxy)
PROXY_IP = "192.168.1.6"  # Ganti dengan IP laptop temanmu yang jadi Proxy
PROXY_PORT = 9999         # Ganti sesuai port yang disepakati dengan Proxy

def send_single_request(request_id=1):
    """Fungsi untuk mengirim satu HTTP GET Request ke Proxy"""
    try:
        # 1. Membuat socket TCP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Mulai hitung waktu untuk analisis QoS (Delay)
        start_time = time.time()
        
        # 2. Konek ke Proxy
        client_socket.connect((PROXY_IP, PROXY_PORT))
        
        # 3. Menyusun HTTP Request sederhana untuk meminta index.html
        http_request = "GET /index.html HTTP/1.1\r\n"
        http_request += f"Host: {PROXY_IP}\r\n"
        http_request += "Connection: close\r\n\r\n"
        
        # 4. Kirim request
        client_socket.sendall(http_request.encode())
        
        # 5. Terima respon dari Proxy
        response = b""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            response += data
            
        end_time = time.time()
        delay = (end_time - start_time) * 1000 # Mengubah ke milidetik (ms)
        
        # 6. Cetak hasil untuk log & bahan laporan QoS
        print(f"[REQ {request_id}] Berhasil menerima respon dalam {delay:.2f} ms")
        # print(response.decode()) # Uncomment ini kalau mau lihat isi HTML-nya
        
    except Exception as e:
        print(f"[REQ {request_id}] Gagal terhubung ke Proxy: {e}")
    finally:
        client_socket.close()

def send_multi_request(total_requests):
    """Fungsi untuk mengirim banyak request secara bersamaan menggunakan Thread"""
    print(f"[*] Memulai pengiriman {total_requests} request secara simultan...")
    threads = []
    
    for i in range(total_requests):
        # Setiap request dijalankan di dalam thread-nya sendiri
        t = threading.Thread(target=send_single_request, args=(i+1,))
        threads.append(t)
        t.start()
        
    # Tunggu semua thread selesai
    for t in threads:
        t.join()
    print("[*] Semua multi-request selesai dikirim.")

if __name__ == "__main__":
    # Menu interaktif untuk testing
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