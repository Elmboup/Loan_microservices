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
- Docker + Docker Compose

Lancement:

```bash
docker compose up -d --build
```

Arret:

```bash
docker compose down
```

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
