from app.services.cache import get_title_with_credits


def find_shared(title_id_1, media_type_1, title_id_2, media_type_2):
    """Find shared cast and crew between two titles (uses DB cache)."""
    details_1 = get_title_with_credits(title_id_1, media_type_1)
    details_2 = get_title_with_credits(title_id_2, media_type_2)

    # Build lookup dicts by person_id
    cast_1 = {c["person_id"]: c for c in details_1["cast"]}
    cast_2 = {c["person_id"]: c for c in details_2["cast"]}
    crew_1 = {c["person_id"]: c for c in details_1["crew"]}
    crew_2 = {c["person_id"]: c for c in details_2["crew"]}

    # Set intersection
    shared_cast_ids = set(cast_1.keys()) & set(cast_2.keys())
    shared_crew_ids = set(crew_1.keys()) & set(crew_2.keys())

    # Remove people who appear in shared cast from shared crew (avoid duplicates)
    shared_crew_ids -= shared_cast_ids

    shared_cast = []
    for pid in shared_cast_ids:
        shared_cast.append({
            "person_id": pid,
            "name": cast_1[pid]["name"],
            "profile_path": cast_1[pid]["profile_path"],
            "role_1": cast_1[pid].get("character", ""),
            "role_2": cast_2[pid].get("character", ""),
            "order": min(cast_1[pid].get("display_order", 999),
                         cast_2[pid].get("display_order", 999)),
        })
    shared_cast.sort(key=lambda x: x["order"])

    shared_crew = []
    for pid in shared_crew_ids:
        shared_crew.append({
            "person_id": pid,
            "name": crew_1[pid]["name"],
            "profile_path": crew_1[pid]["profile_path"],
            "role_1": crew_1[pid].get("job", ""),
            "role_2": crew_2[pid].get("job", ""),
            "department": crew_1[pid].get("department", ""),
        })
    dept_order = {"Directing": 0, "Writing": 1, "Production": 2, "Sound": 3, "Camera": 4}
    shared_crew.sort(key=lambda x: (dept_order.get(x["department"], 99), x["name"]))

    return {
        "title_1": {"title": details_1["title"], "year": details_1["release_year"],
                     "media_type": details_1["media_type"], "poster_path": details_1["poster_path"]},
        "title_2": {"title": details_2["title"], "year": details_2["release_year"],
                     "media_type": details_2["media_type"], "poster_path": details_2["poster_path"]},
        "shared_cast": shared_cast,
        "shared_crew": shared_crew,
        "total_shared": len(shared_cast) + len(shared_crew),
    }
