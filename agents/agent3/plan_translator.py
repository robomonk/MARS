# agents/agent3/plan_translator.py
from .models import AbstractProtocol, BuildPlan, BuildStep
import uuid # For generating unique plan_id

def translate_protocol_to_build_plan(protocol: AbstractProtocol) -> BuildPlan:
    # Initial dummy translation logic
    steps = []

    # Safely access data_requirement
    if protocol.data_requirement == 'structured_sql_db':
        # Ensure BuildStep arguments match the model definition
        # (action, type, name, details are the fields)
        steps.append(BuildStep(
            action='create_resource',
            type='bigquery_dataset',
            name=f'experiment_data_{protocol.protocol_id[:8]}',
            details={'description': 'Dataset for structured experiment data.'}
        ))
    elif protocol.data_requirement == 'text_file':
        steps.append(BuildStep(
            action='create_resource',
            type='cloud_storage_bucket',
            name=f'text_files_{protocol.protocol_id[:8]}',
            details={'description': 'Storage for text file based data.'}
        ))

    # Generate a unique plan_id using UUID
    generated_plan_id = str(uuid.uuid4())

    # Create the BuildPlan object, ensuring all required fields are present
    # BuildPlan requires: plan_id, protocol_id, steps, status
    build_plan = BuildPlan(
        plan_id=generated_plan_id,
        protocol_id=protocol.protocol_id, # Link back to the protocol
        steps=steps,
        status='pending_approval' # Default status
    )

    return build_plan
