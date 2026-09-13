# AraFakeNews Streamlit Evaluation App

This folder contains the Streamlit human-evaluation app extracted from the
final `%%writefile app.py` cell of `Untitled135.ipynb`.

## Folder structure

```text
AraFakeNews_Streamlit_Deployment/
├── app.py
├── requirements.txt
├── README.md
└── data/
    └── GeneratedImagesToEvaluate/
        ├── generated_image_dataset_filtered.csv
        ├── user_demographics.csv          # created automatically
        └── <evaluation image files>
```

## Required data

Copy these into `data/GeneratedImagesToEvaluate/`:

1. `generated_image_dataset_filtered.csv`
2. The image files referenced by the CSV.

The app expects the CSV to contain at least:
- `generated_image_path`
- `title`
- optionally `caption`

The app automatically creates the evaluation columns if they do not exist.

## Important deployment note

The original notebook used Google Colab paths such as `/content/...`.
The extracted deployment version has been adapted to use paths relative to
the repository instead.

The app currently saves participant demographics and ratings back into CSV
files. A cloud deployment's local filesystem should NOT be treated as a
permanent database. Before collecting real thesis participants, configure
persistent storage (for example Google Sheets, Supabase, or another database)
so ratings cannot disappear after a restart/redeploy.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
# arafakenews-evaluation
