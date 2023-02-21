import asyncio, requests, json, time
import hmac, hashlib
from binance import AsyncClient, BinanceSocketManager
from prometheus_client import start_http_server, Counter, Gauge


kline_counter = Counter("KLINE", "total number of transaction has been made")
LTMA_calculated = Gauge("LTMA", "amount of calculated LTMA")
STMA_calculated = Gauge("STMA", "amount of calculated STMA")
buy_counter = Counter("BUY", "Number of times for buying")
sell_counter = Counter("SELL", "Number of times for selling")

async def main():
    client = await AsyncClient.create(testnet='wss://testnet.binance.vision/')
    bm = BinanceSocketManager(client)

    # chose to use kline_socket method to get data
    symbol = 'BTCUSDT'
    ts = bm.kline_socket(symbol)

    async with ts as tscm:
        # place order logic
        def place_order(symbol, side, quantity, price):
            # Define the endpoint URL
            url = "https://testnet.binance.vision/api/v3/order"

            # Define the API key and secret
            api_key = "Xb8usz6gjCRsSpNtdJqjq6xLBpEs5TxJXKDdoCWWVnGVQRVfwHRUQe97n5fHiGzc"
            secret_key = "3yfTfXZnUW7RggAGfAEr5ZXYGb0YSMngXmHAuJD8T17JzwAfWJ9yn3P85IjeTR7j"

            # Define the request payload
            payload = {
                "symbol": symbol, #"BTCUSDT",
                "side": side, #"BUY",
                "type": "LIMIT",
                "timeInForce": "GTC",
                "quantity": quantity, #"0.5",
                "price": price, #"1000",
                "recvWindow": 5000,
                "timestamp": int(time.time() * 1000)
            }

            # Create the signature for the request
            query_string = '&'.join([f'{key}={value}' for key, value in payload.items()])
            signature = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
            query_string = query_string + '&signature=' + signature

            # Send a POST request to the endpoint with the query string
            headers = {
                "X-MBX-APIKEY": api_key
            }
            response = requests.post(url, headers=headers, data=query_string)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                data = json.loads(response.text)
                # print(data)
                if data['side'] == "SELL":
                    sell_counter.inc()
                elif data['side'] == "BUY":
                    buy_counter.inc()
            
            else:
                # If the request was not successful, print the error message
                raise ValueError("Failed to place order: " + response.text)
                # print("Request failed with status code:", response.status_code, response.text)

        close_price_list = []   #Latest LTMA and STMA are included

        while len(close_price_list) < 121: # 리스트가 120개를 넘어갈때, 기존 기준 MA120을 넘어가기 때문에.
            res = await tscm.recv()
            close_price = float(res['k']['c'])
            kline_counter.inc() 
            is_kline_closed = res['k']['x']
            
            if is_kline_closed is True:
                close_price_list.append(close_price)    # 최신 close price를 리스트에 가장 뒤에 추가
                print(f"current list is {close_price_list}") # 데이터 로깅을 위한 프린팅 

                if len(close_price_list) > 3: # 20부터 축적된 데이터로 ltma&stma계산 가능
                    ltma = sum(close_price_list) / len(close_price_list)
                    print(f"ltma count is {len(close_price_list)}")
                    LTMA_calculated.set(ltma) # monitoring LTMA
                    print(f"LTMA is {ltma}")

                    stma = sum(close_price_list[2:]) / len(close_price_list[2:])
                    STMA_calculated.set(stma) # monitoring STMA
                    print(f"ltma count is {len(close_price_list[2:])}")
                    print(f"STMA is {stma}")
                    
                    buying_amount = 0.001   # amount depends on your own risk tolerance
                    selling_amount = 0.001  

                    # 매수&매도 판단 로직:
                    if stma > ltma:
                        print(f"STMA is greater than LTMA, BUY signal!")
                        place_order(symbol, 'BUY', buying_amount, close_price)
                    elif stma < ltma:
                        print(f"STMA is less than LTMA, SELL signal!")
                        place_order(symbol, 'SELL', selling_amount, close_price)
                    else: # Just in case if stma = ltma (almost impossible)
                        pass

        await client.close_connection()
        print("It is now above max MA120, close the connection!")

if __name__ == "__main__":
    start_http_server(8000) # Prometheus monitoring port
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


# =========== Kline Streams DataSet =============
# {
#   "e": "kline",     // Event type
#   "E": 123456789,   // Event time
#   "s": "BNBBTC",    // Symbol
#   "k": {
#     "t": 123400000, // Kline start time
#     "T": 123460000, // Kline close time
#     "s": "BNBBTC",  // Symbol
#     "i": "1m",      // Interval
#     "f": 100,       // First trade ID
#     "L": 200,       // Last trade ID
#     "o": "0.0010",  // Open price
#     "c": "0.0020",  // Close price
#     "h": "0.0025",  // High price
#     "l": "0.0015",  // Low price
#     "v": "1000",    // Base asset volume
#     "n": 100,       // Number of trades
#     "x": false,     // Is this kline closed?
#     "q": "1.0000",  // Quote asset volume
#     "V": "500",     // Taker buy base asset volume
#     "Q": "0.500",   // Taker buy quote asset volume
#     "B": "123456"   // Ignore
#   }
# }