# Loan Microservices

Monorepo Python (FastAPI) pour l'implementation d'un processus de demande de pret immobilier en microservices, avec RabbitMQ, Celery, SSE/WebSocket et dashboard de suivi.

## 1) Objectif du projet

Ce projet couvre les attentes principales du TD3:
- decomposition du processus en microservices
- communication evenementielle via RabbitMQ
- traitements asynchrones via Celery
- mecanisme de compensation (Saga)
- notifications temps reel (SSE + WebSocket)
- dashboard de suivi

## 2) Architecture

Services exposes:
- `loan-service` (port `8001`): creation dossier, gestion des documents, statut global
- `credit-service` (port `8002`): verification credit (asynchrone)
- `property-service` (port `8003`): evaluation du bien (asynchrone)
- `decision-service` (port `8004`): agrege credit + bien, publie decision
- `insurance-service` (port `8005`): genere un devis assurance (asynchrone)
- `agreement-service` (port `8006`): collecte accord/refus client final
- `notification-service` (port `8007`): SSE, WebSocket, dashboard HTML

Infrastructure:
- RabbitMQ (broker d'evenements): `5672`, UI: `15672`
- Redis (backend Celery)
- Flower (monitoring Celery): `5555`

## 3) Flux metier corrige (alignement BPMN)

### Regle cle
Les evaluations `credit` et `property` ne se declenchent **qu'apres** l'evenement `loan.documents.received`.

Concretement:
1. `POST /loans`
2. `loan.created`
3. si dossier incomplet -> `loan.documents.requested`
4. quand dossier complet (`POST /loans/{id}/documents`) -> `loan.documents.received`
5. ensuite seulement:
   - `credit.checked`
   - `property.evaluated`
6. puis `decision.made` + `loan.approved` ou `loan.rejected`
7. si approuve: `acceptance.package.sent`, puis accord client via `agreement-service`
8. finalisation: `loan.final.approved` ou `loan.cancelled`

## 4) Evenements principaux

Envelope commun:

```json
{
  "event_id": "<uuid>",
  "event_type": "<routing_key>",
  "timestamp": "<iso>",
  "loan_id": "<uuid>",
  "payload": {},
  "attempt": 0
}
```

Routing keys:
- `loan.created`
- `loan.documents.requested`
- `loan.documents.received`
- `credit.checked`
- `property.evaluated`
- `decision.made`
- `loan.approved`
- `loan.rejected`
- `credit.compensate`
- `credit.compensated`
- `acceptance.package.sent`
- `agreement.received`
- `agreement.accepted`
- `agreement.declined`
- `loan.final.approved`
- `loan.cancelled`
- `insurance.quote.ready`

## 5) Demarrage

Prerequis:
- Docker + Docker Compose (pour développement local)

Lancement:

```bash
docker compose up -d --build
```

Arret:

```bash
docker compose down
```

### 5a) Déploiement sur Kubernetes (Minikube)

Un dossier `k8s/` contient des manifests prêts à l'emploi. Le flux est identique à Docker Compose mais chaque service tourne dans un pod, avec RabbitMQ et Redis déployés en tant que déploiements également.

1. démarrez Minikube :
   ```bash
   minikube start
   ```
2. pointez votre shell sur le démon docker de Minikube afin de construire les images localement :
   ```bash
   eval "$(minikube docker-env)"
   ```
3. lancez le script de build et déploiement :
   ```bash
   cd k8s
   ./deploy.sh
   ```
   Il reconstruit toutes les images (`loan-service:latest`, `credit-service:latest`, …) puis applique les manifests (`Namespace`, RabbitMQ, Redis, micro‑services + workers).
4. vérifiez que les ressources sont en place :
   ```bash
   kubectl -n loan-app get pods,svc
   ```
5. pour accéder aux API en local vous pouvez utiliser `kubectl port-forward` ou créer un Ingress/NodePort. Par exemple :
   ```bash
   kubectl -n loan-app port-forward svc/loan-service 8001:8000
   # puis ouvrir http://localhost:8001/docs
   ```

Cette configuration est spécialement conçue pour du développement local. Les images sont construites directement dans le daemon de Minikube et identifiées par leur tag `latest`.

#### Passage à un cluster cloud (GKE, EKS, AKS...)

Pour déployer en production sur un service managé (Google Kubernetes Engine par exemple) :

1. **Préparez vos images** : poussez-les vers un registre accessible par le cluster (Google Container Registry, Docker Hub, …) :
   ```bash
   # depuis un shell local
   docker build -t gcr.io/myproj/loan-service:1.0 -f services/loan-service/Dockerfile .
   docker push gcr.io/myproj/loan-service:1.0
   # idem pour chaque service et les workers
   ```
2. **Adaptez les manifests**
   - remplacez les `image: loan-service:latest` par la référence complète du registre.
   - gérez les `Secrets` (login RabbitMQ/Redis) plutôt que des variables en dur.
   - configurez PersistentVolumes/PVC si vous souhaitez persister RabbitMQ/Redis ou utiliser un service managé.
   - ajoutez des `Readiness`/`Liveness` probes, ressources, autoscaling.
3. **Appliquez les manifests avec `kubectl`** sur votre cluster GKE :
   ```bash
   kubectl create namespace loan-app
   kubectl -n loan-app apply -f k8s/namespace.yaml
   kubectl -n loan-app apply -f k8s/rabbitmq-deployment.yaml
   kubectl -n loan-app apply -f k8s/redis-deployment.yaml
   kubectl -n loan-app apply -f k8s/services-deployments.yaml
   ```
4. **Exposez les services**
   - utilisez un LoadBalancer/Ingress pour obtenir des URL publiques.
   - configurez éventuellement un Ingress Controller (gd prêt sur GKE) et un certificat TLS.

Les étapes de test (création de prêt, visualisation dashboard) restent identiques ; seule la connexion réseau change.

> ➤ la partie `deploy.sh` peut être conservée pour les clusters locaux, ou convertie en CI/CD pipeline qui construit/push les images et applique les manifests automatiquement.

## 6) URLs utiles

- Loan Service: http://localhost:8001/docs
- Credit Service: http://localhost:8002/docs
- Property Service: http://localhost:8003/docs
- Decision Service: http://localhost:8004/docs
- Insurance Service: http://localhost:8005/docs
- Agreement Service: http://localhost:8006/docs
- Notification Service: http://localhost:8007/docs
- Dashboard: http://localhost:8007/
- RabbitMQ UI: http://localhost:15672 (`guest/guest`)
- Flower: http://localhost:5555

## 7) Test de validation du flux corrige

### Etape A - Creation dossier incomplet

```bash
curl -s -X POST http://localhost:8001/loans \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"client-flow-test","insurance_interest":true}'
```

Recuperer `loan_id`, puis verifier les evenements:

```bash
curl -s http://localhost:8007/loans/<loan_id>/events
```

Attendu a ce stade:
- present: `loan.created`, `loan.documents.requested`
- absent: `credit.checked`, `property.evaluated`, `decision.made`

### Etape B - Completer les documents

```bash
curl -s -X POST http://localhost:8001/loans/<loan_id>/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":{"id":"id.pdf","income_proof":"income.pdf","property_docs":"deed.pdf"}}'
```

Puis:

```bash
curl -s http://localhost:8007/loans/<loan_id>/events
```

Attendu apres complementation:
- `loan.documents.received`
- `credit.checked`
- `property.evaluated`
- `decision.made`
- puis `loan.approved`/`loan.rejected`

## 8) Saga, durabilite, retries, DLQ

- Exchange durable `events` (topic)
- DLX: `events.dlx`
- queues durables + DLQ par service (`<service>.dlq`)
- ack explicite
- retries par champ `attempt` (max 3)
- echec final -> `nack(requeue=False)` vers DLQ

Compensation implementee:
- si `property.evaluated` arrive avec `property_ok=false`, le `decision-service` publie:
  - `loan.rejected`
  - `credit.compensate`
- `credit-service` publie ensuite `credit.compensated`

## 9) Monitoring

- Flower: suivi des workers/taches Celery
- endpoint `GET /metrics` sur chaque service
- logs docker compose pour tracer les evenements

## 10) Limites actuelles

- stockage en memoire (pas de base persistante)
- pas de tests automatises (pytest) pour l'instant
- certains traitements sont simules (sleep) pour representer les taches longues
