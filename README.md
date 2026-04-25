# MediVend — Smart Pharmacy Platform
### Full Source Code

```
medivend/
├── frontend/
│   └── index.html              ← Full web app (single-file, no build needed)
├── backend/
│   ├── main.py                 ← FastAPI server
│   ├── routes/
│   │   ├── auth.py             ← Login / register
│   │   ├── prescriptions.py    ← Queue management
│   │   ├── inventory.py        ← Stock CRUD
│   │   ├── predictions.py      ← ML forecast API
│   │   └── analytics.py        ← Revenue & audit
│   ├── models.py               ← Pydantic schemas
│   └── supabase_client.py      ← DB connection
├── ml_model/
│   ├── forecast_model.py       ← Seasonal regression forecaster
│   ├── train.py                ← Training pipeline
│   └── requirements.txt
├── scraper/
│   ├── drug_scraper.py         ← Main scraper (SFDA + OpenFDA)
│   ├── sales_simulator.py      ← Augment scraped data with trends
│   └── requirements.txt
└── database/
    └── schema.sql              ← Supabase table definitions
```
