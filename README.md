# Loan Microservices

Monorepo Python pour un processus de demande de prêt immobilier en microservices.

## Prérequis
- Docker + Docker Compose

## Lancer
```bash
docker compose up --build
```

## URLs utiles
- Loan Service: http://localhost:8001/docs
- Credit Service: http://localhost:8002/docs
- Property Service: http://localhost:8003/docs
- Decision Service: http://localhost:8004/docs
- Insurance Service: http://localhost:8005/docs
- Agreement Service: http://localhost:8006/docs
- Notification Service: http://localhost:8007/docs
- RabbitMQ UI: http://localhost:15672 (guest/guest)
- Flower: http://localhost:5555

## Scénario de test (happy path)
1) Créer une demande de prêt
```bash
curl -s -X POST http://localhost:8001/loans \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"client-123","insurance_interest":true}'
```
2) Suivre les événements via SSE
```bash
curl -N http://localhost:8007/events
```
3) Exemple WebSocket (wscat requis)
```bash
wscat -c ws://localhost:8007/ws/<loan_id>
```
4) Vérifier une décision
```bash
curl -s http://localhost:8004/decisions/<loan_id>
```

## Tests rapides (complétude)
1) Création incomplète (doit publier `loan.created` puis `loan.documents.requested`)
```bash
curl -s -X POST http://localhost:8001/loans \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"client-abc","insurance_interest":false}'
```
2) Compléter les documents (doit publier `loan.documents.received`)
```bash
curl -s -X POST http://localhost:8001/loans/<loan_id>/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":{"id":"id.pdf","income_proof":"income.pdf","property_docs":"deed.pdf"}}'
```

## Tests rapides (decision-service)
1) Créer un loan + compléter les docs (déclenche `credit.checked` et `property.evaluated`)
```bash
curl -s -X POST http://localhost:8001/loans \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"client-xyz","insurance_interest":true}'
```
```bash
curl -s -X POST http://localhost:8001/loans/<loan_id>/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":{"id":"id.pdf","income_proof":"income.pdf","property_docs":"deed.pdf"}}'
```
2) Vérifier les logs decision-service (`decision.made` + `loan.approved`/`loan.rejected`) et/ou SSE
```bash
curl -N http://localhost:8007/events
```
3) Vérifier la décision
```bash
curl -s http://localhost:8004/decisions/<loan_id>
```

## Tests rapides (insurance-service)
1) Créer un loan avec `insurance_interest=true` puis compléter les docs
```bash
curl -s -X POST http://localhost:8001/loans \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"client-quote","insurance_interest":true}'
```
```bash
curl -s -X POST http://localhost:8001/loans/<loan_id>/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":{"id":"id.pdf","income_proof":"income.pdf","property_docs":"deed.pdf"}}'
```
2) Observer l'événement `insurance.quote.ready` via SSE
```bash
curl -N http://localhost:8007/events
```
3) Vérifier l'API debug insurance
```bash
curl -s http://localhost:8005/insurance/<loan_id>
```

## Tests rapides (agreement + finalisation)
1) Créer un loan puis compléter les docs
```bash
curl -s -X POST http://localhost:8001/loans \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"client-final","insurance_interest":true}'
```
```bash
curl -s -X POST http://localhost:8001/loans/<loan_id>/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":{"id":"id.pdf","income_proof":"income.pdf","property_docs":"deed.pdf"}}'
```
2) Attendre `loan.approved` (via SSE) puis vérifier `acceptance.package.sent`
```bash
curl -N http://localhost:8007/events
```
3) Envoyer l'accord (accepté)
```bash
curl -s -X POST http://localhost:8006/loans/<loan_id>/agreement \
  -H 'Content-Type: application/json' \
  -d '{"accepted":true,"comment":"ok"}'
```
4) Vérifier `loan.final.approved` via SSE + statut `APPROVED` côté loan-service
```bash
curl -s http://localhost:8001/loans/<loan_id>
```
5) Tester un refus
```bash
curl -s -X POST http://localhost:8006/loans/<loan_id>/agreement \
  -H 'Content-Type: application/json' \
  -d '{"accepted":false,"comment":"no"}'
```
6) Vérifier `loan.cancelled` via SSE + statut `CANCELLED` côté loan-service
```bash
curl -s http://localhost:8001/loans/<loan_id>
```

## Contrats d’événements
Envelope commun:
```json
{
  "event_id": "<uuid>",
  "event_type": "<routing_key>",
  "timestamp": "<iso>",
  "loan_id": "<uuid>",
  "payload": {}
}
```
Routing keys:
- `loan.created`
- `loan.documents.received`
- `loan.documents.requested`
- `credit.checked`
- `credit.compensate`
- `credit.compensated`
- `property.evaluated`
- `property.compensate`
- `decision.made`
- `loan.approved`
- `loan.rejected`
- `acceptance.package.sent`
- `agreement.received`
- `agreement.accepted`
- `agreement.declined`
- `loan.final.approved`
- `loan.cancelled`
- `insurance.quote.ready`

## Endpoints principaux
- Loan Service: `POST /loans`, `POST /loans/{id}/documents`, `GET /loans/{id}`
- Credit Service: `GET /health`, `GET /debug`
- Property Service: `GET /health`, `GET /debug`
- Decision Service: `GET /health`, `GET /decisions/{loan_id}`
- Insurance Service: `GET /health`
- Agreement Service: `POST /loans/{id}/agreement`
- Notification Service: `GET /events`, `GET /health`, `WS /ws/{loan_id}`

## Notes
- Stockage en mémoire pour MVP (TODO DB).
- Celery simule les traitements (sleep).
- Les workers Celery utilisent des queues dédiées: `credit`, `property`, `insurance`.

## Compensation (Saga) + Fiabilité messages
Mécanisme:
- Si `property.evaluated` arrive avec `property_ok=false`, le `decision-service` publie `loan.rejected` et déclenche la compensation `credit.compensate`.
- `credit-service` consomme `credit.compensate`, marque le crédit comme compensé et publie `credit.compensated` (optionnel).
- Les statuts finaux (`REJECTED`, `CANCELLED`, `APPROVED`) ignorent les événements tardifs côté `loan-service`.

Durabilité, retries, DLQ:
- Exchange durable: `events` (topic) + DLX `events.dlx` (direct).
- Queues durables avec DLQ par service (`<service>.dlq`).
- Ack explicite. En cas d’exception:
  - retry jusqu’à 3 tentatives via `attempt` dans l’envelope
  - puis `nack(requeue=False)` vers DLQ.

Chaos testing:
- `FAILURE_RATE_PROPERTY` et `FAILURE_RATE_CREDIT` (0..1) injectent des échecs.
- Un échec publie `property_ok=false` ou `credit_ok=false` pour déclencher la compensation.

## Tests (Saga + DLQ)
1) Forcer un échec property
```bash
export FAILURE_RATE_PROPERTY=1.0
docker compose up --build
```
2) Créer un loan + compléter les docs
```bash
curl -s -X POST http://localhost:8001/loans \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"client-saga","insurance_interest":true}'
```
```bash
curl -s -X POST http://localhost:8001/loans/<loan_id>/documents \
  -H 'Content-Type: application/json' \
  -d '{"documents":{"id":"id.pdf","income_proof":"income.pdf","property_docs":"deed.pdf"}}'
```
3) Observer via SSE: `loan.rejected` + `credit.compensate` + `credit.compensated`
```bash
curl -N http://localhost:8007/events
```
4) Tester DLQ (retries dépassés)
- Simuler une exception non récupérable dans un handler.
- Vérifier la queue `<service>.dlq` via RabbitMQ UI (http://localhost:15672).
