"""Require all published synthetic extraction labels to stay correct."""

from scripts.evaluate import evaluate


def test_published_parser_benchmark():
    result = evaluate()
    assert not result["failures"], result["failures"]
