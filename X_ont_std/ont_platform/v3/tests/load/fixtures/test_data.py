"""Benchmark SPARQL query definitions for load testing"""

# Pattern #18: Simple ID lookup with property extraction
QUERY_PATTERN_18 = """
PREFIX ex: <http://test.org/>
SELECT ?name WHERE {
    ex:ship1 ex:name ?name
}
"""

# Pattern #19: Type filtering
QUERY_PATTERN_19 = """
PREFIX ex: <http://test.org/>
SELECT ?ship WHERE {
    ?ship a ex:Ship
}
"""

# Pattern #20: Numeric comparison with FILTER
QUERY_PATTERN_20 = """
PREFIX ex: <http://test.org/>
SELECT ?part ?cost WHERE {
    ?part ex:cost ?cost
    FILTER (?cost > 500)
}
"""

# Pattern #21: Equality filtering
QUERY_PATTERN_21 = """
PREFIX ex: <http://test.org/>
SELECT ?ship WHERE {
    ?ship ex:status "Active"
}
"""

# Pattern #24: 1-hop relationship + property filter
QUERY_PATTERN_24 = """
PREFIX ex: <http://test.org/>
SELECT ?part ?cost WHERE {
    ex:supplier1 ex:supplies ?part .
    ?part ex:cost ?cost
    FILTER (?cost > 500)
}
"""

# Pattern #25: 2-hop relationship join
QUERY_PATTERN_25 = """
PREFIX ex: <http://test.org/>
SELECT ?part WHERE {
    ex:ship1 ex:has_block ?block .
    ?block ex:has_part ?part
}
"""

# Pattern #26: 2-hop relationship + final property filter
QUERY_PATTERN_26 = """
PREFIX ex: <http://test.org/>
SELECT ?part ?rating WHERE {
    ex:project1 ex:involves_supplier ?supplier .
    ?supplier ex:supplies ?part .
    ?part ex:quality_rating ?rating
    FILTER (?rating >= 5)
}
"""

# Combined queries suite
BENCHMARK_QUERIES = {
    "Pattern_18_Lookup": QUERY_PATTERN_18,
    "Pattern_19_Type": QUERY_PATTERN_19,
    "Pattern_20_NumFilter": QUERY_PATTERN_20,
    "Pattern_21_EqFilter": QUERY_PATTERN_21,
    "Pattern_24_1HopFilter": QUERY_PATTERN_24,
    "Pattern_25_2Hop": QUERY_PATTERN_25,
    "Pattern_26_2HopFilter": QUERY_PATTERN_26,
}
