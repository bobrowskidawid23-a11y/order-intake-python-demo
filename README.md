# Order Intake Python Demo

Mały, bezpieczny pipeline przyjmowania zamówień: walidacja danych, dokładne dopasowanie SKU, kalkulacja wartości i kolejka ręcznej weryfikacji. System działa **fail-closed** — nieznanego produktu nie zastępuje podobną nazwą.

## Co pokazuje

- logikę biznesową w Pythonie 3.11+,
- ochronę przed ponownym przetworzeniem tego samego źródła,
- jawny status `needs_review` dla niepewnych danych,
- prosty endpoint REST bez zewnętrznych zależności,
- testy jednostkowe.

Wszystkie dane, kody i ceny są syntetyczne.

## Testy

```bash
python -m unittest discover -s tests -v
```

## Demo API

```bash
python -m order_intake_demo.api
curl -X POST http://127.0.0.1:8080/orders/process \
  -H "Content-Type: application/json" \
  --data @examples/order.json
```

## Technologie

Python, standard library HTTP API, `decimal`, `unittest`.

Demo API utrzymuje rejestr `source_id` w pamięci procesu. W systemie produkcyjnym taki rejestr powinien znajdować się w trwałej bazie danych z unikalnym indeksem.
