import requests
from brownie import chain, PoolCreationHelper, accounts, Contract
from bal_addresses import read_addressbook
account = accounts.load("dd_PoolCreation")
deploy_nonce=2

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

chainname = CHAIN_NAME_BY_ID[chain.id]
r=read_addressbook(chainname)
vault = r["20210418-vault/Vault"]
weightedFactory = r["20230320-weighted-pool-v4/WeightedPoolFactory"]
stableFactory = r["20230320-composable-stable-pool-v4/ComposableStablePoolFactory"]
assert account.nonce == deploy_nonce, "Wrong Nonce"
helper = PoolCreationHelper.deploy(vault, weightedFactory, stableFactory, {"from": account})
PoolCreationHelper.publish_source(PoolCreationHelper[len(PoolCreationHelper)-1])

