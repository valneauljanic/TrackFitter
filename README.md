# **Track-fitter**


**TrackFitter** je web aplikacija koja korisnicima omogućuje unos podataka o završenim treninzima, kao što su datum, vrijeme, intenzitet, trajanje i vrsta treninga. Na kraju svakog mjeseca, aplikacija generira statistiku treninga za taj mjesec, pružajući pregled aktivnosti i omogućujući praćenje napretka uz vizualizaciju.

## USE-CASE
![Use Case: TrackFitter](docs/use-case.png)


## Funkcionalnosti
- CRUD nad treninzima (unos, pregled, uređivanje, brisanje)
- Mjesečna statistika: broj treninga, ukupno trajanje (min), prosječni intenzitet
- Vizualizacije (linijski i stupčasti graf)
- REST API rute u JSON-u

## Tehnologije

- Python 3.11
- Flask
- PonyORM
- SQLite
- HTML/CSS/Bootstrap
- Chart.js
- Docker/Compose

## Kloniranje repozitorija i pokretanje s Docker Compose (port 8000)
```bash
git clone https://github.com/valneauljanic/TrackFitter.git
cd TrackFitter
docker compose up --build
```
Otvori u pregledniku
[http://localhost:8000/](http://localhost:8000/)



