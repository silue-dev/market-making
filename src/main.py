import numpy as np
from random import random
from plot import plot_performance
from brownian import brownian_motion

class MarketMaker:
    """
    This class implements a simulation of a market maker based on the 
    Avellaneda-Stoikov High-Frequency Trading (HFT) model. The 
    Avellaneda-Stoikov model is a mathematical framework used in 
    quantitative finance to model the optimal strategy for a market 
    maker, considering factors like inventory, risk aversion, and 
    market impact.

    In this implementation, the market maker sets bid (r_b) and ask 
    (r_a) prices for a stock, with these prices being influenced by 
    the stock's reserve price (r), which is adjusted for the market 
    maker's current inventory (q) and a gamma parameter that 
    represents risk aversion. The spread between bid and ask prices 
    is determined by both the gamma and k parameters, where k 
    measures market impact.

    The stock price movements are simulated using a Brownian motion 
    model, characterized by parameters mu (drift) and sigma (volatility). 
    The market maker's performance is evaluated in terms of cash flow, 
    inventory, and profit and loss (PnL) over the simulation period.


    Arguments
    ----------
    s0 (float):     The starting price of the stock.
    n (int):        The number of time steps in the simulation.
    dt (float):     The time step duration.
    mu (float):     The drift of the stock price.
    sigma (float):  The volatility of the stock price.
    gamma (float):  The risk aversion parameter.
    k (float):      The market impact parameter.

    Returns
    -------
    tuple of arrays: 
        Contains time series data for time, stock price, reserve price, 
        ask price, bid price, inventory, and PnL.
    """

    def __init__(self, s0, n, dt, mu, sigma, gamma, k):
        self.s0 = s0
        self.n = n
        self.dt = dt
        self.mu = mu
        self.sigma = sigma
        self.gamma = gamma
        self.k = k

        # Time steps
        self.t = np.linspace(0.0, n * dt, n)
        
        # Order execution probability factors
        self.M = 1
        self.A = 1.0 / dt / np.exp(k * self.M / 2)

    def run(self):
        # Trading time
        T = self.n * self.dt

        # Cash
        cash = np.empty(self.n)
        cash[0] = 0

        # Inventory
        q = np.empty(self.n)
        q[0] = 0

        # PnL
        pnl = np.empty(self.n)
        pnl[0] = 0

        # Reserve price and quotes
        r = np.empty(self.n)
        r_a = np.empty(self.n)
        r_b = np.empty(self.n)

        # Generate a stock price
        s = brownian_motion(s0=self.s0, 
                            n=self.n, 
                            dt=self.dt, 
                            mu=self.mu, 
                            sigma=self.sigma)
        
        # Run market maker on stock
        for i in range(self.n):
            # Compute reserve price and spread
            r[i] = s[i] - q[i] * self.gamma * self.sigma**2 * (T - self.dt * i)
            spread = 2 / self.gamma * np.log(1 + self.gamma / self.k)

            # Compute quotes
            r_a[i] = r[i] + spread / 2
            r_b[i] = r[i] - spread / 2

            if i < self.n - 1:
                # Since we don't have an order book, we must compute 
                # the probability that the asks and/or bids get executed:
                ### Deltas
                delta_a = r_a[i] - s[i]
                delta_b = s[i] - r_b[i]
                ### Intensities
                lambda_a = self.A * np.exp(-self.k * delta_a)
                lambda_b = self.A * np.exp(-self.k * delta_b)
                ### Order execution probabilities
                p_exec_a = 1 - np.exp(-lambda_a * self.dt)
                p_exec_b = 1 - np.exp(-lambda_b * self.dt)

                # We execute one order if a side gets hit
                executed_a = 0
                executed_b = 0
                if random() < p_exec_a:
                    executed_a = 1
                if random() < p_exec_b:
                    executed_b = 1

                # Compute inventory, cash, and PnL
                q[i+1] = q[i] - executed_a + executed_b
                cash[i+1] = cash[i] + r_a[i] * executed_a - r_b[i] * executed_b
                pnl[i+1] = cash[i+1] + q[i+1] * s[i]
        
        return self.t, s, r, r_a, r_b, q, pnl


if __name__ == "__main__":
    marketmaker = MarketMaker(s0=100,
                              n=250,
                              dt=0.01,
                              mu=0,
                              sigma=2,
                              gamma=0.1,
                              k=1.5)
    
    # Simulate
    pnls = []
    n_sim = 100
    for i in range(n_sim):
        t, s, r, r_a, r_b, q, pnl = marketmaker.run()
        pnls.append(pnl)
    
    # Plots
    plot_performance(t, s, r, r_a, r_b, q, np.array(pnls))