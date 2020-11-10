#! /usr/bin/env python3

from bs4 import BeautifulSoup
import requests
import datetime
import os
import pprint
import pickle
import argparse
import hashlib

DOMAIN = 'https://amma.org'
BASE = DOMAIN + '/groups/north-america/amma-center-michigan'
EVENTS = BASE + '/events'
NEWS = BASE + '/news'
EVENT_CUTOFF_DAYS = 30
NEWS_CUTOFF_DAYS = 180

def cache_request (full_url):
    digest = hashlib.sha256(full_url.encode('utf-8')).hexdigest()
    cache_filename = '.cache/' + digest
    if os.path.exists(cache_filename):
        return pickle.load(open(cache_filename, 'rb'))

    details_html = requests.get(full_url).text
    ofile = open(cache_filename, 'wb')
    pickle.dump(details_html, ofile)
    ofile.close()
    return details_html

def load_event_details (event):
    print('Downloading event: {}'.format(event['title']))
    details_html = cache_request('{}/{}'.format(DOMAIN, event['link']))
    soup = BeautifulSoup(details_html, 'html.parser')
    main_content = soup.find(id="main-content")
    image = main_content.find('div', class_='field-name-field-img-opt')
    if image is not None:
        image = image.find('img')['src']
    body = main_content.find('div', class_='field-name-body')
    body_items = body.find_all('div', class_='field-item')
    body = [
        str(body_item)
        for body_item in body_items
    ]
    return {
        'image': image,
        'body': body
    }

# def load_news_details (event):
#     print('Downloading news: {}'.format(event['title']))
#     details_html = cache_request('{}/{}'.format(DOMAIN, event['link']))
#     soup = BeautifulSoup(details_html, 'html.parser')
#     main_content = soup.find(id="main-content")
#     image = main_content.find('div', class_='field-name-field-img-opt')
#     if image is not None:
#         image = image.find('img')['src']
#     body = main_content.find('div', class_='field-name-body')
#     body_items = body.find_all('div', class_='field-item')
#     body = [
#         str(body_item)
#         for body_item in body_items
#     ]
#     return {
#         'image': image,
#         'body': body
#     }




def parse_event_html (event):
    sections = event.find_all(class_='field-content')
    if len(sections) < 3:
        return None
    date_section, title_section, summary_section = sections
    day = date_section.find(class_='event-day-num').text
    month = date_section.find(class_='event-month').text
    time = date_section.find(class_='event-time').text
    link = title_section.find('a')['href']
    title = title_section.find('a').text
    summary = summary_section.text
    start_date = datetime.datetime.strptime(
        '{} {} 2020 {}'.format(month, day, time.split(' - ')[0]),
        '%b %d %Y %I:%M%p'
    )
    end_date = datetime.datetime.strptime(
        '{} {} 2020 {}'.format(month, day, time.split(' - ')[1]),
        '%b %d %Y %I:%M%p'
    )
    # print('{} - {}: {}'.format(start_date, end_date, title))
    return {
        'link': link,
        'title': title,
        'summary': summary,
        'start': start_date,
        'end': end_date
    }


def parse_news_html (event):
    sections = event.find_all(class_='field-content')
    if len(sections) < 4:
        return None
    title_section, date_section, location_section, summary_section = sections
    link = title_section.find('a')['href']
    title = title_section.find('a').text
    date = datetime.datetime.strptime(
        date_section.text,
        '%B %d, %Y'
    )
    summary = summary_section.text
    return {
        'link': link,
        'title': title,
        'summary': summary,
        'date': date,
    }

def load_all(url):
    # returned parsed name of event, the date, and the link for more info
    print('Downloading list: {}'.format(url))

    view_id_suffix = 'events'
    parse_listing_fn = parse_event_html
    parse_details_fn = load_event_details

    if url is NEWS:
        view_id_suffix = 'news'
        parse_listing_fn = parse_news_html
        # parse_details_fn = load_news_details

    soup = BeautifulSoup(cache_request(url), 'html.parser')
    listings = soup.find_all('div', class_='view-id-group_{}'.format(view_id_suffix))

    parsed_listings = []
    for listing in listings:
        all_items = listing.find_all('div', class_='views-row')
        for item in all_items:
            event_or_news = parse_listing_fn(item)
            if event_or_news is None: continue
            event_or_news['details'] = parse_details_fn(event_or_news)
            parsed_listings.append(event_or_news)
    return parsed_listings


def generate_bulletin_from_template (events, news):
    entry_template = open('template/entry.html', 'r').read()
    wrapper_template = open('template/wrapper.html', 'r').read()
    cutoff_date = datetime.datetime.now() + datetime.timedelta(days=EVENT_CUTOFF_DAYS)
    news_cutoff_date = datetime.datetime.now() - datetime.timedelta(days=NEWS_CUTOFF_DAYS)
    events_html = []
    news_html = []
    already_generated = {}

    for event in events:
        if event['start'] > cutoff_date:
            continue
        if event['link'] in already_generated:
            continue
        already_generated[event['link']] = True
        FMT_STR = '%A %B %d %I:%M %p'
        from_datestr = event['start'].strftime(FMT_STR)
        to_datestr = event['end'].strftime(FMT_STR)
        datestr = '{} - {}'.format(from_datestr, to_datestr)
        imagehtml = '<img src="{}" style="width:550px" />'.format(event['details']['image'])
        event_html = entry_template.replace('{{ title }}', event['title'])
        event_html = event_html.replace('{{ date }}', datestr)
        event_html = event_html.replace('{{ image }}', imagehtml)
        event_html = event_html.replace('{{ content }}', event['details']['body'][0])
        events_html.append(event_html)
    events_header = '<center><h1>Events</h1></center><br />'

    for news_item in news:
        # if news_item['date'] < news_cutoff_date:
        #     continue
        FMT_STR = '%A %B, %d'
        datestr = news_item['date'].strftime(FMT_STR)
        if news_item['details']['image'] is not None:
            imagehtml = '<img src="{}" style="width:550px" />'.format(news_item['details']['image'])
        else:
            imagehtml = ''
        event_html = entry_template.replace('{{ title }}', news_item['title'])
        event_html = event_html.replace('{{ date }}', datestr)
        event_html = event_html.replace('{{ image }}', imagehtml)
        event_html = event_html.replace('{{ content }}', news_item['details']['body'][0])
        news_html.append(event_html)
    news_header = '<center><h1>News</h1></center><br />'



    return wrapper_template.replace('{{ body }}', '{} {} <hr /> {} {}'.format(
        events_header,
        '\n'.join(events_html),
        news_header,
        '\n'.join(news_html)
    ))




def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--force', action='store_true')
    # args = parser.parse_args()

    events = load_all(EVENTS)
    news = load_all(NEWS)

    # Put into the HTML template
    html = generate_bulletin_from_template(events, news)
    soup = BeautifulSoup(html, 'html.parser')
    print(soup.prettify())


if __name__ == '__main__':
    main()
