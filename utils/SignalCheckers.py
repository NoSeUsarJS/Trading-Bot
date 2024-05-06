# RSI already has been equal or less than {value}
# RSI come back to {value}
def RSI_is_less(rsi, value):
    if rsi <= value:
        return True

    return False

# Fast EMA overpass slow EMA
def EMA_overpass(fast_ema, slow_ema):
    if fast_ema > slow_ema:
        return True
    
    return False

# RSI is equal or more than {value}
# RSI already has been equal or more than {value}
def RSI_is_more(rsi, value):
    if rsi >= value:
        return True
    
    return False

def is_bullish(sma, past_sma):
    if sma >= past_sma:
        return True
    
    return False