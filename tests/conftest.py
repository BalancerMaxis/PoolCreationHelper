import pytest
import time
from brownie import (
    interface,
    accounts,
    WeightedPoolInitHelper,
    Contract
)
from dotmap import DotMap
import pytest
import json


##  Accounts
VAULT_ADDRESS = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"
WHALE = "0x25ab7dc4ddcacb6fe75694904db27602175245f1"  ## ARB UNIv3 LDO/WETH
WETH_ADDRESS = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"  ## ARB
LDO_ADDRESS = "0x13Ad51ed4F1B7e9Dc168d8a00cB3f4dDD85EfA60"  ## ARB
WEIGHTED_POOL_FACTORY = "0xc7E5ED1054A24Ef31D827E6F86caA58B3Bc168d7"  ## V4 on ARB
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture()
def ordered_token_list(ldo, weth):
    return [ldo.address, weth.address]

@pytest.fixture()
def unordered_token_list(ldo,weth):
    return [weth.address, ldo.address]

@pytest.fixture()
def whale():
    return WHALE


@pytest.fixture()
def vault():
    return interface.IVault(VAULT_ADDRESS)


@pytest.fixture()
def caller():
    return accounts[0]


@pytest.fixture()
def factory():
    return Contract(WEIGHTED_POOL_FACTORY)


@pytest.fixture()
def ldo():
    return interface.IERC20(LDO_ADDRESS)


@pytest.fixture()
def weth():
    return interface.IERC20(WETH_ADDRESS)


@pytest.fixture()
def pool(ordered_token_list, caller, factory, helper, weth, ldo):
    tx = helper.createWeightedPool("Test name", "TEST", ordered_token_list, [], [50, 50], 300, b"salty")
    poolAddress = tx.events["PoolCreated"]["pool"]
    with open("abis/WeightedPool.json", "r") as f:
        pool = Contract.from_abi("WeightedPool", poolAddress, json.load(f))
    return pool


@pytest.fixture()
def helper(deploy):
    return deploy


@pytest.fixture()
def deploy(caller, vault, factory, ldo, weth, whale):
    """
    Deploys, vault and test strategy, mock token and wires them up.
    """

    ldo.transfer(caller, 1000*10**18, {"from": whale})
    weth.transfer(caller, 10*10**18, {"from": whale})

    helper = WeightedPoolInitHelper.deploy(
        vault,
        factory,
        {"from": caller}
    )

    print(helper.address)

    return helper


