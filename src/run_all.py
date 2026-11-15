"""Execute tout le pipeline de bout en bout : python src/run_all.py"""
import importlib, time
for m in ["s01_prepare_sales", "s02_generate_reviews", "s03_nlp_enrich", "s04_export_powerbi", "s05_validate_effects"]:
    t = time.time(); print(f"\n=== {m} ===")
    importlib.import_module(m).main(); print(f"({time.time()-t:.1f}s)")
