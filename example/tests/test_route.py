"""
Routing tests.

Routing is the cheapest useful thing a domain-specific retrieval system does, and
the easiest to get quietly wrong: a router that silently sends everything to one
collection still returns plausible answers, so nothing looks broken.

These tests pin the two properties that matter — that a query lands in the right
collection, and that an unrecognised query lands somewhere explicit rather than
being forced into the nearest match.
"""
from example.route import DOMAINS, route


def test_coding_query_routes_to_coding():
    assert route("what were national discharges for MS-DRG 871") == "coding"


def test_risk_adjustment_routes_to_coding():
    assert route("HCC coefficient for diabetes with chronic complications") == "coding"


def test_coverage_query_routes_to_coverage():
    assert route("is transcatheter aortic valve replacement covered by Medicare") == "coverage"


def test_lcd_query_routes_to_coverage():
    assert route("which contractors publish an LCD for botulinum toxin") == "coverage"


def test_quality_query_routes_to_quality():
    assert route("national 30-day readmission rate for heart failure") == "quality"


def test_infection_query_routes_to_quality():
    assert route("what is the national CLABSI standardised infection ratio") == "quality"


def test_routing_is_case_insensitive():
    assert route("NATIONAL READMISSION RATE") == route("national readmission rate")


def test_unmatched_query_falls_back_to_general():
    """
    A query the router does not recognise goes to `general`, not to whichever
    domain happened to score highest. Forcing a match is how a router starts
    answering coverage questions out of the coding corpus.
    """
    assert route("what is the weather in Kansas City") == "general"


def test_general_is_a_declared_domain():
    """The fallback must be a real collection, not a magic string."""
    assert "general" in DOMAINS
