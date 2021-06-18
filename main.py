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
NEWS_CUTOFF_DAYS = 30

def cache_request (full_url, force=False):
    digest = hashlib.sha256(full_url.encode('utf-8')).hexdigest()
    cache_filename = '.cache/' + digest
    if os.path.exists(cache_filename) and force is False:
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
    if time == 'A Multi-Day Event':
        start_date = datetime.datetime.strptime(
            '{} {} 2021 1:11am'.format(month, day),
            '%b %d %Y %I:%M%p'
        )
        end_date = start_date + datetime.timedelta(days=7)
    else:
        start_date = datetime.datetime.strptime(
            '{} {} 2021 {}'.format(month, day, time.split(' - ')[0]),
            '%b %d %Y %I:%M%p'
        )
        end_date = datetime.datetime.strptime(
            '{} {} 2021 {}'.format(month, day, time.split(' - ')[1]),
            '%b %d %Y %I:%M%p'
        )
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

    soup = BeautifulSoup(cache_request(url, force=True), 'html.parser')
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

    events_table_rows = []
    for event in events:
        if event['end'] > cutoff_date:
            continue
        if event['link'] in already_generated:
            continue
        already_generated[event['link']] = True
        FMT_STR = '%A, %B %-d. %-I:%M %p'
        start_date = event['start']
        end_date = event['end']
        if start_date.day == end_date.day and start_date.month == end_date.month:
            start_ampm = start_date.strftime('%p')
            end_ampm = end_date.strftime('%p')
            if start_ampm == end_ampm:
                from_datestr = start_date.strftime('%A, %B %-d. %-I:%M')
            else:
                from_datestr = start_date.strftime(FMT_STR)
            to_datestr = end_date.strftime('%-I:%M %p')
        else:
            from_datestr = start_date.strftime(FMT_STR)
            to_datestr = end_date.strftime(FMT_STR)
        datestr = '{} - {}'.format(from_datestr, to_datestr)
        event_html = entry_template.replace('{{ title }}', event['title'])
        event_html = event_html.replace('{{ date }}', datestr)
        if event['details']['image'] is None:
            imagehtml = ''
        else:
            imagehtml = '<p style="text-align: center;"><img src="{}" style="width:300px" /></p>'.format(event['details']['image'])
        event_html = event_html.replace('{{ image }}', imagehtml)
        event_html = event_html.replace('{{ content }}', event['details']['body'][0])
        events_html.append(event_html)
        events_table_rows.append('<tr><td>{}</td><td>{}</td><td><a href="{}/{}">Read more</a></td></tr>'.format(
            event['title'], datestr, DOMAIN, event['link']
        ))
    wrapper_template = wrapper_template.replace('{{ events_body }}', '\n'.join(events_html))
    wrapper_template = wrapper_template.replace('{{ events_table }}', '\n'.join(events_table_rows))

    news_table_rows = []
    for news_item in news:
        if news_item['date'] < news_cutoff_date:
            continue
        FMT_STR = '%A, %B %d'
        datestr = news_item['date'].strftime(FMT_STR)
        if news_item['details']['image'] is not None:
            imagehtml = '<img src="{}" style="width:300px" />'.format(news_item['details']['image'])
        else:
            imagehtml = ''
        event_html = entry_template.replace('{{ title }}', news_item['title'])
        event_html = event_html.replace('{{ date }}', datestr)
        event_html = event_html.replace('{{ image }}', imagehtml)
        event_html = event_html.replace('{{ content }}', news_item['details']['body'][0])
        news_html.append(event_html)
        news_table_rows.append('<tr><td>{}</td><td>{}</td><td><a href="{}/{}">Read more</a></td></tr>'.format(
            news_item['title'], datestr, DOMAIN, news_item['link']
        ))
    wrapper_template = wrapper_template.replace('{{ news_body }}', '\n'.join(news_html))
    wrapper_template = wrapper_template.replace('{{ news_table }}', '\n'.join(news_table_rows))
    return wrapper_template




def main():
    events = load_all(EVENTS)
    news = load_all(NEWS)

    # Put into the HTML template
    html = generate_bulletin_from_template(events, news)
    soup = BeautifulSoup(html, 'html.parser')

    ofile = open('bulletin.html', 'w')
    ofile.write(soup.prettify())
    ofile.close()


if __name__ == '__main__':
    main()
