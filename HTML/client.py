import socket
import threading
import time

# Konfigurasi: Masukkan IP dan Port milik Device 2 (Proxy)
PROXY_IP = "10.105.163.54"  # IP Laptop Proxy
PROXY_PORT = 9090          # Port TCP Proxy

# Konfigurasi Langsung ke Server untuk UDP Pinger (Sesuai modul, QoS UDP langsung ke Server Port 9000)
SERVER_IP = "10.105.163.249" 
UDP_PORT = 9000

def send_single_request(request_id=1):
    """Fungsi untuk mengirim satu HTTP GET Request ke Proxy"""
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
    """Fungsi untuk mengirim banyak request secara bersamaan menggunakan Thread"""
    print(f"[*] Memulai pengiriman {total_requests} request secara simultan...")
    threads = []
    for i in range(total_requests):
        t = threading.Thread(target=send_single_request, args=(i+1,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
    print("[*] Semua multi-request selesai dikirim.")

def send_udp_pinger():
    """Fungsi Pengukuran QoS: Mengirim 10 Paket UDP Echo ke Server Port 9000"""
    print(f"\n[*] Memulai Pengujian QoS UDP Pinger ke {SERVER_IP}:{UDP_PORT}...")
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1.0) # Timeout 1 detik jika paket hilang
    
    rtt_list = []
    packets_sent = 10
    packets_received = 0
    
    for seq in range(1, packets_sent + 1):
        send_time = time.time()
        payload = f"Ping {seq} {send_time}"
        
        try:
            udp_socket.sendto(payload.encode('utf-8'), (SERVER_IP, UDP_PORT))
            data, address = udp_socket.recvfrom(2048)
            recv_time = time.time()
            
            # Hitung RTT dalam milidetik
            rtt = (recv_time - send_time) * 1000
            rtt_list.append(rtt)
            packets_received += 1
            print(f"Reply dari {address[0]}: bytes={len(data)} seq={seq} RTT={rtt:.2f} ms")
        except socket.timeout:
            print(f"Request seq={seq} Timed Out (Packet Drop).")
            
        time.sleep(0.1) # Jeda antar ping
        
    udp_socket.close()
    
    # --- HITUNG STATISTIK KINERJA QOS ---
    print("\n========= STATISTIK KINERJA QOS =========")
    packet_loss = ((packets_sent - packets_received) / packets_sent) * 100
    print(f"Paket: Dikirim = {packets_sent}, Diterima = {packets_received}, Loss = {packet_loss:.1f}%")
    
    if rtt_list:
        min_rtt = min(rtt_list)
        max_rtt = max(rtt_list)
        avg_rtt = sum(rtt_list) / len(rtt_list)
        print(f"Round Trip Time (RTT) -> Min: {min_rtt:.2f} ms | Max: {max_rtt:.2f} ms | Avg: {avg_rtt:.2f} ms")
    else:
        print("Gagal menghitung RTT karena semua paket loss (100% Loss).")
    print("=========================================")

if __name__ == "__main__":
    while True:
        print("\n=== MENU CLIENT ===")
        print("1. Kirim Single Request (TCP HTTP)")
        print("2. Kirim Multi-Request Simultan (TCP HTTP)")
        print("3. Jalankan Pengujian Kinerja QoS (UDP Pinger)")
        print("4. Keluar")
        pilihan = input("Pilih menu (1/2/3/4): ")
        
        if pilihan == "1":
            send_single_request()
        elif pilihan == "2":
            jumlah = int(input("Masukkan jumlah request: "))
            send_multi_request(jumlah)
        elif pilihan == "3":
            send_udp_pinger()
        elif pilihan == "4":
            print("Keluar dari program.")
            break
        else:
            print("Pilihan tidak valid!")