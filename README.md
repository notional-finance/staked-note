# Staked NOTE

The goal of Staked NOTE is to align NOTE token holders with the long term success of the Notional protocol. NOTE holders can stake their NOTE to earn additional yield while signalling that they are willing to provide valuable liquidity over the long term. It's design is inspired by the Aave Safety Module (stkAAVE) and the Vote Escrowed Curve DAO token (veCRV). Over time we hope to achieve:

- Reduced NOTE circulating supply
- On Chain liquidity for trading NOTE
- NOTE token holders can share in the success of the protocol
- Long term nToken liquidity for Notional

There are three primary components of the Staked NOTE design:

- [Staked NOTE (stNOTE)](#staked-note): NOTE tokens used to provide liquidity for NOTE/ETH trading (in an 80/20 Balancer Pool) as well as acting as a backstop for Notional in the event of a [collateral shortfall event](#collateral-shortfall-event).
- [Vote Escrowed Staked NOTE (vestNOTE)](#vote-escrowed-staked-note): stNOTE tokens which are escrowed for the long term to incentive staked long term nToken holdings.
- [Treasury Manager](#treasury-management): an account appointed by NOTE governors to carry out specific Notional treasury management functions.

## Staked NOTE

### Minting stNOTE

Staked NOTE (stNOTE) is minted to NOTE token holders in return for either NOTE or underlying stNOTE Balancer Pool Tokens (BPT). If only NOTE is supplied then some will be sold as ETH to mint the corresponding amount of BPT. All NOTE staked in stNOTE is used to provide liquidity in an 80/20 NOTE/ETH Balancer Pool. The 80/20 ratio reduces the impact of impermanent loss to stNOTE holders while they earn trading fees on NOTE/ETH.

### Redeeming stNOTE

stNOTE is also used as a backstop during a [collateral shortfall event](#collateral-shortfall-event). When this is triggered via governance, 30% of underlying stNOTE BPT will be transferred to the [Treasury Manager](#treasury-manager) to be sold to recover the collateral shortfall. Therefore, to prevent stNOTE holders from front running a collateral shortfall event the stNOTE contract will enforce a cool down period before stNOTE withdraws can occur. Users who choose to initiate a cool down period will not have a claim on any additional BPT minted during their cool down period.

### stNOTE Yield Sources

stNOTE will earn yield from:

- Notional treasury management will periodically trade Notional protocol profits into ETH in order to purchase NOTE and increase the overall BPT share that stNOTE holders have a claim on.
- Governance may decide to incentivize stNOTE with additional NOTE tokens for some initial bootstrapping period.
- Trading fees on the Balancer Pool. Since we anticipate that the stNOTE BPT pool will the the deepest liquidity for NOTE on chain, most NOTE DEX trading will likely come through this pool. stNOTE holders will be able to set the trading fee on the pool.

### stNOTE Voting

stNOTE holders will also be able to vote in Notional governance just like NOTE holders. Relying on the spot claim of NOTE tokens in the Balancer Pool can be manipulated so the voting weight of a single stNOTE will have to either be:

- Set by an external oracle (TODO: maybe consider chainlink here...)
- Calculated via some sort of on chain oracle mechanism

## Vote Escrowed Staked NOTE

stNOTE holders are free to exit their liquidity at any time (subject to a cool down period of between two weeks to a month). However, in order to further incentivize long term holdings we also introduce Vote Escrowed Staked NOTE (vestNOTE).

