from pytest_bdd import scenarios
import os

# Use absolute path for features directory
features_path = os.path.join(os.path.dirname(__file__), "features")
scenarios(features_path)


