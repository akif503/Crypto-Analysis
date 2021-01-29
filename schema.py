
# Schema for https://www.coinbase.com/api/v2/assets/prices?base=CAD
"""
data: [{base: COIN_NAME
        base_id: ...
        currency: CAD
        prices: {
            latest: ...
            latest_price: {
                amount: {
                    amount: ...
                    currency: ...
                    scale: 2
                }
                percent_change: {
                    all: 
                    day:
                    hour:
                    month:
                    week:
                    year:
                }
                timestamp: ...
            }
        unit_price_scale: 2
        }}
        ... (repeat)
       ]

"""

# Schema for https://www.coinbase.com/api/v2/assets/prices/baseid?base=CAD
# E.g for ETH - https://www.coinbase.com/api/v2/assets/prices/d85dce9b-5b73-5c3c-8978-522ce1d1c1b4?base=CAD
"""
data: {
    base: ETH
    base_id: 
    currency: CAD
    prices: [
        all: {
            percent_change: 
            prices: [[price, volume]] 
        },

        day: {
            percent_change: 
            prices: [[...]] 
        }
        
        hour: {
            percent_change: 
            prices: [[...]] 
        }
        
        latest: ...
        latest_price: {
            amount: {
                amount: ...
                currency: CAD
                scale: 2
            }
            percent_change: {
                all: 
                day:
                hour:
                month:
                week:
                year:
            }
            timestamp: ...
        }
        month: {
            ...
        }

        week: {
            ...
        }

        year: {
            ...
        }
    ]
    unit_price_scale: 2
}
"""

# Schema prices inside the above schema
"""
(interval): {
    percent_change: # change with (intervel-1)
    prices: [price, timestamp]
}
"""