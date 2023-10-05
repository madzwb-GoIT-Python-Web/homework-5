import aiohttp
import argparse
import asyncio
import json
import platform

from datetime import date, timedelta, datetime
from http import HTTPStatus
# from concurrent.futures.thread import ThreadPoolExecutor

URL = "https://api.privatbank.ua/p24api/exchange_rates"

CURRENCIES = {
    "USD": "U.S. dollar",
    "EUR": "euro",
    "CHF": "swiss franc",
    "GBP": "british pound",
    "PLZ": "polish zloty",
    "SEK": "swedish krona",
    "XAU": "gold",
    "CAD": "canadian dollar",
}
def format_result(result, currencies):
    return {
        result['date']:
            dict(sorted(
                {
                    rate['currency']: {
                        'sale'     : rate.get('saleRate'     , rate['saleRateNB']),
                        'purchase' : rate.get('purchaseRate' , rate['purchaseRateNB']),
                    } for rate in   filter(
                                        lambda x: x['currency'] in currencies,
                                        result['exchangeRate']
                                    )
                }.items(),
                key=lambda x: currencies.index(x[0])
            ))
    }
def get_result(response, text):
    if response.status == HTTPStatus.OK:
        data = json.loads(text)
        return data

async def request(session, url, date, currencies):
    async with session.get(url, params={"date": date.strftime("%d.%m.%Y")}) as response:
        print(f"Getting exchanges for {date}")
        try:
            result = get_result(response, await response.text())
            if result:
                result = format_result(result, currencies)
                return result
        except Exception as e:
            print(e)
        return {date: None}

def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "days",
        help        = "Days to request,\n\
        if not specified will be - '0'.",
        type        = int,
        choices     = [_ for _ in range(10)],
        action      = "store",
        default     = 0,
        # required    = False,
        nargs       = '?'
    )
    parser.add_argument(
        "currencies",
        help        = "Request's currencies,\n\
        if not specified will be - 'EUR' and 'USD'.",
        type        = str.upper,
        choices     = list(CURRENCIES.keys()),
        action      = "store",
        default     = "EUR",
        # required    = False,
        nargs       = '*'
    )
    return parser

async def main() -> None:
    parser = argparser()
    args = parser.parse_args()
    start = datetime.now()

    coroutines = []
    results = []
    async with aiohttp.ClientSession() as session:

        archive_date = date.today() - timedelta(days=args.days)
        while archive_date <= date.today():
            print(archive_date)
            coroutine = request(session, URL, archive_date, args.currencies)
            coroutines.append(coroutine)
            archive_date += timedelta(days=1)

        try:
            results = await asyncio.gather(*coroutines)
        except aiohttp.ClientError as e:
            print(e)
            return
        except Exception as e:
            print(e)
            return

    end = datetime.now()
    print(json.dumps(results))
    delta = end - start
    print(f"Processed: {delta.seconds}")
    pass


if __name__ == '__main__':
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())