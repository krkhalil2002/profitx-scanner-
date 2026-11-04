import os
import sys

# Lets tests import filters.py / providers.py the same way Lambda does.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions", "scanner"))
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
