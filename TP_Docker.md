# TP Docker — Conteneurs, volumes, réseaux et Docker Compose

| | |
|---|---|
| **Durée estimée** | 3 h |
| **Prérequis** | Bases du terminal Linux ; Docker Engine ou Docker Desktop (avec Compose v2) |
| **Rendu** | Compte rendu (commandes utilisées + réponses aux questions) et fichiers `Dockerfile` / `docker-compose.yml` écrits |

## Objectifs

À l'issue de ce TP, vous saurez :

- manipuler des conteneurs en mode interactif (`run`, `exec`, `logs`, `stop`, `rm`) ;
- construire une image à partir d'un `Dockerfile` ;
- conserver des données avec les **volumes** (volumes nommés et *bind mounts*) ;
- faire communiquer des conteneurs grâce aux **réseaux** Docker ;
- décrire et lancer une application multi-services avec **Docker Compose**.

## Organisation du dossier

```
tp-docker/
├── TP_Docker.md          ← cet énoncé
├── ex1/app/hello.py      ← programme interactif (exercice 1)
├── ex2/site/index.html   ← site statique (exercice 2)
├── ex3/web/index.html    ← page servie par nginx (exercice 3)
├── ex4/app/              ← application Flask + Redis (exercice 4)
└── ex5/                  ← projet de synthèse (exercice 5)
    ├── app/              ← API Flask + PostgreSQL
    ├── db/init.sql
    ├── proxy/nginx.conf
    └── .env.example
```

## Conventions

- Toutes les commandes sont à lancer **depuis la racine du TP** (le dossier `tp-docker/`), sauf indication contraire.
- `$(pwd)` désigne le dossier courant. Sous PowerShell, utilisez `${PWD}` ; sous Windows, un terminal WSL2 est recommandé.
- Les questions sont numérotées **Q1, Q2…** : répondez-y dans votre compte rendu.
- **Nettoyez** à la fin de chaque exercice (commandes données) : les exercices réutilisent les mêmes noms et les mêmes ports (8080, 8081, 8082, 5000).

## Barème indicatif

| Exercice | Thème | Points |
|---|---|---|
| 1 | Docker simple et interaction | 4 |
| 2 | Volumes | 4 |
| 3 | Réseaux | 4 |
| 4 | Docker Compose (premier projet) | 4 |
| 5 | Projet de synthèse | 4 |

---

## Exercice 1 — Docker simple et interaction

**Objectif :** lancer des conteneurs, interagir avec eux, puis construire sa première image.

### Partie A — Vérification de l'installation

1. Lancez `docker --version` puis `docker info` et relevez les versions du client et du serveur.
2. Lancez `docker run hello-world` et lisez attentivement le message affiché.

> **Q1.** Quelles sont les étapes réalisées par Docker, d'après le message de `hello-world` ?

### Partie B — Shell interactif dans un conteneur

3. Lancez un conteneur Alpine interactif :
   ```bash
   docker run -it --name alpine1 alpine sh
   ```
4. À l'intérieur du conteneur, exécutez : `cat /etc/os-release`, `hostname`, `whoami`, `ps`, `touch /fichier-test`, `ls /`, puis `exit`.

> **Q2.** Que signifient les options `-i` et `-t` ?
> **Q3.** Pourquoi le conteneur s'arrête-t-il quand vous quittez le shell ?

5. Listez les conteneurs avec `docker ps` puis `docker ps -a`. Redémarrez le conteneur en mode interactif : `docker start -ai alpine1`, puis `ls /`.

> **Q4.** Le fichier `/fichier-test` existe-t-il toujours ? Pourquoi ?

6. Quittez, supprimez le conteneur (`docker rm alpine1`), puis relancez `docker run -it --name alpine1 alpine sh` et faites `ls /`.

> **Q5.** Le fichier existe-t-il encore ? Que peut-on en conclure ?

7. Lancez `docker run -it --rm alpine sh`, quittez, puis vérifiez avec `docker ps -a`.

> **Q6.** Quel est le rôle de l'option `--rm` ?

### Partie C — Conteneur en arrière-plan : un serveur web

8. Lancez nginx en arrière-plan et publiez son port :
   ```bash
   docker run -d --name web -p 8080:80 nginx
   ```
   Ouvrez <http://localhost:8080> (ou `curl http://localhost:8080`).
9. Suivez les journaux avec `docker logs -f web` (Ctrl+C pour quitter) en rechargeant la page.
10. Ouvrez un shell dans le conteneur et modifiez la page d'accueil :
    ```bash
    docker exec -it web bash
    echo "<h1>Bonjour TP Docker</h1>" > /usr/share/nginx/html/index.html
    exit
    ```
    Rechargez la page.
11. Exécutez `docker top web`, `docker stats --no-stream` et `docker inspect web`.

> **Q7.** Quelle est l'adresse IP du conteneur et quel est le mapping de ports (retrouvez-les dans `docker inspect`) ?
> **Q8.** Quelle est la différence entre `docker run` et `docker exec` ?

12. Arrêtez et supprimez le conteneur (`docker stop web && docker rm web`), recréez-le avec la même commande qu'à l'étape 8 et rechargez la page.

> **Q9.** La modification de l'étape 10 est-elle conservée ? Pourquoi ? (Cette question prépare l'exercice 2.)

### Partie D — Votre première image

Le fichier `ex1/app/hello.py` est un mini-quiz interactif en Python.

13. Écrivez un `Dockerfile` dans `ex1/app/` qui :
    - part de l'image `python:3.12-slim` ;
    - utilise `/app` comme répertoire de travail ;
    - copie `hello.py` ;
    - lance `python hello.py` au démarrage.
14. Construisez l'image et vérifiez-la :
    ```bash
    docker build -t quiz:1.0 ex1/app
    docker images
    ```
15. Lancez d'abord `docker run quiz:1.0`, puis `docker run -it --rm quiz:1.0`.

> **Q10.** Que se passe-t-il sans `-it` ? Pourquoi ? (Regardez `docker ps -a`.)

16. Lancez `docker run -it --rm -e APP_ENV=prod quiz:1.0` et comparez l'affichage.

> **Q11.** Quelle est la différence entre une image et un conteneur ?

**Nettoyage :** `docker rm -f web alpine1 2>/dev/null`

**Livrables :** le `Dockerfile` et les réponses Q1 à Q11.

---

## Exercice 2 — Les volumes 

**Objectif :** conserver des données au-delà de la vie d'un conteneur.

### Partie A — Sans volume

1. Écrivez une donnée dans un conteneur :
   ```bash
   docker run --name sans-volume alpine sh -c "echo 'donnée importante' > /data.txt && cat /data.txt"
   ```
2. Supprimez le conteneur, puis tentez de relire le fichier :
   ```bash
   docker rm sans-volume
   docker run --rm alpine cat /data.txt
   ```

> **Q1.** Pourquoi le fichier a-t-il disparu ?

### Partie B — Volume nommé

3. Créez et inspectez un volume :
   ```bash
   docker volume create mes-donnees
   docker volume ls
   docker volume inspect mes-donnees
   ```
4. Écrivez dans le volume depuis un premier conteneur, puis relisez depuis un **autre** conteneur :
   ```bash
   docker run --rm -v mes-donnees:/data alpine sh -c "echo 'persistant' > /data/message.txt"
   docker run --rm -v mes-donnees:/data alpine cat /data/message.txt
   ```

> **Q2.** Le fichier est-il retrouvé ? Pourquoi ?

5. Partagez le volume entre deux conteneurs **simultanés** :
   ```bash
   docker run -dit --name a -v mes-donnees:/data alpine
   docker run -dit --name b -v mes-donnees:/data alpine
   docker exec a sh -c "echo 'écrit par a' > /data/from-a.txt"
   docker exec b cat /data/from-a.txt
   ```

> **Q3.** Donnez un cas d'usage réel du partage d'un volume entre deux conteneurs.

### Partie C — Bind mount : développer un site statique

Le dossier `ex2/site/` contient une page `index.html`.

6. Servez ce dossier avec nginx, en lecture seule :
   ```bash
   docker run -d --name site -p 8081:80 -v "$(pwd)/ex2/site:/usr/share/nginx/html:ro" nginx
   ```
7. Ouvrez <http://localhost:8081>, puis modifiez le titre dans `index.html` avec votre éditeur et rechargez la page (Ctrl+F5) **sans redémarrer** le conteneur.

> **Q4.** La modification est-elle visible immédiatement ? Pourquoi ?

8. Essayez d'écrire depuis le conteneur :
   ```bash
   docker exec site sh -c "echo test > /usr/share/nginx/html/test.txt"
   ```

> **Q5.** Pourquoi cette commande échoue-t-elle ?
> **Q6.** Complétez un tableau comparant volume nommé et bind mount (gestion par Docker, emplacement, cas d'usage typique).

### Partie D — Persistance d'une base PostgreSQL

9. Lancez PostgreSQL avec un volume nommé pour ses données :
   ```bash
   docker run -d --name pg -e POSTGRES_PASSWORD=secret -v pgdata:/var/lib/postgresql/data postgres:16-alpine
   ```
10. Après quelques secondes, créez des données :
    ```bash
    docker exec -it pg psql -U postgres
    ```
    ```sql
    CREATE TABLE etudiants (id SERIAL PRIMARY KEY, nom TEXT);
    INSERT INTO etudiants (nom) VALUES ('Amine'), ('Lina');
    SELECT * FROM etudiants;
    \q
    ```
11. Supprimez **brutalement** le conteneur, puis recréez-le avec la même commande qu'à l'étape 9 et relisez la table :
    ```bash
    docker rm -f pg
    # ... même commande docker run qu'à l'étape 9 ...
    docker exec -it pg psql -U postgres -c "SELECT * FROM etudiants;"
    ```

> **Q7.** Les données sont-elles toujours là ? Expliquez.
> **Q8.** Où le volume `pgdata` est-il stocké sur l'hôte (voir `docker volume inspect pgdata`) ?

### Partie E — Sauvegarde d'un volume (bonus)

12. Sauvegardez `pgdata` dans une archive `.tgz` du dossier courant, à l'aide d'un conteneur Alpine temporaire qui monte à la fois le volume et le dossier courant.

**Nettoyage :**
```bash
docker rm -f pg site a b
docker volume rm mes-donnees pgdata
```

**Livrables :** réponses Q1 à Q8 et la commande de sauvegarde (étape 12).

---

## Exercice 3 — Les réseaux )

**Objectif :** comprendre comment les conteneurs communiquent entre eux et avec l'hôte.

### Partie A — Découverte

1. Listez les réseaux : `docker network ls`.
2. Inspectez le réseau `bridge` : `docker network inspect bridge` (sous-réseau, passerelle).

> **Q1.** Quel est le rôle des réseaux `bridge`, `host` et `none` ?

### Partie B — Le réseau `bridge` par défaut

3. Lancez deux conteneurs et récupérez l'IP de `c2` :
   ```bash
   docker run -dit --name c1 alpine
   docker run -dit --name c2 alpine
   docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' c2
   ```
4. Depuis `c1`, pingez `c2` **par son IP**, puis **par son nom** :
   ```bash
   docker exec c1 ping -c 2 <IP_DE_C2>
   docker exec c1 ping -c 2 c2
   ```

> **Q2.** Pourquoi le ping par nom échoue-t-il sur le réseau par défaut ?

5. Supprimez les conteneurs : `docker rm -f c1 c2`.

### Partie C — Réseau défini par l'utilisateur

6. Créez un réseau et relancez les conteneurs dessus :
   ```bash
   docker network create tp-net
   docker run -dit --name c1 --network tp-net alpine
   docker run -dit --name c2 --network tp-net alpine
   docker exec c1 ping -c 2 c2
   docker network inspect tp-net
   ```

> **Q3.** Pourquoi le ping par nom fonctionne-t-il maintenant ?

7. Supprimez `c1` et `c2`.

### Partie D — Serveur web et client

Le dossier `ex3/web/` contient une page `index.html`.

8. Lancez nginx sur `tp-net`, **sans publier de port** :
   ```bash
   docker run -d --name web --network tp-net -v "$(pwd)/ex3/web:/usr/share/nginx/html:ro" nginx
   ```
9. Interrogez-le depuis un conteneur client **temporaire** :
   ```bash
   docker run --rm --network tp-net alpine wget -qO- http://web
   ```

> **Q4.** Pourquoi cela fonctionne-t-il alors qu'aucun port n'est publié ?

10. Essayez d'ouvrir <http://localhost:8082> depuis votre navigateur.

> **Q5.** La page est-elle accessible depuis l'hôte ? Pourquoi ?

11. Supprimez `web` et relancez-le en publiant le port (`-p 8082:80`), puis rechargez la page.

> **Q6.** Quelle est la différence entre l'accès par nom de conteneur et l'accès par port publié ?

### Partie E — Isolation entre réseaux

12. Créez un second réseau et un conteneur « intrus » :
    ```bash
    docker network create autre-net
    docker run -dit --name intrus --network autre-net alpine
    docker exec intrus ping -c 2 web
    ```
13. Connectez l'intrus à `tp-net`, retestez, puis déconnectez-le :
    ```bash
    docker network connect tp-net intrus
    docker exec intrus ping -c 2 web
    docker network disconnect tp-net intrus
    docker exec intrus ping -c 2 web
    ```

> **Q7.** Quel est l'intérêt de l'isolation par réseaux dans une application réelle ?

**Nettoyage :**
```bash
docker rm -f web intrus c1 c2 2>/dev/null
docker network rm tp-net autre-net
```

**Livrables :** réponses Q1 à Q7 et un schéma simple (même à la main) des réseaux de la partie E.

---

## Exercice 4 — Docker Compose : premier projet 

**Objectif :** décrire une application à deux services dans un fichier `docker-compose.yml`.

**Contexte :** `ex4/app/app.py` est une application Flask qui compte les visites d'une page et stocke le compteur dans **Redis**. Elle lit l'adresse de Redis dans la variable d'environnement `REDIS_HOST`.

1. Lisez `app.py` et `requirements.txt`.
2. Écrivez `ex4/app/Dockerfile` :
   - image de base `python:3.12-slim`, répertoire `/app` ;
   - copie de `requirements.txt` puis installation (`pip install --no-cache-dir -r requirements.txt`) ;
   - **ensuite** copie de `app.py` ;
   - port 5000, commande `flask --app app run --host=0.0.0.0 --port=5000`.

> **Q1.** Pourquoi copie-t-on `requirements.txt` *avant* le code de l'application ?

3. Écrivez `ex4/docker-compose.yml` avec deux services :
   - **web** : construit depuis `./app`, publie le port `5000:5000`, variable `REDIS_HOST=redis`, démarre après `redis` ;
   - **redis** : image `redis:7-alpine`, lancé avec `redis-server --appendonly yes`, données dans un **volume nommé** `redis-data` monté sur `/data`.
4. Depuis `ex4/` : démarrez et testez.
   ```bash
   cd ex4
   docker compose up -d --build
   docker compose ps
   curl http://localhost:5000/     # à répéter 3 fois
   docker compose logs -f web      # Ctrl+C pour quitter
   docker compose exec redis redis-cli GET visites
   ```
5. Testez la persistance :
   ```bash
   docker compose down
   docker compose up -d
   curl http://localhost:5000/
   docker compose down -v
   docker compose up -d
   curl http://localhost:5000/
   ```

> **Q2.** Le compteur est-il conservé après `docker compose down` puis `up` ?
> **Q3.** Et après `docker compose down -v` ? Pourquoi ?
> **Q4.** Comment le service `web` trouve-t-il `redis` ? (Regardez `docker network ls`.)
> **Q5.** Que se passerait-il avec `docker compose up -d --scale web=2` ? Pourquoi ?

**Nettoyage :** `docker compose down -v` (dans `ex4/`).

**Livrables :** `Dockerfile`, `docker-compose.yml`, réponses Q1 à Q5.

---

## Exercice 5 — Projet de synthèse : API de tâches multi-services

**Objectif :** assembler tout le TP (volumes, réseaux, Compose) dans une architecture réaliste à plusieurs niveaux.

### Architecture à réaliser

```
Navigateur ──► proxy (nginx, :8080) ──► api (Flask + gunicorn, :5000) ──► db (PostgreSQL)
               └──── réseau frontend ────┘└──────── réseau backend ───────────┘
                                         adminer (:8081) ──► db   (réseau backend)
```

| Service | Image | Réseaux | Exposé à l'hôte |
|---|---|---|---|
| `proxy` | `nginx:alpine` | `frontend` | `8080:80` |
| `api` | construite depuis `./app` | `frontend` et `backend` | non |
| `db` | `postgres:16-alpine` | `backend` | non |
| `adminer` | `adminer:4` | `backend` | `8081:8080` |

### Cahier des charges

- Nom de projet fixé à `tp5` (clé `name:` en tête du fichier Compose).
- Les identifiants de la base sont lus dans un fichier `.env` (créez-le à partir de `.env.example` ; variables `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).
- **db** : données dans un volume nommé `pgdata` ; `db/init.sql` monté en lecture seule dans `/docker-entrypoint-initdb.d/` ; *healthcheck* avec `pg_isready` ; redémarrage `unless-stopped`.
- **api** : `Dockerfile` à écrire dans `ex5/app/` (python:3.12-slim, installation des dépendances avant la copie du code, démarrage par `gunicorn --bind 0.0.0.0:5000 app:app`) ; variable `DB_HOST=db` et les identifiants ci-dessus ; ne démarre que lorsque `db` est **healthy** ; redémarrage `unless-stopped`.
- **proxy** : monte `proxy/nginx.conf` en lecture seule dans `/etc/nginx/conf.d/default.conf`.

### Travail demandé

1. Lisez les fichiers fournis (`app/app.py`, `db/init.sql`, `proxy/nginx.conf`).
2. Écrivez `ex5/app/Dockerfile`, `ex5/.env` et `ex5/docker-compose.yml`.
3. Validez et démarrez (depuis `ex5/`) :
   ```bash
   cd ex5
   cp .env.example .env
   docker compose config
   docker compose up -d --build
   docker compose ps          # attendre l'état « healthy »
   ```
4. Testez l'API **à travers le proxy** :
   ```bash
   curl http://localhost:8080/tasks
   curl -X POST -H "Content-Type: application/json" -d '{"title":"Réviser Docker"}' http://localhost:8080/tasks
   curl -X PUT http://localhost:8080/tasks/1/done
   curl -X DELETE http://localhost:8080/tasks/2
   ```
5. Persistance : créez une tâche, faites `docker compose down`, puis `up -d` et listez les tâches. Faites ensuite `docker compose down -v`, `up -d` et listez de nouveau.
6. Isolation des réseaux :
   ```bash
   docker run --rm --network tp5_frontend alpine ping -c 1 api
   docker run --rm --network tp5_frontend alpine ping -c 1 db
   docker run --rm --network tp5_backend  alpine ping -c 1 proxy
   ```
7. Ouvrez Adminer sur <http://localhost:8081> (système *PostgreSQL*) et connectez-vous à la base.
8. Panne : `docker compose stop db`, appelez `curl -i http://localhost:8080/tasks`, puis `docker compose start db` et rappelez-le.

> **Q1.** Pourquoi seul `proxy` publie-t-il un port pour l'API ?
> **Q2.** Pourquoi `depends_on` seul ne garantit-il pas que la base est prête ? Que change `condition: service_healthy` ?
> **Q3.** Les tâches survivent-elles à `down` ? à `down -v` ? Pourquoi les deux tâches initiales réapparaissent-elles après `down -v` ?
> **Q4.** Quels résultats obtenez-vous aux trois `ping` de l'étape 6 et pourquoi ?
> **Q5.** Dans Adminer, quel nom de serveur faut-il saisir pour joindre la base ? Pourquoi pas `localhost` ?
> **Q6.** Que se passe-t-il pendant la panne de l'étape 8, et au redémarrage de `db` ?
> **Q7.** Pourquoi stocker les identifiants dans `.env` plutôt que dans le fichier Compose ? Que faut-il faire de ce fichier avec Git ?

**Bonus :** ajoutez un `.dockerignore` dans `ex5/app/`, faites tourner l'API avec un utilisateur non root, et ajoutez un *healthcheck* à l'API.

**Nettoyage :** `docker compose down -v` (dans `ex5/`).

**Livrables :** `Dockerfile`, `.env`, `docker-compose.yml`, réponses Q1 à Q7.

---

## Annexe — Aide-mémoire

| Besoin | Commande |
|---|---|
| Lancer un conteneur interactif | `docker run -it [--rm] [--name N] IMAGE [CMD]` |
| Lancer en arrière-plan | `docker run -d -p HOTE:CONTENEUR IMAGE` |
| Lister conteneurs / images | `docker ps [-a]` / `docker images` |
| Shell dans un conteneur actif | `docker exec -it NOM sh` |
| Journaux | `docker logs [-f] NOM` |
| Arrêter / supprimer | `docker stop NOM` / `docker rm [-f] NOM` |
| Construire une image | `docker build -t NOM:TAG DOSSIER` |
| Volumes | `docker volume create\|ls\|inspect\|rm` |
| Monter un volume / un dossier | `-v NOM:/chemin` / `-v "$(pwd)/dossier:/chemin[:ro]"` |
| Réseaux | `docker network create\|ls\|inspect\|connect\|disconnect\|rm` |
| Compose : démarrer / arrêter | `docker compose up -d [--build]` / `docker compose down [-v]` |
| Compose : état, logs, exec | `docker compose ps` / `logs -f SERVICE` / `exec SERVICE CMD` |
| Compose : valider le fichier | `docker compose config` |
| Tout nettoyer (attention !) | `docker system prune` |
