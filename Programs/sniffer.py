from scapy.all import *
import sqlite3
from datetime import datetime, timedelta

db_file = "BVB.db"

dhcp_leases = {}
dhcp_server_ip = "10.202.255.254"

def decode_option(option_value):
    if isinstance(option_value, bytes):
        try:
            return option_value.decode('utf-8')
        except UnicodeDecodeError:
            return option_value.decode('latin-1', errors='replace')
    return option_value

def create_db():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS dhcp_leases (
                      src_mac TEXT,
                      src_ip TEXT, 
                      dst_mac TEXT,
                      dst_ip TEXT, 
                      timestamp TEXT, 
                      dhcp_type TEXT,
                      packet_idx INT,
                      hostname TEXT,
                      server_id TEXT,
                      lease_time INT)''')
    conn.commit()
    conn.close()

def insert_into_db(src_mac, src_ip, dst_mac, dst_ip, timestamp, dhcp_type, packet_idx, hostname, server_id, lease_time):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        insert_query = "INSERT INTO dhcp_leases (src_mac, src_ip, dst_mac, dst_ip, timestamp, dhcp_type, packet_idx, hostname, server_id, lease_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        data = (src_mac, src_ip, dst_mac, dst_ip, timestamp, dhcp_type, packet_idx, hostname, server_id, lease_time)
        cursor.execute(insert_query, data)
        conn.commit()

    except Exception as e:
        print(f"Erreur lors de l'insertion dans la base de données : {e}")
    finally:
        if conn:
            conn.close()

def check_expired_leases():
    current_time = datetime.now()
    expired_leases = []
    for _, lease_info in dhcp_leases.items():
        if current_time > lease_info['expiration']:
            expired_leases.append(_)
    
    if expired_leases:
        print("Baux expirés :")
        for client_mac in expired_leases:
            lease_info = dhcp_leases[client_mac]
            print(f"Source MAC: {client_mac}, Source IP: {lease_info['src_ip']}, Destination MAC: {client_mac}, Destination IP: {lease_info['dst_ip']}, Timestamp: {lease_info['timestamp']}, DHCP Type: {lease_info['dhcp_type']}, Packet IDX: {lease_info['packet_idx']}, Hostname: {lease_info['hostname']}, Server ID: {lease_info['server_id']}, Lease Time: {lease_info['lease_time']}")
            del dhcp_leases[client_mac]

def handle_dhcp_packet(packet):
    if packet.haslayer(DHCP):
        dhcp_type = None
        packet_idx = packet[IP].id

        if packet[DHCP].options[0][1] == 1:  # DHCP Discover
            dhcp_type = "Discover"
        elif packet[DHCP].options[0][1] == 2:  # DHCP Offer
            dhcp_type = "Offer"
        elif packet[DHCP].options[0][1] == 3:  # DHCP Request
            dhcp_type = "Request"
        elif packet[DHCP].options[0][1] == 5:  # DHCP Ack
            dhcp_type = "Ack"
        elif packet[DHCP].options[0][1] == 6:  # DHCP Nak
            dhcp_type = "Nak"
        elif packet[DHCP].options[0][1] == 7:  # DHCP Decline
            dhcp_type = "Decline"
        elif packet[DHCP].options[0][1] == 8:  # DHCP Release
            dhcp_type = "Release"
        elif packet[DHCP].options[0][1] == 9:  # DHCP Inform
            dhcp_type = "Inform"
            
        if dhcp_type is not None:
            print(f"Captured DHCP {dhcp_type} packet")
            print(packet.show())  # Ajout de cette ligne pour afficher les détails du paquet

            src_mac = packet[Ether].src
            src_ip = packet[IP].src
            dst_mac = packet[Ether].dst
            dst_ip = packet[IP].dst
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            client_id = None
            hostname = None
            server_id = None
            lease_time = None

            for option in packet[DHCP].options:
                if option[0] == 'client_id':
                    client_id = decode_option(option[1])
                elif option[0] == 'hostname':
                    hostname = decode_option(option[1])
                elif option[0] == 'server_id':
                    server_id = decode_option(option[1])
                elif option[0] == 'lease_time':
                    lease_time = int.from_bytes(option[1], byteorder='big') if isinstance(option[1], bytes) else option[1]

            expiration_time = None
            if lease_time is not None:
                expiration_time = datetime.now() + timedelta(seconds=lease_time)

            dhcp_leases[src_mac] = {
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'timestamp': timestamp,
                'dhcp_type': dhcp_type,
                'packet_idx': packet_idx,
                'hostname': hostname,
                'server_id': server_id,
                'lease_time': lease_time,
                'expiration': expiration_time
            }

            insert_into_db(src_mac, src_ip, dst_mac, dst_ip, timestamp, dhcp_type, packet_idx, hostname, server_id, lease_time)

def start_dhcp_capture(interface):
    try:
        print(f"Starting DHCP capture on interface {interface}...")
#        sniff(filter="udp and (port 67 or port 68) and (udp[8:1] = 1 or udp[8:1] = 2 or udp[8:1] = 3 or udp[8:1] = 5)", prn=handle_dhcp_packet, iface=interface, store=False)
        sniff(filter="udp and (port 67 or port 68)", prn=handle_dhcp_packet, iface=None, store=False)
    except KeyboardInterrupt:
        print("Capture stopped.")

if __name__ == "__main__":
    interface = "any"

    create_db()  # Créer la base de données et la table DHCP_leases
    start_dhcp_capture(interface)
