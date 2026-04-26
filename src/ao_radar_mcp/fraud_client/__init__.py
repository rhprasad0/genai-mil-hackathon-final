"""Fraud-mock client.

Wraps ``boto3.client('lambda').invoke`` against the fraud-mock Lambda. The
only domain-level outbound integration. There is no general HTTP client.
"""
