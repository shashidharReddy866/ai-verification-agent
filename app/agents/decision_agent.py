from typing import Any, Dict
 
 
def run_decision_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decision Agent — The final step in the graph.
    Reviews the matching results and identity flags to make a final VERIFIED or FAILED decision.
    Consolidates all metadata into a clean final response.
    """
    matching = state.get("matching_result", {})
    identity = state.get("identity_result", {})
   
    # In case matching_agent hasn't been updated yet to use 'matching_result'
    if not matching and "final_result" in state:
        matching = state.get("final_result", {})
 
    failure_reasons = matching.get("failure_reasons", [])
    confidence_score = matching.get("confidence_score", 0.0)
   
    # Final Verdict logic
    # We can add additional business rules here if needed.
    # For now, we'll base it on whether there are any failure reasons.
    passed = len(failure_reasons) == 0
    status = "VERIFIED" if passed else "FAILED"
 
    final_result = {
        "status": status,
        "confidence_score": confidence_score,
        "identity_verified": passed,
        "can_proceed": passed,
        "flags": identity.get("flags", []),
        "failure_reason": "; ".join(failure_reasons) if failure_reasons else None,
        "decision_metadata": {
            "matching_scores": {
                "name": identity.get("name_score"),
                "dob": 1.0 if identity.get("dob_matched") else 0.0,
                "id": identity.get("id_score"),
                "quality": identity.get("quality_score"),
                "ocr": identity.get("ocr_confidence")
            }
        }
    }
 
    return {**state, "final_result": final_result}
