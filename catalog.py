"""Curated evergreen research. Numerical examples are calculations, not market quotes."""
CATALOG = [
 dict(slug='inflation', title='Prices rising slower still means prices are rising', source='https://www.federalreserve.gov/faqs/economy_14419.htm', evidence='Inflation is a general increase in the overall price level; individual price changes alone do not measure it.', scenes=[
 ('Inflation fell. So why is your shopping still expensive?', 'INFLATION FELL. PRICES DID NOT.'),
 ('A lower positive inflation rate means prices are rising more slowly.', 'SLOWER RISE'),
 ('Imagine a basket costing one hundred. Ten percent inflation makes it one hundred ten.', '100 → 110'),
 ('Then two percent inflation makes that one hundred twelve point two. Not one hundred two.', '110 → 112.20'),
 ('These are hypothetical numbers. Falling prices would be deflation.', 'ILLUSTRATION • NOT CURRENT RATES'),
 ('The rate can fall while your bill keeps climbing. That is the difference.', 'WATCH THE LEVEL. NOT JUST THE RATE.')]),
 dict(slug='compounding', title='The extra one you missed in compound interest', source='https://www.investor.gov/financial-tools-calculators/calculators/compound-interest-calculator', evidence='Compound growth depends on starting principal, time, rate and compounding frequency. Example verified: 100 × 1.1 × 1.1 = 121.', scenes=[
 ('One hundred growing ten percent twice becomes one hundred twenty one. Why the extra one?', 'WHERE DID THE EXTRA 1 COME FROM?'),
 ('First period: one hundred earns ten. Your balance becomes one hundred ten.', '100 + 10 = 110'),
 ('Second period: ten percent now applies to one hundred ten. That earns eleven.', '110 × 10% = 11'),
 ('The original hundred earned ten. The previous interest earned one more.', 'INTEREST ON INTEREST'),
 ('That is compounding. These fixed returns are just an illustration, not a promise.', 'HYPOTHETICAL • NOT A RETURN PROMISE'),
 ('Time and the rate both matter. Fees and losses can change the result.', 'THE BASE CHANGES THE RESULT')]),
 dict(slug='basket', title='One expensive item does not tell you inflation', source='https://www.bankofengland.co.uk/explainers/what-is-inflation', evidence='A consumer price index tracks a representative basket; comparing the index across time gives a rate of inflation.', scenes=[
 ('Your coffee costs more. Does that tell you the inflation rate?', 'ONE PRICE ≠ THE WHOLE ECONOMY'),
 ('Not by itself. Inflation measures a broader change in prices over time.', 'LOOK AT THE BASKET'),
 ('Price indexes combine many goods and services into a representative basket.', 'GOODS + SERVICES'),
 ('Compare that basket across time to estimate the change in the price level.', 'SAME BASKET. DIFFERENT DATE.'),
 ('Your own spending mix may be different, so your experience can differ too.', 'YOUR BASKET MAY DIFFER'),
 ('One price is a clue. The wider basket tells the bigger story.', 'A CLUE IS NOT THE WHOLE PICTURE')])
]
def plan_for(item):
    return dict(title=item['title'], topic=item['slug'], scenes=[dict(narration=n,caption=c) for n,c in item['scenes']], sources=[dict(url=item['source'], evidence=item['evidence'], verified_at='2026-10-30')], rights='Original generated typography and geometric animation; offline synthetic narration; no third-party music or footage.', fact_checked=True)
