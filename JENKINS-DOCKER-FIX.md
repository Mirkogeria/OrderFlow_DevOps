# Jenkins + Docker: Troubleshooting & Best Practices

## Problemi riscontrati e soluzioni

---

### 1. `No module named pytest` nei container di test

**Errore:**
```
/usr/local/bin/python: No module named pytest
```

**Causa:**
Il multi-stage Dockerfile usava `pip install --prefix=/install` per installare le dipendenze nel builder stage, poi copiava con `COPY --from=builder /install /usr/local`. Questo approccio non sempre preserva correttamente la struttura dei moduli Python (script entry-points, `.dist-info`, ecc.), causando moduli mancanti nel runtime stage.

**Soluzione:**
Sostituito `--prefix` con un **virtual environment** in tutti e 3 i Dockerfile (`order-service`, `inventory-service`, `notification-service`).

**Prima (non funzionante):**
```dockerfile
# Builder
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime
COPY --from=builder /install /usr/local
```

**Dopo (funzionante):**
```dockerfile
# Builder
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Runtime
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

**Perche funziona:** Il virtual environment e una struttura autocontenuta e coerente. Copiandolo intatto nel runtime stage, tutti i moduli, binari e metadata restano nei path corretti.

---

### 2. `permission denied` su Docker socket

**Errore:**
```
ERROR: permission denied while trying to connect to the Docker daemon socket
at unix:///var/run/docker.sock
```

**Causa:**
L'utente `jenkins` dentro il container non ha i permessi per accedere al socket Docker dell'host (`/var/run/docker.sock`).

**Hotfix immediato (non persistente):**
```bash
docker exec -u root jenkins2 chmod 666 /var/run/docker.sock
```
> Nota: questo fix viene perso al restart del container. Va rieseguito ogni volta.

**Soluzione persistente (consigliata):**

1. Trovare il GID del gruppo `docker` sull'host:
   ```bash
   stat -c '%g' /var/run/docker.sock
   ```

2. Creare il gruppo nel container con lo stesso GID e aggiungere jenkins:
   ```bash
   docker exec -u root jenkins2 bash -c "\
     groupadd -g <GID> docker && \
     usermod -aG docker jenkins"
   ```

3. Restart del container:
   ```bash
   docker restart jenkins2
   ```

**Prerequisito fondamentale:**
Il socket Docker dell'host deve essere montato nel container Jenkins. Verificare che il container sia stato creato con:
```bash
-v /var/run/docker.sock:/var/run/docker.sock
```

---

## Best Practices

### Docker-in-Docker per Jenkins

| Pratica | Descrizione |
|---------|-------------|
| **Montare il socket** | Usare sempre `-v /var/run/docker.sock:/var/run/docker.sock` per dare accesso Docker al container Jenkins |
| **GID matching** | Il GID del gruppo `docker` nel container deve corrispondere a quello dell'host |
| **Non usare `chmod 666`** in produzione | Apre il socket a tutti gli utenti del sistema — usare solo in sviluppo/test |
| **Named volumes per Jenkins home** | Usare `-v jenkins_home:/var/jenkins_home` per persistere dati tra restart |

### Multi-stage Dockerfile per Python

| Pratica | Descrizione |
|---------|-------------|
| **Usare venv invece di `--prefix`** | Piu affidabile per copiare dipendenze tra stage |
| **Separare dipendenze dev/prod** | Usare `requirements.txt` per produzione e `requirements-dev.txt` per test (pytest, ecc.) |
| **Non usare `root` in produzione** | Creare un utente dedicato (`appuser`) con `USER appuser` |
| **HEALTHCHECK** | Sempre includere un healthcheck per orchestratori (Docker Compose, K8s) |
| **`.dockerignore`** | Escludere `.git`, `__pycache__`, `*.pyc`, `.env` dalla build |

### Jenkinsfile

| Pratica | Descrizione |
|---------|-------------|
| **`timeout`** | Impostare sempre un timeout per evitare build bloccate |
| **`disableConcurrentBuilds`** | Evitare build parallele sullo stesso branch |
| **`parallel` stages** | Usare stage paralleli per build/test indipendenti (come fatto per i 3 servizi) |
| **Cleanup nel `post.always`** | Pulire container e immagini temporanee per non riempire il disco |
| **`set -eo pipefail`** | Negli script bash, per catturare errori in pipe |

---

## Comando di avvio Jenkins consigliato

```bash
docker run -d \
  --name jenkins2 \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

Dopo il primo avvio, eseguire il fix permessi persistente (sezione 2).
