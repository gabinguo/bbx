import requests
import urllib.parse as uparse
import logging
import json
from typing import List
from .util import normalize_answer
from .sparql_queries import request_from_endpoint, query_subject_wikidata_wikipedia_url, query_all_labels, query_label, \
    query_object, construct_query_for_entity
from tqdm import tqdm
from multiprocessing import Pool as ProcessPool
import uuid
import random
import time
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s\t[%(levelname)s]\t%(message)s', datefmt='%Y-%m-%d,%H:%M:%S')


def request_object(entity, property):
    entity_url = f"http://www.wikidata.org/entity/{entity}"
    property_url = f"http://www.wikidata.org/prop/direct/{property}"
    response_content = request_from_endpoint(query=query_object.format(entity=entity_url, property=property_url))
    answers = []
    for answer in response_content["results"]["bindings"]:
        answers.append(answer['answer_entity']['value'])
    return answers


# get the label(s) of property
def request_all_labels(identifier: str):
    property_url = f"http://www.wikidata.org/prop/direct/{identifier}"
    results = request_from_endpoint(query_all_labels.format(entity=property_url))
    labels = []
    for result in results["results"]["bindings"]:
        labels.append(result["label"]["value"])
    if len(labels) != 0:
        return labels
    raise ValueError("Labels returned is empty, check the query.")


# get the label for subject
def request_label(entity):
    entity_url = f"http://www.wikidata.org/entity/{entity}"
    response = request_from_endpoint(query_label.format(entity=entity_url))
    label = response["results"]["bindings"][0]["label"]["value"]
    return label


def fetch_full_text(title):
    url = "https://en.wikipedia.org/w/api.php"
    querystring = {"action": "query",
                   "format": "json",
                   "titles": uparse.unquote(title),
                   "prop": "extracts",
                   "explaintext": "",
                   "exlimit": "max",
                   "redirects": ""}
    try:
        response = requests.request("GET", url, params=querystring, timeout=15)
    except requests.exceptions.ReadTimeout:
        response = requests.request("GET", url, params=querystring, timeout=60)
    json_response = json.loads(response.text).get('query').get('pages')
    key = list(json_response.keys())
    return json.loads(response.text).get('query').get('pages').get(key[0]).get('extract')


def process_full_text(article: str):
    def remove_empty_lines(article, limit=10):
        paragraphs = article.split("\n")
        paragraphs = [para for para in paragraphs if len(para.split()) > limit]
        return "\n".join(paragraphs)

    return remove_empty_lines(article)


def construct_question(labels, number=5):
    labels.sort(key=lambda s: -len(s))
    question_list = labels[0:min(len(labels), number)]
    question_list = [q + ' ?' for q in question_list]
    return question_list


def formulate_queries_in_squad_style(triplets, question_map):
    def fill_squad_fields(title, context, question, question_id, text, answer_start, is_impossible):
        return {
            "title": title,
            "paragraphs": [{
                "context": context,
                "qas": [{
                    "question": question,
                    "id": question_id,
                    "answers": [{
                        "text": text,
                        "answer_start": answer_start
                    }],
                    "is_impossible": is_impossible
                }]
            }]
        }

    query_pool = []
    for relation in triplets:
        for entity in triplets[relation]:
            subject_label = triplets[relation][entity]["subject_label"]
            subject_article = triplets[relation][entity]["subject_article"]
            text = triplets[relation][entity]["text"]
            for question_ in question_map[relation]:
                query = ""
                if subject_article.find(text) != -1:
                    query = fill_squad_fields(subject_label, subject_article, question_, str(uuid.uuid4()),
                                              text, subject_article.find(text), False)
                elif subject_article.find(text.lower()) != -1:
                    query = fill_squad_fields(subject_label, subject_article, question_, str(uuid.uuid4()),
                                              text.lower(), subject_article.find(text.lower()), False)
                elif subject_article.find(normalize_answer(text)) != -1:
                    query = fill_squad_fields(subject_label, subject_article, question_, str(uuid.uuid4()),
                                              normalize_answer(text),
                                              subject_article.find(normalize_answer(text)), False)
                if query:
                    query_pool.append(query)
    return query_pool


# query the triplets from one specific category
def request_triplets(category: str = "Q7889", relations: List[str] = None, limit=500, top_k=5,
                     relation_excluded=["P31"], num_workers=12):
    if not category or category[0] != 'Q':
        raise ValueError("category can't be None and it must start with 'Q'.")
    if not relations:
        logging.info(f"relations is empty, will automatic query the top-{top_k} relations for category: {category}")
        query_top_k_relations = construct_query_for_entity(category)
        results = request_from_endpoint(query_top_k_relations)
        relations = [result['p']['value'].split('/')[-1] for result in results if
                     result['p']['value'].split('/')[-1] not in relation_excluded]

    triplets = {}
    for relation in tqdm(relations, desc="Request Wikidata/Wikipedia url of subject: "):
        property_url = f"http://www.wikidata.org/prop/direct/{relation}"
        resultsAll = request_from_endpoint(
            query_subject_wikidata_wikipedia_url.format(property=property_url, entityId=category, limit=limit))
        result_map = dict()
        for result in resultsAll["results"]["bindings"]:
            qid = result["entity"]["value"].split('/')[-1]
            result_map[qid] = {
                "subject_wikidata_url": result["entity"]["value"],
                "subject_wikipedia_url": result["wikipedia_link"]["value"],
                "subject_label": result["wikipedia_link"]["value"].split("/")[-1]
            }
        triplets[relation] = result_map

    trash_pool = []

    def combined_operations(payload):
        start_time = time.time()
        triplets_, relation_, entity_ = payload
        article_ = process_full_text(
            fetch_full_text(triplets_[relation_][entity_]["subject_label"]))
        answer_url_ = request_object(entity_, relation_)[0]
        answer_label_ = request_label(answer_url_.split("/")[-1])
        print(
            f"Done in {str(round(time.time() - start_time, 2)) + 's':>8}, entity[{entity_}: {triplets_[relation_][entity_]['subject_label']}], relation[{relation_}]",
            end="\n")
        return article_, answer_label_, answer_url_, relation_, entity_

    processes = []
    console = Console()
    with console.status("[bold green]Process the tasks...[/bold green]") as status:
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for relation in tqdm(triplets, desc="Send task to the multi-threading pool"):
                for entity in triplets[relation]:
                    try:
                        processes.append(executor.submit(combined_operations, (triplets, relation, entity)))
                    except:
                        trash_pool.append((relation, entity))
                        logging.info("Trash bin + 1")
                        continue
        for task in as_completed(processes):
            article, answer_label, answer_url, relation_task, entity_task = task.result()
            if article and answer_label and answer_url:
                triplets[relation_task][entity_task]["subject_article"] = article
                triplets[relation_task][entity_task]["text"] = answer_label
                triplets[relation_task][entity_task]["answer_url"] = answer_url
            else:
                trash_pool.append((relation_task, entity_task))
                logging.info("Trash bin + 1")
        console.log("Completed tasks.")

    for trash in trash_pool:
        del triplets[trash[0]][trash[1]]
    logging.info(f"Empty trash bin, {len(trash_pool)} examples are thrown away")

    return triplets


def main():
    """
        Configurations
    """
    start_time = time.time()
    NUMBER_QUESTIONS = 5
    LIMIT_TRIPLETS_PER_RELATION = 10
    NUMBER_WORKERS = 12
    CATEGORY = "Q7889"  # Video Game
    # RELATIONS = ["P123", "P178", "P136", "P495", "P577", "P750", "P400", "P404", "P921", "P737"]
    OUTPUT_FILENAME = "tryout"
    RELATIONS = ["P123"]

    """
        Workflow
    """
    # get the general information about triplets
    triplets = request_triplets(CATEGORY, relations=RELATIONS, limit=LIMIT_TRIPLETS_PER_RELATION,
                                num_workers=NUMBER_WORKERS)

    # label map => question map for properties
    label_map = {relation: request_all_labels(relation) for relation in triplets}
    question_map = {relation: construct_question(label_map[relation], NUMBER_QUESTIONS) for relation in label_map}

    # transform the information to SQuAD style to train Question-Answering Training
    query_pool = formulate_queries_in_squad_style(triplets, question_map)
    random.shuffle(query_pool)

    logging.info(f"[Finished] Generated {len(query_pool)} examples")

    with open(f"./{OUTPUT_FILENAME}.json", 'w') as f:
        json.dump({"version": "known_relations", "data": query_pool}, f)

    logging.info(f"Time used {round(time.time() - start_time, 2)}s")


if __name__ == "__main__":
    main()
