import sys
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint = "http://qanswer-core1.univ-st-etienne.fr/api/endpoint/open/wikidata/sparql"
user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
sparql = SPARQLWrapper(endpoint, agent=user_agent)

# get the wikidata link and wikipedia link to the article  (subject)
# Wikidata: http://www.wikidata.org/entity/QId_of_entity
# Wikipedia: https://en.wikipedia.org/wiki/label_name_of_subject
"""
  params
  : entityId (category QId like video games Q7889)
  : property (relation PId like publisher P123) shoule be in format http://www.wikidata.org/prop/direct/P123
  : limit
"""
query_subject_wikidata_wikipedia_url = """
    PREFIX schema: <http://schema.org/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?entity ?wikipedia_link
        where {{
            ?entity <http://www.wikidata.org/prop/direct/P31> <http://www.wikidata.org/entity/{entityId}> .
            ?entity <{property}> ?answer_entity .
            ?wikipedia_link schema:about ?entity ;
            schema:isPartOf <https://en.wikipedia.org/>.
            }} limit {limit}
"""

# query to get object entity
"""
    :params
    :entity (QId like video games Q7889) in format, http://www.wikidata.org/entity/Q7889
    :property (relation PId like publisher P123) shoule be in format http://www.wikidata.org/prop/direct/P123
"""
query_object = """
    PREFIX schema: <http://schema.org/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    select ?answer_entity
        where {{
            # s needs to have a wikipedia link
            <{entity}> <{property}> ?answer_entity .
            }}
"""

# query to get all labels
"""
    :params
    :entity 
"""
query_all_labels = """
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            select ?label
                where {{
                {{
                    ?property wikibase:directClaim <{entity}> .
                    ?property rdfs:label ?label .
                    filter(lang(?label)='en').
                }} UNION {{
                    ?property wikibase:directClaim <{entity}> .
                    ?property skos:altLabel ?label .
                    filter(lang(?label)='en').
                }}
                }} limit 3000
"""

# get one label for subject
"""
    :params
    :entity entity_url to subject, shoule be in the format like: http://www.wikidata.org/entity/Q7889
"""
query_label = """
    PREFIX wikibase: <http://wikiba.se/ontology#>
    select ?label
        where {{
            <{entity}> rdfs:label ?label.
            filter(lang(?label)='en').
        }} limit 3000
"""

def construct_query_for_entity(entity_id):
    if entity_id[0] == 'Q':
        query = """
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        select ?p ?c where {
                {
                    select ?p (count(?s) as ?c ) where 
                    {
                      ?s  wdt:P31 <http://www.wikidata.org/entity/""" + entity_id + """> .
                      ?s ?p ?o .
                    } group by ?p limit 500
                }
                ?s2 wikibase:directClaim ?p .
                ?s2 wikibase:propertyType wikibase:WikibaseItem
                } order by desc(?c)"""
    else:
        raise ValueError('Wrong EntityId, e.g. Q11032')

    return query

def request_from_endpoint(query=None):
    if query is None:
        raise ValueError("query can't be None")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql_result = sparql.query().convert()
    return sparql_result


# playground
if __name__ == "__main__":
    entity = "http://www.wikidata.org/entity/Q100042"
    property = "http://www.wikidata.org/prop/direct/P123"
    response_content = request_from_endpoint(query=query_object.format(entity=entity, property=property))
    answers = []
    for answer in response_content["results"]["bindings"]:
        answers.append(answer['answer_entity']['value'])
    print(answers)

