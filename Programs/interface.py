import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import requests
import xml.etree.ElementTree as ET
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from collections import Counter
from matplotlib.dates import date2num
from tkinter import filedialog

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualisation de capture de trames")
        self.alert_data = []
        self.alert_rows = set()

        # Création de l'onglet pour les alertes
        self.notebook = ttk.Notebook(root)                      
        self.notebook.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

         # Onglet pour le tableau principal et les boutons de filtre
        frame_tableau = ttk.Frame(self.notebook)
        self.notebook.add(frame_tableau, text="Accueil")

        # Onglet pour les alertes
        frame_alertes = ttk.Frame(self.notebook)
        self.notebook.add(frame_alertes, text="Alertes")

        # Bouton Afficher le graphique
        self.show_graph_button = tk.Button(frame_alertes, text="Afficher le graphique", command=self.show_graphique)
        self.show_graph_button.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Création du cadre pour le compteur d'alertes
        self.alert_count_frame = ttk.Frame(frame_alertes)
        self.alert_count_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # Configuration des poids des colonnes et lignes pour le redimensionnement
        root.columnconfigure(3, weight=1)

        # Créer le cadre pour afficher le nombre de requêtes DHCP par type dans frame_tableau
        self.dhcp_count_frame = ttk.Frame(frame_tableau)
        self.dhcp_count_frame.grid(row=2, column=8, padx=0, pady=10, sticky="nsew")

        # Étiquettes pour le nombre de requêtes par type
        self.dhcp_labels = []
        for i, dhcp_type in enumerate(["Discover", "Offer", "Request", "Ack", "Nak", "Decline", "Release", "Inform"]):
            label = ttk.Label(self.dhcp_count_frame, text=f"{dhcp_type}: 0",font=('Arial', 13, 'bold'))
            label.grid(row=i, column=2, padx=0, pady=15, sticky="sw")
            self.dhcp_labels.append(label)

        self.dhcp_count_frame.columnconfigure(1, weight=1)
       
        
        # Création du tableau pour les alertes
        self.tree_alertes = ttk.Treeview(frame_alertes, columns=("Date d'analyse de la trame", "Description", "Motif", "Source MAC", "Source IP", "Destination MAC", "Destination IP", "DHCP Type", "Packet Index", "Hostname", "Server ID", "Lease Time"), show="headings")
        self.tree_alertes.heading("Date d'analyse de la trame", text="Date de détection de la trame")
        self.tree_alertes.heading("Description", text="Description")
        self.tree_alertes.heading("Motif", text="Motif")
        self.tree_alertes.heading("Source MAC", text="Source MAC")
        self.tree_alertes.heading("Source IP", text="Source IP")
        self.tree_alertes.heading("Destination MAC", text="Destination MAC")
        self.tree_alertes.heading("Destination IP", text="Destination IP")
        self.tree_alertes.heading("DHCP Type", text="DHCP Type")
        self.tree_alertes.heading("Packet Index", text="Packet Index")
        self.tree_alertes.heading("Hostname", text="Hostname")
        self.tree_alertes.heading("Server ID", text="Server ID")
        self.tree_alertes.heading("Lease Time", text="Lease Time")
        self.tree_alertes.grid(row=0, column=0, padx=10, pady=50, sticky="nsew")

        # Lier la fonction show_alert_details pour les éléments avec le 'alert'
        self.tree_alertes.tag_bind('alert', '<ButtonRelease-1>', self.show_alert_details)

        # Bouton Quitter
        quit_button = tk.Button(root, text="Quitter", command=root.destroy)
        quit_button.grid(row=4, column=2, padx=10, pady=10, sticky="se")

        # Création du tableau pour les trames
        self.tree = ttk.Treeview(frame_tableau, columns=("Source MAC", "Source IP", "Destination MAC", "Destination IP", "Timestamp", "DHCP Type", "Packet Index", "Hostname", "Server ID", "Lease Time"), show="headings")
        self.tree.heading("Source MAC", text="Source MAC")
        self.tree.heading("Source IP", text="Source IP")
        self.tree.heading("Destination MAC", text="Destination MAC")
        self.tree.heading("Destination IP", text="Destination IP")
        self.tree.heading("Timestamp", text="Timestamp")
        self.tree.heading("DHCP Type", text="DHCP Type")
        self.tree.heading("Packet Index", text="Packet Index")
        self.tree.heading("Hostname", text="Hostname")
        self.tree.heading("Server ID", text="Server ID")
        self.tree.heading("Lease Time", text="Lease Time")
        self.tree.grid(row=2, column=0, padx=10, pady=10, columnspan=4, sticky="nsew")
        
        self.tree.tag_bind('alert', '<ButtonRelease-1>', self.show_frame_details)
        self.tree.bind('<ButtonRelease-1>', self.show_frame_details)

        # Barre de recherche
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_tree)
        self.search_entry = ttk.Entry(frame_tableau, textvariable=self.search_var, width=20)
        self.search_entry.grid(row=0, column=0, padx=160, pady=10, sticky="w")

        # Texte barre de recherche
        ttk.Label(frame_tableau, text="Options de recherches :").grid(row=0, column=0, padx=0, pady=10, sticky="w")

        # Bouton Détection d'Alertes
        detect_button = tk.Button(frame_tableau, text="Analyser la capture", command=self.detect_alerts)
        detect_button.grid(row=0, column=8, padx=10, pady=10, sticky="e")

        # Menu déroulant pour le filtrage par type de DHCP
        dhcp_types = ["Discover", "Offer", "Request", "Ack", "Nak", "Decline", "Release", "Inform"]
        self.dhcp_filter_var = tk.StringVar()
        self.dhcp_filter_var.set("Tous")  # Default value
        dhcp_filter_menu = ttk.Combobox(frame_tableau, textvariable=self.dhcp_filter_var, values=["Tous"] + dhcp_types)
        dhcp_filter_menu.grid(row=1, column=0, padx=100, pady=10, sticky="w")
        dhcp_filter_menu.bind("<<ComboboxSelected>>", self.update_tree)
        ttk.Label(frame_tableau, text="Filtres DHCP :").grid(row=1, column=0, padx=0, pady=10, sticky="w")

        # Menu déroulant pour le filtrage par date
        date_filters = ["Toutes", "Dernières 10 minutes", "Dernière heure", "Dernières 24 heures", "Dernière semaine", "Dernier mois"]
        self.date_filter_var = tk.StringVar()
        self.date_filter_var.set("Toutes")  # Valeur par défaut
        ttk.Label(frame_tableau, text="Filtres Date :").grid(row=1, column=1, padx=10, pady=10, sticky="w")
        date_filter_menu = ttk.Combobox(frame_tableau, textvariable=self.date_filter_var, values=date_filters)
        date_filter_menu.grid(row=1, column=1, padx=100, pady=10, sticky="w")
        date_filter_menu.bind("<<ComboboxSelected>>", self.update_tree)
    
        # Configuration des poids des colonnes et lignes pour le redimensionnement
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)
        root.rowconfigure(2, weight=1)
        frame_alertes.columnconfigure(0, weight=1)
        frame_alertes.rowconfigure(0, weight=1)
        frame_tableau.columnconfigure(0, weight=1)
        frame_tableau.rowconfigure(2, weight=1)

        # Remplissage initial du tableau
        self.update_tree()    

        # Ajout de barres de défilement au tableau principal
        y_scrollbar = ttk.Scrollbar(frame_tableau, orient="vertical", command=self.tree.yview)
        y_scrollbar.grid(row=2, column=5, sticky="ns")
        x_scrollbar = ttk.Scrollbar(frame_tableau, orient="horizontal", command=self.tree.xview)
        x_scrollbar.grid(row=3, column=0, columnspan=3, sticky="ew")

        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Ajout de barres de défilement au tableau d'alertes
        y_scrollbar_alertes = ttk.Scrollbar(frame_alertes, orient="vertical", command=self.tree_alertes.yview)
        y_scrollbar_alertes.grid(row=0, column=1, sticky="w")
        x_scrollbar_alertes = ttk.Scrollbar(frame_alertes, orient="horizontal", command=self.tree_alertes.xview)
        x_scrollbar_alertes.grid(row=1, column=0, sticky="ew")

        self.tree_alertes.configure(yscrollcommand=y_scrollbar_alertes.set, xscrollcommand=x_scrollbar_alertes.set)

        # Ajouter un curseur pour le tableau principal
        self.tree.bind("<Up>", lambda event: self.scroll_tree(event, -1))
        self.tree.bind("<Down>", lambda event: self.scroll_tree(event, 1))

        # Ajouter un curseur pour le tableau d'alertes
        self.tree_alertes.bind("<Up>", lambda event: self.scroll_tree_alertes(event, -1))
        self.tree_alertes.bind("<Down>", lambda event: self.scroll_tree_alertes(event, 1))     

        # Bouton pour enregistrer la capture de trame en fichier texte
        save_button = tk.Button(frame_tableau, text="Enregistrer la capture", command=self.save_capture)
        save_button.grid(row=0, column=9, padx=10, pady=10, sticky="e")
  

    def convert_timestamp(self, timestamp_str):
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            return timestamp
        except ValueError:
            return None

    def update_tree(self, *args):
        # Effacer les données actuelles dans le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Récupération API 
        api_url = "http://10.202.7.1:5000/api"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            # Réponse XML
            root = ET.fromstring(response.text)
            
            # Récupérer la valeur de filtre DHCP
            dhcp_type_filter = self.dhcp_filter_var.get()

            # Récupérer la valeur de recherche
            search_term = self.search_var.get().lower()
            
             # Récupérer la valeur de filtre de date
            date_filter = self.date_filter_var.get()

            # Compteur pour le nombre de requêtes par type
            dhcp_count = {"Discover": 0, "Offer": 0, "Request": 0, "Ack": 0, "Nak": 0, "Decline": 0, "Release": 0, "Inform": 0}
            for item in root.findall(".//item"):
                src_mac, src_ip, dst_mac, dst_ip, timestamp, dhcp_type, packet_idx, hostname, server_id, lease_time = self.get_frame_values(item)
                # Mettre à jour le compteur de requêtes DHCP par type
                dhcp_count[dhcp_type] += 1
                # Filtrer par type DHCP
                if self.filter_by_dhcp_type(dhcp_type, dhcp_type_filter):
                    # Filtrer par recherche
                    if self.filter_by_search_term(search_term, src_mac, src_ip, dst_mac, dst_ip, timestamp, dhcp_type, packet_idx, hostname, server_id, lease_time):
                        # Filtrer par date
                       if self.filter_by_date(timestamp, date_filter):
                            # Ajouter des données au tableau
                            self.tree.insert("", "end", values=(src_mac, src_ip, dst_mac, dst_ip, timestamp, dhcp_type, packet_idx, hostname, server_id, lease_time))
                            # Mettre à jour les étiquettes pour afficher le nombre de requêtes par type
            for i, dhcp_type in enumerate(["Discover", "Offer", "Request", "Ack", "Nak", "Decline", "Release", "Inform"]):
                self.dhcp_labels[i]["text"] = f"{dhcp_type}: {dhcp_count[dhcp_type]}"
    
    def get_frame_values(self, item):
        # Récupérer les valeurs d'une trame à partir de l'élément XML
        src_mac = item.find("src_mac").text
        src_ip = item.find("src_ip").text
        dst_mac = item.find("dst_mac").text
        dst_ip = item.find("dst_ip").text
        timestamp = item.find("timestamp").text
        dhcp_type = item.find("dhcp_type").text
        packet_idx = item.find("packet_idx").text
        hostname = item.find("hostname").text
        server_id = item.find("server_id").text
        lease_time = item.find("lease_time").text

        return src_mac, src_ip, dst_mac, dst_ip, timestamp, dhcp_type, packet_idx, hostname, server_id, lease_time

    def filter_by_dhcp_type(self, dhcp_type, dhcp_type_filter):
        # Filtrer par type DHCP
        return dhcp_type_filter == "Tous" or dhcp_type == dhcp_type_filter

    def filter_by_search_term(self, search_term, *columns):
        # Filtrer par recherche
        return not search_term or any(search_term in col.lower() for col in columns)

    def filter_by_date(self, timestamp, date_filter):
        # Filtrer par date
        if date_filter == "Toutes":
            return True
        elif date_filter == "Dernières 10 minutes": 
            return datetime.now() - datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") < timedelta(minutes=10)
        elif date_filter == "Dernière heure": 
            return datetime.now() - datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") < timedelta(hours=1)
        elif date_filter == "Dernières 24 heures": 
            return datetime.now() - datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") < timedelta(hours=24)
        elif date_filter == "Dernière semaine":
            return datetime.now() - datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") < timedelta(weeks=1)
        elif date_filter == "Dernier mois":
            return datetime.now() - datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") < timedelta(days=30)
        else:
            return True
        
    def apply_date_filter(self):
        start_date_str = self.start_date_var.get()
        end_date_str = self.end_date_var.get()

        if not start_date_str or not end_date_str: 
            return

        start_date = self.convert_timestamp(start_date_str)
        end_date = self.convert_timestamp(end_date_str)

        if not start_date or not end_date:
            return
    
        
    def detect_alerts(self):
    # Effacer les données actuelles dans le tableau d'alertes
        for item in self.tree_alertes.get_children():
            self.tree_alertes.delete(item)
        
        if hasattr(self, 'graphique_frame'): # Graphique
            self.graphique_frame.destroy()
    # Récupération API 
        api_url = "http://10.202.7.1:5000/api"
        response = requests.get(api_url)
    
        if response.status_code == 200:
        # Réponse XML
            root = ET.fromstring(response.text)
        
            alert_detected = False

            for item in root.findall(".//item"):
                frame_values = self.get_frame_values(item)
                alert_type, alert_description = self.analyze_frame(frame_values)
                if alert_type is not None:
               # Ajouter l'alerte détectée au tableau d'alertes
                    self.tree_alertes.insert("", "end", values=(frame_values[4], alert_type, alert_description, frame_values[0], frame_values[1], frame_values[2], frame_values[3], frame_values[5], frame_values[6], frame_values[7], frame_values[8], frame_values[9]), tags=('alert',))

                # Ajouter un 'alert' à la trame dans le tableau principal
                    self.tree.insert("", "end", values=frame_values, tags=('alert',))
                    self.alert_data.extend([frame_values[1], frame_values[8]]) #On renseigne pour le type d'alertes

                print(f"Alerte détectée dans une trame à {frame_values[4]} avec comme Source MAC {frame_values[0]}!")
                alert_detected = True
            
            if alert_detected:
            # Mettre en rouge les lignes dans le tableau principal qui ont eu une alerte
                self.color_rows_with_alerts()
        # Affiche le compteur d'alertes
                self.show_alert_count()

            if not alert_detected:
                print("Aucune alerte détectée.")

    def analyze_frame(self, frame_values):
        alert_type = None
        alert_description = None

        if frame_values[8] == "192.168.1.11":
            alert_type = "Server ID Danger"
            alert_description = "L'ID du Server est inconnu"
        elif frame_values[1] == "172.20.10.4":
            alert_type = "Source IP Danger"
            alert_description = "Mauvaise plage d'IP"
        return alert_type, alert_description

    def add_alert_to_table(self, alert_values):
        # Ajouter une alerte au tableau principal
        self.tree_alertes.insert('', 'end', values=alert_values)

    def show_alert_details(self, event):
        selected_item_alertes = self.tree_alertes.selection()
        print("Selected Item:", selected_item_alertes)  # Vérifiez si l'élément est correctement sélectionné
        if selected_item_alertes:
            item_values_alertes = self.tree_alertes.item(selected_item_alertes, 'values')
            print("Item Values:", item_values_alertes)  # Vérifiez les valeurs de l'élément

            # Créer des étiquettes pour afficher tous les détails
            details_window = tk.Toplevel(self.root)
            details_window.title("Détails de la trame - Alertes")

            frame_details_alertes = {
                "Date d'analyse de la trame": item_values_alertes[0],
                'Description': item_values_alertes[1],
                'Motif': item_values_alertes[2],
                'Source MAC': item_values_alertes[3],
                'Source IP': item_values_alertes[4],
                'Destination MAC': item_values_alertes[5],
                'Destination IP': item_values_alertes[6],
                'DHCP Type': item_values_alertes[7],
                'Packet Index': item_values_alertes[8],
                'Hostname': item_values_alertes[9],
                'Server ID': item_values_alertes[10],
                'Lease Time': item_values_alertes[11]
            }

            for key, value in frame_details_alertes.items():
                label = tk.Label(details_window, text=f"{key}: {value}")
                label.pack()

            # Bouton pour quitter la fenêtre
            tk.Button(details_window, text="Fermer", command=details_window.destroy).pack()
        else:
            print("Aucune alerte sélectionnée.")


    def show_frame_details(self, event):                    #Pour afficher les détails dans le tableau principal 
            selected_item = self.tree.selection()
            if selected_item:
                item_values = self.tree.item(selected_item, 'values')
                
                # Récupérer les détails de la trame à partir du tableau principal
                frame_details = {
                    'Source MAC': item_values[0],
                    'Source IP': item_values[1],
                    'Destination MAC': item_values[2],
                    'Destination IP': item_values[3],
                    'Timestamp': item_values[4],
                    'DHCP Type': item_values[5],
                    'Packet Index': item_values[6],
                    'Hostname': item_values[7],
                    'Server ID': item_values[8],
                    'Lease Time': item_values[9],
                }

                # Afficher les détails dans une nouvelle fenêtre
                details_window = tk.Toplevel(self.root)
                details_window.title("Détails de la trame")

                # Créer des étiquettes pour afficher tous les détails
                for key, value in frame_details.items():
                    label = tk.Label(details_window, text=f"{key}: {value}")
                    label.pack()

                # Bouton pour quitter la fenêtre
                tk.Button(details_window, text="Fermer", command=details_window.destroy).pack()
            else:
                print("Aucune alerte sélectionnée.")

    def color_rows_with_alerts(self):
        for i, item in enumerate(self.tree_alertes.get_children()):
            values = self.tree.item(item, 'values')
            if values and values[1] in self.alert_data and values[8] in self.alert_data:  # Vérifiez si Source IP et Server ID sont dans self.alert_data
                self.tree.tag_configure('alert', background='red')  # Tag 'alert' pour distinguer les alertes
                self.tree.item(item, tags=('alert',))

    def show_graphique(self):
        # Créer une nouvelle fenêtre pour afficher le graphique
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Graphique des alertes")

        alert_types = ["Server ID Danger", "Source IP Danger"]
        alert_counts = {alert_type: 0 for alert_type in alert_types}

        for item in self.tree_alertes.get_children():
            values = self.tree_alertes.item(item, 'values')
            if values and values[1] in alert_types:
                alert_counts[values[1]] += 1

        labels = list(alert_counts.keys())
        sizes = list(alert_counts.values())
        colors = ['red', 'orange']

        # Ajouter un canevas au cadre pour afficher le graphique
        graphique_canvas = FigureCanvasTkAgg(plt.figure(figsize=(4, 4)), master=graph_window)
        graphique_canvas.get_tk_widget().pack(fill='both', expand=True)

        # Ajouter un titre au graphique
        plt.title("Moyennes d'alertes détectées")

        # Afficher le graphique dans le canevas
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')

        # Mettre à jour le canevas
        graphique_canvas.draw()

        # Bouton pour quitter la fenêtre
        tk.Button(graph_window, text="Fermer", command=graph_window.destroy).pack()

    def show_alert_count(self):
        alert_count = len(self.tree_alertes.get_children())

        # Ajouter le nombre d'alertes en chiffres
        alert_count_label = ttk.Label(self.alert_count_frame, text=f"Nombres d'alertes : {alert_count}", font=('Arial', 13, 'bold'))
        alert_count_label.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")

    def scroll_tree(self, event, direction):
        current_index = self.tree.index(self.tree.focus())
        new_index = current_index + direction
        if 0 <= new_index < len(self.tree.get_children()):
            self.tree.selection_set(self.tree.get_children()[new_index])
            self.tree.focus(self.tree.get_children()[new_index])

    def scroll_tree_alertes(self, event, direction):
        current_index = self.tree_alertes.index(self.tree_alertes.focus())
        new_index = current_index + direction
        if 0 <= new_index < len(self.tree_alertes.get_children()):
            self.tree_alertes.selection_set(self.tree_alertes.get_children()[new_index])
            self.tree_alertes.focus(self.tree_alertes.get_children()[new_index])

    def collect_alerts_data(self, root):
        
        alerts_data = []
        for item in root.findall(".//item"):
        
            timestamp_str, has_alert = self.get_alerts_data(item)
            if has_alert:
                timestamp = self.convert_timestamp(timestamp_str)
                alerts_data.append((timestamp, has_alert))
        return alerts_data
    
    def save_capture(self):```
        # Demander à l'utilisateur où enregistrer le fichier
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")])

        if file_path:
            # Récupérer les données de capture de trame
            capture_data = self.get_capture_data()

            # Écrire les données dans le fichier texte
            with open(file_path, 'w') as file:
                for data_entry in capture_data:
                    file.write("\t".join(map(str, data_entry)) + "\n")

            print(f"Capture de trame enregistrée dans {file_path}")

    def get_capture_data(self):
        # Récupérer les données de capture de trame depuis le tableau
        capture_data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if values:
                capture_data.append(values)
        return capture_data


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
