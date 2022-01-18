# Staked NOTE

The goal of Staked NOTE is to align NOTE token holders with the long term success of the Notional protocol. NOTE holders can stake their NOTE to earn additional yield while signalling that they are willing to provide valuable liquidity over the long term. It's design is inspired by the Aave Safety Module (stkAAVE). Over time we hope to achieve:

- Reduced NOTE circulating supply
- On Chain liquidity for trading NOTE
- NOTE token holders can share in the success of the protocol

There are two primary components of the Staked NOTE design:

- [Staked NOTE (sNOTE)](#staked-note): NOTE tokens used to provide liquidity for NOTE/ETH trading (in an 80/20 Balancer Pool) as well as acting as a backstop for Notional in the event of a [collateral shortfall event](#collateral-shortfall-event).
- [Treasury Manager](#treasury-management): an account appointed by NOTE governors to carry out specific Notional treasury management functions.

## Staked NOTE

### Minting sNOTE

Staked NOTE (sNOTE) is minted to NOTE token holders in return for either NOTE or underlying sNOTE Balancer Pool Tokens (BPT). If only NOTE is supplied then some will be sold as ETH to mint the corresponding amount of BPT. All NOTE staked in sNOTE is used to provide liquidity in an 80/20 NOTE/ETH Balancer Pool. The 80/20 ratio reduces the impact of impermanent loss to sNOTE holders while they earn trading fees on NOTE/ETH.

### Redeeming sNOTE

sNOTE is also used as a backstop during a [collateral shortfall event](#collateral-shortfall-event). When this is triggered via governance, 30% of underlying sNOTE BPT will be transferred to the [Treasury Manager](#treasury-manager) to be sold to recover the collateral shortfall. Therefore, to prevent sNOTE holders from front running a collateral shortfall event the sNOTE contract will enforce a cool down period before sNOTE withdraws can occur. Users who choose to initiate a cool down period will not have a claim on any additional BPT minted during their cool down period.

### Collateral Shortfall Event

In the event of a hack or account insolvencies, the Notional protocol may not have sufficient collateral to pay lenders their principal plus interest. In this event, NOTE governors will declare a collateral shortfall event and withdraw up to 30% of the sNOTE BPT tokens into NOTE and ETH. The NOTE portion will be sold or auctioned in order to generate collateral to repay lenders.

### sNOTE Yield Sources

sNOTE will earn yield from:

- Notional treasury management will periodically trade Notional protocol profits into ETH in order to purchase NOTE and increase the overall BPT share that sNOTE holders have a claim on.
- Governance may decide to incentivize sNOTE with additional NOTE tokens for some initial bootstrapping period.
- Trading fees on the Balancer Pool. Since we anticipate that the sNOTE BPT pool will the the deepest liquidity for NOTE on chain, most NOTE DEX trading will likely come through this pool. sNOTE holders will be able to set the trading fee on the pool.

### sNOTE Voting Power

sNOTE holders will also be able to vote in Notional governance just like NOTE holders. The voting power of an sNOTE token is based on the amount of underlying NOTE the Balancer pool tokens have a claim on, using Balancer's provided price oracles.

Because the price oracle will be a lagged weighted average, the sNOTE voting power will likely be slightly higher or lower than the spot claim on Balancer pool tokens.
