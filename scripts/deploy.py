import requests
from brownie import chain, PoolCreationHelper, accounts, Contract

account = accounts.load("dd_PoolCreation")
BALANCER_DEPLOYMENTS_URL = "https://raw.githubusercontent.com/balancer-labs/balancer-v2-monorepo/master/pkg/deployments"
CHAIN_NAME_BY_ID = {
        1: "mainnet",
        137: "polygon",
        42161: "arbitrum",
        10: "optimism",
        100: "gnosis",
        42: "goerli",
}

def monorepoLookup(task, contract):
    chainname = CHAIN_NAME_BY_ID[chain.id]
    deployment_output = requests.get( f"{BALANCER_DEPLOYMENTS_URL}/tasks/{task}/output/{chainname}.json").json()
    target_address = deployment_output[contract]
    return target_address

vault = monorepoLookup("20210418-vault", "Vault")
weightedFactory = monorepoLookup("20230320-weighted-pool-v4", "WeightedPoolFactory")
stableFactory = monorepoLookup("20230320-composable-stable-pool-v4", "ComposableStablePoolFactory")

helper = PoolCreationHelper.deploy(vault, weightedFactory, stableFactory, {"from": account})
PoolCreationHelper.publish_source(PoolCreationHelper[0])

