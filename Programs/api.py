from flask import Flask, jsonify, request, Response
import sqlite3
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime

app = Flask(__name__)

# Configuration de la base de données
def get_db_connection():
    conn = sqlite3.connect('BVB.db')
    conn.row_factory = sqlite3.Row
    return conn

# Fonction pour convertir les résultats en XML
def convert_to_xml(data):
    root = Element('data')
    for row in data:
        item = SubElement(root, 'item')
        for key in row.keys():
            SubElement(item, key).text = str(row[key])
    return root

# Route pour obtenir toutes les ressources au format XML
@app.route('/api', methods=['GET'])
def get_ressources():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases')
    ressources = cursor.fetchall()
    conn.close()

    # Convertir les résultats en XML
    xml_data = convert_to_xml(ressources)
    # Retourner la réponse avec le type de contenu XML
    return Response(tostring(xml_data), content_type='application/xml')

# Route pour obtenir le champ src_mac au format XML
@app.route('/api/src_mac', methods=['GET'])
def get_src_macs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT src_mac FROM dhcp_leases')
    src_macs = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(src_macs)
    return Response(tostring(xml_data), content_type='application/xml')

# Route pour obtenir les adresses IP sources
@app.route('/api/src_ip', methods=['GET'])
def get_src_ips():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT src_ip FROM dhcp_leases')
    src_ips = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(src_ips)
    return Response(tostring(xml_data), content_type='application/xml')

# Route pour obtenir les adresses IP destinations
@app.route('/api/dst_ip', methods=['GET'])
def get_dst_ips():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT dst_ip FROM dhcp_leases')
    dst_ips = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(dst_ips)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour obtenir les adresses macs destinations
@app.route('/api/dst_mac', methods=['GET'])
def get_dst_macs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT dst_mac FROM dhcp_leases')
    dst_macs = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(dst_macs)
    return Response(tostring(xml_data), content_type='application/xml')

# Route pour obtenir les timestamps des trames
@app.route('/api/timestamp', methods=['GET'])
def get_timestamp():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp FROM dhcp_leases')
    timestamps = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(timestamps)
    return Response(tostring(xml_data), content_type='application/xml')

# Route pour obtenir les types de DHCP
@app.route('/api/dhcp_type', methods=['GET'])
def get_dhcp_types():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT dhcp_type FROM dhcp_leases')
    dhcp_types = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(dhcp_types)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les trames par adresse ip source
@app.route('/api/src_ip/<string:src_ip>', methods=['GET'])
def get_src_ip_by_src_ip(src_ip):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE src_ip = ?', (src_ip,))
    all_src_ips = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_src_ips)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les trames par ip de destination
@app.route('/api/dst_ip/<string:dst_ip>', methods=['GET'])
def get_dst_ip_by_dst_ip(dst_ip):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE dst_ip = ?', (dst_ip,))
    all_dst_ips = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_dst_ips)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les trames par adresse mac destination
@app.route('/api/dst_mac/<string:dst_mac>', methods=['GET'])
def get_dst_macs_by_dst_mac(dst_mac):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE dst_mac = ?', (dst_mac,))
    all_dst_macs = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_dst_macs)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les trames par adresse MAC
@app.route('/api/src_mac/<string:src_mac>', methods=['GET'])
def get_src_macs_by_src_mac(src_mac):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE src_mac = ?', (src_mac,))
    all_src_macs = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_src_macs)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les trames par type de dhcp
@app.route('/api/dhcp_type/<string:dhcp_type>', methods=['GET'])
def get_dhcp_type_by_dhcp_type(dhcp_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE dhcp_type = ?', (dhcp_type,))
    all_dhcp_types = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_dhcp_types)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher des statistiques pour les adresses MAC
@app.route('/api/stats/src_mac', methods=['GET'])
def get_stats_src_macs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT src_mac FROM dhcp_leases')
    all_src_macs = cursor.fetchall()
    xml_data = Element('Statistiques')
    for row in all_src_macs:
        src_mac = row['src_mac']
        cursor.execute('SELECT COUNT(*) FROM dhcp_leases WHERE src_mac = ?', (src_mac,))
        total_frames = cursor.fetchone()[0]
        mac_element = SubElement(xml_data, 'mac')
        mac_element.set('address', src_mac)
        total_frames_element = SubElement(mac_element, 'Nombre_total')
        total_frames_element.text = str(total_frames)
    conn.close()
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les statistiques pour les adresses sources IP
@app.route('/api/stats/src_ip', methods=['GET'])
def get_stats_src_ips():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT src_ip FROM dhcp_leases')
    all_src_ips = cursor.fetchall()
    xml_data = Element('Statistiques')
    for row in all_src_ips:
        src_ip = row['src_ip']
        cursor.execute('SELECT COUNT(*) FROM dhcp_leases WHERE src_ip = ?', (src_ip,))
        total_frames = cursor.fetchone()[0]
        src_ip_element = SubElement(xml_data, 'src_ip')
        src_ip_element.set('address', src_ip)
        total_frames_element = SubElement(src_ip_element, 'Nombre_total')
        total_frames_element.text = str(total_frames)
    conn.close()
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les statistiques pour les adresses destinations IP
@app.route('/api/stats/dst_ip', methods=['GET'])
def get_stats_dst_ips():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT dst_ip FROM dhcp_leases')
    all_dst_ips = cursor.fetchall()
    xml_data = Element('Statistiques')
    for row in all_dst_ips:
        dst_ip = row['dst_ip']
        cursor.execute('SELECT COUNT(*) FROM dhcp_leases WHERE dst_ip = ?', (dst_ip,))
        total_frames = cursor.fetchone()[0]
        dst_ip_element = SubElement(xml_data, 'dst_ip')
        dst_ip_element.set('address', dst_ip)
        total_frames_element = SubElement(dst_ip_element, 'Nombre_total')
        total_frames_element.text = str(total_frames)
    conn.close()
    return Response(tostring(xml_data), content_type='application/xml')
       
# Route pour afficher les statistiques pour tous les types de DHCP
@app.route('/api/stats/dhcp_type', methods=['GET'])
def get_stats_dhcp_types():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT dhcp_type FROM dhcp_leases')
    all_dhcp_types = cursor.fetchall()
    xml_data = Element('Statistiques')
    for row in all_dhcp_types:
        dhcp_type = row['dhcp_type']
        cursor.execute('SELECT COUNT(*) FROM dhcp_leases WHERE dhcp_type = ?', (dhcp_type,))
        total_frames = cursor.fetchone()[0]
        dhcp_type_element = SubElement(xml_data, 'dhcp_type')
        dhcp_type_element.set('type', dhcp_type)
        total_frames_element = SubElement(dhcp_type_element, 'Nombre_total')
        total_frames_element.text = str(total_frames)
    conn.close()
    return Response(tostring(xml_data), content_type='application/xml')
       
# Route pour obtenir les timestamps des trames par ordre croissant
@app.route('/api/timestamp_asc', methods=['GET'])
def get_timestamp_asc():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases ORDER BY datetime(timestamp) ASC')
    timestamps = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(timestamps)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour obtenir les timestamp des trames par ordre décroissant
@app.route('/api/timestamp_desc', methods=['GET'])
def get_timestamp_desc():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases ORDER BY datetime(timestamp) DESC')
    trames = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(trames)
    return Response(tostring(xml_data), content_type='application/xml')

# Fonction pour obtenir les trames entre deux timestamps avec le champ que l'on souhaite avoir pendant le timestamp
@app.route('/api/trames_between', methods=['GET'])
def get_trames_between():
    conn = get_db_connection()
    cursor = conn.cursor()
    start_timestamp = request.args.get('start')
    end_timestamp = request.args.get('end')

    # Obtenir les parties de l'URL pour le champ et la valeur de recherche afin de les utiliser
    field_and_value = request.args.get('field_value')
    if field_and_value:
        field, value = field_and_value.split('/')
    else:
        field, value = None, None

    if start_timestamp and end_timestamp:
        # Obtenir la requête SQL en fonction des timestamps de l'utilisateur
        query = 'SELECT * FROM dhcp_leases WHERE datetime(timestamp) BETWEEN ? AND ?'
        params = (start_timestamp, end_timestamp)

        # Si l'utilisateur utilise un champ et une valeur de recherche on l'ajoute dans la requête
        if field and value:
            query += f' AND {field} = ?'
            params += (value,)
        cursor.execute(query, params)
    else:
        return Response("Il faut un timestamp de début et de fin.", status=400)
    trames = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(trames)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les trames par packet_idx
@app.route('/api/packet_idx/<string:packet_idx>', methods=['GET'])
def get_packet_idx_by_packet_idx(packet_idx):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE packet_idx = ?', (packet_idx,))
    all_packet_idxs = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_packet_idxs)
    return Response(tostring(xml_data), content_type='application/xml')
    
# Route pour afficher les trames par hostname
@app.route('/api/hostname/<string:hostname>', methods=['GET'])
def get_hostname_by_hostname(hostname):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE hostname = ?', (hostname,))
    all_hostnames = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_hostnames)
    return Response(tostring(xml_data), content_type='application/xml')

# Route pour afficher les trames par server_id
@app.route('/api/server_id/<string:server_id>', methods=['GET'])
def get_server_id_by_server_id(server_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE server_id = ?', (server_id,))
    all_server_ids = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_server_ids)
    return Response(tostring(xml_data), content_type='application/xml')

# Route pour afficher les trames par lease_time
@app.route('/api/lease_time/<string:lease_time>', methods=['GET'])
def get_lease_time_by_lease_time(lease_time):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dhcp_leases WHERE lease_time = ?', (lease_time,))
    all_lease_times = cursor.fetchall()
    conn.close()
    xml_data = convert_to_xml(all_lease_times)
    return Response(tostring(xml_data), content_type='application/xml')

# Pour exécuter l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
