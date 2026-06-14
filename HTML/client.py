import socket
import time
import os
import webbrowser
import re
import posixpath

# =================================================================
# KONFIGURASI TARGET (Sesuaikan IP saat demo)
# =================================================================
PROXY_IP = "10.105.163.54"      # IP Laptop B (Proxy Server)
PROXY_TCP_PORT = 9090       # Port TCP Proxy Anda

SERVER_IP = "10.105.163.249"     # IP Laptop A (Web Server) untuk UDP Pinger
UDP_PORT = 9000             # Port UDP Langsung ke Server (Sesuai Modul)

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_web")

def request_file(filepath):
    """Mengirim satu HTTP GET Request ke Proxy Anda"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((PROXY_IP, PROXY_TCP_PORT))
        
        request = (
            f"GET {filepath} HTTP/1.1\r\n"
            f"Host: {PROXY_IP}\r\n"
            f"Connection: close\r\n\r\n"
        )
        s.sendall(request.encode("utf-8"))
        
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
        s.close()

        if not response:
            return None, b""
            
        if b"\r\n\r\n" in response:
            header_raw, body = response.split(b"\r\n\r\n", 1)
        else:
            header_raw, body = response, b""
            
        status_line = header_raw.decode("utf-8", errors="ignore").split("\r\n")[0]
        return status_line, body
    except Exception as e:
        print(f"  [!] Gagal mengunduh {filepath}: {e}")
        return None, b""

def save_file(filepath, data):
    """Menyimpan file ke dalam folder lokal client_web"""
    rel = filepath.lstrip("/")
    full_path = os.path.join(SAVE_DIR, rel.replace("/", os.sep))
    folder = os.path.dirname(full_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(data)
    return full_path

def extract_assets(html_bytes, current_dir):
    """Smart Asset Scraper: Membedah HTML untuk mencari CSS, JS, Gambar, dan Halaman Lain"""
    html = html_bytes.decode("utf-8", errors="ignore")
    patterns = [
        r'href=["\']([^"\'#?]+\.css)["\']',
        r'src=["\']([^"\'#?]+\.js)["\']',
        r'src=["\']([^"\'#?]+\.(png|jpg|jpeg|gif|ico|svg|webp))["\']',
        r'href=["\']([^"\'#?]+\.(png|ico|svg))["\']',
        r'href=["\']([^"\'#?]+\.html)["\']',
    ]
    assets = []
    for p in patterns:
        for match in re.findall(p, html, re.IGNORECASE):
            path = match if isinstance(match, str) else match[0]
            if path.startswith("http://") or path.startswith("https://"):
                continue
            
            if not path.startswith("/"):
                combined_path = posixpath.join(current_dir, path)
                path = posixpath.normpath(combined_path)
            else:
                path = posixpath.normpath(path)
                
            if not path.startswith("/"):
                path = "/" + path
                
            if path not in assets:
                assets.append(path)
    return assets

def download_site(start_path):
    """Mengunduh seluruh halaman dan aset secara rekursif via Proxy"""
    import shutil
    if os.path.exists(SAVE_DIR):
        shutil.rmtree(SAVE_DIR)
    os.makedirs(SAVE_DIR, exist_ok=True)

    downloaded = set()
    queue = [start_path]

    print(f"\n[INFO] Mulai mengunduh website dari Proxy -> {PROXY_IP}:{PROXY_TCP_PORT}...")
    
    while queue:
        filepath = queue.pop(0)
        if filepath in downloaded:
            continue

        status, body = request_file(filepath)
        if not status or "200" not in status or not body:
            print(f"  [MISS/ERROR] {filepath} -> Status: {status}")
            downloaded.add(filepath)
            continue

        save_file(filepath, body)
        downloaded.add(filepath)
        print(f"  [OK DOWNLOADED] {filepath} ({len(body)} bytes)")

        if filepath.endswith(".html") or filepath == "/":
            current_dir = posixpath.dirname(filepath)
            assets = extract_assets(body, current_dir)
            for asset in assets:
                if asset not in downloaded and asset not in queue:
                    queue.append(asset)

    print(f"\n[INFO] Selesai! Total {len(downloaded)} file disimpan ke: {SAVE_DIR}")
    return os.path.join(SAVE_DIR, start_path.lstrip("/").replace("/", os.sep))

def run_http_client():
    print("\nMasukkan halaman awal website (contoh: /index.html)")
    filename = input("Halaman: ").strip()
    if not filename.startswith("/"):
        filename = "/" + filename

    main_path = download_site(filename)

    if os.path.exists(main_path):
        print("[INFO] Membuka website di Web Browser...")
        webbrowser.open(f"file:///{main_path.replace(os.sep, '/')}")
    else:
        print("[Error] File utama tidak ditemukan di lokal.")

def run_udp_pinger():
    """Mengukur Kinerja QoS: Delay, Packet Loss, Jitter, dan Throughput"""
    packets_sent = 10
    print(f"\n[*] Memulai Pengujian Kinerja QoS (UDP Pinger) ke {SERVER_IP}:{UDP_PORT} sebanyak {packets_sent}x...")
    
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(1.5)
    
    rtt_list = []
    packets_received = 0
    t_start = time.time()
    
    for seq in range(1, packets_sent + 1):
        send_time = time.time()
        payload = f"Ping {seq} {send_time}"
        
        try:
            udp_socket.sendto(payload.encode('utf-8'), (SERVER_IP, UDP_PORT))
            data, address = udp_socket.recvfrom(2048)
            recv_time = time.time()
            
            rtt = (recv_time - send_time) * 1000
            rtt_list.append(rtt)
            packets_received += 1
            print(f"  Reply dari {address[0]}: bytes={len(data)} seq={seq} RTT={rtt:.2f} ms")
        except socket.timeout:
            print(f"  Request seq={seq} Timed Out (Packet Drop).")
            
        time.sleep(0.1)
        
    t_end = time.time()
    udp_socket.close()
    
    # --- PERHITUNGAN MATEMATIKA PARAMETER QOS ---
    print("\n========= STATISTIK ANALISIS KINERJA QOS =========")
    packet_loss = ((packets_sent - packets_received) / packets_sent) * 100
    print(f"Packet Loss  : {packet_loss:.1f}% (Dikirim: {packets_sent}, Diterima: {packets_received})")
    
    if rtt_list:
        # 1. Metrik Delay (RTT)
        min_rtt = min(rtt_list)
        max_rtt = max(rtt_list)
        avg_rtt = sum(rtt_list) / len(rtt_list)
        print(f"Minimum RTT  : {min_rtt:.2f} ms")
        print(f"Maximum RTT  : {max_rtt:.2f} ms")
        print(f"Average RTT  : {avg_rtt:.2f} ms")
        
        # 2. Metrik Jitter (Adopsi Rumus Selisih Absolut Berurutan)
        jitter = 0
        if len(rtt_list) > 1:
            diffs = [abs(rtt_list[i] - rtt_list[i-1]) for i in range(1, len(rtt_list))]
            jitter = sum(diffs) / len(diffs)
        print(f"Jitter Jaringan: {jitter:.2f} ms")
        
        # 3. Metrik Throughput (Adopsi Rumus Konversi Bit per Detik)
        # Menghitung estimasi total ukuran byte data yang ditransmisikan
        sample_payload_size = len(f"Ping {packets_sent} {time.time()}".encode())
        total_bytes = packets_sent * sample_payload_size
        durasi = t_end - t_start
        throughput = (total_bytes * 8 / 1000) / durasi if durasi > 0 else 0
        print(f"Throughput   : {throughput:.2f} kbps")
    else:
        print("[!] Gagal menghitung RTT, Jitter, dan Throughput karena 100% Packet Loss.")
    print("==================================================")

if __name__ == "__main__":
    while True:
        print("\n=== MENU ADVANCED CLIENT ===")
        print("1. Jalankan Smart HTTP Client (TCP Automated Scraper)")
        print("2. Jalankan Analisis Kualitas Jaringan (UDP QoS Pinger)")
        print("3. Keluar")
        pilihan = input("Pilih menu (1/2/3): ").strip()
        
        if pilihan == "1":
            run_http_client()
        elif pilihan == "2":
            run_udp_pinger()
        elif pilihan == "3":
            print("Keluar dari program client.")
            break
        else:
            print("[!] Pilihan tidak valid.")