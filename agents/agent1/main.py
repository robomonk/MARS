import logging
from .hypothesis_builder import HypothesisBuilder

def main():
    # Configure basic logging for the application
    # This will cover logs from hypothesis_builder and state_machine if they use the standard logging setup
    logging.basicConfig(
        level=logging.INFO,  # Set to INFO for general run, DEBUG for detailed run
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler() # Outputs logs to stderr by default
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Initializing Agent 1: Hypothesis Builder...")

    try:
        agent = HypothesisBuilder()
        agent.run_interaction_loop()

        if agent.final_hypothesis_json:
            logger.info("Agent 1 finished successfully. Final hypothesis:")
            # The JSON is already printed by the logger in initiate_experiment_design
            # and optionally by the __main__ block of hypothesis_builder if run directly.
            # For main.py, we can just log that it's done or print it again if desired.
            print("\n--- Final Structured Hypothesis (from main.py) ---")
            print(agent.final_hypothesis_json)
        else:
            logger.info("Agent 1 finished, but no hypothesis was finalized.")

    except ImportError as e:
        logger.error(f"Failed to import HypothesisBuilder. Check PYTHONPATH and file structure: {e}")
        print("Error: Could not start the agent due to an import error. Ensure you are running this from the project root or the `agents` directory has been added to PYTHONPATH.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()
