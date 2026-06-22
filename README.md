## Margin Efficiency Engine for Correlated Perps and Predictions

Last week, I bought my first perpetuals futures contract on Kalshi (Long $HYPE). During the process, I didn't have enough cash, so I needed to transfer money from my bank account. However, I accidently sent it to my Predictions portfolio instead of my Perpetuals portfolio, so I had to transfer the cash from my Predictions to Perpetuals portfolio. Then, I was able to purchase $HYPE perpetuals. 

This transfer got me wondering why my predictions and perpetuals where seperated, and what would happen if they were combined. If they were combined, I could easily hedge my perpetuals with predictions, or even try bear/bull spreads and butterfly condors. Applying these options strategies requires margin, which I use for perpetuals but not predictions. For example, if I'm long BTC perp/NO BTC price prediction, I'm locking up way more margin that I need to. If I take losses on the perp and the prediction odds go up or converges to NO, then my gain from the prediction will cover my losses from the perp (if shares/quantity is balanced correctly). This means I don't need to put up as much margin to begin with. 

To test it out, I made this dashboard: https://kalshi-dual-margin-engine.streamlit.app/

Kalshi Dual Margin Engine calculates margin requirements for perpetuals hedged with predictions or vice versa. If bets are inversely coorelated, it calculates how much margin can be unlocked for the user. The dashboard is using BTC Perp and 'Bitcoin price at the end of 2026' as the prediction.

Here is the how the engine works:

  -> You choose the BTC spot price, IV, short/long the BTC perp, the total cost for the perp, the leverage for the perp, the outcome for the prediction, yes/no for the prediction, and total shares of the prediction. 
  
  -> The outcome you choose for the prediction will have a large impact on this engine. The 'Bitcoin price at the end of 2026' prediction is essentially a cash-or-nothing option, so we can use the Black-Scholes formula for c/n option to calculate the theoritical price of this  outcome. The outcomes on this particular market are ranges (BTC between X and Y), so a bull call spread. To calculate the price of this outcome, we do price of X - price of Y.
  
  -> The most important part of this engine is determining the coorelation between the perp and the prediction. We start off by generating 90 days worth of synthetic log returns for BTC with 3% volatility. The, we use the user's inputted spot price and work backwards to map the price from the synthetic returns. Using the 90-day synthetic price history, we calculate the theortical price of the event contract on each previous day. We use the returns (not price) to determine the coorelation between the perp and prediction.
  
  -> After calculating the coorelation, it calculates delta and gamma for the prediction. YES for predictions is positive delta and NO is negative delta. Then, we calculate the exposure for our prediction, and the exposure of the perp. If they are opposite, then we have an off-setting position (hedge).

-> Using the exposure of the perp and prediction, it calculates the VaR for both. 99% CI, and 5% haircut for perp and 12% haircut for the prediction.

-> After the VaR calculation, we calculate our unified margin requirement for the perp and prediction. Predictions have extreme tail-risk as the probability of the market approaches 0 or 1. This causes the delta of the prediction to be extremely volatile. To account for this, the engine calculates a gamma surcharge which increases the margin requirement when the spot price is near the edges of the outcome. The margin requirements is calculated using the Gaussian-Copula, because Copula models joint-tail dependency and can easily recognize when two positions are hedges.

-> Finally to calculate our optimized margin requirement: isolated margin (don't consider coorelation) - unified margin (consider coorelation).
