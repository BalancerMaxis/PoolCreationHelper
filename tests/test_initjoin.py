import brownie
from brownie import Contract
import time
import pytest
import json


def test_deploy(deploy):
    return


def test_create_weighted(weightedPool):
    return

def test_create_stableswap(stablePool):
    return


def test_weighted_init_join_unordered(helper, dai, usdc,usdt, weightedPool, caller, unordered_token_list):
    with brownie.reverts():
        tx = helper.initJoinWeightedPool(weightedPool.getPoolId(), unordered_token_list, [1000000, 100000, 100000], {'from': caller})


def test_weighted_init_join_ordered(helper, dai, usdc, usdt, weightedPool, caller, ordered_token_list):
    tx = helper.initJoinWeightedPool(weightedPool.getPoolId(), ordered_token_list, [10000, 100000, 10000], {'from': caller})
    assert weightedPool.balanceOf(caller) > 0
    return tx

def test_init_join_use_orderer(helper, dai, usdc, usdt, weightedPool, caller):
    ## Tokens approved in conftest
    tokens = [usdc, usdt, dai]
    amounts = [10000000, 1000000, 1000]
    sortTokens, sortAmounts = helper.sortAmountsByAddresses(tokens, amounts)
    tx = helper.initJoinWeightedPool(weightedPool.getPoolId(), sortTokens, sortAmounts, {'from': caller})
    assert weightedPool.balanceOf(caller) > 0
    return tx

def test_create_and_join_weighted(helper, caller, unordered_token_list):
    ## approvals for usdt, usdc and dai in conftest

    amounts = [234235, 12321, 2387843]
    sortTokens, sortAmounts = helper.sortAmountsByAddresses(unordered_token_list, amounts)
    tx = helper.createAndJoinWeightedPool("stupid 3 pool for arbs", "B-weigted-33USDC/33USDT/3DAI", sortTokens, [], sortAmounts, [33,33,34], 300, b"how 'bout some pepper?")
    return tx

def test_2_pools_same_salt(ordered_token_list, caller, weightedFactory, helper, dai, usdc):
    tx = helper.createWeightedPool("Test name", "TEST", ordered_token_list, [], [33, 33, 34], 300, b"same same")
    poolAddress = tx.events["PoolCreated"]["pool"]
    with open("abis/WeightedPool.json", "r") as f:
        pool = Contract.from_abi("WeightedPool", poolAddress, json.load(f))
    ## second one
    tx = helper.createWeightedPool("Test name", "TEST", ordered_token_list, [], [33, 33, 34], 300, b"same same")
    poolAddress = tx.events["PoolCreated"]["pool"]
    with open("abis/WeightedPool.json", "r") as f:
        pool = Contract.from_abi("WeightedPool", poolAddress, json.load(f))
        
def test_sweep(caller, helper, dai):
    system_balance = dai.balanceOf(caller) + dai.balanceOf(helper)
    caller_balance = dai.balanceOf(caller)
    assert dai.balanceOf(caller) > 0
    dai.transfer(helper, dai.balanceOf(caller), {"from": caller})
    assert dai.balanceOf(caller) == 0
    helper.sweep(dai, caller, {"from": caller})
    assert dai.balanceOf(caller) >= caller_balance
    assert dai.balanceOf(caller) + dai.balanceOf(helper) == system_balance

def test_ownable(helper, owner, caller,dai):
    helper.transferOwnership(owner, {"from": caller})
    dai.transfer(helper, 42069, {"from": caller})
    with brownie.reverts():
        helper.sweep(dai, owner, {"from": caller})
    with brownie.reverts():
        helper.changeFactories(dai.address, dai.address, {"from": caller})
    helper.sweep(dai, owner, {"from": owner})
    tx = helper.changeFactories(dai.address, dai.address, {"from": owner})
    assert len(tx.events) == 1;

def test_change_factory(helper, caller, whale):
    tx = helper.changeFactories(whale, whale, {"from": caller})
    assert len(tx.events) == 1
    assert helper.weightedFactory() == whale;
    assert helper.stableFactory() == whale;

