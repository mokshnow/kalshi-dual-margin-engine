# kalshi-dual-margin-engine
Margin Efficiency Engine for Uncorrelated Hedges with Perps and Predictions

Last week, I bought my first perpetuals futures contract on Kalshi (Long $HYPE). During the process, I didn't have enough cash, so I needed to transfer money from my bank account. However, I accidently sent it to my Predictions portfolio instead of my Perpetuals portfolio, so I had to transfer the cash from my Predictions to Perpetuals portfolio. Then, I was able to purchase $HYPE perpetuals. 

This transfer got me wondering why my predictions and perpetuals where seperated, and what would happen if they were combined. If they were combined, I could easily hedge my perpetuals with predictions, or even try bear/bull spreads and butterfly condors. Applying these options strategies requires margin, which I use for perpetuals but not predictions. For example, if I'm long BTC perp/NO BTC price prediction, I'm locking up way more margin that I need to. If I take losses on the perp and the prediction odds go up or wins, then my gain from the prediction will cover my losses from the perp (if shares/quantity is balanced correctly). This means I don't need to put up as much margin to begin with. To test it out, I made this dashboard: https://kalshi-dual-margin-engine-qqra9ttf8xoxel43oekz6h.streamlit.app/.

Kalshi Dual Margin Engine calculates margin requirements for perpetuals hedged with predictions or vice versa. If bets are uncoorelated, it calculates how much margin can be unlocked for the user. The dashboard is using BTC Perp and 'Bitcoin price at the end of 2026' as the prediction.

Here is the how the engine works:

-> You choose the BTC spot price, implied volatility, short/long the BTC perp, the total cost for the perp, the leverage for the perp, the     outcome for the prediction, yes/no for the prediction, and total shares of the prediction. 

-> The outcome you choose for the prediction will have a large impact on this engine. The 'Bitcoin price at the end of 2026' prediction is     essentially a cash-or-nothing option, so we can use the Black-Scholes formula for c/n option to calculate the theoritical price of this     outcome. The outcomes on this particular market are ranges (BTC between X and Y), so a bull call spread. To calculate the price of this     outcome, we do price of X - price of Y.

-> After selecting all the criterias, the engine will calculate the coorelation (rho) between the perp and prediction.

