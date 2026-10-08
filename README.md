# Panelboard Enclosure Sizing

Streamlit report comparing standard panelboard enclosure sizes for Siemens P1–P5 interiors:

- **Recommended — 3 sizes:** 50" × 20" × 5.75", 74" × 20" × 5.75", and a 90" × 38" power box.
- **Alternative — 4 sizes:** adds Siemens' P3 box, 80" × 24" × 7.75".

Each chart plots every panelboard from 30 project submittals (all manufacturers) by its submitted width and height,
with the standard boxes drawn as outlines. Sizing follows the Siemens SpeedFax Section 11 selection tables.

`data/panels.csv` is anonymized: one row per panelboard with manufacturer, Siemens family, amps, poles,
the box size its Siemens interior needs (`need_*`) and the box size as submitted (`submitted_*`).
Project names, panel tags and submittal notes are not included.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
