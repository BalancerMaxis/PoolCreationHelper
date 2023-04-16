import pytest
import time
from brownie import (
    interface,
    accounts,
    PoolCreationHelper,
    Contract,
network
)
from brownie.exceptions import VirtualMachineError

from dotmap import DotMap
import pytest
import json


##  Accounts
VAULT_ADDRESS = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
WHALE = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"  ## CRV 3pool mainnet
DAI_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
WEIGHTED_POOL_FACTORY = "0x897888115Ada5773E02aA29F775430BFB5F34c51"  ## V4 on mainnet
STABLESWAP_FACTORY = "0xfADa0f4547AB2de89D1304A668C39B3E09Aa7c76" # 20230320-composable-stable-pool-v4 on mainnet
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture()
def unordered_token_list():
    return [USDT_ADDRESS, DAI_ADDRESS, USDC_ADDRESS]

@pytest.fixture()
def ordered_token_list(unordered_token_list, helper):
    try:
        (addresses, foo, bar, foobar) = helper.sortForWeighted(unordered_token_list, [],[5,10,15], [0 , 0, 0])
        return addresses
    except VirtualMachineError:
        return unordered_token_list

@pytest.fixture()
def whale():
    return WHALE


@pytest.fixture()
def vault():
    return Contract(VAULT_ADDRESS)


@pytest.fixture()
def caller():
    return accounts[0]

@pytest.fixture()
def owner():
    return accounts[1]


@pytest.fixture()
def weightedFactory():
    return Contract.from_explorer(WEIGHTED_POOL_FACTORY)


@pytest.fixture()
def stableFactory():
    return Contract.from_explorer(STABLESWAP_FACTORY)


@pytest.fixture()
def dai():
    return Contract.from_explorer(DAI_ADDRESS)


@pytest.fixture()
def usdc():
    return Contract(USDC_ADDRESS)


@pytest.fixture()
def usdt():
    return Contract.from_explorer(USDT_ADDRESS)



@pytest.fixture()
def weightedPool(ordered_token_list, caller, helper):
    tx = helper.createWeightedPool("Test Weighted", "HEAVY", ordered_token_list, [], [33, 33, 34], 300, b"salty")
    poolAddress = tx.events["PoolCreated"]["pool"]
    with open("abis/WeightedPool.json", "r") as f:
        pool = Contract.from_abi("WeightedPool", poolAddress, json.load(f))
    return pool

@pytest.fixture()
def stablePool(ordered_token_list, helper):
    tx = helper.createStablePool("Test Stable", "STABLE", ordered_token_list, 1000, [], [], 300, b"xyz")
    poolAddress = tx.events["PoolCreated"]["pool"]
    with open("abis/IComposibleStable.json", "r") as f:
        pool = Contract.from_abi("IComposableStable", poolAddress, json.load(f))
    return pool


@pytest.fixture()
def helper(deploy):
    return deploy


@pytest.fixture()
def deploy(caller, vault, weightedFactory, stableFactory, dai, usdc, usdt, whale):
    """
    Deploys, vault and test strategy, mock token and wires them up.
    """

    dai.transfer(caller, 100000*10**dai.decimals(), {"from": whale})
    usdc.transfer(caller, 100000*10**usdc.decimals(), {"from": whale})
    usdt.transfer(caller, 100000*10**usdt.decimals(), {"from": whale})
    accounts[2].transfer(caller, accounts[2].balance()) ## extra eth from some oog error that probs wwas not due to oog
    helper = PoolCreationHelper.deploy(
        vault,
        weightedFactory,
        stableFactory,
        {"from": caller}
    )
    dai.approve(helper, 1000000000000, {"from": caller})
    usdc.approve(helper, 100000000000, {"from": caller})
    usdt.approve(helper, 100000000000, {"from": caller})
    print(helper.address)

    return helper
