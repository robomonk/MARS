# agents/agent3/execution_engine.py
import logging
from google.cloud import bigquery, storage
from google.cloud import aiplatform_v1beta1 as aiplatform  # Use v1beta1 for Notebooks
from .models import BuildStep # Adjusted relative import based on instruction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_build_step(step: BuildStep, project_id: str, location: str) -> bool:
    """
    Executes a single build step.

    Args:
        step: The BuildStep object to execute.
        project_id: The GCP project ID.
        location: The GCP location/region.

    Returns:
        True if the step was executed successfully, False otherwise.
    """
    logger.info(f"Executing step: {step.action} {step.type} {step.name}")

    try:
        if step.action == "create_resource":
            if step.type == "bigquery_dataset":
                client = bigquery.Client(project=project_id)
                dataset_id = f"{project_id}.{step.name}"
                dataset = bigquery.Dataset(dataset_id)
                if step.details and "description" in step.details:
                    dataset.description = step.details["description"]
                # dataset.location is not directly set on create, it uses client's location or project default
                client.create_dataset(dataset, timeout=30)
                logger.info(f"Successfully created BigQuery dataset: {dataset_id}")
                return True

            elif step.type == "gcs_bucket":
                client = storage.Client(project=project_id)
                bucket_name = step.name
                # Bucket names must be globally unique, often prefixed with project_id
                # For this implementation, we assume step.name is already globally unique or appropriately prefixed.
                bucket = client.create_bucket(bucket_name, location=location)
                logger.info(f"Successfully created GCS bucket: {bucket.name} in location {location}")
                return True

            elif step.type == "vertex_ai_notebook":
                # Ensure API is enabled: Vertex AI API, Notebooks API
                # Ensure service account has necessary permissions: Vertex AI User, Notebooks Admin (or more granular)
                client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
                client = aiplatform.NotebookServiceClient(client_options=client_options)

                parent = f"projects/{project_id}/locations/{location}"
                notebook_instance_id = step.name # This becomes the {instance_id} in the resource name

                # Default instance configuration (can be expanded via step.details)
                instance = {
                    "machine_type": "n1-standard-4", # Example machine type
                    # Add other configurations like vm_image, container_image, network, etc. as needed
                }
                if step.details:
                    # Allow overriding/extending instance config via step.details
                    # e.g., step.details = {"machine_type": "e2-medium", "vm_image": {...}}
                    instance.update(step.details.get("instance_config", {}))

                # Construct the NotebookInstance object
                # Note: The actual structure for NotebookInstance might be more complex.
                # This is a simplified version. Refer to GCP documentation for full spec.
                # The API expects a google.cloud.aiplatform_v1beta1.types.NotebookInstance object
                notebook_instance_obj = aiplatform.types.NotebookInstance(
                    name=f"{parent}/instances/{notebook_instance_id}", # Full resource name
                    machine_type=instance["machine_type"],
                    # Add other fields based on 'instance' dict and API requirements
                )
                if "vm_image" in instance: # Example for vm_image
                    notebook_instance_obj.vm_image = aiplatform.types.VmImage(**instance["vm_image"])
                elif "container_image" in instance: # Example for container_image
                     notebook_instance_obj.container_image = aiplatform.types.ContainerImage(**instance["container_image"])


                operation = client.create_instance(
                    parent=parent,
                    instance_id=notebook_instance_id,
                    instance=notebook_instance_obj
                )
                logger.info(f"Sent request to create Vertex AI Notebook: {notebook_instance_id}. Waiting for operation to complete...")
                # For long-running operations, you might not want to block here in a real API.
                # Consider returning a 202 Accepted and handling completion asynchronously.
                # For this exercise, we'll wait for a result.
                operation.result() # This will block until the operation is done or fails.
                logger.info(f"Successfully created Vertex AI Notebook: {notebook_instance_id}")
                return True

            else:
                logger.error(f"Unsupported resource type: {step.type}")
                return False
        else:
            logger.error(f"Unsupported action: {step.action}")
            return False

    except Exception as e:
        logger.error(f"Failed to execute step {step.name} ({step.type}): {e}", exc_info=True)
        # In a real scenario, you might want to include more details from the exception
        # or re-raise a custom exception.
        return False
