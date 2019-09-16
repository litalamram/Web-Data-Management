import sys
import requests
import lxml.html
import rdflib
from rdflib import XSD, Literal, RDF
import re

wiki_prefix = "http://en.wikipedia.org"
ontology = rdflib.Graph()


def question_1():
    print "pm " + how_many_pm()
    print "countries " + how_many_countries()
    print "republic " + how_many_republic()
    print "monarchy " + how_many_monarchy()


def how_many_countries():
    q = "SELECT (count(distinct ?c) as ?num)  " \
        "WHERE {" \
        " ?c a <http://example.org/country>  . " \
        "}"
    gra = rdflib.Graph()
    gra.parse("ontology.nt", format="nt")
    rows = gra.query(q)
    return list(rows)[0][0]


def how_many_pm():
    q = "SELECT (count(distinct ?p) as ?num)  " \
        "WHERE {" \
        " ?c  <http://example.org/prime_minister> ?p . " \
        "}"
    gra = rdflib.Graph()
    gra.parse("ontology.nt", format="nt")
    rows = gra.query(q)
    return list(rows)[0][0]


def how_many_republic():
    q = "SELECT (count(distinct ?c) as ?num)  " \
        "WHERE {" \
        " ?c  <http://example.org/government> ?p . " \
        "FILTER regex(str(?p), 'republic')" \
        "}"
    gra = rdflib.Graph()
    gra.parse("ontology.nt", format="nt")
    rows = gra.query(q)
    return list(rows)[0][0]


def how_many_monarchy():
    q = "SELECT (count(distinct ?c) as ?num)  " \
        "WHERE {" \
        " ?c  <http://example.org/government> ?p . " \
        "FILTER regex(str(?p), 'monarchy')" \
        "}"
    gra = rdflib.Graph()
    gra.parse("ontology.nt", format="nt")
    rows = gra.query(q)
    return list(rows)[0][0]


def get_query_answer(query):
    gra = rdflib.Graph()
    gra.parse("ontology.nt", format="nt")
    res = gra.query(query)
    return list(res)


def add_to_ontology(part1, part2, part3, is_date=False, is_string=False):
    part1 = part1.rstrip()
    part3 = part3.rstrip()
    part1 = part1.replace(" ", "_").replace("\n", "")
    part3 = part3.replace(" ", "_").replace("\n", "")

    str1 = rdflib.URIRef('http://example.org/' + part1)
    str2 = rdflib.URIRef('http://example.org/' + part2)

    if is_date:
        str3 = Literal(part3, datatype=XSD.date)
    elif is_string:
        str3 = Literal(part3, datatype=XSD.string)
    else:
        str3 = rdflib.URIRef('http://example.org/' + part3)

    ontology.add((str1, str2, str3))


def add_type_to_ontology(part1, part3):
    part1 = part1.replace(" ", "_").replace("\n", "")
    part3 = part3.replace(" ", "_").replace("\n", "")

    str1 = rdflib.URIRef('http://example.org/' + part1)

    str3 = rdflib.URIRef('http://example.org/' + part3)

    ontology.add((str1, RDF.type, str3))


def get_country_info(url, name):
    res = requests.get(url)
    doc = lxml.html.fromstring(res.content)
    a = doc.xpath("//table[contains(@class, 'infobox')]")
    if len(a) == 0:
        return

    # prime minister
    pm = a[0].xpath(".//tr[th//text()[.='Prime Minister']]/td")
    if len(pm) > 0:
        pm_name = pm[0].xpath(".//text()")[0]
        pm_link = pm[0].xpath(".//a/@href")
        add_to_ontology(name, "prime_minister", pm_name)
        if len(pm_link) > 0:
            get_person_info(wiki_prefix + pm_link[0], pm_name)

    # president
    president = a[0].xpath(".//tr[th//text()[.='President']]/td")

    if len(president) > 0:
        president_name = president[0].xpath(".//text()")[0]
        president_link = president[0].xpath(".//a/@href")[0]
        add_to_ontology(name, "president", president_name)
        if len(president_link) > 0:
            get_person_info(wiki_prefix + president_link, president_name)

    # government
    government = a[0].xpath(".//tr[th//text()[contains(., 'Government')]]/td//text()[not(ancestor::sup)]")
    if len(government) > 0:
        gov = ' '.join([g.rstrip() for g in government if len(g.rstrip()) > 0])
        gov = gov.split("( de jure )")[0]
        gov = gov.split("(de jure)")[0]
        add_to_ontology(name, "government", gov)

    # capital city
    capital = a[0].xpath(".//th[contains(text(), 'Capital')]/../td//text()")
    if len(capital) > 0:
        add_to_ontology(name, "capital", capital[0])

    # area
    area = a[0].xpath(".//th[contains(a/text(), 'Area')]/../following-sibling::tr/td/text()")
    if len(area) > 0:
        add_to_ontology(name, "area", area[0].replace('\u00A0', '') + '2', False, True)

    # population
    population = a[0].xpath(".//th[contains(a/text(), 'Population')]/../following-sibling::tr/td/text()")
    if len(population) > 0:
        add_to_ontology(name, "population", population[0].split(" ")[0], False, True)


def get_person_info(url, name):
    res = requests.get(url)
    doc = lxml.html.fromstring(res.content)
    a = doc.xpath("//table[contains(@class, 'infobox')]")
    if len(a) == 0:
        return

    dob = a[0].xpath(".//td//span[@class='bday']//text()")
    if len(dob) > 0:
        add_to_ontology(name, "birth_date", dob[0], True)
    else:
        dob = a[0].xpath(".//th[contains(text(), 'Born')]/../td//text()")
        if len(dob) > 0:
            add_to_ontology(name, "birth_date", dob[0], True)


def get_all_countries(url):
    res = requests.get(url)
    document = lxml.html.fromstring(res.content)

    # countries table
    rows = document.xpath("//h2/span[contains(text(),'List')]/following::table//tr/td[2]/a")

    # iterate over the countries
    for r in rows:
        countries = r.xpath("./text()")
        countries_links = r.xpath("./@href")
        for i in range(len(countries)):
            add_type_to_ontology(countries[i], "country")
            get_country_info(wiki_prefix + countries_links[i], countries[i])


def build_ontology(file_name):
    f = open(file_name, 'a+')
    get_all_countries("https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)")
    ontology.serialize(file_name, format="nt")
    f.close()


def parse_question(nl_question):
    # who/what is the ... of ...?
    q1 = "SELECT ?e " \
         "WHERE {{" \
         "    <http://example.org/{0}>  <http://example.org/{1}> ?e ." \
         "}}"

    # who is...?
    q2 = "SELECT ?e ?r " \
         "WHERE {{" \
         "    ?e ?r <http://example.org/{0}> ." \
         "}}"

    # when was the... of ... born?
    q3 = "SELECT ?date " \
         "WHERE {{" \
         "    <http://example.org/{0}> <http://example.org/{1}> ?e ." \
         "    ?e <http://example.org/birth_date> ?date" \
         "}}"

    if nl_question.startswith("Who is the"):
        relation, entity = re.findall(r"Who is the (.*?) of (.*?)\?", nl_question)[0]
        query = q1.format(entity.replace(' ', '_'), relation.lower().replace(' ', '_'))

    elif nl_question.startswith("Who"):
        entity = re.findall(r"Who is (.*?)\?", nl_question)[0]
        query = q2.format(entity.replace(' ', '_'))

    elif nl_question.startswith("What"):
        relation, entity = re.findall(r"What is the (.*?) of (.*?)\?", nl_question)[0]
        query = q1.format(entity.replace(' ', '_'), relation.lower().replace(' ', '_'))

    elif nl_question.startswith("When"):
        relation, entity = re.findall(r"When was the (.*?) of (.*?) born\?", nl_question)[0]
        query = q3.format(entity.replace(' ', '_'), relation.lower().replace(' ', '_'))

    else:
        print("wrong question")
        sys.exit(-1)

    res = get_query_answer(query)
    if len(res) > 0:
        if nl_question.startswith("Who is") and not nl_question.startswith("Who is the"):
            print "{0} of".format(res[0][1].replace("http://example.org/", "").replace("_", " ").capitalize()),
            countries = [r[0].replace("http://example.org/", "").replace("_", " ") for r in res]
            print ", ".join(countries)

        else:
            print res[0][0].replace("http://example.org/", "").replace("_", " ")
    return res


if __name__ == '__main__':
    if sys.argv[1] == "create":
        build_ontology(sys.argv[2])
    elif sys.argv[1] == "question":
        q = " ".join(sys.argv[2:])
        parse_question(q)
