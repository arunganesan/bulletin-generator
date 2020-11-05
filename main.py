#! /usr/bin/env python3

from bs4 import BeautifulSoup
import requests
import datetime

BASE = 'https://amma.org/groups/north-america/amma-center-michigan'
EVENTS = BASE + '/events'
NEWS = BASE = '/news'


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

    print('{} - {}: {}'.format(start_date, end_date, title))

def load_all_events():
    events_html = requests.get(EVENTS).text

    # returned parsed name of event, the date, and the link for more info
    soup = BeautifulSoup(events_html, 'html.parser')
    event_listings = soup.find_all('div', class_='view-id-group_events')
    for listing in event_listings:
        events = listing.find_all('div', class_='views-row')
        for event in events:
            parse_event_html(event)



def main():
    events = load_all_events()


if __name__ == '__main__':
    main()
