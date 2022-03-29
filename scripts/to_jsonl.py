#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import codecs
import fnmatch
import logging
import itertools
from multiprocessing import Pool

import bs4
from tqdm import tqdm


def recursive_iglob(rootdir='.', pattern='*'):
    """Recursive version of iglob.
    Taken from https://gist.github.com/whophil/2a999bcaf0ebfbd6e5c0d213fb38f489
    """
    for root, dirnames, filenames in os.walk(rootdir):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def fix_unclosed(tag_name, html):
    return re.sub(r'(<{}.*[^/-])>'.format(tag_name), r'\1 />', html)


def convert_jptimes(input_file, content):
    content = fix_unclosed('meta', content)
    content = fix_unclosed('link', content)
    doc = bs4.BeautifulSoup(content, 'html.parser')

    file_name_components = input_file.split('/')
    date = '/'.join(file_name_components[2:5])
    categories = file_name_components[5:-1]
    file_name = file_name_components[-1]
    url = 'https://' + input_file

    try:
        author = doc.find('meta', attrs={'name': 'author'})['content']
    except TypeError:
        try:
            author = doc.find('a', attrs={'class': 'author'}).text
        except AttributeError:
            logging.warning('jp:No author in {}'.format(input_file))

    # Extracting title
    title = doc.find('meta', property='og:title')
    if not title:
        logging.error('no title for {}'.format(input_file))
        #print(doc.find_all('meta'))
        #input()
        return
    title = re.sub(r'\s+', ' ', title['content']).strip()
    title = re.sub(r'\| The Japan Times', '', title)

    if not len(title):
        logging.error('no title for {}'.format(input_file))
        return

    # Extracting headline
    headline = doc.find('meta', property='og:description')
    if not headline:
        logging.error('no headline for {}'.format(input_file))
        return
    headline = re.sub(r'\s+', ' ', headline['content']).strip()

    if not len(headline):
        logging.error('no headline for {}'.format(input_file))
        return

    # Extracting article content
    body = doc.find('div', attrs={'id': 'jtarticle'})

    if not body:
        logging.error('no body for {}'.format(input_file))
        return

    body = re.sub(r'\s+', ' ', body.get_text(separator=' ')).strip()

    if not len(body):
        logging.error('no body for {}'.format(input_file))
        return

    # Extracting keywords
    keywords = doc.find('meta', attrs={'name': 'keywords'})
    if keywords is None:
        logging.error('no keywords for {}'.format(input_file))
        return

    keywords = re.sub(r'\s+', ' ', keywords['content']).strip()
    keywords = keywords.split(', ')
    # remove empty keywords
    keywords = [k.split(';') for k in keywords if k]

    if not keywords:
        logging.error('no keywords for {}'.format(input_file))
        return

    return {
        'title': title, 'headline': '', 'abstract': body,
        'keyword': keywords, 'file_name': file_name,
        'date': date, 'categories': categories, 'url': url,
        'author': author
    }


def convert_nytimes(input_file, content):
    doc = bs4.BeautifulSoup(content, 'html.parser')

    file_name_components = input_file.split('/')
    date = '/'.join(file_name_components[1:4])
    categories = file_name_components[4:-1]
    file_name = '.'.join(file_name_components[-1].split('.')[:-1])
    url = 'http://' + input_file

    # Removing script and style tags
    for script in doc(['script', 'style', 'link', 'button']):
        script.decompose()

    try:
        # Before 2013
        author = doc.find('meta', attrs={'name': 'author'})['content']
    except TypeError:
        # After 2013
        if not doc.find('meta', attrs={'name': 'byl'}):
            logging.warning('ny:No author in {}'.format(input_file))
            return None
        author = doc.find('meta', attrs={'name': 'byl'})['content']
        author = author.replace('By ', '')

    # Extracting title
    title = doc.find('meta', property='og:title')
    if not title:
        logging.error('no title for {}'.format(input_file))
        return
    title = re.sub(r'\s+', ' ', title['content']).strip()

    if not len(title):
        logging.error('no title for {}'.format(input_file))
        return

    # Extracting headline
    headline = doc.find('meta', property='og:description')
    if not headline:
        logging.error('no headline for {}'.format(input_file))
        return
    headline = re.sub(r'\s+', ' ', headline['content']).strip()

    if not len(headline):
        logging.error('no headline for {}'.format(input_file))
        return

    # Extracting article content
    body = doc.find('section', attrs={'name': 'articleBody'})

    if not body:
        body = doc.find_all('p', attrs={'class': 'story-body-text story-content'})
        if not body:
            logging.error('no body for {}'.format(input_file))
            return
        else:
            body = ' '.join([re.sub(r'\s+', ' ', p.get_text(separator=' ')).strip()
                            for p in body])
    else:
        body = re.sub(r'\s+', ' ', body.get_text(separator=' ')).strip()

    if not len(body):
        logging.error('no body for {}'.format(input_file))
        return

    # Extracting keywords
    keywords = doc.find('meta', attrs={'name': 'news_keywords'})

    if keywords is None:
        keywords = doc.find('meta', attrs={'name': 'keywords'})
        if not keywords:
            logging.error('no keywords for {}'.format(input_file))
            return

    keywords = re.sub(r'\s+', ' ', keywords['content']).strip()
    keywords = keywords.split(',')
    # remove empty keywords
    keywords = [k.split(';') for k in keywords if k]

    if not keywords:
        logging.error('no keywords for {}'.format(input_file))
        return

    return {
        'title': title, 'headline': headline, 'abstract': body,
        'keyword': keywords, 'file_name': file_name,
        'date': date, 'categories': categories, 'url': url,
        'author': author
    }


def process_file(input_file, id_=None):
    # Loading soup
    with open(input_file) as g:
        content = g.read()

    if 'nytimes' in input_file:
        res = convert_nytimes(input_file, content)
    elif 'japantimes' in input_file:
        res = convert_jptimes(input_file, content)
    else:
        logging.error(
            'Unrecognised file type : {}'.format(input_file))
    if res and id_:
        res['id'] = id_
    return res


if __name__ == '__main__':
    import argparse

    def arguments():
        parser = argparse.ArgumentParser(
            description='Converts html files to jsonl using a filelist')
        parser.add_argument(
            '-f', '--filelist', type=argparse.FileType('r'),
            help='Filelist file. If not given convert every found '
                 'file into `dataset.jsonl` without id')
        parser.add_argument(
            '-p', '--parallel', type=int,
            help='Number of thread to use for parallel processing')
        args = parser.parse_args()
        return args

    args = arguments()

    logging.basicConfig(level=logging.INFO)

    logging.info('start converting...')

    articles_processed = 0
    output_file = 'dataset.jsonl'
    jptimes_dir = 'www.japantimes.co.jp/'
    nytimes_dir = 'www.nytimes.co.jp/'
    webarchive_dir = 'web.archive.org/'
 
    if args.filelist:
        files = (l.strip().split('\t') for l in args.filelist)
        files = ((i, p.replace('https://', '')) for i, p in files)
        files = [(i, p) for i, p in files if os.path.isfile(p)]
        args.filelist.close()
        output_file = args.filelist.name.replace('url.filelist', 'jsonl')
    else:
        files = itertools.chain(
            #recursive_iglob(rootdir=jptimes_dir, pattern='[!.]*'),
            #recursive_iglob(rootdir=nytimes_dir, pattern='*.html')
            recursive_iglob(rootdir=webarchive_dir, pattern='*.html')
        )
        files = [(None, p) for p in files]

    def process_file_(args):
        return process_file(args[1], id_=args[0])

    logging.info('Writing to {}'.format(output_file))

    with codecs.open(output_file, 'w', 'utf-8') as f:
        with Pool(args.parallel) as pool:
            process = pool.imap_unordered(process_file_, files)

            for res in tqdm(process):
                if res:
                    f.write(json.dumps(res) + '\n')
                    articles_processed += 1

    logging.info('Converted {} articles'.format(articles_processed))
    if args.filelist and articles_processed != len(files):
            logging.info(
                'There are {} missing articles. Please (re)try downloading '
                'articles using download script'.format(len(files) - articles_processed)
            )
