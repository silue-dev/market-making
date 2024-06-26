import numpy as np
from plot import plot_performance
from marketmaker import MarketMaker
from brownian import BrownianMotion
from database import Database

def store_brownian_motions(db: Database, 
                           n_sim: int,
                           s0: int,
                           n: int,
                           dt: float,
                           mu: float,
                           sigma: float) -> None:
    """
    Generates a given number of Brownian motions and store them.

    Arguments
    ---------
    db    :  The database to store the brownian motions in.
    n_sim :  The number of Brownian motions to generate.
    s0    :  The starting price of the stock.
    n     :  The total number of time steps.
    dt    :  The time step.
    mu    :  The drift of the stock.
    sigma :  The volatility of the stock.

    """
    for _ in range(n_sim):
        bm = BrownianMotion(s0, n, dt, mu, sigma)
        serialized_bm = bm.serialize()
        db.insert_brownian_motion(serialized_bm)

def run_simulations(db: Database) -> tuple[np.ndarray, ...]:
    """
    Runs the market making simulation on the Brownian motions stored
    inside the given database.

    Arguments
    ---------
    db :  The database that contains the Brownian motions.

    Returns
    -------
    self.t    :  The array of time steps.
    self.bm.s :  The stock price movement (Brownian motion).
    r         :  The array containing reserve prices at each time step.
    r_a       :  The array of ask prices at each time step.
    r_b       :  The array of bid prices at each time step.
    q         :  The array of inventory snapshots at each time step.
    pnls      :  The PnL array, i.e., the PnL at each time step.

    """
    pnls = []
    brownian_motions = db.fetch_all_brownian_motions()

    for serialized_bm in brownian_motions:
        bm = BrownianMotion.deserialize(serialized_bm[0])
        marketmaker = MarketMaker(bm, k=1.5, gamma=0.1)
        t, s, r, r_a, r_b, q, pnl = marketmaker.run()
        pnls.append(pnl)
    
    return t, s, r, r_a, r_b, q, np.array(pnls)

def main(n_sim: int = 100,
         s0: int = 100,
         n: int = 200,
         dt: float = 0.005,
         mu: float = 0,
         sigma: float = 2) -> None:
    """
    Main execution, which brings together the database setup, stock price
    data generation, market making simulation, and performance plotting.

    Arguments
    ---------
    n_sim :  The number of market making simulations to run.

    """
    db = Database()
    db.connect()
    db.create_table()
    store_brownian_motions(db, n_sim, s0, n, dt, mu, sigma)

    t, s, r, r_a, r_b, q, pnls = run_simulations(db)
    
    db.clear()
    db.close()

    plot_performance(t, s, r, r_a, r_b, q, pnls)


if __name__ == '__main__':
    main(n_sim=100)
