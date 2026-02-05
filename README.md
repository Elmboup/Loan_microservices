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
  -d '{"applicant_name":"Alice","amount":250000,"property_address":"10 rue de Paris","insurance_interest":true}'
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
- `property.evaluated`
- `decision.made`
- `loan.approved`
- `loan.rejected`
- `insurance.quote.ready`
- `agreement.accepted`
- `agreement.declined`

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
