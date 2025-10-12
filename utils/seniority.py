def infer_seniority(title: str | None) -> str | None:
    if not title:
        return None
    t = title.lower()
    if any(k in t for k in ["intern","junior","jr","entry"]): return "entry"
    if any(k in t for k in ["manager","mgr","management","head"]): return "manager"
    if any(k in t for k in ["lead","principal","staff"]): return "lead"
    if any(k in t for k in [" sr ","senior","sr.","senior-"]): return "senior"
    return "mid"
