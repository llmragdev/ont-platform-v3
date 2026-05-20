import pandas as pd
import json

paths = {
    "db": r"E:\ontology_edu\X_rag_std\pre-work\work_2025\rag_comunity\가이드 자료\01-발표가이드\가이드 자료 배포 - 20240401\WC_DB설계서_v1.0_20240321.xlsx",
    "api": r"E:\ontology_edu\X_rag_std\pre-work\work_2025\rag_comunity\가이드 자료\01-발표가이드\가이드 자료 배포 - 20240401\WC_인터페이스명세서_v1.0_20240321.xlsx"
}

output = {}

for key, path in paths.items():
    try:
        xls = pd.ExcelFile(path)
        output[key] = {"sheets": xls.sheet_names, "summary": {}}
        for sheet in xls.sheet_names:
            if sheet.lower() in ["목차", "개정이력", "cover"]: continue
            df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
            output[key]["summary"][sheet] = df.head(3).to_json(orient="records", force_ascii=False)
    except Exception as e:
        output[key] = str(e)

with open(r"E:\ontology_edu\X_rag_std\excel_summary.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("Done")
