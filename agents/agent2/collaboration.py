from .models import Protocol, FeasibilityAssessment # Importing Protocol and FeasibilityAssessment models

def confirm_protocol_with_hypothesizer(protocol_json: Protocol) -> bool:
    """
    Simulates confirming the generated protocol with Agent 1 (Hypothesizer).
    Placeholder implementation.
    """
    print(f"CONFIRMING PROTOCOL WITH HYPOTHESIZER (Agent 1): {protocol_json.protocol_id}")
    # In a real scenario, this would involve an API call or message queue
    return True # Assume confirmed for now

def check_build_feasibility(validation_steps: list[dict], linked_hypothesis_id: str) -> FeasibilityAssessment:
    """
    Checks the build feasibility of the protocol by querying for external data
    and synthesizing it into a FeasibilityAssessment.
    """
    print(f"CHECKING BUILD FEASIBILITY for Hypothesis ID: {linked_hypothesis_id} with {len(validation_steps)} steps.")

    all_queries = []
    for i, step in enumerate(validation_steps):
        step_description = step.get('description', f'step_{i}_unnamed')
        queries = [
            f"Public datasets for {step_description}",
            f"Python libraries for {step_description}",
            f"Availability of computational model for {step_description}"
        ]
        all_queries.extend(queries)

    if not all_queries:
        return FeasibilityAssessment(
            data_obtainability='UNAVAILABLE',
            tools_availability='REQUIRES_DEVELOPMENT',
            confidence_score=0.25,
            summary="No validation steps provided to assess feasibility."
        )

    search_results = fetch_external_data(all_queries)

    # Placeholder logic to synthesize FeasibilityAssessment
    data_obtainability_found = False
    tools_availability_found = False

    summary_parts = [f"Feasibility assessment for Hypothesis ID: {linked_hypothesis_id}"]

    for query, result in search_results.items():
        summary_parts.append(f"- Query '{query}': {result}")
        if "Public datasets for" in query and "mocked_result" in result:
            data_obtainability_found = True
        if "Python libraries for" in query and "mocked_result" in result:
            tools_availability_found = True

    data_obtainability_status = 'PUBLIC' if data_obtainability_found else 'UNAVAILABLE'
    tools_availability_status = 'OPEN_SOURCE' if tools_availability_found else 'REQUIRES_DEVELOPMENT'

    # Example: More nuanced confidence based on findings
    confidence = 0.5
    if data_obtainability_found:
        confidence += 0.15
    if tools_availability_found:
        confidence += 0.15
    if not validation_steps: # Lower confidence if no steps to check
        confidence = 0.25

    # Ensure confidence is within bounds
    confidence = max(0.0, min(1.0, confidence))

    return FeasibilityAssessment(
        data_obtainability=data_obtainability_status,
        tools_availability=tools_availability_status,
        confidence_score=round(confidence, 2), # Round to two decimal places
        summary="\n".join(summary_parts)
    )

def fetch_external_data(search_queries: list[str]) -> dict[str, str]:
    """
    Simulates calling the Google Search API to fetch external data.
    Returns a dictionary of mocked data.
    """
    mocked_results = {}
    for query in search_queries:
        mocked_results[query] = f"mocked_result_for_{query.replace(' ', '_')}"
    return mocked_results
