# Quelques commandes docker utiles 

## Lister les conteneurs pour avoir leurs noms, ID et status

    sudo docker ps -a -q 
    
    ou 
    
    docker ps

## Supprimer un conteneur

    sudo docker rm "nom ou ID du container"

## Construire la première fois l'envrionnement docker

    sudo docker-compose up --build

##  Après avoir build l'environnement pour le relancer 

    sudo docker-compose up

## Obtenir l'adresse IP d'un conteneur spécifié 

    sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "nom ou ID du conteneur"

## Démarrer un conteneur

    docker start "nom ou ID du conteneur"

## Ping d'un conteneur docker vers un autre conteneur pour le test de connectivité

    docker exec -it "nom ou ID du 1er conteneur" ping "IP du 2eme conteneur"

## Entrer dans un conteneur

    docker exec -it "nom ou ID du conteneur" /bin/bash

    ou

    docker exec -it "nom ou ID du conteneur" /bin/sh
