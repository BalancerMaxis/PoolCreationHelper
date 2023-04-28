import brownie
from brownie import Contract
import pytest
import json
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

def test_sortForStable(helper):
    addresses = ["0xBA12222222228d8Ba445958a75a0704d566BF2C8", "0xc9aac768d6389d8e548087f1d42ee4ab0e413b5d", "0x3301Ee63Fb29F863f2333Bd4466acb46CD8323E6"]
    rateProviders = ["0xe66B31678d6C16E9ebf358268a790B763C133750", "0x4b4224de04907bd6F1DA2b833567538b754BD4F1", "0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf"]
    exemptFees = [True, False, True]
    amounts = [100, 200, 300]

    expected_sorted_addresses = ["0x3301Ee63Fb29F863f2333Bd4466acb46CD8323E6", "0xBA12222222228d8Ba445958a75a0704d566BF2C8", "0xc9aac768d6389d8e548087f1d42ee4ab0e413b5d"]
    expected_sorted_rateProviders = ["0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf", "0xe66B31678d6C16E9ebf358268a790B763C133750", "0x4b4224de04907bd6F1DA2b833567538b754BD4F1"]
    expected_sorted_exemptFees = [True, True, False]
    expected_sorted_amounts = [300, 100, 200]

    sorted_addresses, sorted_rateProviders, sorted_exemptFees, sorted_amounts = helper.sortForStable(
        addresses, rateProviders, exemptFees, amounts)

    assert sorted_addresses == expected_sorted_addresses
    assert sorted_rateProviders == expected_sorted_rateProviders
    assert sorted_exemptFees == expected_sorted_exemptFees
    assert sorted_amounts == expected_sorted_amounts


def test_deploy(deploy):
    return


def test_create_weighted(weightedPool):
    return

def test_create_stableswap(stablePool):
    return


def test_weighted_init_join_unordered(helper, dai, usdc,usdt, weightedPool, caller, unordered_token_list):
    with brownie.reverts():
        tx = helper.initJoinWeightedPool(weightedPool.getPoolId(), weightedPool.address, unordered_token_list, [1000000, 100000, 100000], {'from': caller})


def test_weighted_init_join(helper, dai, usdc, usdt, weightedPool, caller):
    ## Tokens approved in conftest
    tokens = [usdc, usdt, dai]
    amounts = [10000000, 1000000, 1000]
    sortTokens, rateProviders, sortAmounts, weights = helper.sortForWeighted(tokens, [], amounts, [33,33,34])
    tx = helper.initJoinWeightedPool(weightedPool.getPoolId(), weightedPool.address, sortTokens, sortAmounts, {'from': caller})
    assert weightedPool.balanceOf(caller) > 0
    return tx


def test_stable_init_join(helper, dai, usdc, usdt, stablePool, caller):
    ## Tokens approved in conftest
    tokens = [usdc, usdt, dai]
    amounts = [1000, 1100, 1050]
    exempt = [False, False, False]
    sortTokens, rateProviders, exemptFees, sortAmounts = helper.sortForStable(tokens, [], exempt, amounts)
    print(sortTokens, sortAmounts)
    tx = helper.initJoinStableSwap(stablePool.getPoolId(), stablePool.address, sortTokens, sortAmounts, {'from': caller})
    assert stablePool.balanceOf(caller) > 0
    return tx

def test_with_composable_bpt(helper, dai, usdc, bpt3pool, caller):
    tokens = [bpt3pool, usdc, dai]
    amounts = [100000000, 1000, 1000]
    exempt = [True, False, False]
    rateProviders = [bpt3pool, ZERO_ADDRESS, ZERO_ADDRESS]
    sortTokens, sortedRateProviders, exemptFees, sortAmounts = helper.sortForStable(tokens, rateProviders, exempt, amounts)
    tx = helper.createStablePool("3pool test", "3pool-dai-usdc", sortTokens, 100, sortedRateProviders, exemptFees, 300, b"bpt test", {"from": caller})
    poolAddress = tx.events["PoolCreated"]["pool"]
    with open("abis/IComposibleStable.json", "r") as f:
        pool = Contract.from_abi("IComposableStable", poolAddress, json.load(f))
    helper.initJoinStableSwap(pool.getPoolId(), pool.address, sortTokens, sortAmounts)

def test_create_and_join_weighted(helper, caller, unordered_token_list):
    ## approvals for usdt, usdc and dai in conftest
    amounts = [234235, 12321, 2387843]
    sortTokens, rateProviders, sortAmounts, weights = helper.sortForWeighted(unordered_token_list, [], amounts, [25, 40, 35])
    tx = helper.createAndJoinWeightedPool("stupid 3 pool for arbs", "B-w-3pool", sortTokens, rateProviders, sortAmounts, weights, 300, b"how 'bout some pepper?", {"from": caller})
    return tx

def test_create_and_join_stable(helper, caller, unordered_token_list):
    ## approvals for usdt, usdc and dai in conftest

    amounts = [234235, 234000, 233000]
    sortTokens, rateProviders, exemptFees, sortAmounts = helper.sortForStable(unordered_token_list, [],  [], amounts)
    tx = helper.createAndJoinStableSwap("stable 3 pool for arbs", "B-stable-3pool", sortTokens, 100, rateProviders, exemptFees, sortAmounts, 300, b"how 'bout some pepper?", {"from": caller})
    return tx

def test_2_pools_same_salt(ordered_token_list, caller, weightedFactory, helper, dai, usdc):
    tx = helper.createWeightedPool("Test name", "TEST", ordered_token_list, [], [33, 33, 34], 300, b"same same", {"from": caller})
    poolAddress = tx.events["PoolCreated"]["pool"]
    with open("abis/WeightedPool.json", "r") as f:
        pool = Contract.from_abi("WeightedPool", poolAddress, json.load(f))
    ## second one
    tx = helper.createWeightedPool("Test name", "TEST", ordered_token_list, [], [33, 33, 34], 300, b"same same", {"from": caller})
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
    assert len(tx.events) == 1

def test_change_factory(helper, caller, whale):
    tx = helper.changeFactories(whale, whale, {"from": caller})
    assert len(tx.events) == 1
    assert helper.weightedFactory() == whale
    assert helper.stableFactory() == whale



