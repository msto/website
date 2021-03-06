#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2017 Matthew Stone <mstone5@mgh.harvard.edu>
# Distributed under terms of the MIT license.

"""

"""

import itertools
from datetime import datetime
from Bio import Entrez


def parse_pubmed_date(article):
    """
    citation : Bio.Entrez.Parser.CitationElement
    """
    issue = article['MedlineCitation']['Article']['Journal']['JournalIssue']
    pub_date = issue['PubDate']

    if 'Day' not in pub_date:
        fmt = "{year} {month}"
        day = None
    else:
        fmt = "{year} {month} {day}"
        day = issue['PubDate']['Day']

    return fmt.format(year=issue['PubDate']['Year'],
                      month=issue['PubDate']['Month'],
                      day=day)


def parse_pubmed_issue(citation):
    """
    citation : Bio.Entrez.Parser.CitationElement
    """
    issue = citation['Journal']['JournalIssue']

    fmt = "{volume}({issue}):{page}"

    return fmt.format(volume=issue['Volume'],
                      issue=issue['Issue'],
                      page=citation['Pagination']['MedlinePgn'])


def set_title_case(title):
    title = title.replace(u'\xa0', ' ').rstrip('.')
    words = title.split()

    cased_title = ''
    for i, word in enumerate(words):
        # if word is all caps (i.e. gene name), leave it as such
        if word.isupper():
            cased = word
        # Only capitalize first word
        elif i == 0:
            cased = word.capitalize()
        else:
            cased = word.lower()

        if i == 0:
            cased_title += cased
        elif i == len(words) - 1:
            cased_title += '\xa0' + cased
        else:
            cased_title += ' ' + cased

    return cased_title


def format_pubmed_citation(article):
    """
    article : Bio.Entrez.Parser.DictionaryElement
    """

    # Parse doi
    for data in article['PubmedData']['ArticleIdList']:
        if data.attributes['IdType'] == 'doi':
            doi = 'DOI: [{0}](https://doi.org/{0})'.format(str(data))
        elif data.attributes['IdType'] == 'pubmed':
            pmid = 'PMID: [{0}](https://www.ncbi.nlm.nih.gov/pubmed/{0})'
            pmid = pmid.format(str(data))

    # get article data
    citation = article['MedlineCitation']['Article']

    def _parse_author(author):
        name = author['LastName'] + ' ' + author['Initials']
        if name == "Stone MR":
            name = "**{0}**".format(name)
        return name

    authors = [_parse_author(author) for author in citation['AuthorList']]
    authors = ', '.join(authors)

    #  title = citation['ArticleTitle'].replace(u'\xa0', ' ').rstrip('.')
    title = citation['ArticleTitle'].rstrip('.')
    title = set_title_case(title)
    journal = citation['Journal']['ISOAbbreviation'].replace('.', '')

    date = parse_pubmed_date(article)
    issue = parse_pubmed_issue(citation)

    # note: trailing doublespace necessary for line break in markdown
    citation = ("{authors}. {title}.  \n"
                "_{journal}_. {date};{issue}.  \n"
                "{pmid}. {doi}.")
    citation = citation.format(**locals())

    return citation


def scrape_pubmed(idlist):
    """
    idlist : list of str
        pubmed IDs
    """
    Entrez.email = 'matthew.stone12@gmail.com'
    handle = Entrez.efetch(db='pubmed', retmode='xml', id=','.join(idlist))
    results = Entrez.read(handle)
    articles = results['PubmedArticle']

    def _timestamp(article):
        date = parse_pubmed_date(article)
        if len(date.split()) == 3:
            return datetime.strptime(parse_pubmed_date(article), '%Y %b %d')
        else:
            return datetime.strptime(parse_pubmed_date(article), '%Y %b')

    articles = sorted(articles, key=lambda a: _timestamp(a))[::-1]

    citations = [format_pubmed_citation(article) for article in articles]

    return citations


def get_year(citation):
    return citation.split('\n')[1].split('_. ')[1].split()[0]


def write_citations(citations, fout):
    idx = len(citations)
    citations = sorted(citations, key=get_year)[::-1]

    for year, cites in itertools.groupby(citations, get_year):
        fout.write('### {year}\n'.format(year=year))

        citelist = []
        for i, cite in enumerate(cites):
            cite = '{0}\n'.format(cite)
            idx -= 1
            citelist.append(cite)

        cites = '\n'.join(citelist)
        fout.write(cites)
        fout.write('\n')


def main():
    PUBMED_LIST = open("_data/pubmed_ids.list")
    pubmed_ids = [p.strip() for p in PUBMED_LIST.readlines()]

    # terrible don't do any of this
    BIORXIV_LIST = open("_data/biorxiv_citations.md")
    biorxiv_citations = []
    for line in BIORXIV_LIST:
        citation = line + next(BIORXIV_LIST) + next(BIORXIV_LIST).strip()
        biorxiv_citations.append(citation)

        try:
            next(BIORXIV_LIST)
        except:
            continue

    CITATION_PAGE = open("publications.md", 'w')

    CITATION_PAGE.write("---\n"
                        "layout: page\n"
                        "title: Publications\n"
                        "permalink: /publications/\n"
                        "---\n")

    citations = scrape_pubmed(pubmed_ids)
    citations = citations + biorxiv_citations
    write_citations(citations, CITATION_PAGE)


if __name__ == '__main__':
    main()
