# PoolCreationHelper

This helper contract makes it easier for you to create and init join a pool from etherscan or a multisig.  It hides a bunch of the funny math and odd mechanics.  

## Prepairing your inputs
The contract takes a bunch ordered lists which are rows in a table.  The lists must all be the same length, and the same index pertains to the same thing.

The inputs must be ordered by address, such that the address list has 0x00 first and 0xfff last.  You can use the sort functions (read) to resort your lists if they are not correct.

### Rate Providers
Rate providers are used to capture the exchange rate between redeemable tokens.  For example wstETH increases in the amount of ETH it is(or will be) redeemable for.

The rate provider simply has a function getRate() which returns this ratio.  You can read more about how to deploy a Rate Provider in the [docs](https://docs.balancer.fi/reference/contracts/rate-providers.html).

If rate providers are specified, then protocol fees are taken from the staking intrest earned (increase in rate), and the pool paritipates in the core pool program if it has a gauge.

Weighted pools never need rate providers, but if there is a staked/wrapped token that increases in value they can be used to make the pool into a core pool.

Stableswaps require a rate provider for tokens that increase in value in order to know how to properly maintain peg.

No rate provider is required for any base token that is not wrapped or staked into something that increases in value.

For each token, no rate provider is specified by providing the ZeroAddress `0x0000000000000000000000000000000000000000`

You can pass [] in the rate providers array to have no rate providers for any tokens.

### Exempt Fees
Given the example of a stableswap that pairs some coin, say GHO with a BPT, say Balancer 3 Pool, a rate provider is required to capture the increase in USD value that the pool token receives from fee capture.  In this case, fees are taken on this value, but the fees were already paid by the underlying pool.  
In this case, exempt fees can be set to true for this token/rate provider and fees will not be charged on the upwards rebasing of that token.  Note that any pool that wishs to receive a gauge is expected not to use exempt fees exempt for avoiding double taxation. 

Exempt fees must be set to false for any token that does not have a rate provider (has ZeroAddress as rate provider). 

## Deployed addresses

### V2 Nonce 2
Address: `0x93118d4853646a869732898cEa3bCF309e1607A6`
Deployments:
[mainnet](https://etherscan.io/address/0x93118d4853646a869732898cea3bcf309e1607a6)
[arbi](https://arbiscan.io/address/0x93118d4853646a869732898cea3bcf309e1607a6)
[matic](https://polygonscan.com/address/0x93118d4853646a869732898cea3bcf309e1607a6)
[gnosis](https://gnosisscan.io/address/0x93118d4853646a869732898cea3bcf309e1607a6)
[op](https://optimistic.etherscan.io/address/0x93118d4853646a869732898cea3bcf309e1607a6)


## Using from a multisig

You can find an example [multisig payload](./multisg-payloads/arbitrum-dai-mim-frax-stable-and-weighted-pool-9-dollars-each-token.json) by clicking on it.

This payload includes 2 transactions to join a dai-min-frax pool.  1 is stableswap, one is weighted.

You can edit this file, remove the type you don't want, update the inputs and then load it into transaciton builder to simulate and then execute a pool creation.

