# Documentation développeur

## 1. Présentation du projet

Dans le cadre de la SAE501 il nous a été demandé moi et mes collègues le développement d'un logiciel permettant de surveiller l'attribution, le renouvellement et l'expiration des baux DHCP dans un réseau local. Cette application logiciel est développé en Python, offrant une interface graphique, une base de données pour stocker les informations capturées, et une API REST pour permettre l'accès et la gestion des données.

## 2. Fonctionnalités principales

L'application est divisé en 3 partie comme on peut le voir ci-dessous :

#### Capture de trames DHCP :

- Surveillance en temps réel des trames DHCP pour détecter les événements d'attribution, de renouvellement et d'expiration des baux.

- Affichage détaillé des informations contenues dans chaque trame capturée.

#### API REST :

- Exposition d'une API REST pour permettre l'accès aux données capturées.

#### Interface Graphique :

- Interface utilisateur intuitive permettant de visualiser les informations sur les baux DHCP.

- Fonctionnalités de filtrage et de recherche pour faciliter l'exploration des données.

## 3. Partie capture de trames DHCP

Pour ma part je me suis occupé du développement de l'application d'écoute du réseau et du déploiement de l'application entière c'est à dire avec le lancement des différentes partie. Je vais dans cette documentation détaillé en profondeur les différentes fonction du code de capture de trames et du déploiement.

Le script de capture de trame est codé avec Python et utilise la bibliothèque Scapy pour capturer et analyser les trames DHCP sur un réseau local. Je vais par la suite détaillé fonction par fonction son fonctionnement.

### Code capture de trames (sniffer.py) sous Python

```python
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
```

### Fonction `decode_option(option_value)`

```python
def decode_option(option_value):
    if isinstance(option_value, bytes):
        try:
            return option_value.decode('utf-8')
        except UnicodeDecodeError:
            return option_value.decode('latin-1', errors='replace')
    return option_value
```

Cette fonction prend une valeur d'option DHCP en binaire en entrée et la décode en une chaîne de caractères en utilisant l'encodage UTF-8 ou Latin-1 avec gestion des erreurs. Elle est utilisée pour décoder les valeurs des options DHCP qui peuvent être présentes dans les paquets.

J'ai ajouté cette fonction après avoir rencontré un problème pendant mes test j'ai remarqué qu'il y avait des paquets que je ne pouvais pas capturer car il y avait des caractères en UTF-8 qui n'était pas décodable.

### Fonction `create_db()`

```python
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
```

### Fonction `insert_into_db(...)`

```python
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
```

Cette fonction prend plusieurs paramètres liés à une trame DHCP capturée et les insère dans la base de données SQLite. 

Voici ce que chaque paramètre représente :

- `src_mac`: Adresse MAC source

- `src_ip`: Adresse IP source

- `dst_mac`: Adresse MAC de destination

- `dst_ip`: Adresse IP de destination

- `timestamp`: Horodatage de la capture

- `dhcp_type`: Type de trame DHCP (Discover, Offer, Request, etc.)

- `packet_idx`: Identifiant du paquet IP (exemple: packet[IP].id)

- `hostname`: Nom d'hôte (si disponible dans les options DHCP)

- `server_id`: Identifiant du serveur DHCP (si disponible dans les options DHCP)

- `lease_time`: Durée du bail DHCP (si disponible dans les options DHCP)

### Fonction `check_expired_leases()`

```python
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
```

Cette fonction parcourt les baux DHCP enregistrés dans le dictionnaire `dhcp_leases`. Pour chaque bail expiré (comparaison avec l'heure actuelle), elle l'ajoute à une liste `expired_leases`. Ensuite, elle affiche les informations de chaque bail expiré et les supprime du dictionnaire `dhcp_leases`.

### Fonction `handle_dhcp_packet(packet)`

```python
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
```

Cette fonction est appelée chaque fois qu'une trame DHCP est capturée. Elle analyse le type de trame DHCP (Discover, Offer, Request, etc.) en utilisant les options DHCP et extrait les informations pertinentes telles que l'adresse MAC source, l'adresse IP source, l'adresse MAC de destination, l'adresse IP de destination, le type de trame DHCP, le nom d'hôte, l'identifiant du serveur DHCP, et la durée du bail DHCP. Ces informations sont ensuite utilisées pour mettre à jour le dictionnaire `dhcp_leases` et insérer les données dans la base de données avec la fonction `insert_into_db()`.

### Fonction `start_dhcp_capture(interface)`

```python
def start_dhcp_capture(interface):
    try:
        print(f"Starting DHCP capture on interface {interface}...")
#        sniff(filter="udp and (port 67 or port 68) and (udp[8:1] = 1 or udp[8:1] = 2 or udp[8:1] = 3 or udp[8:1] = 5)", prn=handle_dhcp_packet, iface=interface, store=False)
        sniff(filter="udp and (port 67 or port 68)", prn=handle_dhcp_packet, iface=None, store=False)
    except KeyboardInterrupt:
        print("Capture stopped.")
```

Cette fonction utilise la bibliothèque Scapy pour démarrer la capture des trames DHCP sur une interface réseau spécifiée. Elle filtre les trames en fonction des ports UDP 67 et 68, ainsi que du type de message DHCP. La fonction `handle_dhcp_packet()` est utilisée comme fonction de rappel pour chaque trame capturée.

### Fonction `__main__`

```python
if __name__ == "__main__":
    interface = "any"

    create_db()  # Créer la base de données et la table DHCP_leases
    start_dhcp_capture(interface)
```

Cette fonction vérifie si le script est exécuté en tant que programme principal (et non en tant que module importé) et commence le processus en appelant `create_db()` pour initialiser la base de données, puis en démarrant la capture avec `start_dhcp_capture()` sur l'interface spécifiée.

## 4. Partie déploiement

Comme je l'avais expliqué précedemment mon objectif était de développer un programme de capture de trame en python mais aussi de déployer l'ensemble des programmes crée par mon équipe. Pour cela j'ai opté pour une architecture basée sur Docker et Docker Compose. L'ensemble du système est conçu pour déployé facilement l'application et offre une solution complète pour la capture de trames, l'API, et l'interface graphique.

### Structure du projet

Le dossier principal du projet, contient les éléments essentiels pour le déploiement du système. Voici une description de la structure du projet :

- docker-compose.yml : Fichier de configuration Docker Compose qui définit les services, réseaux, et volumes nécessaires pour le déploiement de l'application.

- requirements.txt : Fichier spécifiant les dépendances Python nécessaires pour les différents composants de l'application.

Le dossier contient également deux sous-dossiers :

- Dockerfiles :

    - Dockerfile-api : Fichier de configuration pour la construction du conteneur regroupant l'API et le sniffer. Il inclut les dépendances spécifiques à ces composants.

    - Dockerfile-tkinter : Fichier de configuration pour la construction du conteneur de l'interface graphique. Il inclut les dépendances nécessaires à l'interface.

- Programs :

    - sniffer.py : Programme Python pour la capture de trames DHCP réseaux

    - api.py : Programme Python qui implémente l'API pour interagir avec l'application.
    
    - interface.py : Programme Python pour l'interface graphique de l'application.

### Fichier docker-compose.yml

```yaml
version: '3'
services:
  dockerfile-api:
    build:
      context: /home/test/Bureau/SAE501-502-BVB-Capture-de-trame-Etudiant-n-1
      dockerfile: Dockerfiles/Dockerfile-api
    network_mode: host
    ports:
      - "5000:5000"
    environment:
      REGISTRY_HTTP_TLS_DISABLE: "true"

  dockerfile-tkinter:
    build:
      context: /home/test/Bureau/SAE501-502-BVB-Capture-de-trame-Etudiant-n-1
      dockerfile: Dockerfiles/Dockerfile-tkinter
    stdin_open: true
    tty: true
    environment:
      - DISPLAY=$DISPLAY
#      - XHOST_IP=172.19.0.2
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
    network_mode: host
```

Le fichier docker-compose que j'ai crée définit deux services, `dockerfile-api` et `dockerfile-tkinter`, dans mon fichier de projet SAE.

Je vais par la suite détaillé les fonctionnalités de chaque services :

#### Service `dockerfile-api`

- Build du conteneur :

    ```yaml
    dockerfile-api:
    build:
      context: /home/test/Bureau/SAE501-502-BVB-Capture-de-trame-Etudiant-n-1
      dockerfile: Dockerfiles/Dockerfile-api
    ```

    - Le service utilise le fichier `Dockerfile-api` situé dans le dossier `Dockerfiles` pour construire le conteneur. Le chemin complet vers le contexte du build est spécifié dans la section `context`.

- Network mode :

    ```yaml
    network_mode: host
    ```
   
    - Le service utilise le mode de réseau de l'hôte. 
    Cela va permettre au conteneur de partager le réseau de l'hôte, ce qui peut être utile pour accéder à des services fonctionnant sur l'hôte directement.

- Ports exposés :

    ```yaml
    ports:
      - "5000:5000"
    ```

    - Le port 5000 du conteneur est exposé sur le port 5000 du PC hôte. Cela permet d'accéder à l'API exposée par ce service depuis l'hôte.

- Variables d'environnement :

    ```yaml
    environment:
      REGISTRY_HTTP_TLS_DISABLE: "true"
    ```

    - La variable d'environnement `REGISTRY_HTTP_TLS_DISABLE` est définie sur "true" afin de désactiver le support TLS dans le registre Docker. J'ai du ajouter cette variable pour pouvoir accéder à l'API en HTTP avec l'adresse suivante http://IP:5000/api.

#### Service `dockerfile-tkinter`

- Build du conteneur :

    ```yaml
    dockerfile-tkinter:
    build:
      context: /home/test/Bureau/SAE501-502-BVB-Capture-de-trame-Etudiant-n-1
      dockerfile: Dockerfiles/Dockerfile-tkinter
    ```

    - Comme pour le service précédent, ce service utilise le fichier `Dockerfile-tkinter` situé dans le dossier `Dockerfiles` pour construire le conteneur.

- Mode interactif :

    ```yaml
    stdin_open: true
    tty: true
    ```

    - Les options `stdin_open` et `tty` sont définies en `true` pour permettre une interaction avec le conteneur, ce qui est nécessaire pour les applications GUI comme Tkinter.

- Variables d'environnement :

    ```yaml
    environment:
      - DISPLAY=$DISPLAY
    ```

    - J'ai ajouté la variable d'environnement `DISPLAY` est définie pour permettre à l'application GUI d'afficher ses fenêtres graphiques sur l'hôte. C'est une option importante car sans cela pas d'affichage de l'interface.

- Volumes pour l'affichage X11 :

    ```yaml
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
    ```

    - Lorsqu'on utilise des conteneurs Docker pour exécuter des applications graphiques basées sur X11 comme Tkinter, il fallait que je monte un volume X11 pour permettre au conteneur d'accéder au serveur X11 du PC hôte. Cela est nécessaire dans mon cas car je souhaitais exécuter mon interface graphique dans un conteneur Docker tout en affichant l'interface utilisateur sur le bureau de du PC hôte.

- Network mode :

     ```yaml
    network_mode: host
    ```

    - Comme le service précédent, celui-ci utilise également le mode de réseau de l'hôte.


#### REMARQUES

Les chemins complets (`context` et `dockerfile`) dans le fichier docker-compose doivent être adaptés à la structure de répertoires et à la localisation réelle des fichiers Dockerfile.

### Fichier requirements.txt

    Flask==2.1.0
    Werkzeug==2.0.2
    scapy==2.4.5
    requests==2.26.0
    matplotlib==3.4.3
    
Le fichier requirements.txt est utilisé pour spécifier les dépendances Python nécessaires pour pouvoir exécuter l'application. Chaque ligne du fichier représente une bibliothèque ou un module Python spécifique ainsi que sa version.

### Fichier Dockerfile-api

    FROM python:3.9

    RUN apt-get update && apt-get install -y libpcap-dev && rm -rf /var/lib/apt/lists/*

    COPY Programs/sniffer.py /app/sniffer.py

    COPY Programs/api.py /app/api.py

    WORKDIR /app

    COPY requirements.txt /app/requirements.txt

    RUN pip --no-cache-dir install -r requirements.txt

    EXPOSE 5000

    CMD ["sh", "-c", "python3 sniffer.py & python3 api.py"]

Ce fichier Dockerfile est utilisé pour construire une image Docker qui servira de base à mon application de capture de trames réseau et d'API. 

Je vais analyser ce fichier en détail pour en expliquer toutes les subtilités :

    FROM python:3.9

Cette ligne spécifie l'image de base à utiliser. Ici, elle utilise l'image officielle Python 3.9. Cela signifie que mon conteneur sera basé sur une image Python, avec Python 3.9 d'installé.

    RUN apt-get update && apt-get install -y libpcap-dev && rm -rf /var/lib/apt/lists/*

Cette ligne met à jour le système d'exploitation à l'intérieur du conteneur, installe le paquet libpcap-dev (qui est utilisé pour la capture de paquets avec Scapy) puis supprime les listes des paquets téléchargés. J'ai fait cela car ça permet de garder l'image du conteneur plus légère en éliminant les fichiers temporaires.

    COPY Programs/sniffer.py /app/sniffer.py

Cette instruction va copier le script Python de capture de trames (`sniffer.py`) depuis le répertoire local `Programs` vers le répertoire `/app` à l'intérieur du conteneur.

    COPY Programs/api.py /app/api.py

De la même manière, cette instruction copie le script Python de l'API (`api.py`) depuis le répertoire local `Programs` vers le répertoire `/app` à l'intérieur du conteneur.

    WORKDIR /app

Cette ligne définit le répertoire de travail à l'intérieur du conteneur comme étant `/app`. Cela signifie que toutes les commandes suivantes seront exécutées dans ce répertoire.

    COPY requirements.txt /app/requirements.txt

Comme précédemment cette ligne copie le fichier requirements.txt depuis le répertoire local vers le répertoire `/app` à l'intérieur du conteneur.

    RUN pip --no-cache-dir install -r requirements.txt

Cette ligne utilise `pip` pour installer les dépendances Python spécifiées dans le fichier `requirements.txt`. L'option `--no-cache-dir` indique à pip de ne pas utiliser le cache pour la récupération des paquets, ce qui est utile pour réduire la taille de l'image.

    EXPOSE 5000

Cette ligne expose le port 5000 à l'intérieur du conteneur. Cela n'ouvre pas le port sur l'hôte, mais indique que l'application à l'intérieur du conteneur utilisera ce port pour écouter les connexions.

    CMD ["sh", "-c", "python3 sniffer.py & python3 api.py"]

Cette ligne spécifie la commande qui sera exécutée lorsque le conteneur sera démarré. Elle lance le script de capture de trames en arrière-plan (`python3 sniffer.py`) suivi de l'exécution de l'API (`python3 api.py`).

### Fichier Dockerfile-tkinter

    
    FROM python:3.9-slim

    RUN apt-get update && apt-get install -y iputils-ping

    COPY Programs/interface.py /app/interface.py

    WORKDIR /app

    RUN apt-get update && apt-get install -y python3-tk

    COPY requirements.txt /app/requirements.txt

    RUN pip --no-cache-dir install -r requirements.txt

    CMD ["python3", "interface.py"]

Ce fichier Dockerfile est utilisé pour construire une image Docker qui servira de base à mon interface graphique.

    FROM python:3.9-slim

Comme il a été vu précédemment, cette ligne spécifie l'image de base à utiliser.

    RUN apt-get update && apt-get install -y iputils-ping

Cette ligne met à jour le système d'exploitation du conteneur et installe le paquet `iputils-ping`, qui est utile pour le débogage ou la vérification de la connectivité réseau à l'intérieur du conteneur.

    COPY Programs/interface.py /app/interface.py

Cette ligne va copier le programme `interface.py` situé dans le répertoire `Programs` vers le répertoire `/app` à l'intérieur du conteneur.

    WORKDIR /app

Définition du répertoire de travail dans le conteneur. Toutes les commandes suivantes seront exécutées dans ce répertoire.

    RUN apt-get update && apt-get install -y python3-tk

Mise à jour du conteneur et installe le paquet python3-tk, qui est nécessaire pour les applications Tkinter.

    COPY requirements.txt /app/requirements.txt

Copie du fichier `requirements.txt` sur le répertoire du conteneur `/app`.

    RUN pip --no-cache-dir install -r requirements.txt

Installation des dépendances Python spécifié sur le fichier `requirements.txt`.

    CMD ["python3", "interface.py"]

Spécification de la commande qui sera exécutée lorsque le conteneur sera démarré. Elle lance l'application Tkinter en exécutant le script interface.py.

Se référer au [README](https://github.com/matheobalazuc/SAE501-502-BVB/blob/Capture-de-trame-Etudiant-n%C2%B01/README.md) (guide d'installation) pour le déploiement de l'application.