import math
import requests

HOME_LAT, HOME_LON = (47.6194776, -122.3341376)


def handler(event, context):
    total_slots = 0

    # Fred hutch
    resp = requests.get("https://d2ez0zkh6r5hup.cloudfront.net/v2/locations/AM8450",
                        params={"origin": "booking_widget"},
                        headers={"Authorization": "Bearer 90dd1fcea0074e7eb4b11e3753a0a334"})
    resp.raise_for_status()

    slots = resp.json()['data']['slots']

    for slot in slots:
        total_slots += slot['availability']

        if slot['availability'] > 0:
            print("{} Slots available at {}".format(slot['availability'], slot['appointment_date']))

    # CVS
    resp = requests.get("https://www.cvs.com/immunizations/covid-19-vaccine.vaccine-status.WA.json?vaccineinfo=",
        headers={"Referer": "https://www.cvs.com/immunizations/covid-19-vaccine?icid=cvs-home-hero1-link2-coronavirus-vaccine"})
    resp.raise_for_status()

    seattle_status = next(filter(
        lambda status: status['city'] == "SEATTLE",
        resp.json()['responsePayloadData']['data']['WA']
    ))['status']

    if seattle_status != "Fully Booked":
        print("CVS Slot available")
        total_slots += 1

    # Safeway
    resp = requests.get("https://s3-us-west-2.amazonaws.com/mhc.cdn.content/vaccineAvailability.json")
    resp.raise_for_status()

    for location in resp.json():
        if distance(HOME_LAT, HOME_LON, float(location['lat']), float(location['long'])) > 15:
            continue

        if location['availability'] == 'no':
            continue

        print('Slot available at', location['address'])
        total_slots += 1

    print("Total slots:", total_slots)


def distance(lat1, lon1, lat2, lon2):
    p = math.pi/180
    a = 0.5 - math.cos((lat2-lat1)*p)/2 + math.cos(lat1*p)\
         * math.cos(lat2*p) * (1-math.cos((lon2-lon1)*p))/2
    return 12742 * math.asin(math.sqrt(a))